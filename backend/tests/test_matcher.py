from app.services.matcher import calculate_match


def test_matcher_uses_education_field_of_study_and_explains_it():
    result = calculate_match(
        {
            "skills": ["Python", "FastAPI"],
            "total_experience_years": 2,
            "education": [{"degree": "B.Tech", "field_of_study": "Computer Science"}],
            "experience": [],
            "projects": [],
        },
        {
            "title": "Python Backend Engineer",
            "description": "Build Python APIs and backend systems.",
            "required_skills": ["Python", "FastAPI"],
            "preferred_skills": [],
            "minimum_experience": 2,
            "education_requirement": "B.Tech Computer Science",
        },
    )
    assert result["component_scores"]["education"] == 100.0
    assert any("Education relevance" in line for line in result["explanation"])


def test_matcher_does_not_need_identity_or_employer_names():
    candidate = {
        "full_name": "Alex Morgan",
        "skills": ["Python"],
        "total_experience_years": 1,
        "experience": [{"role": "Python Developer", "company": "Prestigious Company", "responsibilities": ["Built Python services"]}],
        "education": [], "projects": [],
    }
    job = {"title": "Python Developer", "description": "Build Python services.", "required_skills": ["Python"], "preferred_skills": [], "minimum_experience": 0}
    result = calculate_match(candidate, job)
    assert 0 <= result["overall_score"] <= 100
    assert "Prestigious Company" not in " ".join(result["explanation"])
    assert "Alex Morgan" not in " ".join(result["explanation"])
