"""
Public routes - homepage, job listings, company directory, info pages.
"""
from flask import Blueprint, render_template, request, redirect, url_for
from app.services.job_service import (
    search_jobs, get_job_by_id, get_featured_jobs,
    get_job_categories, get_top_companies, get_platform_stats,
    is_job_saved, is_job_applied
)
from app.models.fraud_report import FraudReport, ReportReason
from flask_login import current_user
from extensions import db

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    featured_jobs = get_featured_jobs(6)
    categories = get_job_categories()
    top_companies = get_top_companies(6)
    stats = get_platform_stats()
    return render_template('index.html',
                           featured_jobs=featured_jobs,
                           categories=categories,
                           top_companies=top_companies,
                           stats=stats)


@public_bp.route('/jobs')
def jobs():
    keyword = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    industry = request.args.get('industry', '').strip()
    employment_type = request.args.get('employment_type', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    company = request.args.get('company', '').strip()
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)

    paginated = search_jobs(
        keyword=keyword or None,
        location=location or None,
        industry=industry or None,
        employment_type=employment_type or None,
        work_mode=work_mode or None,
        company=company or None,
        sort=sort, page=page, per_page=20
    )

    categories = get_job_categories()

    # Check saved/applied status for authenticated seekers
    saved_ids = set()
    applied_ids = set()
    if current_user.is_authenticated and current_user.is_seeker:
        from app.models.saved_job import SavedJob
        from app.models.application import Application
        saved_ids = {s.job_id for s in current_user.saved_jobs}
        applied_ids = {a.job_id for a in current_user.applications}

    return render_template('jobs/list.html',
                           pagination=paginated,
                           jobs=paginated.items,
                           keyword=keyword,
                           location=location,
                           industry=industry,
                           employment_type=employment_type,
                           work_mode=work_mode,
                           company=company,
                           sort=sort,
                           categories=categories,
                           saved_ids=saved_ids,
                           applied_ids=applied_ids)


@public_bp.route('/jobs/<int:job_id>', endpoint='job_details')
@public_bp.route('/jobs/<int:job_id>', endpoint='job_detail')
def job_detail(job_id):
    job = get_job_by_id(job_id)
    if not job:
        from flask import abort
        abort(404)

    is_saved = False
    is_applied = False
    match_result = None

    if current_user.is_authenticated and current_user.is_seeker:
        is_saved = is_job_saved(current_user.id, job_id)
        is_applied = is_job_applied(current_user.id, job_id)

        if current_user.seeker_profile:
            from app.services.matching_service import get_matching_service
            svc = get_matching_service()
            profile = current_user.seeker_profile
            profile_dict = {
                'skills': profile.skills,
                'years_of_experience': profile.years_of_experience,
                'preferred_roles': profile.preferred_roles,
                'preferred_locations': profile.preferred_locations,
                'preferred_work_mode': profile.preferred_work_mode,
                'headline': profile.headline,
                'summary': profile.summary,
                'preferred_industries': profile.preferred_industries,
            }
            # Include selected resume text
            selected_resume = next(
                (r for r in current_user.resumes if r.is_selected), None
            )
            if selected_resume:
                profile_dict['resume_text'] = selected_resume.extracted_text or ''

            job_dict = {
                'job_title': job.job_title,
                'required_skills': job.required_skills,
                'preferred_skills': job.preferred_skills,
                'description': job.description,
                'location': job.location,
                'work_mode': job.work_mode,
                'experience_min': job.experience_min,
                'experience_max': job.experience_max,
                'industry': job.industry,
            }
            match_result = svc.compute_match(profile_dict, job_dict)

    fraud_count = FraudReport.query.filter_by(job_id=job_id).count()

    return render_template('jobs/details.html',
                           job=job,
                           is_saved=is_saved,
                           is_applied=is_applied,
                           match_result=match_result,
                           fraud_count=fraud_count)


@public_bp.route('/companies')
def companies():
    from app.models.employer import Employer
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    industry = request.args.get('industry', '').strip()

    query = Employer.query.filter_by(is_active=True)
    if search:
        query = query.filter(Employer.company_name.ilike(f'%{search}%'))
    if industry:
        query = query.filter(Employer.industry.ilike(f'%{industry}%'))

    paginated = query.order_by(Employer.company_name.asc()).paginate(
        page=page, per_page=24, error_out=False
    )
    return render_template('companies.html', pagination=paginated,
                           employers=paginated.items, search=search, industry=industry)


@public_bp.route('/companies/<int:employer_id>')
def company_detail(employer_id):
    from app.models.employer import Employer
    employer = db.session.get(Employer, employer_id)
    if not employer:
        from flask import abort
        abort(404)
    jobs = employer.jobs[:10]
    return render_template('company_detail.html', employer=employer, jobs=jobs)


@public_bp.route('/about')
def about():
    return render_template('about.html')


@public_bp.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')


@public_bp.route('/contact')
def contact():
    return render_template('contact.html')
