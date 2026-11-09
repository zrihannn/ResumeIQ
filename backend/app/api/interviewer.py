from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.security import require_roles
from app.db.session import get_db
from app.models.entities import Application, Candidate, Interview, User
from app.services.serializers import candidate_out, document_out

router = APIRouter(prefix="/api/interviewer", tags=["Interviewer portal"], dependencies=[Depends(require_roles("interviewer"))])


class InterviewReviewUpdate(BaseModel):
    status: str | None = None
    scorecard: dict | None = None
    notes: str | None = Field(default=None, max_length=5000)


def _is_assigned(item: Interview, user: User) -> bool:
    assigned = {str(value).strip().lower() for value in (item.interviewers or []) if str(value).strip()}
    return user.email.lower() in assigned or user.display_name.lower() in assigned


def _interview_query(db: Session):
    return db.query(Interview).options(
        joinedload(Interview.application).joinedload(Application.candidate).joinedload(Candidate.documents),
        joinedload(Interview.application).joinedload(Application.job),
    )


def _review_out(item: Interview) -> dict:
    app = item.application
    return {
        "id": item.id,
        "application_id": item.application_id,
        "candidate_id": app.candidate_id,
        "candidate_name": app.candidate.full_name,
        "candidate_headline": app.candidate.headline,
        "job_title": app.job.title,
        "title": item.title,
        "interview_type": item.interview_type,
        "scheduled_at": item.scheduled_at,
        "duration_minutes": item.duration_minutes,
        "location_or_link": item.location_or_link,
        "status": item.status,
        "scorecard": item.scorecard or {},
        "notes": item.notes,
    }


@router.get("/me/interviews")
def my_interviews(user: User = Depends(require_roles("interviewer")), db: Session = Depends(get_db)):
    items = _interview_query(db).order_by(Interview.scheduled_at.asc()).all()
    return [_review_out(item) for item in items if _is_assigned(item, user)]


@router.get("/me/interviews/{interview_id}")
def interview_detail(interview_id: int, user: User = Depends(require_roles("interviewer")), db: Session = Depends(get_db)):
    item = _interview_query(db).filter(Interview.id == interview_id).first()
    if not item or not _is_assigned(item, user):
        raise HTTPException(404, "Assigned interview not found.")
    candidate = item.application.candidate
    return {
        "interview": _review_out(item),
        "candidate": candidate_out(candidate),
        "documents": [document_out(doc) for doc in candidate.documents],
    }


@router.patch("/me/interviews/{interview_id}")
def update_interview_review(
    interview_id: int,
    payload: InterviewReviewUpdate,
    user: User = Depends(require_roles("interviewer")),
    db: Session = Depends(get_db),
):
    item = _interview_query(db).filter(Interview.id == interview_id).first()
    if not item or not _is_assigned(item, user):
        raise HTTPException(404, "Assigned interview not found.")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide an interview status, scorecard or feedback note.")
    if "status" in changes and changes["status"] not in {"scheduled", "completed", "cancelled", "rescheduled"}:
        raise HTTPException(422, "Invalid interview status.")
    if "scorecard" in changes and not isinstance(changes["scorecard"], dict):
        raise HTTPException(422, "Scorecard must be an object.")
    for field, value in changes.items():
        if value is not None:
            setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _review_out(item)
