from app.models.entities import Candidate, ResumeDocument, Job, Application, MatchResult, Interview, ActivityEvent


def candidate_out(candidate: Candidate, include_profile: bool = True) -> dict:
    result = {
        "id": candidate.id, "full_name": candidate.full_name, "email": candidate.email, "phone": candidate.phone,
        "location": candidate.location, "headline": candidate.headline, "summary": candidate.summary,
        "total_experience_years": candidate.total_experience_years,
        "skills": candidate.skills or [], "soft_skills": candidate.soft_skills or [], "tools": candidate.tools or [],
        "links": candidate.links or {}, "extraction_quality": candidate.extraction_quality or {},
        "document_count": len(candidate.documents), "created_at": candidate.created_at, "updated_at": candidate.updated_at,
    }
    if include_profile:
        result.update({
            "experience": candidate.experience or [], "education": candidate.education or [], "projects": candidate.projects or [],
            "certifications": candidate.certifications or [], "achievements": candidate.achievements or [],
            "publications": candidate.publications or [], "languages": candidate.languages or [],
            "volunteering": candidate.volunteering or [],
        })
    return result


def document_out(document: ResumeDocument) -> dict:
    return {
        "id": document.id, "candidate_id": document.candidate_id, "original_filename": document.original_filename,
        "content_type": document.content_type, "file_size": document.file_size, "page_count": document.page_count,
        "parser_version": document.parser_version, "extraction_method": document.extraction_method,
        "warnings": document.warnings or [], "created_at": document.created_at,
    }


def job_out(job: Job) -> dict:
    return {
        "id": job.id, "title": job.title, "department": job.department, "location": job.location,
        "work_mode": job.work_mode, "employment_type": job.employment_type, "description": job.description,
        "responsibilities": job.responsibilities or [], "required_skills": job.required_skills or [],
        "preferred_skills": job.preferred_skills or [], "minimum_experience": job.minimum_experience,
        "maximum_experience": job.maximum_experience, "education_requirement": job.education_requirement,
        "status": job.status, "application_count": len(job.applications), "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def application_out(application: Application) -> dict:
    return {
        "id": application.id, "candidate_id": application.candidate_id, "job_id": application.job_id,
        "candidate_name": application.candidate.full_name, "candidate_email": application.candidate.email,
        "candidate_headline": application.candidate.headline, "candidate_experience": application.candidate.total_experience_years,
        "candidate_skills": application.candidate.skills or [], "job_title": application.job.title,
        "department": application.job.department, "stage": application.stage, "source": application.source,
        "notes": application.notes, "created_at": application.created_at, "updated_at": application.updated_at,
    }


def match_out(match: MatchResult, candidate: Candidate) -> dict:
    return {
        "id": match.id, "candidate_id": candidate.id, "candidate_name": candidate.full_name,
        "candidate_email": candidate.email, "candidate_headline": candidate.headline,
        "candidate_experience": candidate.total_experience_years, "overall_score": match.overall_score,
        "component_scores": match.component_scores or {}, "matched_skills": match.matched_skills or [],
        "missing_skills": match.missing_skills or [], "explanation": match.explanation or [],
        "matching_method": match.matching_method, "computed_at": match.computed_at,
    }


def interview_out(interview: Interview) -> dict:
    app = interview.application
    return {
        "id": interview.id, "application_id": interview.application_id, "candidate_id": app.candidate_id,
        "candidate_name": app.candidate.full_name, "job_title": app.job.title, "title": interview.title,
        "interview_type": interview.interview_type, "scheduled_at": interview.scheduled_at,
        "duration_minutes": interview.duration_minutes, "location_or_link": interview.location_or_link,
        "interviewers": interview.interviewers or [], "status": interview.status,
        "scorecard": interview.scorecard or {}, "notes": interview.notes,
    }


def activity_out(event: ActivityEvent) -> dict:
    return {
        "id": event.id, "entity_type": event.entity_type, "entity_id": event.entity_id,
        "action": event.action, "description": event.description, "metadata": event.metadata_json or {},
        "actor_user_id": event.actor_user_id, "actor_email": event.actor_email,
        "created_at": event.created_at,
    }
