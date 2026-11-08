from __future__ import annotations
from datetime import datetime
import re
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    department: str = Field(default="Engineering", max_length=180)
    location: str = Field(default="Remote", max_length=180)
    work_mode: Literal["remote", "hybrid", "onsite"] = "remote"
    employment_type: Literal["full-time", "part-time", "contract", "internship", "temporary"] = "full-time"
    description: str = Field(min_length=20, max_length=12000)
    responsibilities: list[str] = Field(default_factory=list, max_length=30)
    required_skills: list[str] = Field(default_factory=list, max_length=80)
    preferred_skills: list[str] = Field(default_factory=list, max_length=80)
    minimum_experience: float = Field(default=0, ge=0, le=60)
    maximum_experience: float | None = Field(default=None, ge=0, le=60)
    education_requirement: str | None = Field(default=None, max_length=180)

    @field_validator("required_skills", "preferred_skills", "responsibilities")
    @classmethod
    def clean_lists(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    department: str | None = Field(default=None, max_length=180)
    location: str | None = Field(default=None, max_length=180)
    work_mode: Literal["remote", "hybrid", "onsite"] | None = None
    employment_type: Literal["full-time", "part-time", "contract", "internship", "temporary"] | None = None
    description: str | None = Field(default=None, min_length=20, max_length=12000)
    responsibilities: list[str] | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    minimum_experience: float | None = Field(default=None, ge=0, le=60)
    maximum_experience: float | None = Field(default=None, ge=0, le=60)
    education_requirement: str | None = Field(default=None, max_length=180)
    status: Literal["open", "paused", "closed"] | None = None


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=180)
    email: str | None = Field(default=None, max_length=254)
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

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


ApplicationStage = Literal["new", "screening", "interview", "offer", "hired", "rejected"]


class ApplicationCreate(BaseModel):
    candidate_id: int = Field(gt=0)
    job_id: int = Field(gt=0)
    stage: ApplicationStage = "new"
    source: str = Field(default="resume_upload", max_length=80)
    notes: str = Field(default="", max_length=5000)


class ApplicationUpdate(BaseModel):
    stage: ApplicationStage | None = None
    notes: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, max_length=80)


class InterviewCreate(BaseModel):
    application_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=180)
    interview_type: Literal["screening", "technical", "behavioral", "managerial", "culture", "final"] = "technical"
    scheduled_at: datetime
    duration_minutes: int = Field(default=45, ge=15, le=360)
    location_or_link: str | None = Field(default=None, max_length=500)
    interviewers: list[str] = Field(default_factory=list, max_length=20)
    notes: str = Field(default="", max_length=5000)


class InterviewUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=180)
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=15, le=360)
    location_or_link: str | None = Field(default=None, max_length=500)
    interviewers: list[str] | None = None
    status: Literal["scheduled", "completed", "cancelled", "rescheduled"] | None = None
    scorecard: dict | None = None
    notes: str | None = Field(default=None, max_length=5000)
