"""
Fraud Report model.
"""
from datetime import datetime
from extensions import db


class ReportReason:
    FAKE_JOB = 'fake_job'
    MONEY_REQUEST = 'money_request'
    MISLEADING = 'misleading'
    IMPERSONATION = 'impersonation'
    SUSPICIOUS_CONTACT = 'suspicious_contact'
    DUPLICATE_SPAM = 'duplicate_spam'
    OTHER = 'other'

    LABELS = {
        FAKE_JOB: 'Suspected Fake Job',
        MONEY_REQUEST: 'Request for Money / Suspicious Fees',
        MISLEADING: 'Misleading Job Description',
        IMPERSONATION: 'Impersonation of a Company',
        SUSPICIOUS_CONTACT: 'Suspicious Contact Information',
        DUPLICATE_SPAM: 'Duplicate or Spam Listing',
        OTHER: 'Other Concerns',
    }


class ReportStatus:
    PENDING = 'pending'
    INVESTIGATING = 'investigating'
    RESOLVED = 'resolved'
    DISMISSED = 'dismissed'


class FraudReport(db.Model):
    __tablename__ = 'fraud_reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True, index=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=True, index=True)
    report_reason = db.Column(db.String(50), nullable=False)
    report_description = db.Column(db.Text)
    report_status = db.Column(db.String(30), default=ReportStatus.PENDING, nullable=False)
    internal_notes = db.Column(db.Text)
    assigned_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    # Relationships
    reporter = db.relationship('User', back_populates='fraud_reports', foreign_keys=[reporter_user_id])
    job = db.relationship('Job', back_populates='fraud_reports', foreign_keys=[job_id])
    employer = db.relationship('Employer', back_populates='fraud_reports', foreign_keys=[employer_id])
    assigned_admin = db.relationship('User', foreign_keys=[assigned_admin_id])

    @property
    def reason(self):
        return self.report_reason

    @property
    def description(self):
        return self.report_description

    def __repr__(self):
        return f'<FraudReport id={self.id} reason={self.report_reason} status={self.report_status}>'
