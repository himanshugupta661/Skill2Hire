"""
User model - core authentication entity.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class UserRole:
    SEEKER = 'seeker'
    EMPLOYER = 'employer'
    ADMIN = 'admin'


class AccountStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True, index=True)
    email_normalized = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.SEEKER)
    account_status = db.Column(db.String(20), nullable=False, default=AccountStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)

    # Relationships
    seeker_profile = db.relationship('SeekerProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    employer = db.relationship('Employer', back_populates='user', uselist=False, cascade='all, delete-orphan')
    resumes = db.relationship('Resume', back_populates='user', cascade='all, delete-orphan')
    applications = db.relationship('Application', back_populates='applicant', cascade='all, delete-orphan')
    saved_jobs = db.relationship('SavedJob', back_populates='user', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    fraud_reports = db.relationship('FraudReport', back_populates='reporter', foreign_keys='FraudReport.reporter_user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_seeker(self):
        return self.role == UserRole.SEEKER

    @property
    def is_employer(self):
        return self.role == UserRole.EMPLOYER

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_active(self):
        return self.account_status == AccountStatus.ACTIVE

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'


class SeekerProfile(db.Model):
    __tablename__ = 'seeker_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    headline = db.Column(db.String(200))
    summary = db.Column(db.Text)
    skills = db.Column(db.Text)  # Comma-separated skill list
    education = db.Column(db.Text)  # JSON-serializable text
    experience = db.Column(db.Text)  # JSON-serializable text
    years_of_experience = db.Column(db.Float, default=0.0)
    current_location = db.Column(db.String(200))
    preferred_roles = db.Column(db.String(500))
    preferred_locations = db.Column(db.String(500))
    preferred_industries = db.Column(db.String(500))
    preferred_employment_type = db.Column(db.String(100))
    preferred_work_mode = db.Column(db.String(50))
    expected_salary_min = db.Column(db.Integer)
    expected_salary_max = db.Column(db.Integer)
    portfolio_url = db.Column(db.String(300))
    linkedin_url = db.Column(db.String(300))
    github_url = db.Column(db.String(300))
    profile_completion = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='seeker_profile')

    def get_skills_list(self):
        if not self.skills:
            return []
        return [s.strip().lower() for s in self.skills.split(',') if s.strip()]

    def compute_completion(self):
        fields = [self.headline, self.summary, self.skills,
                  self.education, self.experience, self.preferred_roles,
                  self.preferred_locations, self.years_of_experience]
        filled = sum(1 for f in fields if f)
        self.profile_completion = int((filled / len(fields)) * 100)
        return self.profile_completion

    @property
    def profile_completion_pct(self):
        return self.profile_completion or 0

    def __repr__(self):
        return f'<SeekerProfile user_id={self.user_id}>'
