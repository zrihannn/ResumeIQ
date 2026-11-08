from app.core.config import settings
from app.services.resume_storage import delete_resume, read_resume, save_resume


def test_local_resume_storage_round_trip(tmp_path):
    previous_dir = settings.resume_storage_dir
    previous_backend = settings.resume_storage_backend
    settings.resume_storage_dir = tmp_path / "resumes"
    settings.resume_storage_backend = "local"
    try:
        save_resume("test-resume.pdf", b"%PDF-test", "application/pdf")
        assert read_resume("test-resume.pdf") == b"%PDF-test"
        delete_resume("test-resume.pdf")
        assert read_resume("test-resume.pdf") is None
    finally:
        settings.resume_storage_dir = previous_dir
        settings.resume_storage_backend = previous_backend
