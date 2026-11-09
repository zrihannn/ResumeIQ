from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import hash_password
from app.models.entities import Application, Candidate, Interview, Job, User


def test_public_candidate_and_private_recruiter_boundaries(client):
    previous = settings.auth_enabled
    settings.auth_enabled = True
    try:
        registration = client.post("/api/auth/register", json={
            "display_name": "Public Candidate",
            "email": "candidate.portal@example.com",
            "password": "candidate-portal-password-123",
        })
        assert registration.status_code == 201, registration.text
        candidate_headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}

        assert client.get("/api/public/dashboard").status_code == 200
        assert client.get("/api/public/roles").status_code == 200
        assert client.get("/api/candidates", headers=candidate_headers).status_code == 403
        assert client.get("/api/applications", headers=candidate_headers).status_code == 403

        profile = client.get("/api/candidate/me", headers=candidate_headers)
        assert profile.status_code == 200
        candidate_id = profile.json()["candidate"]["id"]

        updated = client.patch("/api/candidate/me", headers=candidate_headers, json={
            "headline": "Backend and applied AI engineer",
            "phone": "+91 99999 00000",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "projects": [{"name": "ResumeIQ", "technologies": ["FastAPI", "React"]}],
        })
        assert updated.status_code == 200, updated.text

        hidden = client.get("/api/public/candidates")
        assert hidden.status_code == 200
        assert all(item["id"] != candidate_id for item in hidden.json())

        consent = client.patch("/api/candidate/me/public-profile", headers=candidate_headers, json={
            "enabled": True,
            "display_name": "Public Candidate",
        })
        assert consent.status_code == 200

        public_list = client.get("/api/public/candidates")
        assert public_list.status_code == 200
        public_candidate = next(item for item in public_list.json() if item["id"] == candidate_id)
        assert public_candidate["display_name"] == "Public Candidate"
        assert "email" not in public_candidate
        assert "phone" not in public_candidate
        assert "projects" in public_candidate

        db = client.test_db()
        try:
            job = Job(
                title="Junior Backend Engineer",
                description="Build secure APIs and data services for a recruitment platform.",
                status="open",
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id
        finally:
            db.close()

        public_role = client.get(f"/api/public/roles/{job_id}")
        assert public_role.status_code == 200
        assert public_role.json()["title"] == "Junior Backend Engineer"

        application = client.post(f"/api/candidate/me/applications?job_id={job_id}", headers=candidate_headers)
        assert application.status_code == 201, application.text
        assert client.get("/api/candidate/me/applications", headers=candidate_headers).json()[0]["stage"] == "new"
        assert client.post(f"/api/candidate/me/applications?job_id={job_id}", headers=candidate_headers).status_code == 409
    finally:
        settings.auth_enabled = previous


def test_interviewer_can_only_review_assigned_interviews(client):
    previous = settings.auth_enabled
    settings.auth_enabled = True
    db = client.test_db()
    try:
        interviewer = User(
            email="assigned.interviewer@example.com",
            display_name="Assigned Interviewer",
            password_hash=hash_password("interviewer-password-123"),
            role="interviewer",
        )
        first_candidate = Candidate(full_name="Candidate One", email="one@example.com", phone="1111111111")
        second_candidate = Candidate(full_name="Candidate Two", email="two@example.com", phone="2222222222")
        job = Job(title="Platform Engineer", description="Build dependable platform services and APIs.")
        db.add_all([interviewer, first_candidate, second_candidate, job])
        db.flush()
        first_app = Application(candidate_id=first_candidate.id, job_id=job.id)
        second_app = Application(candidate_id=second_candidate.id, job_id=job.id)
        db.add_all([first_app, second_app])
        db.flush()
        assigned = Interview(
            application_id=first_app.id,
            title="Technical interview",
            scheduled_at=datetime(2026, 11, 10, 10, 0, tzinfo=timezone.utc),
            interviewers=["assigned.interviewer@example.com"],
            scorecard={"private": "initial"},
            notes="Private reviewer context",
        )
        unassigned = Interview(
            application_id=second_app.id,
            title="Another interview",
            scheduled_at=datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc),
            interviewers=["someone.else@example.com"],
        )
        db.add_all([assigned, unassigned])
        db.commit()
        assigned_id = assigned.id
    finally:
        db.close()

    try:
        login = client.post("/api/auth/login", json={
            "email": "assigned.interviewer@example.com",
            "password": "interviewer-password-123",
        })
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        listing = client.get("/api/interviewer/me/interviews", headers=headers)
        assert listing.status_code == 200
        assert len(listing.json()) == 1
        assert listing.json()[0]["candidate_name"] == "Candidate One"

        assert client.get("/api/candidates", headers=headers).status_code == 403
        detail = client.get(f"/api/interviewer/me/interviews/{assigned_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["candidate"]["email"] == "one@example.com"

        saved = client.patch(f"/api/interviewer/me/interviews/{assigned_id}", headers=headers, json={
            "status": "completed",
            "scorecard": {"recommendation": "yes", "technical": "Strong fundamentals"},
            "notes": "Proceed to next round.",
        })
        assert saved.status_code == 200, saved.text
        assert saved.json()["scorecard"]["recommendation"] == "yes"
    finally:
        settings.auth_enabled = previous
