"""
Unit tests for AI Matchmaking Engine (TF-IDF, Skill Extraction & Multi-metric Scoring).
"""
from app.services.matching_service import get_matching_service


def test_matching_service_high_compatibility(app):
    with app.app_context():
        svc = get_matching_service()
        candidate = {
            'skills': 'Python, Django, PostgreSQL, Docker, AWS, REST APIs',
            'years_of_experience': 5.0,
            'preferred_roles': 'Backend Developer, Python Engineer',
            'preferred_locations': 'Bengaluru, Remote',
            'preferred_work_mode': 'remote',
            'headline': 'Senior Backend Python Specialist',
            'summary': '5 years scaling Django web microservices on AWS with Docker.'
        }
        job = {
            'job_title': 'Senior Python Engineer',
            'required_skills': 'Python, Django, PostgreSQL, Docker',
            'preferred_skills': 'AWS, REST APIs',
            'description': 'Seeking an experienced backend developer in Python and Django.',
            'location': 'Bengaluru, Karnataka',
            'work_mode': 'remote',
            'experience_min': 3,
            'experience_max': 6,
        }
        result = svc.compute_match(candidate, job)

        assert 'score' in result
        assert result['score'] >= 70.0  # High match
        assert 'matching_skills' in result
        assert len(result['matching_skills']) > 0
        assert 'python' in [s.lower() for s in result['matching_skills']]


def test_matching_service_low_compatibility(app):
    with app.app_context():
        svc = get_matching_service()
        candidate = {
            'skills': 'Graphic Design, Photoshop, Figma, Illustrator',
            'years_of_experience': 1.0,
            'preferred_roles': 'Graphic Designer',
            'preferred_locations': 'Kolkata',
            'preferred_work_mode': 'onsite',
            'headline': 'Junior Creative Designer',
            'summary': 'Passionate about vector graphics and branding.'
        }
        job = {
            'job_title': 'Lead Embedded Systems & C++ Architect',
            'required_skills': 'C++, RTOS, Linux Kernel, ARM, Assembly',
            'preferred_skills': 'Verilog, FPGA',
            'description': 'Hardware device driver engineering.',
            'location': 'Bengaluru, Karnataka',
            'work_mode': 'onsite',
            'experience_min': 8,
            'experience_max': 12,
        }
        result = svc.compute_match(candidate, job)

        assert result['score'] < 30.0  # Low match
        assert len(result.get('missing_skills', [])) > 0
