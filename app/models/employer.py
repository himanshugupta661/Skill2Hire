"""
Employer and Company Profile model.
"""
from datetime import datetime
from extensions import db


class VerificationStatus:
    NOT_SUBMITTED = 'not_submitted'
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    MORE_INFO = 'more_info'


class Employer(db.Model):
    __tablename__ = 'employers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(200), nullable=False)
    company_name_normalized = db.Column(db.String(200))
    description = db.Column(db.Text)
    industry = db.Column(db.String(100))
    website = db.Column(db.String(300))
    business_email = db.Column(db.String(200))
    location = db.Column(db.String(200))
    company_size = db.Column(db.String(50))
    logo_path = db.Column(db.String(300))
    verification_status = db.Column(db.String(30), default=VerificationStatus.NOT_SUBMITTED, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='employer')
    jobs = db.relationship('Job', back_populates='employer', cascade='all, delete-orphan',
                           foreign_keys='Job.employer_id')
    verification_requests = db.relationship('VerificationRequest', back_populates='employer',
                                            cascade='all, delete-orphan')
    fraud_reports = db.relationship('FraudReport', back_populates='employer',
                                    foreign_keys='FraudReport.employer_id')

    @property
    def is_verified(self):
        return self.verification_status == VerificationStatus.APPROVED

    @property
    def active_jobs_count(self):
        from app.models.job import Job, JobStatus
        return Job.query.filter_by(employer_id=self.id, job_status=JobStatus.ACTIVE).count()

    def __repr__(self):
        return f'<Employer {self.company_name}>'
