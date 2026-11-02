"""
SavedJob model - bookmarked jobs by job seekers.
"""
from datetime import datetime
from extensions import db


class SavedJob(db.Model):
    __tablename__ = 'saved_jobs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='saved_jobs')
    job = db.relationship('Job', back_populates='saved_by')

    # Unique constraint - can't save the same job twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'job_id', name='uq_saved_job_user_job'),
    )

    def __repr__(self):
        return f'<SavedJob user={self.user_id} job={self.job_id}>'
