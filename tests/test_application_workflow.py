"""
Unit tests for Seeker Application Submission and Fraud Reporting.
"""
from extensions import db
from app.models.user import User
from app.models.job import Job
from app.models.application import Application, ApplicationStatus
from app.models.fraud_report import FraudReport, ReportStatus, ReportReason
from app.services.application_service import submit_application, withdraw_application, update_application_status


def test_application_lifecycle(app):
    with app.app_context():
        seeker = User.query.filter_by(email='seeker@test.com').first()
        job = Job.query.filter_by(job_title='Senior Python Engineer').first()

        # Submit Application
        sub_res = submit_application(
            user_id=seeker.id,
            job_id=job.id,
            resume_id=None,
            cover_letter="Passionate about Python scaling.",
            match_result={'score': 85.5, 'breakdown': {}, 'matching_skills': ['python']}
        )
        assert sub_res['success'] is True

        app_obj = Application.query.filter_by(job_id=job.id, applicant_user_id=seeker.id).first()
        assert app_obj is not None
        assert app_obj.application_status == ApplicationStatus.SUBMITTED
        assert app_obj.match_score == 85.5

        # Employer updates status to Under Review
        up_res = update_application_status(app_obj.id, ApplicationStatus.UNDER_REVIEW, changed_by_user_id=2)
        assert up_res['success'] is True
        assert app_obj.application_status == ApplicationStatus.UNDER_REVIEW

        # Employer shortlists candidate
        up_res2 = update_application_status(app_obj.id, ApplicationStatus.SHORTLISTED, changed_by_user_id=2)
        assert up_res2['success'] is True
        assert app_obj.application_status == ApplicationStatus.SHORTLISTED


def test_fraud_reporting(app):
    with app.app_context():
        seeker = User.query.filter_by(email='seeker@test.com').first()
        job = Job.query.filter_by(job_title='Senior Python Engineer').first()

        # Report job
        report = FraudReport(
            reporter_user_id=seeker.id,
            job_id=job.id,
            report_reason=ReportReason.MONEY_REQUEST,
            report_description="Third-party agency asked for upfront payment.",
            report_status=ReportStatus.PENDING
        )
        db.session.add(report)
        db.session.commit()

        saved_report = FraudReport.query.filter_by(job_id=job.id).first()
        assert saved_report is not None
        assert saved_report.reason == ReportReason.MONEY_REQUEST
        assert saved_report.report_status == ReportStatus.PENDING
