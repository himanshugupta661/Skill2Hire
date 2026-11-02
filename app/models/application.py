"""
Application model with status tracking.
"""
from datetime import datetime
from extensions import db


class ApplicationStatus:
    SUBMITTED = 'submitted'
    UNDER_REVIEW = 'under_review'
    SHORTLISTED = 'shortlisted'
    INTERVIEW = 'interview'
    REJECTED = 'rejected'
    HIRED = 'hired'
    WITHDRAWN = 'withdrawn'

    ALL = [SUBMITTED, UNDER_REVIEW, SHORTLISTED, INTERVIEW, REJECTED, HIRED, WITHDRAWN]

    # Valid transitions: status -> list of allowed next statuses
    TRANSITIONS = {
        SUBMITTED: [UNDER_REVIEW, REJECTED, WITHDRAWN],
        UNDER_REVIEW: [SHORTLISTED, REJECTED, WITHDRAWN],
        SHORTLISTED: [INTERVIEW, REJECTED, WITHDRAWN],
        INTERVIEW: [HIRED, REJECTED, WITHDRAWN],
        REJECTED: [],
        HIRED: [],
        WITHDRAWN: [],
    }

    @classmethod
    def can_transition(cls, current, next_status):
        return next_status in cls.TRANSITIONS.get(current, [])


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    applicant_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=True)
    cover_letter = db.Column(db.Text)
    match_score = db.Column(db.Float)
    match_details = db.Column(db.Text)  # JSON string of matching breakdown
    application_status = db.Column(db.String(30), default=ApplicationStatus.SUBMITTED, nullable=False)
    employer_notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = db.relationship('Job', back_populates='applications')
    applicant = db.relationship('User', back_populates='applications')
    resume = db.relationship('Resume', back_populates='applications')
    status_history = db.relationship('ApplicationStatusHistory', back_populates='application',
                                     cascade='all, delete-orphan', order_by='ApplicationStatusHistory.changed_at')

    # Unique constraint - one application per job per user
    __table_args__ = (
        db.UniqueConstraint('job_id', 'applicant_user_id', name='uq_application_job_user'),
    )

    def __repr__(self):
        return f'<Application job={self.job_id} user={self.applicant_user_id} status={self.application_status}>'


class ApplicationStatusHistory(db.Model):
    __tablename__ = 'application_status_history'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    old_status = db.Column(db.String(30))
    new_status = db.Column(db.String(30), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('Application', back_populates='status_history')

    def __repr__(self):
        return f'<StatusHistory app={self.application_id} {self.old_status}->{self.new_status}>'
