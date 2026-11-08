from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth import router as auth_router
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import entities


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auth_enabled:
        if settings.secret_key == "local-development-only-change-me" or len(settings.secret_key) < 32 or "replace-with" in settings.secret_key.lower():
            raise RuntimeError("AUTH_ENABLED is true but SECRET_KEY is weak or unset. Configure a random secret of at least 32 characters.")
        if bool(settings.bootstrap_admin_email) != bool(settings.bootstrap_admin_password):
            raise RuntimeError("Configure both BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD, or leave both empty.")
        if settings.bootstrap_admin_password and len(settings.bootstrap_admin_password) < 12:
            raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD must contain at least 12 characters.")
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
    settings.resume_storage_dir.mkdir(parents=True, exist_ok=True)
    if settings.auth_enabled:
        with SessionLocal() as db:
            from app.models.entities import User
            from sqlalchemy import func
            if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
                exists = db.query(User).filter(func.lower(User.email) == settings.bootstrap_admin_email).first()
                if not exists:
                    db.add(User(email=settings.bootstrap_admin_email, display_name="Workspace administrator", password_hash=hash_password(settings.bootstrap_admin_password), role="admin"))
                    db.commit()
            if not db.query(User.id).first():
                raise RuntimeError("Authentication is enabled but no workspace account exists. Configure BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD, then restart.")
    yield


app = FastAPI(
    title="ResumeIQ API",
    description="Resume parsing, candidate intelligence, hiring workflow and transparent role matching.",
    version="2.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(auth_router)
app.include_router(router)
