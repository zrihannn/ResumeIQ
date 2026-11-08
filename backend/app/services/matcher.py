from __future__ import annotations
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.trained_ranker import predict as predict_trained


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", value.lower())


def _semantic_score(candidate_text: str, job_text: str) -> float:
    if not candidate_text.strip() or not job_text.strip():
        return 0.0
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=18000).fit_transform([candidate_text[:30000], job_text[:18000]])
        return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        return 0.0


def calculate_match(candidate: dict, job: dict) -> dict:
    candidate_skills = candidate.get("skills", [])
    required = job.get("required_skills", [])
    preferred = job.get("preferred_skills", [])
    candidate_set = {_norm(item) for item in candidate_skills}
    required_set = {_norm(item) for item in required}
    preferred_set = {_norm(item) for item in preferred}
    required_match = sorted(required_set & candidate_set)
    preferred_match = sorted(preferred_set & candidate_set)
    required_missing = sorted(required_set - candidate_set)
    required_score = len(required_match) / len(required_set) if required_set else 0.0
    preferred_score = len(preferred_match) / len(preferred_set) if preferred_set else 0.0
    skill_score = (required_score * 0.8 + preferred_score * 0.2) if preferred_set else required_score

    experience_records = candidate.get("experience", [])
    project_records = candidate.get("projects", [])
    education_records = candidate.get("education", [])
    profile_text = " ".join([
        candidate.get("headline") or "", candidate.get("summary") or "",
        " ".join(candidate_skills), " ".join(candidate.get("tools", [])),
        " ".join(item.get("role") or "" for item in experience_records),
        " ".join(" ".join(item.get("responsibilities", [])) for item in experience_records),
        " ".join(" ".join(item.get("technologies", [])) for item in experience_records),
        " ".join(item.get("description") or "" for item in project_records),
        " ".join(" ".join(item.get("technologies", [])) for item in project_records),
        " ".join(item.get("degree") or "" for item in education_records),
        " ".join(item.get("field_of_study") or "" for item in education_records),
        " ".join(item.get("name") or "" for item in candidate.get("certifications", [])),
        " ".join(item.get("text") or "" for item in candidate.get("achievements", [])),
        " ".join(item.get("text") or "" for item in candidate.get("publications", [])),
        " ".join(item.get("text") or "" for item in candidate.get("volunteering", [])),
        " ".join(item.get("language") or "" for item in candidate.get("languages", [])),
    ])
    role_text = " ".join([job.get("title") or "", job.get("description") or "", " ".join(job.get("responsibilities", [])), " ".join(required), " ".join(preferred)])
    semantic_score = _semantic_score(profile_text, role_text)

    experience = candidate.get("total_experience_years")
    minimum = float(job.get("minimum_experience") or 0)
    maximum = job.get("maximum_experience")
    if experience is None or minimum <= 0:
        experience_score = 1.0 if minimum <= 0 else 0.5
    elif experience < minimum:
        experience_score = max(0.0, experience / minimum)
    elif maximum and experience > maximum:
        experience_score = max(0.65, maximum / experience)
    else:
        experience_score = 1.0

    education_requirement = (job.get("education_requirement") or "").lower().strip()
    education_text = " ".join(
        " ".join(filter(None, [item.get("degree"), item.get("field_of_study")]))
        for item in education_records
    ).lower()
    if not education_requirement:
        education_score = 1.0
    elif not education_text:
        education_score = 0.5
    elif education_requirement in education_text:
        education_score = 1.0
    else:
        requirement_terms = {term for term in re.findall(r"[a-z0-9+#.]+", education_requirement) if len(term) > 1}
        education_terms = {term for term in re.findall(r"[a-z0-9+#.]+", education_text) if len(term) > 1}
        overlap = len(requirement_terms & education_terms) / max(1, len(requirement_terms))
        education_score = 1.0 if overlap >= 0.85 else 0.8 if overlap >= 0.6 else 0.65 if overlap >= 0.3 else 0.55

    weights = {"skills": 0.45, "semantic_relevance": 0.30, "experience": 0.15, "education": 0.10}
    baseline_total = skill_score * weights["skills"] + semantic_score * weights["semantic_relevance"] + experience_score * weights["experience"] + education_score * weights["education"]
    trained_total = predict_trained(candidate, job, profile_text, role_text, education_score)
    total = trained_total if trained_total is not None else baseline_total
    explanation = []
    if required_match:
        explanation.append(f"Matches {len(required_match)} of {len(required_set)} required skills: {', '.join(required_match[:8])}.")
    if required_missing:
        explanation.append(f"Missing required skills: {', '.join(required_missing[:8])}.")
    if experience is not None:
        explanation.append(f"Profile indicates about {experience:g} years of experience; role minimum is {minimum:g} years.")
    if experience is None and minimum > 0:
        explanation.append("Experience duration was not confidently extracted; the experience component uses a neutral estimate until reviewed.")
    if education_requirement and not education_text:
        explanation.append("Education details are missing from the parsed profile; no negative education conclusion is inferred.")
    elif education_requirement:
        explanation.append(f"Education relevance was estimated from degree and field-of-study evidence against the role requirement: {education_score * 100:.0f}%.")
    explanation.append("Only job-related profile content is used for relevance; names and employer identities are excluded. Scores are estimates, not hiring decisions.")
    return {
        "overall_score": round(total * 100, 1),
        "component_scores": {
            "skills": round(skill_score * 100, 1), "semantic_relevance": round(semantic_score * 100, 1),
            "experience": round(experience_score * 100, 1), "education": round(education_score * 100, 1),
            "weights": weights,
        },
        "matched_skills": [item for item in required if _norm(item) in candidate_set] + [item for item in preferred if _norm(item) in candidate_set],
        "missing_skills": [item for item in required if _norm(item) not in candidate_set],
        "explanation": explanation,
        "matching_method": "supervised-hybrid-ranker" if trained_total is not None else "hybrid-tfidf-skills-experience-education-v2",
    }
