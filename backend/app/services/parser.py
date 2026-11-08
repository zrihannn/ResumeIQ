from __future__ import annotations

import re
from collections import OrderedDict
from datetime import date
from typing import Any

PARSER_VERSION = "2.2.0"

SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python"], "Java": ["java"], "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"], "C++": ["c++", "cpp"], "C#": ["c#", "c sharp"],
    "C": ["c language", "programming in c"], "Go": ["golang", "go language"], "Rust": ["rust language"],
    "Kotlin": ["kotlin"], "Swift": ["swift language"], "PHP": ["php"], "Ruby": ["ruby language"],
    "Scala": ["scala"], "R": ["r programming", "r language"], "MATLAB": ["matlab"],
    "Bash": ["bash", "shell scripting"], "PowerShell": ["powershell"], "SQL": ["sql", "structured query language"],
    "PostgreSQL": ["postgresql", "postgres"], "MySQL": ["mysql"], "SQLite": ["sqlite"],
    "MongoDB": ["mongodb", "mongo db"], "Redis": ["redis"], "FastAPI": ["fastapi", "fast api"],
    "Django": ["django"], "Flask": ["flask"], "Spring Boot": ["spring boot"],
    "React": ["react", "react.js", "reactjs"], "Next.js": ["next.js", "nextjs"],
    "Node.js": ["node.js", "nodejs", "node js"], "Express.js": ["express.js", "expressjs"],
    "HTML": ["html", "html5"], "CSS": ["css", "css3"], "Tailwind CSS": ["tailwind", "tailwind css"],
    "REST APIs": ["rest api", "rest apis", "restful api", "restful services"], "GraphQL": ["graphql"],
    "Docker": ["docker", "docker compose", "docker-compose"], "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git"], "GitHub": ["github"], "GitLab": ["gitlab"], "Bitbucket": ["bitbucket"],
    "Linux": ["linux", "ubuntu", "debian"], "Terraform": ["terraform"], "Ansible": ["ansible"],
    "Jenkins": ["jenkins"], "GitHub Actions": ["github actions"], "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "Jira": ["jira"], "Confluence": ["confluence"], "Nginx": ["nginx"],
    "AWS": ["aws", "amazon web services"], "Microsoft Azure": ["azure", "microsoft azure"],
    "Google Cloud": ["gcp", "google cloud", "google cloud platform"],
    "Machine Learning": ["machine learning", "ml"], "Deep Learning": ["deep learning", "dl"],
    "Natural Language Processing": ["natural language processing", "nlp"],
    "Computer Vision": ["computer vision", "opencv", "image processing"],
    "Generative AI": ["generative ai", "genai", "llm", "large language models"],
    "TensorFlow": ["tensorflow"], "PyTorch": ["pytorch", "torch"], "Keras": ["keras"],
    "scikit-learn": ["scikit-learn", "sklearn"], "Pandas": ["pandas"], "NumPy": ["numpy"],
    "Apache Spark": ["apache spark", "pyspark"], "Hadoop": ["hadoop"], "Airflow": ["apache airflow", "airflow"],
    "Kafka": ["apache kafka", "kafka"], "Snowflake": ["snowflake"], "Databricks": ["databricks"],
    "Salesforce": ["salesforce"], "SAP": ["sap erp", "sap"], "Power Automate": ["power automate"],
    "Figma": ["figma"], "Adobe Photoshop": ["photoshop", "adobe photoshop"],
    "Adobe Illustrator": ["illustrator", "adobe illustrator"], "Adobe Premiere Pro": ["premiere pro", "adobe premiere"],
    "Data Analysis": ["data analysis", "data analytics"], "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"], "Figma": ["figma"], "UI/UX Design": ["ui/ux", "ui ux", "user experience design"],
    "Agile": ["agile", "scrum"],
    "Testing": ["pytest", "unit testing", "integration testing", "selenium", "playwright"],
    "Cybersecurity": ["cybersecurity", "information security", "network security"],
    "Microservices": ["microservices", "microservice architecture"],
    "Problem Solving": ["problem solving", "problem-solving"], "Communication": ["communication skills", "verbal communication"],
    "Leadership": ["leadership", "team leadership"], "Teamwork": ["teamwork", "collaboration"],
    "Project Management": ["project management", "project planning"],
}

SOFT_SKILLS = ["Communication", "Leadership", "Teamwork", "Problem Solving", "Adaptability", "Critical Thinking", "Time Management", "Creativity", "Collaboration", "Project Management", "Analytical Thinking", "Attention to Detail"]

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "about me", "career summary", "objective", "career objective"),
    "experience": ("experience", "work experience", "professional experience", "employment history", "work history", "career history", "internships", "internship experience", "relevant experience"),
    "education": ("education", "academic background", "academic qualifications", "qualifications", "educational background", "education & training"),
    "skills": ("skills", "technical skills", "core competencies", "competencies", "technologies", "technical expertise", "skills & tools", "technical proficiencies"),
    "projects": ("projects", "personal projects", "academic projects", "project experience", "selected projects"),
    "certifications": ("certifications", "certificates", "licenses", "licences", "training & certifications"),
    "achievements": ("achievements", "awards", "honors", "honours", "accomplishments"),
    "publications": ("publications", "research", "papers", "research publications"),
    "languages": ("languages", "language proficiency"),
    "volunteering": ("volunteering", "volunteer experience", "community involvement"),
    "interests": ("interests", "hobbies", "additional information", "extracurricular activities"),
}

DATE_TOKEN = r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(?:19|20)\d{2}|(?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}|(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])|(?:19|20)\d{2})"
DATE_RANGE_RE = re.compile(rf"(?P<start>{DATE_TOKEN})\s*(?:-|–|—|to|through)\s*(?P<end>present|current|now|{DATE_TOKEN})", re.I)
MONTHS = {name.lower(): index for index, name in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip(" \t|•·-–—")


def _normal_heading(value: str) -> str:
    return re.sub(r"[^a-z0-9 &/+.-]", "", value.lower()).strip(" :.-")


def _find_sections(lines: list[str]) -> tuple[dict[str, list[tuple[int, str]]], dict[str, int]]:
    alias_lookup = {_normal_heading(alias): key for key, aliases in SECTION_ALIASES.items() for alias in aliases}
    sections: dict[str, list[tuple[int, str]]] = {key: [] for key in SECTION_ALIASES}
    positions: dict[str, int] = {}
    active: str | None = None
    heading_pattern = re.compile(r"^([A-Za-z][A-Za-z &/+.-]{1,48})(?:\s*[:|])?$")
    for index, line in enumerate(lines):
        candidate = _normal_heading(line)
        if candidate in alias_lookup:
            active = alias_lookup[candidate]
            positions.setdefault(active, index)
            continue
        match = heading_pattern.match(line)
        if match and candidate in alias_lookup:
            active = alias_lookup[candidate]
            positions.setdefault(active, index)
            continue
        if active and line:
            sections[active].append((index, line))
    return sections, positions


def _date_value(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower().replace(".", "")
    if raw in {"present", "current", "now"}:
        return "present"
    numeric = re.fullmatch(r"(\d{1,2})[/-](\d{4})", raw)
    if numeric:
        month, year = int(numeric.group(1)), int(numeric.group(2))
        return f"{year:04d}-{month:02d}" if 1 <= month <= 12 else None
    year_month = re.fullmatch(r"((?:19|20)\d{2})[-/](0?[1-9]|1[0-2])", raw)
    if year_month:
        return f"{year_month.group(1)}-{int(year_month.group(2)):02d}"
    year = re.fullmatch(r"\d{4}", raw)
    if year:
        return year.group(0)
    for name, month in MONTHS.items():
        if raw.startswith(name[:3]):
            year_match = re.search(r"\d{4}", raw)
            if year_match:
                return f"{year_match.group(0)}-{month:02d}"
    return None


def _months_between(start: str | None, end: str | None) -> int | None:
    a, b = _date_value(start), _date_value(end)
    if not a or not b or a == "present":
        return None
    if len(a) == 4:
        a += "-01"
    if b == "present":
        today = date.today()
        by, bm = today.year, today.month
    else:
        if len(b) == 4:
            b += "-12"
        by, bm = int(b[:4]), int(b[5:7])
    ay, am = int(a[:4]), int(a[5:7])
    return max(0, (by - ay) * 12 + bm - am + 1)


def _evidence(lines: list[str], value: Any, pattern: str | None = None) -> dict | None:
    if value is None or value == "" or value == []:
        return None
    current_page = None
    values = value if isinstance(value, list) else [value]
    search_values = [str(item).strip() for item in values if isinstance(item, (str, int, float)) and str(item).strip()]
    for index, line in enumerate(lines):
        page_marker = re.match(r"\[PAGE\s+(\d+)\]", line, re.I)
        if page_marker:
            current_page = int(page_marker.group(1))
            continue
        if pattern and re.search(pattern, line, re.I):
            return {"value": value, "snippet": line[:300], "line": index + 1, "page": current_page, "confidence": 0.98, "method": "pattern"}
        matched = next((item for item in search_values if item.casefold() in line.casefold()), None)
        if matched:
            return {"value": value, "snippet": line[:300], "line": index + 1, "page": current_page, "confidence": 0.9 if isinstance(value, list) else 0.88, "method": "text-context"}
    return {"value": value, "snippet": "", "line": None, "page": None, "confidence": 0.55, "method": "inference"}


def _extract_links(text: str, document_links: list[str]) -> dict[str, str]:
    urls = set(document_links)
    urls.update(re.findall(r"https?://[^\s<>\])}]+", text, re.I))
    result: dict[str, str] = {}
    for url in urls:
        cleaned = url.rstrip(".,;)")
        lower = cleaned.lower()
        if "linkedin.com" in lower:
            result["linkedin"] = cleaned
        elif "github.com" in lower:
            result["github"] = cleaned
        elif "gitlab.com" in lower:
            result["gitlab"] = cleaned
        elif "behance.net" in lower:
            result["behance"] = cleaned
        elif "dribbble.com" in lower:
            result["dribbble"] = cleaned
        elif "mailto:" in lower:
            result["email"] = cleaned.replace("mailto:", "")
        elif "portfolio" not in result:
            result["website"] = cleaned
    return result


def _canonical_skills(text: str) -> tuple[list[str], list[str]]:
    found: OrderedDict[str, None] = OrderedDict()
    haystack = f" {text.lower()} "
    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            escaped = re.escape(alias.lower())
            boundary = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
            if re.search(boundary, haystack):
                found.setdefault(canonical, None)
                break
    soft = [skill for skill in SOFT_SKILLS if skill.lower() in haystack]
    technical = [skill for skill in found if skill not in SOFT_SKILLS]
    return technical, soft


def _education_entries(items: list[tuple[int, str]]) -> list[dict]:
    entries: list[dict] = []
    degree_pattern = re.compile(
        r"\b(Ph\.?D\.?|Doctorate|M\.?Tech|M\.?S\.?|M\.?Sc\.?|MBA|B\.?Tech|B\.?E\.?|B\.?Sc\.?|BCA|MCA|Bachelor(?:'s)?(?:\s+of\s+(?:Science|Arts|Engineering|Computer Applications))?|Master(?:'s)?(?:\s+of\s+(?:Science|Arts|Engineering|Business Administration))?|Diploma|Associate(?:'s)?)\b",
        re.I,
    )
    grade_pattern = re.compile(r"\b(CGPA|GPA|percentage|percent|grade|score)\s*[:= -]?\s*([A-F]\+?|\d+(?:\.\d+)?%?)", re.I)

    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current and (current.get("degree") or current.get("institution")):
            entries.append(current)
        current = None

    def apply_dates(record: dict, line: str) -> None:
        date_match = DATE_RANGE_RE.search(line)
        if date_match:
            record["start_date"] = _date_value(date_match.group("start"))
            record["end_date"] = _date_value(date_match.group("end"))
        else:
            year_match = re.search(r"\b(?:19|20)\d{2}\b", line)
            if year_match and not record.get("end_date"):
                record["end_date"] = year_match.group(0)

    for line_index, raw_line in items:
        line = _clean(raw_line)
        if not line:
            continue
        degree_match = degree_pattern.search(line)
        institution_match = re.search(r"\b(university|college|institute|school|academy)\b", line, re.I)
        if degree_match:
            flush()
            degree = _clean(degree_match.group(0))
            parts = [part.strip(" ,;:-") for part in re.split(r"\s*[|•,]\s*", line) if part.strip(" ,;:-")]
            degree_part = next((part for part in parts if degree_pattern.search(part)), line)
            part_degree_match = degree_pattern.search(degree_part)
            tail = degree_part[part_degree_match.end():].strip(" ,:-") if part_degree_match else ""
            tail = re.sub(r"^of\s+(?:science|arts|engineering|computer applications|business administration)\s+in\s+", "", tail, flags=re.I)
            tail = re.sub(r"^in\s+", "", tail, flags=re.I)
            tail = re.sub(r"\b(?:honours?|with|speciali[sz]ation in)\b.*$", "", tail, flags=re.I).strip(" ,:-")
            institution = next((part for part in parts if re.search(r"\b(university|college|institute|school|academy)\b", part, re.I)), None)
            other_parts = [part for part in parts if part != degree_part and part != institution and not grade_pattern.search(part) and not DATE_RANGE_RE.search(part) and not re.fullmatch(r"(?:19|20)\d{2}", part)]
            field_of_study = tail or (other_parts[0] if other_parts else None)
            current = {
                "degree": degree,
                "field_of_study": field_of_study[:160] if field_of_study else None,
                "institution": institution[:180] if institution else None,
                "start_date": None,
                "end_date": None,
                "grade": None,
                "evidence": {"snippet": line[:300], "line": line_index + 1, "confidence": 0.86 if institution and field_of_study else 0.78, "method": "education-structured-line"},
            }
            apply_dates(current, line)
            grade_match = grade_pattern.search(line)
            if grade_match:
                current["grade"] = f"{grade_match.group(1)} {grade_match.group(2)}"
            continue

        if current:
            if institution_match and not current.get("institution"):
                current["institution"] = line[:180]
                current["evidence"]["confidence"] = 0.88
            elif grade_pattern.search(line):
                grade_match = grade_pattern.search(line)
                current["grade"] = f"{grade_match.group(1)} {grade_match.group(2)}"
            elif DATE_RANGE_RE.search(line) or re.search(r"\b(?:19|20)\d{2}\b", line):
                apply_dates(current, line)
            elif not current.get("field_of_study") and len(line) <= 160 and not re.search(r"\b(CGPA|GPA|percentage|percent|grade|score)\b", line, re.I):
                current["field_of_study"] = line[:160]

    flush()
    return entries[:12]

def _certification_entries(items: list[tuple[int, str]]) -> list[dict]:
    entries: list[dict] = []
    for line_index, raw_line in items:
        line = _clean(raw_line)
        if len(line) < 3:
            continue
        date_match = DATE_RANGE_RE.search(line)
        issue_date = None
        expiry_date = None
        if date_match:
            issue_date = _date_value(date_match.group("start"))
            expiry_date = _date_value(date_match.group("end"))
        else:
            year_match = re.search(r"\b(?:19|20)\d{2}\b", line)
            issue_date = year_match.group(0) if year_match else None
        cleaned = DATE_RANGE_RE.sub("", line)
        cleaned = re.sub(r"\b(?:19|20)\d{2}\b", "", cleaned).strip(" ,-|·")
        parts = [part.strip(" ,-|·") for part in re.split(r"\s+[|•]\s+|\s+-\s+", cleaned) if part.strip(" ,-|·")]
        name = parts[0] if parts else cleaned
        issuer = parts[1] if len(parts) > 1 else None
        credential = re.search(r"\b(?:credential|certificate|license|licence|id)\s*(?:id|no\.?|number)?\s*[:#-]?\s*([A-Z0-9-]{4,})\b", line, re.I)
        entries.append({
            "name": name[:180], "issuer": issuer[:180] if issuer else None,
            "credential_id": credential.group(1) if credential else None,
            "issue_date": issue_date, "expiry_date": expiry_date,
            "evidence": {"snippet": line[:300], "line": line_index + 1, "confidence": 0.72 if issuer else 0.62, "method": "certification-line"},
        })
    return entries[:30]


def _language_entries(items: list[tuple[int, str]]) -> list[dict]:
    entries: list[dict] = []
    proficiency_terms = ("native", "fluent", "advanced", "intermediate", "beginner", "basic", "professional", "conversational")
    for line_index, raw_line in items:
        line = _clean(raw_line)
        if len(line) < 2:
            continue
        parts = [part.strip(" ,;:-") for part in re.split(r"\s+[|•]\s+|\s+[-–—]\s+|\s*\(([^)]*)\)", line) if part and part.strip(" ,;:-")]
        language = parts[0] if parts else line
        proficiency = next((part for part in parts[1:] if any(term in part.lower() for term in proficiency_terms)), None)
        if not proficiency:
            match = re.search(r"\b(native|fluent|advanced|intermediate|beginner|basic|professional|conversational)\b", line, re.I)
            proficiency = match.group(1).title() if match else None
        entries.append({"language": language[:100], "proficiency": proficiency, "evidence": {"snippet": line[:300], "line": line_index + 1, "confidence": 0.74 if proficiency else 0.62, "method": "language-line"}})
    return entries[:20]

def _experience_entries(items: list[tuple[int, str]]) -> list[dict]:
    lines = [(_index, _clean(line)) for _index, line in items if _clean(line)]
    results: list[dict] = []
    current: dict | None = None
    pending_header: list[tuple[int, str]] = []
    action_verbs = re.compile(r"^(?:built|developed|created|implemented|designed|led|managed|owned|improved|delivered|maintained|deployed|analysed|analyzed|configured|tested|supported|automated|reduced|increased|worked|collaborated|responsible)\b", re.I)

    def make_entry(header: str, start_raw: str, end_raw: str, line_no: int, evidence_line: str) -> dict:
        header = _clean(header)
        if "|" in header or "•" in header:
            parts = [part.strip(" ,-|·") for part in re.split(r"\s*[|•]\s*", header) if part.strip(" ,-|·")]
        elif re.search(r"\s+at\s+", header, re.I):
            parts = [part.strip(" ,-|·") for part in re.split(r"\s+at\s+", header, maxsplit=1, flags=re.I)]
        elif "," in header:
            parts = [part.strip(" ,-|·") for part in header.split(",") if part.strip(" ,-|·")]
        else:
            parts = [header] if header else []
        role = parts[0] if parts else None
        company = parts[1] if len(parts) > 1 else None
        location = parts[2] if len(parts) > 2 else None
        return {
            "role": role[:180] if role else None,
            "company": company[:180] if company else None,
            "location": location[:180] if location else None,
            "start_date": _date_value(start_raw),
            "end_date": _date_value(end_raw),
            "is_current": end_raw.lower() in {"present", "current", "now"},
            "duration_months": _months_between(start_raw, end_raw),
            "responsibilities": [],
            "technologies": [],
            "evidence": {"snippet": evidence_line[:300], "line": line_no + 1, "confidence": 0.76 if role and company else 0.68, "method": "date-range-context"},
        }

    for line_no, line in lines:
        date_match = DATE_RANGE_RE.search(line)
        bullet = bool(re.match(r"^(?:[-*•▪]|\d+[.)])\s*", line))
        if date_match and len(line) < 220:
            start_raw, end_raw = date_match.group("start"), date_match.group("end")
            inline_header = _clean(DATE_RANGE_RE.sub("", line))
            header = inline_header or " | ".join(value for _, value in pending_header)
            if current:
                results.append(current)
            current = make_entry(header, start_raw, end_raw, line_no, line if inline_header else " | ".join(value for _, value in pending_header))
            pending_header = []
        elif bullet:
            pending_header = []
            if current:
                statement = re.sub(r"^(?:[-*•▪]|\d+[.)])\s*", "", line).strip()
                if statement:
                    current["responsibilities"].append(statement[:600])
        elif current and (len(line) > 35 or action_verbs.search(line)):
            pending_header = []
            current["responsibilities"].append(line[:600])
        elif len(line) <= 180 and not action_verbs.search(line):
            pending_header.append((line_no, line))
            pending_header = pending_header[-4:]

    if current:
        results.append(current)
    for entry in results:
        combined = " ".join(entry["responsibilities"])
        entry["technologies"], _ = _canonical_skills(combined)
    return results[:20]

def _project_entries(items: list[tuple[int, str]]) -> list[dict]:
    entries: list[dict] = []
    current: dict | None = None
    for line_index, line in items:
        line = _clean(line)
        if not line:
            continue
        is_bullet = bool(re.match(r"^(?:[-*•▪]|\d+[.)])\s*", line))
        if not is_bullet and (len(line) <= 95) and not re.search(r"\b(developed|built|created|implemented|designed|using|with|responsible)\b", line, re.I):
            if current:
                combined = " ".join(current["description_parts"])
                current["description"] = combined[:1200]
                current["technologies"], _ = _canonical_skills(f"{current['name']} {combined}")
                entries.append(current)
            current = {"name": line[:180], "description_parts": [], "technologies": [], "url": None, "start_date": None, "end_date": None, "evidence": {"snippet": line, "line": line_index + 1, "confidence": 0.62, "method": "section-heading"}}
        elif current:
            current["description_parts"].append(re.sub(r"^(?:[-*•▪]|\d+[.)])\s*", "", line))
        elif line:
            current = {"name": line[:180], "description_parts": [], "technologies": [], "url": None, "start_date": None, "end_date": None, "evidence": {"snippet": line, "line": line_index + 1, "confidence": 0.5, "method": "section-line"}}
    if current:
        combined = " ".join(current["description_parts"])
        current["description"] = combined[:1200]
        current["technologies"], _ = _canonical_skills(f"{current['name']} {combined}")
        entries.append(current)
    return entries[:20]


def _simple_entries(items: list[tuple[int, str]], limit: int = 20) -> list[dict]:
    return [{"text": line, "evidence": {"snippet": line[:300], "line": index + 1, "confidence": 0.7, "method": "section-line"}} for index, line in items if len(_clean(line)) > 2][:limit]


def parse_resume(text: str, document_links: list[str] | None = None, filename: str = "") -> dict:
    raw_lines = text.splitlines()
    lines = [_clean(line) for line in raw_lines]
    lines = [line for line in lines if line]
    flat = "\n".join(lines)
    sections, positions = _find_sections(lines)

    email_match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", flat, re.I)
    phone_candidates = re.findall(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", flat)
    phone = next((re.sub(r"\s+", " ", item).strip() for item in phone_candidates if 8 <= len(re.sub(r"\D", "", item)) <= 15), None)

    name = None
    for line in lines[:10]:
        if len(line) > 65 or re.search(r"@|https?://|www\.|\d{4,}", line, re.I):
            continue
        normalized = _normal_heading(line)
        if normalized in {alias for aliases in SECTION_ALIASES.values() for alias in aliases}:
            continue
        words = line.split()
        if 2 <= len(words) <= 5 and all(re.fullmatch(r"[A-Za-z][A-Za-z.'’-]*", word) for word in words):
            name = line.title()
            break
    if not name and filename:
        stem = re.sub(r"[_-]+", " ", filename.rsplit(".", 1)[0])
        stem = re.sub(r"\b(resume|cv|curriculum vitae|updated|final|latest)\b", "", stem, flags=re.I).strip()
        if 2 <= len(stem.split()) <= 4 and stem.replace(" ", "").isalpha():
            name = stem.title()

    links = _extract_links(flat, document_links or [])
    technical_skills, soft_skills = _canonical_skills(flat)
    experience = _experience_entries(sections["experience"])
    education = _education_entries(sections["education"])
    projects = _project_entries(sections["projects"])
    certifications = _certification_entries(sections["certifications"])
    achievements = _simple_entries(sections["achievements"], 30)
    publications = _simple_entries(sections["publications"], 20)
    languages = _language_entries(sections["languages"])
    volunteering = _simple_entries(sections["volunteering"], 20)

    summary_items = sections["summary"]
    summary = " ".join(line for _, line in summary_items).strip()[:2500] or None
    headline = next((line for line in lines[:12] if re.search(r"\b(engineer|developer|analyst|designer|manager|consultant|scientist|architect|intern|specialist)\b", line, re.I) and line != name), None)
    location = None
    for line in lines[:12]:
        if re.search(r"\b(remote|hybrid|india|usa|united states|uk|london|bhubaneswar|delhi|mumbai|bengaluru|bangalore|hyderabad|pune|kolkata|chennai|new york|san francisco)\b", line, re.I):
            if line not in {headline, name}:
                location = line[:180]
                break

    experience_years: float | None = None
    date_intervals = []
    for item in experience:
        start = _date_value(item.get("start_date"))
        end = _date_value(item.get("end_date"))
        if start and start != "present":
            if len(start) == 4:
                start += "-01"
            if end == "present" or not end:
                today = date.today()
                end = f"{today.year:04d}-{today.month:02d}"
            elif len(end) == 4:
                end += "-12"
            start_month = int(start[:4]) * 12 + int(start[5:7])
            end_month = int(end[:4]) * 12 + int(end[5:7])
            if end_month >= start_month:
                date_intervals.append((start_month, end_month))
    if date_intervals:
        date_intervals.sort()
        merged = []
        for start_month, end_month in date_intervals:
            if merged and start_month <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end_month))
            else:
                merged.append((start_month, end_month))
        months = sum(end_month - start_month + 1 for start_month, end_month in merged)
        experience_years = round(min(months / 12, 60), 1)
    if experience_years is None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience", flat, re.I)
        if match:
            experience_years = min(float(match.group(1)), 60)

    evidence = {
        "full_name": _evidence(lines, name),
        "email": _evidence(lines, email_match.group(0) if email_match else None, r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
        "phone": _evidence(lines, phone),
        "location": _evidence(lines, location),
        "headline": _evidence(lines, headline),
        "summary": _evidence(lines, summary),
        "skills": _evidence(lines, technical_skills),
        "experience_years": _evidence(lines, experience_years, r"\b\d+(?:\.\d+)?\s*\+?\s*years?\b"),
    }

    expected_sections = ["experience", "education", "skills", "projects"]
    covered = [section for section in expected_sections if sections[section]]
    warnings: list[str] = []
    if not name:
        warnings.append("Candidate name could not be identified confidently. Review the profile.")
    if not email_match:
        warnings.append("No email address was found.")
    if not sections["experience"]:
        warnings.append("No dedicated experience section was detected.")
    if not sections["education"]:
        warnings.append("No dedicated education section was detected.")
    if not technical_skills:
        warnings.append("No known skills were detected. The skill taxonomy may not cover the resume's terminology.")

    found_count = sum(value is not None and value != [] for value in [name, email_match, phone, location, headline, summary, technical_skills, experience, education, projects])
    completeness = round(found_count / 10, 2)
    section_coverage = round(len(covered) / len(expected_sections), 2)
    quality_score = round((completeness * 0.65 + section_coverage * 0.35) * 100)

    return {
        "schema_version": "2.1",
        "identity": {
            "full_name": name,
            "first_name": name.split()[0] if name else None,
            "last_name": " ".join(name.split()[1:]) if name and len(name.split()) > 1 else None,
            "email": email_match.group(0) if email_match else None,
            "phone": phone,
            "location": location,
            "links": links,
        },
        "professional_profile": {
            "headline": headline,
            "summary": summary,
            "total_experience_years": experience_years,
        },
        "skills": {"technical": technical_skills, "soft": soft_skills, "tools_and_platforms": [item for item in technical_skills if item in {"Docker", "Kubernetes", "Git", "Linux", "AWS", "Microsoft Azure", "Google Cloud", "Power BI", "Tableau", "Figma"}]},
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications,
        "achievements": achievements,
        "publications": publications,
        "languages": languages,
        "volunteering": volunteering,
        "sections_detected": sorted(section for section, items in sections.items() if items),
        "field_evidence": evidence,
        "quality": {
            "score": quality_score,
            "completeness": completeness,
            "section_coverage": section_coverage,
            "warnings": warnings,
            "requires_review": bool(warnings) or quality_score < 65,
        },
    }
