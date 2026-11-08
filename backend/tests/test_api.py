from tests.factories import resume_docx


def upload(client, name="Alex Morgan", email="alex.morgan@example.com"):
    return client.post("/api/candidates/upload", files={"file": ("alex_resume.docx", resume_docx(name, email), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})


def create_job(client):
    return client.post("/api/jobs", json={
        "title": "Python Backend Engineer", "department": "Engineering", "location": "Remote",
        "work_mode": "remote", "employment_type": "full-time",
        "description": "Build and maintain backend services, APIs and data integrations with Python and PostgreSQL.",
        "responsibilities": ["Design APIs", "Improve database performance"],
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "preferred_skills": ["Redis"], "minimum_experience": 2,
        "education_requirement": "B.Tech",
    })


def test_health_dashboard_and_job_crud(client):
    assert client.get("/api/health").status_code == 200
    dashboard = client.get("/api/dashboard").json()
    assert dashboard["total_candidates"] == 0
    created = create_job(client)
    assert created.status_code == 201, created.text
    job_id = created.json()["id"]
    assert client.get("/api/jobs").json()[0]["title"] == "Python Backend Engineer"
    updated = client.patch(f"/api/jobs/{job_id}", json={"status": "paused"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"


def test_resume_upload_and_duplicate_protection(client):
    response = upload(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["candidate"]["full_name"] == "Alex Morgan"
    assert "Python" in payload["candidate"]["skills"]
    assert payload["document"]["parser_version"]
    assert payload["parsed_profile"]["field_evidence"]["email"]
    assert payload["parsed_profile"]["field_evidence"]["email"]["confidence"] >= 0.9
    duplicate_file = client.post("/api/candidates/upload", files={"file": ("alex_resume.docx", resume_docx(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert duplicate_file.status_code == 409
    duplicate_email = upload(client, "Alex M", "alex.morgan@example.com")
    assert duplicate_email.status_code == 409


def test_candidate_correction_and_delete(client):
    created = upload(client).json()["candidate"]
    candidate_id = created["id"]
    updated = client.patch(f"/api/candidates/{candidate_id}", json={"headline": "Senior Python Engineer", "skills": ["Python", "FastAPI"]})
    assert updated.status_code == 200
    assert updated.json()["headline"] == "Senior Python Engineer"
    assert updated.json()["extraction_quality"]["manually_reviewed"] is True
    assert client.delete(f"/api/candidates/{candidate_id}").status_code == 200
    assert client.get(f"/api/candidates/{candidate_id}").status_code == 404


def test_matching_and_application_pipeline(client):
    candidate = upload(client).json()["candidate"]
    job = create_job(client).json()
    match_run = client.post(f"/api/matches/jobs/{job['id']}/run")
    assert match_run.status_code == 200, match_run.text
    result = match_run.json()["results"][0]
    assert 0 <= result["overall_score"] <= 100
    assert "Python" in result["matched_skills"]
    application = client.post("/api/applications", json={"candidate_id": candidate["id"], "job_id": job["id"], "notes": "Review profile"})
    assert application.status_code == 201, application.text
    duplicate = client.post("/api/applications", json={"candidate_id": candidate["id"], "job_id": job["id"]})
    assert duplicate.status_code == 409
    updated = client.patch(f"/api/applications/{application.json()['id']}", json={"stage": "interview", "notes": "Technical screen"})
    assert updated.status_code == 200
    assert updated.json()["stage"] == "interview"


def test_interview_scheduling_and_activity(client):
    candidate = upload(client).json()["candidate"]
    job = create_job(client).json()
    application = client.post("/api/applications", json={"candidate_id": candidate["id"], "job_id": job["id"]}).json()
    interview = client.post("/api/interviews", json={
        "application_id": application["id"], "title": "Technical interview", "interview_type": "technical",
        "scheduled_at": "2026-11-10T10:00:00+05:30", "duration_minutes": 60,
        "interviewers": ["Recruiter", "Engineering Lead"],
    })
    assert interview.status_code == 201, interview.text
    assert interview.json()["candidate_name"] == "Alex Morgan"
    feedback = client.patch(f"/api/interviews/{interview.json()['id']}", json={
        "status": "completed",
        "scorecard": {"technical": 4, "problem_solving": 5, "communication": 4, "overall": 4, "recommendation": "lean_yes"},
        "notes": "Strong API design discussion with clear trade-offs.",
    })
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["scorecard"]["problem_solving"] == 5
    assert feedback.json()["status"] == "completed"
    assert len(client.get("/api/activity").json()) >= 4


def test_upload_rejects_fake_pdf_signature(client):
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("not_really_a_resume.pdf", b"this is not a PDF file", "application/pdf")},
    )
    assert response.status_code == 422
    assert "not a valid PDF" in response.json()["detail"]



def test_upload_rejects_corrupt_pdf_with_validation_error(client):
    response = client.post(
        "/api/candidates/upload",
        files={"file": ("damaged.pdf", b"%PDF-1.7\nnot-a-real-pdf", "application/pdf")},
    )
    assert response.status_code == 422
    assert "PDF could not be read" in response.json()["detail"]
