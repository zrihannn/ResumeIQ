from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{(Path(__file__).resolve().parents[2] / 'resumeiq.db').as_posix()}")
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    resume_storage_dir = Path(os.getenv("RESUME_STORAGE_DIR", str(Path(__file__).resolve().parents[2] / "storage" / "resumes"))).expanduser()
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "15"))
    ocr_enabled = _bool("OCR_ENABLED", False)
    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    auto_create_schema = _bool("AUTO_CREATE_SCHEMA", True)
    secret_key = os.getenv("SECRET_KEY", "local-development-only-change-me")
    auth_enabled = _bool("AUTH_ENABLED", False)
    use_trained_model = _bool("USE_TRAINED_MODEL", False)
    bootstrap_admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    bootstrap_admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
