"""
Application Service - submit, track, and manage job applications.
"""
import json
import logging
from datetime import datetime
from extensions import db
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.job import Job, JobStatus
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)


def submit_application(user_id: int, job_id: int, resume_id=None,
                        cover_letter=None, match_result=None) -> dict:
    """
    Submit a job application.
    Returns {'success': bool, 'message': str, 'application': Application or None}
    """
    job = db.session.get(Job, job_id)
    if not job:
        return {'success': False, 'message': 'Job not found.'}

    if job.job_status != JobStatus.ACTIVE:
        return {'success': False, 'message': 'This job is no longer accepting applications.'}

    if job.application_deadline and job.application_deadline < datetime.utcnow():
        return {'success': False, 'message': 'The application deadline has passed.'}

    # Check for duplicate
    existing = Application.query.filter_by(
        applicant_user_id=user_id, job_id=job_id
    ).first()
    if existing:
        return {'success': False, 'message': 'You have already applied for this job.'}

    match_score = None
    match_details = None
    if match_result:
        match_score = match_result.get('score')
        match_details = json.dumps({
            'breakdown': match_result.get('breakdown', {}),
            'explanation': match_result.get('explanation', ''),
        })

    app = Application(
        job_id=job_id,
        applicant_user_id=user_id,
        resume_id=resume_id,
        cover_letter=cover_letter,
        match_score=match_score,
        match_details=match_details,
        application_status=ApplicationStatus.SUBMITTED,
    )
    db.session.add(app)
    db.session.flush()  # Get app.id

    # Record status history
    history = ApplicationStatusHistory(
        application_id=app.id,
        old_status=None,
        new_status=ApplicationStatus.SUBMITTED,
        changed_by_user_id=user_id,
    )
    db.session.add(history)

    # Notify the seeker
    notif = Notification(
        user_id=user_id,
        title='Application Submitted',
        message=f'Your application for "{job.job_title}" at {job.company_name} was submitted successfully.',
        notification_type=NotificationType.APPLICATION_SUBMITTED,
        related_entity_type='application',
        related_entity_id=app.id,
    )
    db.session.add(notif)

    db.session.commit()
    return {'success': True, 'message': 'Application submitted successfully.', 'application': app}


def update_application_status(application_id: int, new_status: str,
                               changed_by_user_id: int, notes=None) -> dict:
    """
    Update application status with transition validation.
    """
    app = db.session.get(Application, application_id)
    if not app:
        return {'success': False, 'message': 'Application not found.'}

    if not ApplicationStatus.can_transition(app.application_status, new_status):
        return {
            'success': False,
            'message': f'Cannot transition from {app.application_status} to {new_status}.'
        }

    old_status = app.application_status
    app.application_status = new_status
    app.updated_at = datetime.utcnow()

    if notes:
        app.employer_notes = notes

    history = ApplicationStatusHistory(
        application_id=application_id,
        old_status=old_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        notes=notes,
    )
    db.session.add(history)

    # Notify the applicant
    status_labels = {
        ApplicationStatus.UNDER_REVIEW: 'Your application is under review',
        ApplicationStatus.SHORTLISTED: 'You have been shortlisted! 🎉',
        ApplicationStatus.INTERVIEW: 'You have been invited for an interview! 🎯',
        ApplicationStatus.REJECTED: 'Your application was not selected this time',
        ApplicationStatus.HIRED: 'Congratulations! You have been hired! 🎊',
        ApplicationStatus.WITHDRAWN: 'Application withdrawn',
    }
    if new_status in status_labels:
        notif = Notification(
            user_id=app.applicant_user_id,
            title='Application Update',
            message=f'{status_labels[new_status]} — {app.job.job_title} at {app.job.company_name}.',
            notification_type=NotificationType.APPLICATION_STATUS,
            related_entity_type='application',
            related_entity_id=application_id,
        )
        db.session.add(notif)

    db.session.commit()
    return {'success': True, 'message': f'Status updated to {new_status}.'}


def withdraw_application(application_id: int, user_id: int) -> dict:
    """Allow applicant to withdraw their own application."""
    app = Application.query.filter_by(
        id=application_id, applicant_user_id=user_id
    ).first()
    if not app:
        return {'success': False, 'message': 'Application not found.'}

    if app.application_status in [ApplicationStatus.HIRED, ApplicationStatus.REJECTED,
                                   ApplicationStatus.WITHDRAWN]:
        return {'success': False, 'message': f'Cannot withdraw a {app.application_status} application.'}

    return update_application_status(
        application_id, ApplicationStatus.WITHDRAWN, user_id, 'Withdrawn by applicant'
    )
