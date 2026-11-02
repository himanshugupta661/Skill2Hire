"""
Analytics Service - platform-wide statistics for admin dashboard.
"""
from datetime import datetime, timedelta
from extensions import db
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.models.application import Application, ApplicationStatus
from app.models.employer import Employer, VerificationStatus
from app.models.fraud_report import FraudReport, ReportStatus


def get_admin_stats():
    """Get comprehensive platform statistics for admin dashboard."""
    return {
        'users': {
            'total': User.query.count(),
            'seekers': User.query.filter_by(role=UserRole.SEEKER).count(),
            'employers': User.query.filter_by(role=UserRole.EMPLOYER).count(),
            'admins': User.query.filter_by(role=UserRole.ADMIN).count(),
        },
        'jobs': {
            'total': Job.query.count(),
            'active': Job.query.filter_by(job_status=JobStatus.ACTIVE).count(),
            'closed': Job.query.filter_by(job_status=JobStatus.CLOSED).count(),
            'suspended': Job.query.filter_by(job_status=JobStatus.SUSPENDED).count(),
            'dataset': Job.query.filter_by(source_type='dataset').count(),
            'employer_posted': Job.query.filter_by(source_type='employer').count(),
        },
        'employers': {
            'total': Employer.query.count(),
            'verified': Employer.query.filter_by(verification_status=VerificationStatus.APPROVED).count(),
            'pending_verification': Employer.query.filter_by(verification_status=VerificationStatus.PENDING).count(),
        },
        'applications': {
            'total': Application.query.count(),
            'submitted': Application.query.filter_by(application_status=ApplicationStatus.SUBMITTED).count(),
            'under_review': Application.query.filter_by(application_status=ApplicationStatus.UNDER_REVIEW).count(),
            'shortlisted': Application.query.filter_by(application_status=ApplicationStatus.SHORTLISTED).count(),
            'interview': Application.query.filter_by(application_status=ApplicationStatus.INTERVIEW).count(),
            'hired': Application.query.filter_by(application_status=ApplicationStatus.HIRED).count(),
            'rejected': Application.query.filter_by(application_status=ApplicationStatus.REJECTED).count(),
        },
        'fraud': {
            'total': FraudReport.query.count(),
            'pending': FraudReport.query.filter_by(report_status=ReportStatus.PENDING).count(),
            'investigating': FraudReport.query.filter_by(report_status=ReportStatus.INVESTIGATING).count(),
        },
    }


def get_jobs_by_category(limit=10):
    """Jobs grouped by industry for chart."""
    from sqlalchemy import func
    result = db.session.query(
        Job.industry, func.count(Job.id).label('count')
    ).filter(
        Job.job_status == JobStatus.ACTIVE,
        Job.industry != None,
        Job.industry != ''
    ).group_by(Job.industry).order_by(func.count(Job.id).desc()).limit(limit).all()
    return [{'label': r.industry, 'count': r.count} for r in result]


def get_applications_by_status():
    """Application status distribution for chart."""
    from sqlalchemy import func
    result = db.session.query(
        Application.application_status, func.count(Application.id).label('count')
    ).group_by(Application.application_status).all()
    return [{'label': r.application_status, 'count': r.count} for r in result]


def get_user_role_distribution():
    """User role distribution."""
    from sqlalchemy import func
    result = db.session.query(
        User.role, func.count(User.id).label('count')
    ).group_by(User.role).all()
    return [{'label': r.role, 'count': r.count} for r in result]


def get_recent_jobs(limit=5):
    """Most recently posted jobs."""
    return Job.query.order_by(Job.created_at.desc()).limit(limit).all()


def get_recent_applications(limit=5):
    """Most recent applications."""
    return Application.query.order_by(Application.submitted_at.desc()).limit(limit).all()
