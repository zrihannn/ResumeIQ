from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Application, Candidate, CandidateAccount, Interview, Job, MatchResult

router = APIRouter(prefix="/api/public", tags=["Public portal"])


def _masked_name(value: str | None) -> str:
    parts = [part for part in (value or "Candidate").split() if part]
    if len(parts) == 1:
        return parts[0][0] + "Candidate"
    return f"{parts[0]} {parts[-1][0]}."


def _public_profile(candidate: Candidate, account: CandidateAccount) -> dict:
    return {
        "id": candidate.id,
        "display_name": (account.public_name or "").strip() or _masked_name(candidate.full_name),
        "headline": candidate.headline,
        "summary": candidate.summary,
        "location": candidate.location,
        "total_experience_years": candidate.total_experience_years,
        "skills": candidate.skills or [],
        "soft_skills": candidate.soft_skills or [],
        "tools": candidate.tools or [],
        "experience": candidate.experience or [],
        "education": candidate.education or [],
        "projects": candidate.projects or [],
        "certifications": candidate.certifications or [],
        "languages": candidate.languages or [],
        "links": {
            key: value for key, value in (candidate.links or {}).items()
            if key.lower() in {"github", "linkedin", "portfolio", "website"}
        },
        "updated_at": candidate.updated_at,
    }


def _public_job(job: Job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "work_mode": job.work_mode,
        "employment_type": job.employment_type,
        "description": job.description,
        "responsibilities": job.responsibilities or [],
        "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [],
        "minimum_experience": job.minimum_experience,
        "maximum_experience": job.maximum_experience,
        "education_requirement": job.education_requirement,
        "created_at": job.created_at,
    }


@router.get("/dashboard")
def public_dashboard(db: Session = Depends(get_db)):
    public_candidates = db.query(func.count(CandidateAccount.id)).filter(CandidateAccount.public_profile.is_(True)).scalar() or 0
    open_roles = db.query(func.count(Job.id)).filter(Job.status == "open").scalar() or 0
    total_applications = db.query(func.count(Application.id)).scalar() or 0
    scheduled_interviews = db.query(func.count(Interview.id)).filter(Interview.status == "scheduled").scalar() or 0
    stage_counts = {
        stage: db.query(func.count(Application.id)).filter(Application.stage == stage).scalar() or 0
        for stage in ("new", "screening", "interview", "offer", "hired", "rejected")
    }
    skill_counts: Counter[str] = Counter()
    rows = (
        db.query(Candidate.skills)
        .join(CandidateAccount, CandidateAccount.candidate_id == Candidate.id)
        .filter(CandidateAccount.public_profile.is_(True))
        .all()
    )
    for row in rows:
        skill_counts.update({str(value).strip() for value in (row[0] or []) if str(value).strip()})
    return {
        "public_candidate_profiles": public_candidates,
        "open_roles": open_roles,
        "applications_total": total_applications,
        "scheduled_interviews": scheduled_interviews,
        "pipeline": stage_counts,
        "top_public_skills": [{"skill": key, "count": value} for key, value in skill_counts.most_common(10)],
    }


@router.get("/roles")
def public_roles(q: str = "", limit: int = Query(default=100, ge=1, le=200), db: Session = Depends(get_db)):
    query = db.query(Job).filter(Job.status == "open")
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter((Job.title.ilike(term)) | (Job.department.ilike(term)) | (Job.description.ilike(term)))
    return [_public_job(item) for item in query.order_by(desc(Job.created_at)).limit(limit).all()]


@router.get("/roles/{job_id}")
def public_role(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id, Job.status == "open").first()
    if not job:
        raise HTTPException(404, "Published role not found.")
    return _public_job(job)


@router.get("/candidates")
def public_candidates(
    q: str = "",
    skill: str = "",
    limit: int = Query(default=60, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Candidate, CandidateAccount)
        .join(CandidateAccount, CandidateAccount.candidate_id == Candidate.id)
        .filter(CandidateAccount.public_profile.is_(True))
    )
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(Candidate.headline.ilike(term) | Candidate.location.ilike(term) | Candidate.summary.ilike(term))
    rows = query.order_by(desc(Candidate.updated_at)).offset(offset).limit(limit).all()
    profiles = [_public_profile(candidate, account) for candidate, account in rows]
    if skill.strip():
        needle = skill.strip().lower()
        profiles = [item for item in profiles if any(needle in value.lower() for value in item["skills"])]
    return profiles


@router.get("/candidates/{candidate_id}")
def public_candidate(candidate_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Candidate, CandidateAccount)
        .join(CandidateAccount, CandidateAccount.candidate_id == Candidate.id)
        .filter(Candidate.id == candidate_id, CandidateAccount.public_profile.is_(True))
        .first()
    )
    if not row:
        raise HTTPException(404, "Public candidate profile not found.")
    return _public_profile(*row)


@router.get("/insights")
def public_insights(db: Session = Depends(get_db)):
    interview_types = (
        db.query(Interview.interview_type, func.count(Interview.id))
        .group_by(Interview.interview_type)
        .all()
    )
    interview_statuses = (
        db.query(Interview.status, func.count(Interview.id))
        .group_by(Interview.status)
        .all()
    )
    role_statuses = (
        db.query(Job.status, func.count(Job.id))
        .group_by(Job.status)
        .all()
    )
    monthly_applications = (
        db.query(func.strftime("%Y-%m", Application.created_at), func.count(Application.id))
        .group_by(func.strftime("%Y-%m", Application.created_at))
        .order_by(func.strftime("%Y-%m", Application.created_at))
        .limit(12)
        .all()
    )
    if db.bind and db.bind.dialect.name == "postgresql":
        monthly_applications = (
            db.query(func.to_char(Application.created_at, "YYYY-MM"), func.count(Application.id))
            .group_by(func.to_char(Application.created_at, "YYYY-MM"))
            .order_by(func.to_char(Application.created_at, "YYYY-MM"))
            .limit(12)
            .all()
        )
    return {
        "interview_types": [{"type": key, "count": value} for key, value in interview_types],
        "interview_statuses": [{"status": key, "count": value} for key, value in interview_statuses],
        "role_statuses": [{"status": key, "count": value} for key, value in role_statuses],
        "monthly_applications": [{"month": key, "count": value} for key, value in monthly_applications if key],
        "generated_at": datetime.now(timezone.utc),
    }
