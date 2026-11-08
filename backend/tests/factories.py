from io import BytesIO
from docx import Document


def resume_docx(name="Alex Morgan", email="alex.morgan@example.com"):
    document = Document()
    for line in [
        name, "Backend Engineer | Bhubaneswar, India", email, "+91 98765 43210", "https://github.com/alexmorgan",
        "PROFESSIONAL SUMMARY", "Backend engineer with 3 years of experience building Python services and REST APIs. Experienced in designing scalable systems.",
        "SKILLS", "Python, FastAPI, SQL, PostgreSQL, Docker, Git, Redis, Machine Learning, Communication, Teamwork",
        "WORK EXPERIENCE", "Backend Engineer | Example Systems | Jan 2022 - Present",
        "- Designed and maintained FastAPI services for internal applications.", "- Improved PostgreSQL query performance and automated deployments with Docker.",
        "EDUCATION", "B.Tech Computer Science | Example University | 2021",
        "PROJECTS", "Resume Intelligence API", "- Built a document parser using Python, FastAPI, PyMuPDF and PostgreSQL.",
        "CERTIFICATIONS", "AWS Cloud Practitioner - Amazon Web Services - 2024",
        "ACHIEVEMENTS", "Winner, university hackathon 2023",
        "LANGUAGES", "English - Professional, Bengali - Native",
    ]:
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()
