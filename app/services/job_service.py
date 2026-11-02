"""
Job Service - search, filter, paginate, and manage job listings.
"""
import logging
from datetime import datetime
from typing import Optional
from extensions import db
from app.models.job import Job, JobStatus, SourceType
from app.models.saved_job import SavedJob
from app.models.application import Application

logger = logging.getLogger(__name__)


def search_jobs(
    keyword=None, location=None, industry=None, employment_type=None,
    work_mode=None, experience_min=None, experience_max=None,
    salary_min=None, source_type=None, company=None,
    status=JobStatus.ACTIVE, page=1, per_page=20, sort='newest'
):
    """
    Search and filter job listings with pagination.
    Returns (jobs_paginated, total_count)
    """
    query = Job.query.filter_by(job_status=status)

    if keyword:
        kw = f'%{keyword}%'
        query = query.filter(
            db.or_(
                Job.job_title.ilike(kw),
                Job.description.ilike(kw),
                Job.required_skills.ilike(kw),
                Job.company_name.ilike(kw)
            )
        )
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    if industry:
        query = query.filter(Job.industry.ilike(f'%{industry}%'))
    if employment_type:
        query = query.filter(Job.employment_type.ilike(f'%{employment_type}%'))
    if work_mode:
        query = query.filter(Job.work_mode.ilike(f'%{work_mode}%'))
    if company:
        query = query.filter(Job.company_name.ilike(f'%{company}%'))
    if experience_min is not None:
        query = query.filter(
            db.or_(Job.experience_max >= experience_min, Job.experience_max == None)
        )
    if experience_max is not None:
        query = query.filter(
            db.or_(Job.experience_min <= experience_max, Job.experience_min == None)
        )
    if salary_min is not None:
        query = query.filter(
            db.or_(Job.salary_max >= salary_min, Job.salary_max == None)
        )
    if source_type:
        query = query.filter(Job.source_type == source_type)

    # Sorting
    if sort == 'newest':
        query = query.order_by(Job.created_at.desc())
    elif sort == 'title':
        query = query.order_by(Job.job_title.asc())
    elif sort == 'salary_high':
        query = query.order_by(Job.salary_max.desc().nullslast())
    else:
        query = query.order_by(Job.created_at.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated


def get_job_by_id(job_id: int) -> Optional[Job]:
    return db.session.get(Job, job_id)


def get_featured_jobs(limit=6):
    """Get recent active jobs for the homepage."""
    return Job.query.filter_by(job_status=JobStatus.ACTIVE).order_by(
        Job.created_at.desc()
    ).limit(limit).all()


def get_job_categories():
    """Get job categories with counts."""
    from sqlalchemy import func
    result = db.session.query(
        Job.industry, func.count(Job.id).label('count')
    ).filter(
        Job.job_status == JobStatus.ACTIVE,
        Job.industry != None,
        Job.industry != ''
    ).group_by(Job.industry).order_by(func.count(Job.id).desc()).limit(12).all()
    return result


def get_top_companies(limit=8):
    """Get companies with most active listings."""
    from sqlalchemy import func
    result = db.session.query(
        Job.company_name, func.count(Job.id).label('count')
    ).filter(
        Job.job_status == JobStatus.ACTIVE
    ).group_by(Job.company_name).order_by(func.count(Job.id).desc()).limit(limit).all()
    return result


def toggle_save_job(user_id: int, job_id: int) -> dict:
    """Save or unsave a job. Returns {'saved': bool, 'message': str}"""
    job = get_job_by_id(job_id)
    if not job:
        return {'error': 'Job not found.'}

    existing = SavedJob.query.filter_by(user_id=user_id, job_id=job_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return {'saved': False, 'message': 'Job removed from saved list.'}
    else:
        saved = SavedJob(user_id=user_id, job_id=job_id)
        db.session.add(saved)
        db.session.commit()
        return {'saved': True, 'message': 'Job saved successfully.'}


def is_job_saved(user_id: int, job_id: int) -> bool:
    return SavedJob.query.filter_by(user_id=user_id, job_id=job_id).first() is not None


def is_job_applied(user_id: int, job_id: int) -> bool:
    return Application.query.filter_by(
        applicant_user_id=user_id, job_id=job_id
    ).first() is not None


def get_platform_stats():
    """Get platform-wide statistics from the database."""
    from app.models.user import User, UserRole
    from app.models.employer import Employer, VerificationStatus
    return {
        'total_jobs': Job.query.filter_by(job_status=JobStatus.ACTIVE).count(),
        'total_companies': db.session.query(db.func.count(db.func.distinct(Job.company_name))).scalar() or 0,
        'total_seekers': User.query.filter_by(role=UserRole.SEEKER).count(),
        'total_employers': User.query.filter_by(role=UserRole.EMPLOYER).count(),
        'verified_employers': Employer.query.filter_by(
            verification_status=VerificationStatus.APPROVED
        ).count(),
        'total_applications': Application.query.count(),
    }
