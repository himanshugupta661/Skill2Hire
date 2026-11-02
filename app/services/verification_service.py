"""
Verification Service - employer verification workflow.
"""
import logging
from datetime import datetime
from extensions import db
from app.models.employer import Employer, VerificationStatus
from app.models.verification import VerificationRequest
from app.models.notification import Notification, NotificationType
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def submit_verification_request(employer: Employer, form_data: dict) -> dict:
    """Submit or resubmit a verification request."""
    # Only allow submission if not already approved or pending
    if employer.verification_status == VerificationStatus.APPROVED:
        return {'success': False, 'message': 'Your employer account is already verified.'}

    # Cancel any existing pending requests
    existing = VerificationRequest.query.filter_by(
        employer_id=employer.id, verification_status='pending'
    ).first()
    if existing:
        existing.verification_status = 'superseded'

    req = VerificationRequest(
        employer_id=employer.id,
        verification_status='pending',
        business_registration_number=form_data.get('business_registration_number'),
        gst_number=form_data.get('gst_number'),
        company_pan=form_data.get('company_pan'),
        registered_address=form_data.get('registered_address'),
        contact_person=form_data.get('contact_person'),
        contact_designation=form_data.get('contact_designation'),
        contact_phone=form_data.get('contact_phone'),
        additional_info=form_data.get('additional_info'),
    )
    db.session.add(req)
    employer.verification_status = VerificationStatus.PENDING
    db.session.commit()

    return {'success': True, 'message': 'Verification request submitted. Our team will review it shortly.'}


def approve_verification(request_id: int, reviewer_user_id: int, notes: str = None) -> dict:
    """Admin approves a verification request."""
    req = db.session.get(VerificationRequest, request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}

    req.verification_status = 'approved'
    req.reviewer_user_id = reviewer_user_id
    req.reviewer_notes = notes
    req.reviewed_at = datetime.utcnow()

    employer = req.employer
    employer.verification_status = VerificationStatus.APPROVED

    # Notify employer
    notif = Notification(
        user_id=employer.user_id,
        title='Verification Approved ✅',
        message=f'Your company "{employer.company_name}" has been verified on SKILL2HIRE.',
        notification_type=NotificationType.VERIFICATION_DECISION,
        related_entity_type='employer',
        related_entity_id=employer.id,
    )
    db.session.add(notif)

    AuditLog.log(
        action='employer_verified',
        entity_type='employer',
        entity_id=employer.id,
        description=f'Employer {employer.company_name} verified by admin {reviewer_user_id}',
        actor_user_id=reviewer_user_id,
    )

    db.session.commit()
    return {'success': True, 'message': f'{employer.company_name} has been verified.'}


def reject_verification(request_id: int, reviewer_user_id: int,
                         reason: str, notes: str = None) -> dict:
    """Admin rejects a verification request."""
    req = db.session.get(VerificationRequest, request_id)
    if not req:
        return {'success': False, 'message': 'Request not found.'}

    req.verification_status = 'rejected'
    req.reviewer_user_id = reviewer_user_id
    req.reviewer_notes = notes
    req.rejection_reason = reason
    req.reviewed_at = datetime.utcnow()

    employer = req.employer
    employer.verification_status = VerificationStatus.REJECTED

    notif = Notification(
        user_id=employer.user_id,
        title='Verification Not Approved',
        message=(
            f'Your verification request for "{employer.company_name}" was not approved. '
            f'Reason: {reason}. Please contact support for guidance.'
        ),
        notification_type=NotificationType.VERIFICATION_DECISION,
        related_entity_type='employer',
        related_entity_id=employer.id,
    )
    db.session.add(notif)

    AuditLog.log(
        action='employer_verification_rejected',
        entity_type='employer',
        entity_id=employer.id,
        description=f'Verification rejected by admin {reviewer_user_id}. Reason: {reason}',
        actor_user_id=reviewer_user_id,
    )

    db.session.commit()
    return {'success': True, 'message': 'Verification request rejected.'}
