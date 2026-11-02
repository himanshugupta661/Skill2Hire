"""
Resume model with secure file storage and analysis tracking.
"""
from datetime import datetime
from extensions import db


class AnalysisStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    EMPTY = 'empty'


class Resume(db.Model):
    __tablename__ = 'resumes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), default='pdf')
    file_size = db.Column(db.Integer)
    extracted_text = db.Column(db.Text)
    extracted_skills = db.Column(db.Text)  # Comma-separated
    extracted_name = db.Column(db.String(150))
    extracted_email = db.Column(db.String(200))
    extracted_phone = db.Column(db.String(50))
    analysis_status = db.Column(db.String(20), default=AnalysisStatus.PENDING)
    analysis_notes = db.Column(db.Text)
    is_selected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='resumes')
    applications = db.relationship('Application', back_populates='resume')

    def get_extracted_skills_list(self):
        if not self.extracted_skills:
            return []
        return [s.strip().lower() for s in self.extracted_skills.split(',') if s.strip()]

    @property
    def filename(self):
        return self.original_filename

    def __repr__(self):
        return f'<Resume {self.original_filename} user={self.user_id}>'
