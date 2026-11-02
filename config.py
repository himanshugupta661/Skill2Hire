"""
SKILL2HIRE - Configuration Module
"""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'instance', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))  # 5MB
    ALLOWED_EXTENSIONS = {'pdf'}
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Dataset settings
    DATASET_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    DATASET_PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
    DATASET_REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'reports')
    KAGGLE_DATASET_SLUG = 'aaravsharma/indian-job-market-dataset-2025-2026'

    # Matching weights (configurable)
    MATCH_WEIGHT_SKILLS = 0.40
    MATCH_WEIGHT_TEXT = 0.25
    MATCH_WEIGHT_TITLE = 0.15
    MATCH_WEIGHT_EXPERIENCE = 0.10
    MATCH_WEIGHT_LOCATION = 0.10

    # Pagination
    JOBS_PER_PAGE = 20
    USERS_PER_PAGE = 25
    APPLICATIONS_PER_PAGE = 20


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'skill2hire.db')
        if os.path.exists(os.path.join(BASE_DIR, 'instance', 'skill2hire.db'))
        else 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'seva_first.db')
    )


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'tests', 'uploads')
    SECRET_KEY = 'test-secret-key'


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    _default_db = (
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'skill2hire.db')
        if os.path.exists(os.path.join(BASE_DIR, 'instance', 'skill2hire.db'))
        else 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'seva_first.db')
    )
    SQLALCHEMY_DATABASE_URI = _db_url or _default_db


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
