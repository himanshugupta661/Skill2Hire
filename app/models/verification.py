"""
Employer Verification Request model.
"""
from datetime import datetime
from extensions import db


class VerificationRequest(db.Model):
    __tablename__ = 'verification_requests'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=False, index=True)
    verification_status = db.Column(db.String(30), nullable=False, default='pending')
    business_registration_number = db.Column(db.String(100))
    gst_number = db.Column(db.String(50))
    company_pan = db.Column(db.String(20))
    registered_address = db.Column(db.Text)
    contact_person = db.Column(db.String(150))
    contact_designation = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    additional_info = db.Column(db.Text)
    # Stored filenames only — paths managed by server, never exposed
    document_filenames = db.Column(db.Text)  # JSON list of stored filenames
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewer_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employer = db.relationship('Employer', back_populates='verification_requests')
    reviewer = db.relationship('User', foreign_keys=[reviewer_user_id])

    @property
    def review_notes(self):
        return self.reviewer_notes

    def __repr__(self):
        return f'<VerificationRequest employer={self.employer_id} status={self.verification_status}>'
