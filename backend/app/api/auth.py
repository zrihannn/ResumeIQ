from fastapi import APIRouter, Depends, HTTPException, status
import re
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, require_admin, verify_password, auth_guard
from app.db.session import get_db
from app.models.entities import Candidate, CandidateAccount, User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=12, max_length=200)
    role: str = "recruiter"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value



class CandidateRegisterInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=2, max_length=180)
    password: str = Field(min_length=12, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address.")
        return value

def user_out(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "role": user.role, "is_active": user.is_active}


@router.get("/status")
def auth_status():
    return {"enabled": settings.auth_enabled, "bootstrap_configured": bool(settings.bootstrap_admin_email and settings.bootstrap_admin_password)}



@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_candidate(payload: CandidateRegisterInput, db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        raise HTTPException(400, "Candidate registration is unavailable while authentication is disabled.")
    if db.query(User).filter(func.lower(User.email) == payload.email).first():
        raise HTTPException(409, "An account with this email already exists.")
    existing_candidate = db.query(Candidate.id).filter(func.lower(Candidate.email) == payload.email).first()
    if existing_candidate:
        raise HTTPException(409, "A candidate record already uses this email. Contact the recruitment team to link it securely.")
    candidate = Candidate(
        full_name=payload.display_name.strip(),
        email=payload.email,
        extraction_quality={"source": "candidate_registration", "requires_review": False, "manually_reviewed": True},
    )
    user = User(
        email=payload.email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        role="candidate",
    )
    db.add(candidate)
    db.add(user)
    db.flush()
    db.add(CandidateAccount(user_id=user.id, candidate_id=candidate.id))
    db.commit()
    db.refresh(user)
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user_out(user),
    }

@router.post("/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        raise HTTPException(400, "Authentication is disabled in this workspace.")
    user = db.query(User).filter(func.lower(User.email) == payload.email).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"access_token": create_access_token(user), "token_type": "bearer", "user": user_out(user)}


@router.get("/me")
def me(user: User | None = Depends(auth_guard)):
    if not settings.auth_enabled:
        return {"authentication_enabled": False, "user": None}
    return {"authentication_enabled": True, "user": user_out(user)}


@router.get("/users")
def list_users(admin: User | None = Depends(require_admin), db: Session = Depends(get_db)):
    if not settings.auth_enabled or admin is None:
        raise HTTPException(403, "Administrator access is required.")
    users = db.query(User).order_by(User.role.asc(), User.email.asc()).all()
    return [user_out(user) for user in users]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, admin: User | None = Depends(require_admin), db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        raise HTTPException(403, "Enable authentication before creating workspace accounts.")
    if payload.role not in {"admin", "recruiter", "reviewer", "interviewer", "viewer"}:
        raise HTTPException(422, "Role must be admin, recruiter, reviewer or viewer.")
    if db.query(User).filter(func.lower(User.email) == payload.email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=payload.email, display_name=payload.display_name.strip(), password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_out(user)
