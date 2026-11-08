from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import auth_guard, require_roles
from app.db.session import get_db
from app.models.entities import ActivityEvent, Application, Candidate, Interview, Job, MatchResult, ResumeDocument, User
from app.schemas.dto import ApplicationCreate, ApplicationUpdate, CandidateUpdate, InterviewCreate, InterviewUpdate, JobCreate, JobUpdate
from app.services.document_reader import read_document
from app.services.matcher import calculate_match
from app.services.parser import PARSER_VERSION, parse_resume
from app.services.serializers import activity_out, application_out, candidate_out, document_out, interview_out, job_out, match_out

router = APIRouter(prefix="/api", dependencies=[Depends(auth_guard)])
PIPELINE_STAGES = ["new", "screening", "interview", "offer", "hired", "rejected"]
ALLOWED_DOWNLOAD_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def log_event(db: Session, entity_type: str, entity_id: int, action: str, description: str, metadata: dict | None = None, actor: User | None = None) -> None:
    db.add(ActivityEvent(
        entity_type=entity_type, entity_id=entity_id, action=action,
        description=description, metadata_json=metadata or {},
        actor_user_id=actor.id if actor else None, actor_email=actor.email if actor else None,
    ))


def _candidate_profile(candidate: Candidate) -> dict:
    return {
        "full_name": candidate.full_name, "email": candidate.email, "phone": candidate.phone,
        "location": candidate.location, "headline": candidate.headline, "summary": candidate.summary,
        "total_experience_years": candidate.total_experience_years, "skills": candidate.skills or [],
        "soft_skills": candidate.soft_skills or [], "tools": candidate.tools or [],
        "experience": candidate.experience or [], "education": candidate.education or [],
        "projects": candidate.projects or [], "certifications": candidate.certifications or [],
        "achievements": candidate.achievements or [], "publications": candidate.publications or [],
        "languages": candidate.languages or [], "volunteering": candidate.volunteering or [], "links": candidate.links or {},
    }


def _job_profile(job: Job) -> dict:
    return {
        "title": job.title, "description": job.description, "responsibilities": job.responsibilities or [],
        "required_skills": job.required_skills or [], "preferred_skills": job.preferred_skills or [],
        "minimum_experience": job.minimum_experience, "maximum_experience": job.maximum_experience,
        "education_requirement": job.education_requirement,
    }


def _safe_name(filename: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)[:180] or "resume"


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database connection is unavailable.") from exc
    return {"status": "ok", "service": "ResumeIQ API", "database": "ok", "parser_version": PARSER_VERSION, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    open_jobs = db.query(func.count(Job.id)).filter(Job.status == "open").scalar() or 0
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    total_applications = db.query(func.count(Application.id)).scalar() or 0
    active_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "scheduled").scalar() or 0
    match_count = db.query(func.count(MatchResult.id)).scalar() or 0
    average_score = db.query(func.avg(MatchResult.overall_score)).scalar() or 0
    stage_counts = {stage: db.query(func.count(Application.id)).filter(Application.stage == stage).scalar() or 0 for stage in PIPELINE_STAGES}
    recent_candidates = db.query(Candidate).order_by(desc(Candidate.created_at)).limit(6).all()
    recent_activity = db.query(ActivityEvent).order_by(desc(ActivityEvent.created_at)).limit(8).all()
    skills: dict[str, int] = {}
    for item in db.query(Candidate.skills).all():
        for skill in item[0] or []:
            skills[skill] = skills.get(skill, 0) + 1
    return {
        "total_candidates": total_candidates, "open_jobs": open_jobs, "total_jobs": total_jobs,
        "total_applications": total_applications, "active_interviews": active_interviews,
        "matches_computed": match_count, "average_match_score": round(float(average_score), 1),
        "pipeline": stage_counts,
        "top_skills": sorted([{"skill": key, "count": value} for key, value in skills.items()], key=lambda item: item["count"], reverse=True)[:10],
        "recent_candidates": [candidate_out(item, include_profile=False) for item in recent_candidates],
        "recent_activity": [activity_out(item) for item in recent_activity],
    }


@router.get("/candidates")
def list_candidates(q: str = "", skill: str = "", needs_review: bool | None = None, limit: int = Query(default=100, ge=1, le=300), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)):
    query = db.query(Candidate)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(Candidate.full_name.ilike(term), Candidate.email.ilike(term), Candidate.headline.ilike(term), Candidate.location.ilike(term)))
    results = query.order_by(desc(Candidate.updated_at)).offset(offset).limit(limit).all()
    output = [candidate_out(item, include_profile=False) for item in results]
    if skill.strip():
        needle = skill.strip().lower()
        output = [item for item in output if any(needle in value.lower() for value in item["skills"])]
    if needs_review is not None:
        output = [item for item in output if bool((item.get("extraction_quality") or {}).get("requires_review")) is needs_review]
    return output


@router.post("/candidates/upload", status_code=status.HTTP_201_CREATED)
async def upload_candidate(file: UploadFile = File(...), db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    filename = _safe_name(file.filename or "resume")
    content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Resume exceeds the {settings.max_upload_mb} MB upload limit.")
    checksum = hashlib.sha256(content).hexdigest()
    duplicate_document = db.query(ResumeDocument).filter(ResumeDocument.checksum_sha256 == checksum).first()
    if duplicate_document:
        raise HTTPException(409, detail={"message": "This exact resume file has already been uploaded.", "candidate_id": duplicate_document.candidate_id})
    try:
        document_content = read_document(filename, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if len(document_content.text.strip()) < 35:
        raise HTTPException(422, "Too little text could be extracted. Try a text-based PDF, a clearer scan with OCR enabled, or a DOCX file.")
    parsed = parse_resume(document_content.text, document_content.links, filename)
    identity = parsed["identity"]
    email = identity.get("email")
    if email:
        duplicate_candidate = db.query(Candidate).filter(func.lower(Candidate.email) == email.lower()).first()
        if duplicate_candidate:
            raise HTTPException(409, detail={"message": "A candidate with this email already exists. Review the existing profile before adding another record.", "candidate_id": duplicate_candidate.id, "candidate_name": duplicate_candidate.full_name})

    profile = parsed["professional_profile"]
    skill_data = parsed["skills"]
    name = identity.get("full_name") or "Needs review"
    candidate = Candidate(
        full_name=name, email=email, phone=identity.get("phone"), location=identity.get("location"),
        headline=profile.get("headline"), summary=profile.get("summary"), total_experience_years=profile.get("total_experience_years"),
        skills=skill_data.get("technical", []), soft_skills=skill_data.get("soft", []), tools=skill_data.get("tools_and_platforms", []),
        experience=parsed.get("experience", []), education=parsed.get("education", []), projects=parsed.get("projects", []),
        certifications=parsed.get("certifications", []), achievements=parsed.get("achievements", []),
        publications=parsed.get("publications", []), languages=parsed.get("languages", []),
        volunteering=parsed.get("volunteering", []), links=identity.get("links", {}), extraction_quality=parsed.get("quality", {}),
    )
    stored_filename = f"{secrets.token_hex(18)}{Path(filename).suffix.lower()}"
    settings.resume_storage_dir.mkdir(parents=True, exist_ok=True)
    stored_path = settings.resume_storage_dir / stored_filename
    try:
        stored_path.write_bytes(content)
        db.add(candidate)
        db.flush()
        document = ResumeDocument(
            candidate_id=candidate.id, original_filename=filename, stored_filename=stored_filename,
            content_type=content_type, checksum_sha256=checksum, file_size=len(content),
            page_count=document_content.page_count, parser_version=PARSER_VERSION,
            extraction_method=document_content.extraction_method, extracted_text=document_content.text,
            parsed_payload=parsed, warnings=document_content.warnings + parsed["quality"]["warnings"],
        )
        db.add(document)
        db.flush()
        log_event(db, "candidate", candidate.id, "resume_uploaded", f"Resume uploaded and parsed for {candidate.full_name}.", {"document_id": document.id, "filename": filename, "parser_version": PARSER_VERSION}, _actor)
        db.commit()
        db.refresh(candidate)
        db.refresh(document)
    except IntegrityError as exc:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(409, "This resume conflicts with an existing candidate or document record.") from exc
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise
    return {"candidate": candidate_out(candidate), "document": document_out(document), "parsed_profile": parsed, "warnings": document.warnings or []}


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).options(joinedload(Candidate.documents)).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate not found.")
    documents = [document_out(item) for item in candidate.documents]
    latest_payload = candidate.documents[-1].parsed_payload if candidate.documents else {}
    return {"candidate": candidate_out(candidate), "documents": documents, "field_evidence": latest_payload.get("field_evidence", {}), "sections_detected": latest_payload.get("sections_detected", [])}


@router.patch("/candidates/{candidate_id}")
def update_candidate(candidate_id: int, payload: CandidateUpdate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found.")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(candidate, field, value)
    quality = dict(candidate.extraction_quality or {})
    quality["manually_reviewed"] = True
    quality["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    quality["manually_corrected_fields"] = sorted(set(quality.get("manually_corrected_fields", [])) | set(changes))
    candidate.extraction_quality = quality
    log_event(db, "candidate", candidate.id, "profile_corrected", f"Candidate profile updated: {candidate.full_name}.", {"fields": list(changes)}, _actor)
    db.commit()
    db.refresh(candidate)
    return candidate_out(candidate)


@router.get("/candidates/{candidate_id}/documents")
def candidate_documents(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found.")
    docs = db.query(ResumeDocument).filter(ResumeDocument.candidate_id == candidate_id).order_by(desc(ResumeDocument.created_at)).all()
    return [document_out(item) for item in docs]


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(ResumeDocument, document_id)
    if not document:
        raise HTTPException(404, "Resume document not found.")
    path = settings.resume_storage_dir / document.stored_filename
    if not path.is_file():
        raise HTTPException(404, "The stored resume file is missing.")
    return FileResponse(path, media_type=document.content_type, filename=document.original_filename)


@router.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    candidate = db.query(Candidate).options(joinedload(Candidate.documents)).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate not found.")
    files = [settings.resume_storage_dir / item.stored_filename for item in candidate.documents]
    name = candidate.full_name
    log_event(db, "candidate", candidate.id, "candidate_deleted", f"Deleted candidate profile: {name}.", {"document_count": len(files)}, _actor)
    db.delete(candidate)
    db.commit()
    for path in files:
        path.unlink(missing_ok=True)
    return {"deleted": True, "candidate_id": candidate_id, "candidate_name": name}


@router.get("/jobs")
def list_jobs(status_filter: str = Query(default="", alias="status"), q: str = "", db: Session = Depends(get_db)):
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(Job.title.ilike(term), Job.department.ilike(term), Job.description.ilike(term)))
    return [job_out(item) for item in query.order_by(desc(Job.created_at)).all()]


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    job = Job(**payload.model_dump())
    db.add(job)
    db.flush()
    log_event(db, "job", job.id, "job_created", f"Created role: {job.title}.", actor=_actor)
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).options(joinedload(Job.applications)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found.")
    return job_out(job)


@router.patch("/jobs/{job_id}")
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(job, field, value)
    log_event(db, "job", job.id, "job_updated", f"Updated role: {job.title}.", {"fields": list(changes)}, _actor)
    db.commit()
    db.refresh(job)
    return job_out(job)


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    title = job.title
    log_event(db, "job", job.id, "job_deleted", f"Deleted role: {title}.", actor=_actor)
    db.delete(job)
    db.commit()
    return {"deleted": True, "job_id": job_id, "job_title": title}


@router.get("/applications")
def list_applications(job_id: int | None = None, stage: str = "", db: Session = Depends(get_db)):
    query = db.query(Application).options(joinedload(Application.candidate), joinedload(Application.job))
    if job_id is not None:
        query = query.filter(Application.job_id == job_id)
    if stage:
        if stage not in PIPELINE_STAGES:
            raise HTTPException(422, f"Stage must be one of: {', '.join(PIPELINE_STAGES)}")
        query = query.filter(Application.stage == stage)
    items = query.order_by(desc(Application.updated_at)).all()
    return [application_out(item) for item in items]


@router.post("/applications", status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter", "reviewer"))):
    candidate = db.get(Candidate, payload.candidate_id)
    job = db.get(Job, payload.job_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found.")
    if not job:
        raise HTTPException(404, "Job not found.")
    item = Application(**payload.model_dump())
    db.add(item)
    try:
        db.flush()
        log_event(db, "application", item.id, "application_created", f"{candidate.full_name} added to {job.title}.", actor=_actor)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This candidate is already in the pipeline for this role.") from exc
    item = db.query(Application).options(joinedload(Application.candidate), joinedload(Application.job)).filter(Application.id == item.id).one()
    return application_out(item)


@router.patch("/applications/{application_id}")
def update_application(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter", "reviewer"))):
    item = db.query(Application).options(joinedload(Application.candidate), joinedload(Application.job)).filter(Application.id == application_id).first()
    if not item:
        raise HTTPException(404, "Application not found.")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide at least one field to update.")
    for field, value in changes.items():
        if value is not None:
            setattr(item, field, value)
    log_event(db, "application", item.id, "application_updated", f"Updated application for {item.candidate.full_name}.", {"fields": list(changes), "stage": item.stage}, _actor)
    db.commit()
    db.refresh(item)
    return application_out(item)


@router.delete("/applications/{application_id}")
def delete_application(application_id: int, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter"))):
    item = db.get(Application, application_id)
    if not item:
        raise HTTPException(404, "Application not found.")
    log_event(db, "application", item.id, "application_deleted", f"Deleted application for {item.candidate.full_name}.", {"job_title": item.job.title}, _actor)
    db.delete(item)
    db.commit()
    return {"deleted": True, "application_id": application_id}


@router.get("/matches/jobs/{job_id}")
def list_job_matches(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    rows = db.query(MatchResult, Candidate).join(Candidate, Candidate.id == MatchResult.candidate_id).filter(MatchResult.job_id == job_id).order_by(desc(MatchResult.overall_score)).all()
    return [match_out(match, candidate) for match, candidate in rows]


@router.post("/matches/jobs/{job_id}/run")
def run_job_matching(job_id: int, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter", "reviewer"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    candidates = db.query(Candidate).all()
    if not candidates:
        raise HTTPException(400, "Upload at least one resume before running matching.")
    existing = {row.candidate_id: row for row in db.query(MatchResult).filter(MatchResult.job_id == job_id).all()}
    job_profile = _job_profile(job)
    output = []
    for candidate in candidates:
        scored = calculate_match(_candidate_profile(candidate), job_profile)
        row = existing.get(candidate.id)
        if row is None:
            row = MatchResult(candidate_id=candidate.id, job_id=job.id, **scored)
            db.add(row)
        else:
            for field, value in scored.items():
                setattr(row, field, value)
            row.computed_at = datetime.now(timezone.utc)
        output.append((row, candidate))
    log_event(db, "job", job.id, "matching_run", f"Matched {len(candidates)} candidates against {job.title}.", {"candidate_count": len(candidates)}, _actor)
    db.commit()
    for row, _ in output:
        db.refresh(row)
    return {"job_id": job.id, "job_title": job.title, "candidate_count": len(candidates), "results": [match_out(row, candidate) for row, candidate in sorted(output, key=lambda pair: pair[0].overall_score, reverse=True)]}


@router.get("/interviews")
def list_interviews(status_filter: str = Query(default="", alias="status"), db: Session = Depends(get_db)):
    query = db.query(Interview).options(joinedload(Interview.application).joinedload(Application.candidate), joinedload(Interview.application).joinedload(Application.job))
    if status_filter:
        query = query.filter(Interview.status == status_filter)
    items = query.order_by(Interview.scheduled_at.asc()).all()
    return [interview_out(item) for item in items]


@router.post("/interviews", status_code=status.HTTP_201_CREATED)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter", "reviewer"))):
    application = db.get(Application, payload.application_id)
    if not application:
        raise HTTPException(404, "Application not found.")
    item = Interview(**payload.model_dump())
    db.add(item)
    db.flush()
    log_event(db, "interview", item.id, "interview_scheduled", f"Scheduled {item.title} for {application.candidate.full_name}.", actor=_actor)
    db.commit()
    item = db.query(Interview).options(joinedload(Interview.application).joinedload(Application.candidate), joinedload(Interview.application).joinedload(Application.job)).filter(Interview.id == item.id).one()
    return interview_out(item)


@router.patch("/interviews/{interview_id}")
def update_interview(interview_id: int, payload: InterviewUpdate, db: Session = Depends(get_db), _actor=Depends(require_roles("admin", "recruiter", "reviewer"))):
    item = db.query(Interview).options(joinedload(Interview.application).joinedload(Application.candidate), joinedload(Interview.application).joinedload(Application.job)).filter(Interview.id == interview_id).first()
    if not item:
        raise HTTPException(404, "Interview not found.")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(item, field, value)
    log_event(db, "interview", item.id, "interview_updated", f"Updated interview for {item.application.candidate.full_name}.", {"fields": list(changes)}, _actor)
    db.commit()
    db.refresh(item)
    return interview_out(item)


@router.get("/activity")
def list_activity(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    items = db.query(ActivityEvent).order_by(desc(ActivityEvent.created_at)).limit(limit).all()
    return [activity_out(item) for item in items]
