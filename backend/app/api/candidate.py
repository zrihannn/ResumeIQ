from __future__ import annotations

import hashlib
import mimetypes
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import require_roles
from app.db.session import get_db
from app.models.entities import Application, Candidate, CandidateAccount, Interview, Job, ResumeDocument, User
from app.services.document_reader import read_document
from app.services.parser import PARSER_VERSION, parse_resume
from app.services.resume_storage import delete_resume, read_resume, save_resume
from app.services.serializers import candidate_out, document_out

router = APIRouter(prefix="/api/candidate", tags=["Candidate portal"], dependencies=[Depends(require_roles("candidate"))])


class CandidateProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=60)
    location: str | None = Field(default=None, max_length=180)
    headline: str | None = Field(default=None, max_length=240)
    summary: str | None = Field(default=None, max_length=4000)
    total_experience_years: float | None = Field(default=None, ge=0, le=60)
    skills: list[str] | None = None
    soft_skills: list[str] | None = None
    tools: list[str] | None = None
    experience: list[dict] | None = None
    education: list[dict] | None = None
    projects: list[dict] | None = None
    certifications: list[dict] | None = None
    achievements: list[dict] | None = None
    publications: list[dict] | None = None
    languages: list[dict] | None = None
    volunteering: list[dict] | None = None
    links: dict[str, str] | None = None


class PublicProfileUpdate(BaseModel):
    enabled: bool
    display_name: str | None = Field(default=None, max_length=120)


def _owned_candidate(db: Session, user: User) -> tuple[Candidate, CandidateAccount]:
    account = db.query(CandidateAccount).filter(CandidateAccount.user_id == user.id).first()
    if not account:
        raise HTTPException(404, "Candidate profile is not linked to this account.")
    candidate = db.query(Candidate).options(joinedload(Candidate.documents)).filter(Candidate.id == account.candidate_id).first()
    if not candidate:
        raise HTTPException(404, "Candidate profile not found.")
    return candidate, account


def _safe_name(filename: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)[:180] or "resume"


@router.get("/me")
def get_my_profile(user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, account = _owned_candidate(db, user)
    documents = sorted(candidate.documents, key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return {
        "candidate": candidate_out(candidate),
        "documents": [document_out(item) for item in documents],
        "public_profile": {"enabled": account.public_profile, "display_name": account.public_name},
    }


@router.patch("/me")
def update_my_profile(payload: CandidateProfileUpdate, user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide at least one profile field to update.")
    for field, value in changes.items():
        if value is not None:
            setattr(candidate, field, value)
    quality = dict(candidate.extraction_quality or {})
    quality["manually_reviewed"] = True
    quality["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    quality["candidate_edited_fields"] = sorted(set(quality.get("candidate_edited_fields", [])) | set(changes))
    candidate.extraction_quality = quality
    db.commit()
    db.refresh(candidate)
    return candidate_out(candidate)


@router.patch("/me/public-profile")
def update_public_profile(payload: PublicProfileUpdate, user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    _, account = _owned_candidate(db, user)
    account.public_profile = payload.enabled
    account.public_name = (payload.display_name or "").strip() or None
    db.commit()
    return {"enabled": account.public_profile, "display_name": account.public_name}


@router.post("/me/resumes", status_code=status.HTTP_201_CREATED)
async def upload_my_resume(file: UploadFile = File(...), user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    filename = _safe_name(file.filename or "resume")
    if not filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(415, "Only PDF and DOCX resumes are supported.")
    content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Resume exceeds the {settings.max_upload_mb} MB upload limit.")
    checksum = hashlib.sha256(content).hexdigest()
    duplicate = db.query(ResumeDocument).filter(ResumeDocument.checksum_sha256 == checksum).first()
    if duplicate:
        raise HTTPException(409, "This exact resume file has already been uploaded.")
    try:
        document_content = read_document(filename, content)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    if len(document_content.text.strip()) < 35:
        raise HTTPException(422, "Too little text could be extracted from this resume.")
    parsed = parse_resume(document_content.text, document_content.links, filename)
    parsed_email = (parsed.get("identity") or {}).get("email")
    if parsed_email and parsed_email.lower() != (candidate.email or "").lower():
        duplicate_candidate = db.query(Candidate).filter(func.lower(Candidate.email) == parsed_email.lower(), Candidate.id != candidate.id).first()
        if duplicate_candidate:
            raise HTTPException(409, "This resume appears to belong to a different candidate record. Contact the recruitment team.")
    identity = parsed.get("identity") or {}
    profile = parsed.get("professional_profile") or {}
    skill_data = parsed.get("skills") or {}
    name = identity.get("full_name")
    if name and not candidate.full_name:
        candidate.full_name = name
    updates = {
        "phone": identity.get("phone"),
        "location": identity.get("location"),
        "headline": profile.get("headline"),
        "summary": profile.get("summary"),
        "total_experience_years": profile.get("total_experience_years"),
        "skills": skill_data.get("technical", []),
        "soft_skills": skill_data.get("soft", []),
        "tools": skill_data.get("tools_and_platforms", []),
        "experience": parsed.get("experience", []),
        "education": parsed.get("education", []),
        "projects": parsed.get("projects", []),
        "certifications": parsed.get("certifications", []),
        "achievements": parsed.get("achievements", []),
        "publications": parsed.get("publications", []),
        "languages": parsed.get("languages", []),
        "volunteering": parsed.get("volunteering", []),
        "links": identity.get("links", {}),
        "extraction_quality": parsed.get("quality", {}),
    }
    for field, value in updates.items():
        if value is not None and value != [] and value != {}:
            setattr(candidate, field, value)
    stored_filename = f"{secrets.token_hex(18)}{Path(filename).suffix.lower()}"
    stored = False
    try:
        save_resume(stored_filename, content, content_type)
        stored = True
        db.add(candidate)
        db.flush()
        document = ResumeDocument(
            candidate_id=candidate.id,
            original_filename=filename,
            stored_filename=stored_filename,
            content_type=content_type,
            checksum_sha256=checksum,
            file_size=len(content),
            page_count=document_content.page_count,
            parser_version=PARSER_VERSION,
            extraction_method=document_content.extraction_method,
            extracted_text=document_content.text,
            parsed_payload=parsed,
            warnings=document_content.warnings + parsed["quality"]["warnings"],
        )
        db.add(document)
        db.commit()
        db.refresh(candidate)
        db.refresh(document)
    except IntegrityError as exc:
        db.rollback()
        if stored:
            try:
                delete_resume(stored_filename)
            except Exception:
                pass
        raise HTTPException(409, "This resume conflicts with an existing document record.") from exc
    except Exception:
        db.rollback()
        if stored:
            try:
                delete_resume(stored_filename)
            except Exception:
                pass
        raise
    return {"candidate": candidate_out(candidate), "document": document_out(document), "parsed_profile": parsed}


@router.delete("/me/resumes/{document_id}")
def delete_my_resume(document_id: int, user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    document = db.query(ResumeDocument).filter(ResumeDocument.id == document_id, ResumeDocument.candidate_id == candidate.id).first()
    if not document:
        raise HTTPException(404, "Resume document not found.")
    stored_filename = document.stored_filename
    db.delete(document)
    db.commit()
    try:
        delete_resume(stored_filename)
    except Exception:
        pass
    return {"deleted": True, "document_id": document_id}


@router.get("/me/resumes/{document_id}/download")
def download_my_resume(document_id: int, user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    document = db.query(ResumeDocument).filter(ResumeDocument.id == document_id, ResumeDocument.candidate_id == candidate.id).first()
    if not document:
        raise HTTPException(404, "Resume document not found.")
    content = read_resume(document.stored_filename)
    if content is None:
        raise HTTPException(404, "The stored resume file is missing.")
    return Response(
        content=content,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{_safe_name(document.original_filename)}"'},
    )


@router.get("/me/applications")
def list_my_applications(user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    items = (
        db.query(Application)
        .options(joinedload(Application.job))
        .filter(Application.candidate_id == candidate.id)
        .order_by(desc(Application.created_at))
        .all()
    )
    return [{
        "id": item.id,
        "job_id": item.job_id,
        "job_title": item.job.title,
        "department": item.job.department,
        "location": item.job.location,
        "stage": item.stage,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    } for item in items]


@router.post("/me/applications", status_code=status.HTTP_201_CREATED)
def apply_to_role(job_id: int, user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    job = db.query(Job).filter(Job.id == job_id, Job.status == "open").first()
    if not job:
        raise HTTPException(404, "This role is no longer accepting applications.")
    item = Application(candidate_id=candidate.id, job_id=job.id, stage="new", source="candidate_portal", notes="")
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "You have already applied to this role.") from exc
    db.refresh(item)
    return {"id": item.id, "job_id": job.id, "job_title": job.title, "stage": item.stage, "created_at": item.created_at}


@router.get("/me/interviews")
def list_my_interviews(user: User = Depends(require_roles("candidate")), db: Session = Depends(get_db)):
    candidate, _ = _owned_candidate(db, user)
    items = (
        db.query(Interview)
        .join(Application, Interview.application_id == Application.id)
        .options(joinedload(Interview.application).joinedload(Application.job))
        .filter(Application.candidate_id == candidate.id)
        .order_by(Interview.scheduled_at.asc())
        .all()
    )
    return [{
        "id": item.id,
        "application_id": item.application_id,
        "job_title": item.application.job.title,
        "title": item.title,
        "interview_type": item.interview_type,
        "scheduled_at": item.scheduled_at,
        "duration_minutes": item.duration_minutes,
        "location_or_link": item.location_or_link,
        "status": item.status,
    } for item in items]
