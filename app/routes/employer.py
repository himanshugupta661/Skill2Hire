"""
Employer routes — dashboard, profile, jobs, applicants, verification.
"""
import json
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, abort)
from flask_login import login_required, current_user
from extensions import db
from app.utils.decorators import employer_required
from app.models.job import Job, JobStatus, SourceType
from app.models.application import Application, ApplicationStatus
from app.models.employer import Employer, VerificationStatus
from app.services.application_service import update_application_status
from app.services.verification_service import submit_verification_request
from app.services.matching_service import get_matching_service
from app.utils.helpers import parse_salary, parse_experience

employer_bp = Blueprint('employer', __name__)


def _get_employer():
    """Get the current employer profile or abort."""
    emp = current_user.employer
    if not emp:
        abort(403)
    return emp


@employer_bp.route('/dashboard')
@employer_required
def dashboard():
    emp = _get_employer()
    jobs = Job.query.filter_by(employer_id=emp.id).order_by(Job.created_at.desc()).all()
    app_count = sum(j.applications_count for j in jobs)
    active_jobs = [j for j in jobs if j.job_status == JobStatus.ACTIVE]

    # Recent applications across all employer's jobs
    job_ids = [j.id for j in jobs]
    recent_apps = []
    if job_ids:
        recent_apps = Application.query.filter(
            Application.job_id.in_(job_ids)
        ).order_by(Application.submitted_at.desc()).limit(10).all()

    app_stats = {}
    for status in ApplicationStatus.ALL:
        app_stats[status] = sum(
            1 for a in recent_apps if a.application_status == status
        )

    from app.services.notification_service import get_user_notifications, get_unread_count
    notifications = get_user_notifications(current_user.id, 5)
    unread = get_unread_count(current_user.id)

    return render_template('employer/dashboard.html',
                           employer=emp,
                           jobs=jobs[:5],
                           total_jobs=len(jobs),
                           active_jobs_count=len(active_jobs),
                           app_count=app_count,
                           recent_apps=recent_apps,
                           app_stats=app_stats,
                           notifications=notifications,
                           unread_count=unread)


@employer_bp.route('/profile', methods=['GET', 'POST'])
@employer_required
def profile():
    emp = _get_employer()
    if request.method == 'POST':
        emp.company_name = request.form.get('company_name', '').strip()[:200]
        emp.description = request.form.get('description', '').strip()[:3000]
        emp.industry = request.form.get('industry', '').strip()[:100]
        emp.website = request.form.get('website', '').strip()[:300]
        emp.business_email = request.form.get('business_email', '').strip()[:200]
        emp.location = request.form.get('location', '').strip()[:200]
        emp.company_size = request.form.get('company_size', '').strip()[:50]
        emp.company_name_normalized = emp.company_name.lower()
        current_user.full_name = request.form.get('contact_name', current_user.full_name).strip()
        db.session.commit()
        flash('Company profile updated.', 'success')
        return redirect(url_for('employer.profile'))
    return render_template('employer/profile.html', employer=emp)


@employer_bp.route('/jobs')
@employer_required
def jobs():
    emp = _get_employer()
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = Job.query.filter_by(employer_id=emp.id)
    if status_filter:
        query = query.filter_by(job_status=status_filter)
    paginated = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('employer/jobs.html',
                           pagination=paginated, jobs=paginated.items,
                           employer=emp, status_filter=status_filter,
                           statuses=[JobStatus.DRAFT, JobStatus.ACTIVE, JobStatus.CLOSED])


@employer_bp.route('/jobs/new', methods=['GET', 'POST'])
@employer_required
def new_job():
    emp = _get_employer()
    if request.method == 'POST':
        job = _create_or_update_job(None, emp)
        if job:
            db.session.commit()
            flash('Job listing created successfully.', 'success')
            return redirect(url_for('employer.jobs'))
    return render_template('employer/job_form.html', employer=emp, job=None)


@employer_bp.route('/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@employer_required
def edit_job(job_id):
    emp = _get_employer()
    job = Job.query.filter_by(id=job_id, employer_id=emp.id).first_or_404()
    if request.method == 'POST':
        _create_or_update_job(job, emp)
        db.session.commit()
        flash('Job listing updated.', 'success')
        return redirect(url_for('employer.jobs'))
    return render_template('employer/job_form.html', employer=emp, job=job)


@employer_bp.route('/jobs/<int:job_id>/close', methods=['POST'])
@employer_required
def close_job(job_id):
    emp = _get_employer()
    job = Job.query.filter_by(id=job_id, employer_id=emp.id).first_or_404()
    job.job_status = JobStatus.CLOSED
    db.session.commit()
    flash('Job listing closed.', 'info')
    return redirect(url_for('employer.jobs'))


@employer_bp.route('/jobs/<int:job_id>/applicants')
@employer_required
def applicants(job_id):
    emp = _get_employer()
    job = Job.query.filter_by(id=job_id, employer_id=emp.id).first_or_404()
    status_filter = request.args.get('status', '')
    query = Application.query.filter_by(job_id=job_id)
    if status_filter:
        query = query.filter_by(application_status=status_filter)
    apps = query.order_by(Application.submitted_at.desc()).all()

    # Compute match scores for applicants
    svc = get_matching_service()
    job_dict = {
        'job_title': job.job_title,
        'required_skills': job.required_skills,
        'preferred_skills': job.preferred_skills,
        'description': job.description,
        'location': job.location,
        'work_mode': job.work_mode,
        'experience_min': job.experience_min,
        'experience_max': job.experience_max,
    }
    enriched_apps = []
    for app in apps:
        profile = app.applicant.seeker_profile
        match = None
        if profile:
            profile_dict = {
                'skills': profile.skills,
                'years_of_experience': profile.years_of_experience,
                'preferred_roles': profile.preferred_roles,
                'preferred_locations': profile.preferred_locations,
                'preferred_work_mode': profile.preferred_work_mode,
                'headline': profile.headline,
                'summary': profile.summary,
            }
            match = svc.compute_match(profile_dict, job_dict)
        enriched_apps.append({'application': app, 'match': match})

    enriched_apps.sort(key=lambda x: x['match']['score'] if x['match'] else 0, reverse=True)

    return render_template('employer/applicants.html',
                           job=job, employer=emp,
                           enriched_apps=enriched_apps,
                           status_filter=status_filter,
                           statuses=ApplicationStatus.ALL)


@employer_bp.route('/applicants/<int:app_id>/status', methods=['POST'])
@employer_required
def update_status(app_id):
    emp = _get_employer()
    app = db.session.get(Application, app_id)
    if not app or app.job.employer_id != emp.id:
        abort(403)
    new_status = request.form.get('status', '')
    notes = request.form.get('notes', '').strip()[:1000]
    result = update_application_status(app_id, new_status, current_user.id, notes or None)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('employer.applicants', job_id=app.job_id))


@employer_bp.route('/verification', methods=['GET', 'POST'])
@employer_required
def verification():
    emp = _get_employer()
    from app.models.verification import VerificationRequest
    existing_requests = VerificationRequest.query.filter_by(
        employer_id=emp.id
    ).order_by(VerificationRequest.submitted_at.desc()).all()

    if request.method == 'POST':
        form_data = {
            'business_registration_number': request.form.get('business_registration_number', '').strip(),
            'gst_number': request.form.get('gst_number', '').strip(),
            'company_pan': request.form.get('company_pan', '').strip(),
            'registered_address': request.form.get('registered_address', '').strip(),
            'contact_person': request.form.get('contact_person', '').strip(),
            'contact_designation': request.form.get('contact_designation', '').strip(),
            'contact_phone': request.form.get('contact_phone', '').strip(),
            'additional_info': request.form.get('additional_info', '').strip(),
        }
        result = submit_verification_request(emp, form_data)
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'warning')
        return redirect(url_for('employer.verification'))

    return render_template('employer/verification.html',
                           employer=emp, requests=existing_requests)


def _create_or_update_job(job, emp):
    """Create or update a job listing from form data."""
    title = request.form.get('job_title', '').strip()
    if not title:
        flash('Job title is required.', 'danger')
        return None

    salary_str = request.form.get('salary_range', '')
    sal_min, sal_max = parse_salary(salary_str)
    exp_str = request.form.get('experience_requirement', '')
    exp_min, exp_max = parse_experience(exp_str)

    status_val = request.form.get('job_status', JobStatus.ACTIVE)
    if status_val not in [JobStatus.DRAFT, JobStatus.ACTIVE, JobStatus.CLOSED]:
        status_val = JobStatus.ACTIVE

    deadline_str = request.form.get('application_deadline', '')
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        except ValueError:
            pass

    if job is None:
        job = Job(employer_id=emp.id, source_type=SourceType.EMPLOYER,
                  company_name=emp.company_name)
        db.session.add(job)

    job.job_title = title[:200]
    job.description = request.form.get('description', '').strip()
    job.required_skills = request.form.get('required_skills', '').strip()[:1000]
    job.preferred_skills = request.form.get('preferred_skills', '').strip()[:1000]
    job.experience_requirement = exp_str[:100]
    job.experience_min = exp_min
    job.experience_max = exp_max
    job.education_requirement = request.form.get('education_requirement', '').strip()[:200]
    job.location = request.form.get('location', '').strip()[:200]
    job.employment_type = request.form.get('employment_type', '').strip()
    job.work_mode = request.form.get('work_mode', '').strip()
    job.industry = request.form.get('industry', '').strip()[:100]
    job.salary_min = sal_min
    job.salary_max = sal_max
    job.salary_currency = 'INR'
    job.openings = int(request.form.get('openings', 1) or 1)
    job.application_deadline = deadline
    job.job_status = status_val
    job.updated_at = datetime.utcnow()
    return job
