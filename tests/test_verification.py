"""
Unit tests for Employer Verification workflow (submission, approval, rejection).
"""
from extensions import db
from app.models.employer import Employer, VerificationStatus
from app.models.verification import VerificationRequest
from app.services.verification_service import submit_verification_request, approve_verification, reject_verification


def test_verification_workflow(app):
    with app.app_context():
        # Retrieve employer
        emp = Employer.query.filter_by(company_name='Test Corp Pvt Ltd').first()
        emp.verification_status = VerificationStatus.NOT_SUBMITTED
        db.session.commit()

        # Submit verification request
        form_data = {
            'business_registration_number': 'U72900KA2021PTC145678',
            'gst_number': '29ABCDE1234F1Z5',
            'company_pan': 'ABCDE1234F',
            'registered_address': 'Brigade Gateway, Bengaluru',
            'contact_person': 'Test Recruiter',
            'contact_designation': 'HR Lead',
            'contact_phone': '+91 9876543210',
            'additional_info': 'Official MCA certificate attached'
        }
        res = submit_verification_request(emp, form_data)
        assert res['success'] is True
        assert emp.verification_status == VerificationStatus.PENDING

        req = VerificationRequest.query.filter_by(employer_id=emp.id).first()
        assert req is not None
        assert req.business_registration_number == 'U72900KA2021PTC145678'

        # Admin approves request
        app_res = approve_verification(req.id, reviewer_user_id=1, notes="All MCA documents match.")
        assert app_res['success'] is True
        assert emp.verification_status == VerificationStatus.APPROVED
        assert emp.is_verified is True
