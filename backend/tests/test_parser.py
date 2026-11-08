from app.services.parser import parse_resume, _date_value, _months_between


def test_parser_extracts_profile_and_sections():
    text = """Alex Morgan
Backend Engineer | Bhubaneswar
alex.morgan@example.com
+91 98765 43210
SUMMARY
Backend engineer with 3 years of experience building Python APIs.
SKILLS
Python, FastAPI, PostgreSQL, Docker, Git, Communication
EXPERIENCE
Backend Engineer | Example Systems | Jan 2022 - Present
- Built REST APIs using FastAPI.
EDUCATION
B.Tech Computer Science | Example University | 2021
PROJECTS
Resume Intelligence API
- Created a Python resume parser.
CERTIFICATIONS
AWS Cloud Practitioner - 2024
"""
    result = parse_resume(text)
    assert result["identity"]["full_name"] == "Alex Morgan"
    assert result["identity"]["email"] == "alex.morgan@example.com"
    assert "Python" in result["skills"]["technical"]
    assert result["professional_profile"]["total_experience_years"] is not None
    assert result["experience"][0]["company"] == "Example Systems"
    assert result["education"]
    assert result["projects"]
    assert "full_name" in result["field_evidence"]
    assert result["field_evidence"]["skills"]["snippet"]
    assert result["experience"][0]["evidence"]["snippet"]
    assert "experience" in result["sections_detected"]


def test_date_normalization():
    assert _date_value("Jan 2022") == "2022-01"
    assert _date_value("02/2021") == "2021-02"
    assert _date_value("Present") == "present"
    assert _date_value("2022-07") == "2022-07"
    assert _months_between("Jan 2022", "Dec 2022") == 12


def test_parser_structures_education_certifications_and_languages():
    text = """Taylor Reed
taylor.reed@example.com
EDUCATION
B.Tech | Computer Science | Example University | 2021 - 2025 | CGPA: 8.7
CERTIFICATIONS
AWS Solutions Architect - Amazon Web Services - 2024
LANGUAGES
English (Fluent)
Hindi - Native
"""
    result = parse_resume(text)
    education = result["education"][0]
    assert education["degree"] == "B.Tech"
    assert education["field_of_study"] == "Computer Science"
    assert education["institution"] == "Example University"
    assert education["start_date"] == "2021"
    assert education["end_date"] == "2025"
    assert education["grade"] == "CGPA 8.7"
    certification = result["certifications"][0]
    assert certification["name"] == "AWS Solutions Architect"
    assert certification["issuer"] == "Amazon Web Services"
    assert certification["issue_date"] == "2024"
    assert result["languages"][0]["language"] == "English"
    assert result["languages"][0]["proficiency"] == "Fluent"


def test_parser_experience_with_separate_heading_and_date_line():
    text = """Jordan Lee
jordan.lee@example.com
EXPERIENCE
Software Engineer
Example Systems
Bhubaneswar, India
Jan 2022 - Present
- Built REST APIs using Python and FastAPI.
- Improved PostgreSQL query performance.
"""
    result = parse_resume(text)
    role = result["experience"][0]
    assert role["role"] == "Software Engineer"
    assert role["company"] == "Example Systems"
    assert role["location"] == "Bhubaneswar, India"
    assert role["is_current"] is True
    assert any("REST APIs" in item for item in role["responsibilities"])
    assert "Python" in role["technologies"]


def test_parser_groups_multiline_education_record():
    text = """Morgan Hale
morgan.hale@example.com
EDUCATION
Bachelor of Science in Computer Science
Example Technical University
2021 - 2025
CGPA: 8.6
"""
    result = parse_resume(text)
    education = result["education"][0]
    assert education["degree"].lower().startswith("bachelor")
    assert "Computer Science" in education["field_of_study"]
    assert education["institution"] == "Example Technical University"
    assert education["start_date"] == "2021"
    assert education["end_date"] == "2025"
    assert education["grade"] == "CGPA 8.6"


def test_certification_year_is_not_misread_as_issuer():
    result = parse_resume("Casey Park\ncasey.park@example.com\nCERTIFICATIONS\nAWS Certified Developer - 2024")
    certification = result["certifications"][0]
    assert certification["name"] == "AWS Certified Developer"
    assert certification["issuer"] is None
    assert certification["issue_date"] == "2024"
