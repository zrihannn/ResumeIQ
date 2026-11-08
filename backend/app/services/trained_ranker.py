from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from app.core.config import settings
from app.services.ranking_features import pair_matrix

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "artifacts" / "match_ranker.joblib"


@lru_cache(maxsize=1)
def load_bundle():
    if not settings.use_trained_model or not MODEL_PATH.is_file():
        return None
    try:
        import joblib
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def predict(candidate: dict, job: dict, candidate_text: str, job_text: str, education_match: float) -> float | None:
    bundle = load_bundle()
    if not bundle:
        return None
    try:
        pair = {
            "candidate_text": candidate_text, "job_text": job_text,
            "candidate_skills": candidate.get("skills", []), "required_skills": job.get("required_skills", []),
            "preferred_skills": job.get("preferred_skills", []), "candidate_experience": candidate.get("total_experience_years"),
            "minimum_experience": job.get("minimum_experience"), "maximum_experience": job.get("maximum_experience"),
            "education_match": education_match,
        }
        matrix = pair_matrix([pair], bundle["vectorizer"])
        classes = list(bundle["classifier"].classes_)
        positive = classes.index(1)
        return float(bundle["classifier"].predict_proba(matrix)[0][positive])
    except Exception:
        return None
