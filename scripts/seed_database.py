"""
SKILL2HIRE - Database Seeder
Seeds users, employers, verification requests, jobs, applications, and fraud reports.
"""
import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from extensions import db
from app.models.user import User, UserRole, AccountStatus, SeekerProfile
from app.models.employer import Employer, VerificationStatus
from app.models.job import Job, JobStatus, SourceType
from app.models.resume import Resume
from app.models.application import Application, ApplicationStatus
from app.models.verification import VerificationRequest
from app.models.saved_job import SavedJob
from app.models.notification import Notification
from app.models.fraud_report import FraudReport, ReportStatus, ReportReason
from app.services.matching_service import get_matching_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('database_seeder')


def seed_database():
    flask_app = create_app()
    with flask_app.app_context():
        logger.info("Initializing database schema...")
        db.create_all()

        # 1. Admin Users (SKILL2HIRE Platform Admins)
        for admin_email in ['admin@skill2hire.com', 'admin@sevafirst.org']:
            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    full_name='SKILL2HIRE Administrator',
                    email=admin_email,
                    email_normalized=admin_email,
                    role=UserRole.ADMIN,
                    account_status=AccountStatus.ACTIVE
                )
                admin.set_password('Admin@12345')
                db.session.add(admin)
                logger.info(f"Created Admin user: {admin_email}")

        # 2. Verified Employers
        employers_data = [
            {
                "email": "hr@tataconsultancy.com",
                "name": "Rajesh Gopinathan",
                "company": "Tata Consultancy Services",
                "industry": "Information Technology",
                "website": "https://www.tcs.com",
                "location": "Mumbai, Maharashtra",
                "size": "500+",
                "verified": True,
                "cin": "L22210MH1995PLC084781",
                "gst": "27AAACT2727Q1ZW",
                "pan": "AAACT2727Q",
                "desc": "Tata Consultancy Services is an Indian multinational information technology services and consulting company headquartered in Mumbai."
            },
            {
                "email": "careers@infosys.com",
                "name": "Salil Parekh",
                "company": "Infosys Limited",
                "industry": "Information Technology",
                "website": "https://www.infosys.com",
                "location": "Bengaluru, Karnataka",
                "size": "500+",
                "verified": True,
                "cin": "L85110KA1981PLC013115",
                "gst": "29AABCI1234P1Z5",
                "pan": "AABCI1234P",
                "desc": "Infosys is a global leader in next-generation digital services and consulting."
            },
            {
                "email": "talent@flipkart.com",
                "name": "Kalyan Krishnamurthy",
                "company": "Flipkart Internet",
                "industry": "E-Commerce & Tech",
                "website": "https://www.flipkart.com",
                "location": "Bengaluru, Karnataka",
                "size": "500+",
                "verified": True,
                "cin": "U51109KA2012PTC066107",
                "gst": "29AABCF9999K1Z2",
                "pan": "AABCF9999K",
                "desc": "Flipkart is India's leading digital commerce ecosystem empowering local sellers and national consumers."
            },
            {
                "email": "hiring@apextech.in",
                "name": "Vikram Sethi",
                "company": "Apex Tech Labs",
                "industry": "FinTech",
                "website": "https://apextech.in",
                "location": "Hyderabad, Telangana",
                "size": "51-200",
                "verified": False,
                "cin": "U72200TG2022PTC159000",
                "gst": "36AAICA7890B1Z3",
                "pan": "AAICA7890B",
                "desc": "High-growth FinTech startup building decentralized liquidity bridges and real-time payment settlement engines."
            }
        ]

        emp_objects = {}
        for ed in employers_data:
            u = User.query.filter_by(email=ed['email']).first()
            if not u:
                u = User(
                    full_name=ed['name'],
                    email=ed['email'],
                    email_normalized=ed['email'].lower(),
                    role=UserRole.EMPLOYER,
                    account_status=AccountStatus.ACTIVE
                )
                u.set_password('Employer@12345')
                db.session.add(u)
                db.session.flush()

                emp = Employer(
                    user_id=u.id,
                    company_name=ed['company'],
                    company_name_normalized=ed['company'].lower(),
                    description=ed['desc'],
                    industry=ed['industry'],
                    website=ed['website'],
                    business_email=ed['email'],
                    location=ed['location'],
                    company_size=ed['size'],
                    verification_status=VerificationStatus.APPROVED if ed['verified'] else VerificationStatus.PENDING,
                    is_active=True
                )
                db.session.add(emp)
                db.session.flush()

                # Add verification request record
                v_req = VerificationRequest(
                    employer_id=emp.id,
                    business_registration_number=ed['cin'],
                    gst_number=ed['gst'],
                    company_pan=ed['pan'],
                    registered_address=f"Registered corporate suite, {ed['location']}",
                    contact_person=ed['name'],
                    contact_designation="Director / Head of People",
                    contact_phone="+91 98111 22334",
                    verification_status=VerificationStatus.APPROVED if ed['verified'] else VerificationStatus.PENDING,
                    reviewed_at=datetime.utcnow() if ed['verified'] else None,
                    reviewer_notes="Automated MCA registry & GST portal match validated." if ed['verified'] else None
                )
                db.session.add(v_req)
                emp_objects[ed['company']] = emp
            else:
                emp_objects[ed['company']] = u.employer

        # 3. Job Seekers & Profiles
        seekers_data = [
            {
                "email": "rahul.sharma@example.com",
                "name": "Rahul Sharma",
                "headline": "Senior Full-Stack Python & Cloud Developer",
                "summary": "Experienced engineer with 5 years crafting distributed Python architectures, microservices with Django and FastAPI, and resilient AWS deployments.",
                "skills": "Python, Django, PostgreSQL, Docker, AWS, REST APIs, Celery, Redis",
                "experience": 5.0,
                "location": "Bengaluru, Karnataka",
                "preferred_roles": "Senior Backend Developer, Python Engineer, Tech Lead",
                "preferred_locations": "Bengaluru, Pune, Remote",
                "preferred_work_mode": "hybrid",
                "min_sal": 15,
                "max_sal": 25,
                "linkedin": "https://linkedin.com/in/rahulsharma-dev",
                "github": "https://github.com/rahulsharma-dev"
            },
            {
                "email": "priya.patel@example.com",
                "name": "Priya Patel",
                "headline": "Machine Learning & NLP Specialist",
                "summary": "Data scientist with 3.5 years researching transformer architectures, developing recommendation engines, and deploying LLM pipelines with PyTorch.",
                "skills": "Python, Machine Learning, Deep Learning, PyTorch, Transformers, NLP, SQL, Docker",
                "experience": 3.5,
                "location": "Bengaluru, Karnataka",
                "preferred_roles": "Machine Learning Engineer, Data Scientist, AI Researcher",
                "preferred_locations": "Bengaluru, Hyderabad, Remote",
                "preferred_work_mode": "onsite",
                "min_sal": 20,
                "max_sal": 35,
                "linkedin": "https://linkedin.com/in/priyapatel-ai",
                "github": "https://github.com/priyapatel-ai"
            },
            {
                "email": "ananya.singh@example.com",
                "name": "Ananya Singh",
                "headline": "Lead Frontend & React Architect",
                "summary": "Passionate UI/UX and web engineer focused on high-throughput design systems, Next.js, TypeScript, and state management at scale.",
                "skills": "React, TypeScript, Node.js, JavaScript, GraphQL, MongoDB, Jest, CSS3",
                "experience": 4.0,
                "location": "Pune, Maharashtra",
                "preferred_roles": "Senior Frontend Developer, Full Stack Engineer",
                "preferred_locations": "Pune, Mumbai, Remote",
                "preferred_work_mode": "remote",
                "min_sal": 14,
                "max_sal": 22,
                "linkedin": "https://linkedin.com/in/ananyasingh-ui",
                "github": "https://github.com/ananyasingh-ui"
            }
        ]

        seeker_objects = {}
        for sd in seekers_data:
            u = User.query.filter_by(email=sd['email']).first()
            if not u:
                u = User(
                    full_name=sd['name'],
                    email=sd['email'],
                    email_normalized=sd['email'].lower(),
                    role=UserRole.SEEKER,
                    account_status=AccountStatus.ACTIVE
                )
                u.set_password('Seeker@12345')
                db.session.add(u)
                db.session.flush()

                p = SeekerProfile(
                    user_id=u.id,
                    headline=sd['headline'],
                    summary=sd['summary'],
                    skills=sd['skills'],
                    years_of_experience=sd['experience'],
                    current_location=sd['location'],
                    preferred_roles=sd['preferred_roles'],
                    preferred_locations=sd['preferred_locations'],
                    preferred_work_mode=sd['preferred_work_mode'],
                    expected_salary_min=sd['min_sal'],
                    expected_salary_max=sd['max_sal'],
                    linkedin_url=sd['linkedin'],
                    github_url=sd['github']
                )
                p.compute_completion()
                db.session.add(p)

                # Create sample resume
                res_name = f"{sd['name'].replace(' ', '_')}_Resume.pdf"
                res = Resume(
                    user_id=u.id,
                    original_filename=res_name,
                    stored_filename=f"seed_{u.id}_{res_name}",
                    file_path=os.path.join(flask_app.config['UPLOAD_FOLDER'], f"seed_{u.id}_{res_name}"),
                    extracted_text=f"{sd['name']}\n{sd['headline']}\nSkills: {sd['skills']}\nExperience: {sd['experience']} years.\n{sd['summary']}",
                    extracted_skills=sd['skills'],
                    is_selected=True
                )
                db.session.add(res)
                seeker_objects[sd['email']] = (u, res)
            else:
                seeker_objects[sd['email']] = (u, u.resumes[0] if u.resumes else None)

        db.session.commit()

        # 4. Employer Direct Job Listings
        tcs = emp_objects.get("Tata Consultancy Services")
        infosys = emp_objects.get("Infosys Limited")
        flipkart = emp_objects.get("Flipkart Internet")
        apex = emp_objects.get("Apex Tech Labs")

        jobs_list = [
            {
                "emp": tcs,
                "title": "Principal Python Backend Architect",
                "industry": "Information Technology",
                "location": "Bengaluru, Karnataka",
                "mode": "hybrid",
                "sal_min": 20, "sal_max": 30,
                "exp_min": 6, "exp_max": 10,
                "exp_req": "6-10 years",
                "req_skills": "Python, Django, AWS, Docker, PostgreSQL, REST APIs, Microservices",
                "pref_skills": "Kubernetes, Redis, Kafka",
                "desc": "Lead architecture of large-scale enterprise services processing tens of millions of daily transactions. Strong background in Python system optimization and cloud deployment."
            },
            {
                "emp": infosys,
                "title": "Senior Frontend React Engineer",
                "industry": "Information Technology",
                "location": "Pune, Maharashtra",
                "mode": "remote",
                "sal_min": 16, "sal_max": 24,
                "exp_min": 4, "exp_max": 7,
                "exp_req": "4-7 years",
                "req_skills": "React, TypeScript, Node.js, GraphQL, JavaScript, CSS3",
                "pref_skills": "Next.js, Jest, Cypress",
                "desc": "Craft high-performance user interfaces and reusable UI component frameworks for Fortune 500 digital banking platforms."
            },
            {
                "emp": flipkart,
                "title": "Staff AI / ML Algorithm Engineer",
                "industry": "E-Commerce & Tech",
                "location": "Bengaluru, Karnataka",
                "mode": "onsite",
                "sal_min": 30, "sal_max": 48,
                "exp_min": 4, "exp_max": 8,
                "exp_req": "4-8 years",
                "req_skills": "Python, Machine Learning, Deep Learning, PyTorch, Transformers, NLP, SQL",
                "pref_skills": "CUDA, Triton, Vector DB, Distributed Training",
                "desc": "Innovate on massive-scale vector search, personalized ranking, and multimodal generative AI agents powering millions of shoppers."
            },
            {
                "emp": apex,
                "title": "FinTech Backend Python Developer",
                "industry": "FinTech",
                "location": "Hyderabad, Telangana",
                "mode": "hybrid",
                "sal_min": 12, "sal_max": 18,
                "exp_min": 2, "exp_max": 5,
                "exp_req": "2-5 years",
                "req_skills": "Python, FastAPI, PostgreSQL, Docker, Redis",
                "pref_skills": "Solidity, Web3, Celery",
                "desc": "Develop secure payment webhooks, high-frequency settlement daemons, and double-entry ledger engines."
            }
        ]

        created_jobs = []
        for jd in jobs_list:
            if not jd['emp']:
                continue
            j = Job.query.filter_by(job_title=jd['title'], employer_id=jd['emp'].id).first()
            if not j:
                j = Job(
                    employer_id=jd['emp'].id,
                    company_name=jd['emp'].company_name,
                    job_title=jd['title'],
                    industry=jd['industry'],
                    location=jd['location'],
                    work_mode=jd['mode'],
                    salary_min=jd['sal_min'],
                    salary_max=jd['sal_max'],
                    salary_currency='INR',
                    experience_min=jd['exp_min'],
                    experience_max=jd['exp_max'],
                    experience_requirement=jd['exp_req'],
                    education_requirement="B.Tech / B.E. / M.Tech in Computer Science or related",
                    required_skills=jd['req_skills'],
                    preferred_skills=jd['pref_skills'],
                    description=jd['desc'],
                    source_type=SourceType.EMPLOYER,
                    job_status=JobStatus.ACTIVE,
                    employment_type="Full-time",
                    openings=3,
                    application_deadline=datetime.utcnow() + timedelta(days=45)
                )
                db.session.add(j)
                created_jobs.append(j)
            else:
                created_jobs.append(j)

        db.session.commit()

        # 5. Seed Applications & AI Matches
        matching_svc = get_matching_service()
        rahul_user, rahul_resume = seeker_objects["rahul.sharma@example.com"]
        priya_user, priya_resume = seeker_objects["priya.patel@example.com"]
        ananya_user, ananya_resume = seeker_objects["ananya.singh@example.com"]

        apps_to_create = [
            # Rahul applied to TCS Python role
            {
                "user": rahul_user,
                "resume": rahul_resume,
                "job_title": "Principal Python Backend Architect",
                "status": ApplicationStatus.SHORTLISTED,
                "note": "Excited to bring my 5 years of Python microservice scaling to the TCS engineering team."
            },
            # Rahul applied to Apex FinTech role
            {
                "user": rahul_user,
                "resume": rahul_resume,
                "job_title": "FinTech Backend Python Developer",
                "status": ApplicationStatus.UNDER_REVIEW,
                "note": "My background in distributed queuing aligns with high-frequency settlement."
            },
            # Priya applied to Flipkart AI role
            {
                "user": priya_user,
                "resume": priya_resume,
                "job_title": "Staff AI / ML Algorithm Engineer",
                "status": ApplicationStatus.INTERVIEW,
                "note": "Deep experience in Transformer fine-tuning and vector indexing systems."
            },
            # Ananya applied to Infosys React role
            {
                "user": ananya_user,
                "resume": ananya_resume,
                "job_title": "Senior Frontend React Engineer",
                "status": ApplicationStatus.HIRED,
                "note": "Led component system development for banking portals; ready to deliver impact immediately."
            }
        ]

        for ad in apps_to_create:
            target_job = Job.query.filter_by(job_title=ad['job_title']).first()
            if target_job:
                existing_app = Application.query.filter_by(job_id=target_job.id, applicant_user_id=ad['user'].id).first()
                if not existing_app:
                    # Calculate real match score
                    p = ad['user'].seeker_profile
                    p_dict = {
                        'skills': p.skills,
                        'years_of_experience': p.years_of_experience,
                        'preferred_roles': p.preferred_roles,
                        'preferred_locations': p.preferred_locations,
                        'preferred_work_mode': p.preferred_work_mode,
                        'headline': p.headline,
                        'summary': p.summary,
                    }
                    j_dict = {
                        'job_title': target_job.job_title,
                        'required_skills': target_job.required_skills,
                        'preferred_skills': target_job.preferred_skills,
                        'description': target_job.description,
                        'location': target_job.location,
                        'work_mode': target_job.work_mode,
                        'experience_min': target_job.experience_min,
                        'experience_max': target_job.experience_max,
                    }
                    m_res = matching_svc.compute_match(p_dict, j_dict)

                    app_obj = Application(
                        job_id=target_job.id,
                        applicant_user_id=ad['user'].id,
                        resume_id=ad['resume'].id if ad['resume'] else None,
                        cover_letter=ad['note'],
                        application_status=ad['status'],
                        match_score=m_res['score'],
                        match_details=json.dumps(m_res),
                        submitted_at=datetime.utcnow() - timedelta(days=2)
                    )
                    db.session.add(app_obj)

        # 6. Saved Jobs for Rahul
        flipkart_job = Job.query.filter(Job.company_name.ilike('%flipkart%')).first()
        if flipkart_job:
            if not SavedJob.query.filter_by(user_id=rahul_user.id, job_id=flipkart_job.id).first():
                db.session.add(SavedJob(user_id=rahul_user.id, job_id=flipkart_job.id))

        # 7. Notifications
        notifs = [
            (rahul_user.id, "Application Shortlisted!", "Tata Consultancy Services has shortlisted your application for Principal Python Backend Architect.", "info"),
            (priya_user.id, "Interview Scheduled!", "Flipkart Internet scheduled your technical round for Staff AI / ML Algorithm Engineer.", "success"),
            (ananya_user.id, "Offer Extended!", "Congratulations! Infosys Limited extended an employment offer.", "success"),
            (tcs.user_id, "New Candidate Application", "Rahul Sharma applied for Principal Python Backend Architect (AI Match: 92%).", "info")
        ]
        for uid, title, msg, ntype in notifs:
            n = Notification(user_id=uid, title=title, message=msg, notification_type=ntype)
            db.session.add(n)

        # 8. Sample Fraud Report (for Admin Triage demonstration)
        reported_job = Job.query.filter(Job.job_title.ilike('%python%')).first()
        if reported_job and not FraudReport.query.first():
            fr = FraudReport(
                reporter_user_id=rahul_user.id,
                job_id=reported_job.id,
                report_reason=ReportReason.MONEY_REQUEST,
                report_description="Received an unverified WhatsApp message from someone claiming to represent the recruitment department asking for a Rs 1,500 security deposit for laptop courier.",
                report_status=ReportStatus.INVESTIGATING,
                internal_notes="Admin contacted verified HR. Disconfirmed official agency involvement; caution advisory issued."
            )
            db.session.add(fr)

        db.session.commit()
        logger.info("Database seeding successfully finished!")


if __name__ == '__main__':
    seed_database()
