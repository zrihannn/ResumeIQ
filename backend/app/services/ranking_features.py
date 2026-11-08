from __future__ import annotations

import re
import numpy as np
from scipy.sparse import csr_matrix, hstack


def normalize_skill(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", value.lower())


def numeric_features(candidate_skills: list[str], required_skills: list[str], preferred_skills: list[str], candidate_experience: float | None, minimum_experience: float | None, maximum_experience: float | None, education_match: float) -> np.ndarray:
    candidate = {normalize_skill(item) for item in candidate_skills}
    required = {normalize_skill(item) for item in required_skills}
    preferred = {normalize_skill(item) for item in preferred_skills}
    required_coverage = len(candidate & required) / len(required) if required else 0.0
    preferred_coverage = len(candidate & preferred) / len(preferred) if preferred else 0.0
    min_exp = float(minimum_experience or 0)
    exp = float(candidate_experience or 0)
    if min_exp <= 0:
        experience_fit = 1.0
    elif candidate_experience is None:
        experience_fit = 0.5
    else:
        experience_fit = min(1.0, exp / min_exp)
    if maximum_experience is not None and candidate_experience is not None and exp > maximum_experience > 0:
        experience_fit = max(0.65, float(maximum_experience) / exp)
    known_experience = 1.0 if candidate_experience is not None else 0.0
    return np.asarray([required_coverage, preferred_coverage, experience_fit, known_experience, float(education_match)], dtype=np.float32)


def pair_matrix(pairs: list[dict], vectorizer, fit: bool = False):
    candidate_texts = [item["candidate_text"][:30000] for item in pairs]
    job_texts = [item["job_text"][:18000] for item in pairs]
    if fit:
        vectorizer.fit(candidate_texts + job_texts)
    candidate_vectors = vectorizer.transform(candidate_texts)
    job_vectors = vectorizer.transform(job_texts)
    difference = abs(candidate_vectors - job_vectors)
    overlap = candidate_vectors.multiply(job_vectors)
    cosine = np.asarray(overlap.sum(axis=1)).reshape(-1, 1)
    numeric = np.vstack([
        numeric_features(
            item.get("candidate_skills", []), item.get("required_skills", []), item.get("preferred_skills", []),
            item.get("candidate_experience"), item.get("minimum_experience"), item.get("maximum_experience"),
            float(item.get("education_match", 0.5)),
        ) for item in pairs
    ])
    return hstack([difference, overlap, csr_matrix(cosine), csr_matrix(numeric)], format="csr")
