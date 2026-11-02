"""
Job listing model.
"""
from datetime import datetime
from extensions import db


class JobStatus:
    DRAFT = 'draft'
    ACTIVE = 'active'
    CLOSED = 'closed'
    SUSPENDED = 'suspended'
    EXPIRED = 'expired'


class SourceType:
    EMPLOYER = 'employer'
    DATASET = 'dataset'


class EmploymentType:
    FULL_TIME = 'Full-Time'
    PART_TIME = 'Part-Time'
    CONTRACT = 'Contract'
    INTERNSHIP = 'Internship'
    FREELANCE = 'Freelance'
    TEMPORARY = 'Temporary'


class WorkMode:
    ONSITE = 'Onsite'
    REMOTE = 'Remote'
    HYBRID = 'Hybrid'


class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employers.id'), nullable=True, index=True)
    source_type = db.Column(db.String(20), default=SourceType.EMPLOYER, nullable=False)
    source_dataset = db.Column(db.String(100))
    source_record_id = db.Column(db.String(100), index=True)

    # Job Details
    job_title = db.Column(db.String(200), nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    required_skills = db.Column(db.Text)       # Comma-separated
    preferred_skills = db.Column(db.Text)       # Comma-separated
    experience_requirement = db.Column(db.String(100))
    experience_min = db.Column(db.Float)
    experience_max = db.Column(db.Float)
    education_requirement = db.Column(db.String(200))

    # Location & type
    location = db.Column(db.String(200), index=True)
    employment_type = db.Column(db.String(50))
    work_mode = db.Column(db.String(30))
    industry = db.Column(db.String(100), index=True)

    # Salary
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    salary_currency = db.Column(db.String(10), default='INR')

    # Dates
    posting_date = db.Column(db.DateTime)
    application_deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Status
    job_status = db.Column(db.String(20), default=JobStatus.ACTIVE, nullable=False, index=True)
    openings = db.Column(db.Integer, default=1)
    is_flagged = db.Column(db.Boolean, default=False)

    # Relationships
    employer = db.relationship('Employer', back_populates='jobs', foreign_keys=[employer_id])
    applications = db.relationship('Application', back_populates='job', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedJob', back_populates='job', cascade='all, delete-orphan')
    fraud_reports = db.relationship('FraudReport', back_populates='job',
                                    foreign_keys='FraudReport.job_id')

    # Unique constraint for dataset imports
    __table_args__ = (
        db.Index('idx_source_record', 'source_dataset', 'source_record_id'),
    )

    def get_required_skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip().lower() for s in self.required_skills.split(',') if s.strip()]

    def get_preferred_skills_list(self):
        if not self.preferred_skills:
            return []
        return [s.strip().lower() for s in self.preferred_skills.split(',') if s.strip()]

    @property
    def is_active(self):
        return self.job_status == JobStatus.ACTIVE

    @property
    def is_dataset_job(self):
        return self.source_type == SourceType.DATASET

    @property
    def applications_count(self):
        return len(self.applications)

    def __repr__(self):
        return f'<Job {self.job_title} at {self.company_name}>'
