import os
import sys
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from app.models.user import User, UserRole, AccountStatus, SeekerProfile
from app.models.employer import Employer, VerificationStatus
from app.models.job import Job, JobStatus, SourceType


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Create a test admin
        admin = User(
            full_name='Test Admin',
            email='testadmin@sevafirst.org',
            email_normalized='testadmin@sevafirst.org',
            role=UserRole.ADMIN,
            account_status=AccountStatus.ACTIVE
        )
        admin.set_password('Admin@12345')
        db.session.add(admin)

        # Create a test employer
        emp_user = User(
            full_name='Test Recruiter',
            email='recruiter@testcorp.com',
            email_normalized='recruiter@testcorp.com',
            role=UserRole.EMPLOYER,
            account_status=AccountStatus.ACTIVE
        )
        emp_user.set_password('Employer@12345')
        db.session.add(emp_user)
        db.session.flush()

        emp = Employer(
            user_id=emp_user.id,
            company_name='Test Corp Pvt Ltd',
            company_name_normalized='test corp pvt ltd',
            industry='Information Technology',
            verification_status=VerificationStatus.APPROVED,
            is_active=True
        )
        db.session.add(emp)
        db.session.flush()

        # Create a test job
        job = Job(
            employer_id=emp.id,
            company_name=emp.company_name,
            job_title='Senior Python Engineer',
            industry='Information Technology',
            location='Bengaluru, Karnataka',
            work_mode='remote',
            salary_min=15,
            salary_max=25,
            experience_min=3,
            experience_max=6,
            required_skills='Python, Django, PostgreSQL, Docker',
            description='Test role description for automated testing.',
            source_type=SourceType.EMPLOYER,
            job_status=JobStatus.ACTIVE
        )
        db.session.add(job)

        # Create a test seeker
        seeker_user = User(
            full_name='Test Seeker',
            email='seeker@test.com',
            email_normalized='seeker@test.com',
            role=UserRole.SEEKER,
            account_status=AccountStatus.ACTIVE
        )
        seeker_user.set_password('Seeker@12345')
        db.session.add(seeker_user)
        db.session.flush()

        profile = SeekerProfile(
            user_id=seeker_user.id,
            headline='Python Developer',
            skills='Python, Django, Docker',
            years_of_experience=4.0
        )
        db.session.add(profile)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
