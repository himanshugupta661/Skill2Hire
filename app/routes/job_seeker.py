"""
Job Seeker routes — dashboard, profile, applications, resumes, matches.
"""
import os
import json
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, current_app, abort, send_file)
from flask_login import login_required, current_user
from extensions import db
from app.utils.decorators import seeker_required
from app.models.user import SeekerProfile
from app.models.application import Application, ApplicationStatus
from app.models.resume import Resume
from app.models.saved_job import SavedJob
from app.services.job_service import search_jobs, get_job_by_id
from app.services.application_service import submit_application, withdraw_application
from app.services.matching_service import get_matching_service
from app.services.resume_service import (
    validate_pdf_upload, generate_safe_filename, analyze_resume
)
from app.services.notification_service import get_user_notifications, get_unread_count, mark_all_read

seeker_bp = Blueprint('seeker', __name__)


@seeker_bp.route('/dashboard')
@seeker_required
def dashboard():
    profile = current_user.seeker_profile
    apps = Application.query.filter_by(applicant_user_id=current_user.id).all()
    app_stats = {
        'total': len(apps),
        'submitted': sum(1 for a in apps if a.application_status == ApplicationStatus.SUBMITTED),
        'under_review': sum(1 for a in apps if a.application_status == ApplicationStatus.UNDER_REVIEW),
        'shortlisted': sum(1 for a in apps if a.application_status == ApplicationStatus.SHORTLISTED),
        'interview': sum(1 for a in apps if a.application_status == ApplicationStatus.INTERVIEW),
        'rejected': sum(1 for a in apps if a.application_status == ApplicationStatus.REJECTED),
        'hired': sum(1 for a in apps if a.application_status == ApplicationStatus.HIRED),
    }
    saved_count = SavedJob.query.filter_by(user_id=current_user.id).count()
    recent_apps = sorted(apps, key=lambda a: a.submitted_at, reverse=True)[:5]
    notifications = get_user_notifications(current_user.id, 5)
    unread = get_unread_count(current_user.id)

    return render_template('seeker/dashboard.html',
                           profile=profile,
                           app_stats=app_stats,
                           saved_count=saved_count,
                           recent_apps=recent_apps,
                           notifications=notifications,
                           unread_count=unread)


@seeker_bp.route('/profile', methods=['GET', 'POST'])
@seeker_required
def profile():
    p = current_user.seeker_profile
    if not p:
        p = SeekerProfile(user_id=current_user.id)
        db.session.add(p)
        db.session.commit()

    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
        p.headline = request.form.get('headline', '').strip()[:200]
        p.summary = request.form.get('summary', '').strip()[:2000]
        p.skills = request.form.get('skills', '').strip()[:1000]
        p.education = request.form.get('education', '').strip()[:2000]
        p.experience = request.form.get('experience', '').strip()[:3000]
        try:
            p.years_of_experience = float(request.form.get('years_of_experience', 0) or 0)
        except ValueError:
            p.years_of_experience = 0.0
        p.current_location = request.form.get('current_location', '').strip()[:200]
        p.preferred_roles = request.form.get('preferred_roles', '').strip()[:500]
        p.preferred_locations = request.form.get('preferred_locations', '').strip()[:300]
        p.preferred_industries = request.form.get('preferred_industries', '').strip()[:300]
        p.preferred_employment_type = request.form.get('preferred_employment_type', '').strip()
        p.preferred_work_mode = request.form.get('preferred_work_mode', '').strip()
        p.portfolio_url = request.form.get('portfolio_url', '').strip()[:300]
        p.linkedin_url = request.form.get('linkedin_url', '').strip()[:300]
        p.github_url = request.form.get('github_url', '').strip()[:300]
        try:
            p.expected_salary_min = int(request.form.get('expected_salary_min') or 0) or None
            p.expected_salary_max = int(request.form.get('expected_salary_max') or 0) or None
        except ValueError:
            pass
        p.compute_completion()
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('seeker.profile'))

    return render_template('seeker/profile.html', profile=p)


@seeker_bp.route('/applications')
@seeker_required
def applications():
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    query = Application.query.filter_by(applicant_user_id=current_user.id)
    if status_filter:
        query = query.filter_by(application_status=status_filter)
    paginated = query.order_by(Application.submitted_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('seeker/applications.html',
                           pagination=paginated,
                           applications=paginated.items,
                           status_filter=status_filter,
                           statuses=ApplicationStatus.ALL)


@seeker_bp.route('/applications/<int:app_id>')
@seeker_required
def application_detail(app_id):
    app = Application.query.filter_by(
        id=app_id, applicant_user_id=current_user.id
    ).first_or_404()
    match_details = None
    if app.match_details:
        try:
            match_details = json.loads(app.match_details)
        except Exception:
            pass
    return render_template('seeker/application_details.html',
                           application=app, match_details=match_details)


@seeker_bp.route('/applications/<int:app_id>/withdraw', methods=['POST'])
@seeker_required
def withdraw_app(app_id):
    result = withdraw_application(app_id, current_user.id)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('seeker.applications'))


@seeker_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@seeker_required
def apply(job_id):
    job = get_job_by_id(job_id)
    if not job or not job.is_active:
        flash('This job is not available for application.', 'danger')
        return redirect(url_for('public.jobs'))

    resumes = current_user.resumes

    if request.method == 'POST':
        resume_id = request.form.get('resume_id', type=int)
        cover_letter = request.form.get('cover_letter', '').strip()[:3000]

        # Compute match
        profile = current_user.seeker_profile
        match_result = None
        if profile:
            svc = get_matching_service()
            profile_dict = {
                'skills': profile.skills,
                'years_of_experience': profile.years_of_experience,
                'preferred_roles': profile.preferred_roles,
                'preferred_locations': profile.preferred_locations,
                'preferred_work_mode': profile.preferred_work_mode,
                'headline': profile.headline,
                'summary': profile.summary,
            }
            selected_resume = next((r for r in resumes if r.is_selected), None)
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
            }
            match_result = svc.compute_match(profile_dict, job_dict)

        result = submit_application(
            user_id=current_user.id,
            job_id=job_id,
            resume_id=resume_id if resume_id else None,
            cover_letter=cover_letter,
            match_result=match_result
        )
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('seeker.applications'))
        else:
            flash(result['message'], 'danger')

    return render_template('seeker/apply.html', job=job, resumes=resumes)


@seeker_bp.route('/saved-jobs')
@seeker_required
def saved_jobs():
    page = request.args.get('page', 1, type=int)
    paginated = SavedJob.query.filter_by(user_id=current_user.id).order_by(
        SavedJob.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    return render_template('jobs/saved.html',
                           pagination=paginated, saved_jobs=paginated.items)


@seeker_bp.route('/matches')
@seeker_required
def matches():
    profile = current_user.seeker_profile
    if not profile or not profile.skills:
        flash('Complete your profile with skills to see job matches.', 'info')
        return redirect(url_for('seeker.profile'))

    # Build profile dict
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
    selected_resume = next((r for r in current_user.resumes if r.is_selected), None)
    if selected_resume:
        profile_dict['resume_text'] = selected_resume.extracted_text or ''

    # Get paginated jobs
    from app.models.job import Job, JobStatus
    page = request.args.get('page', 1, type=int)
    industry_filter = request.args.get('industry', '').strip()
    min_score = request.args.get('min_score', 0, type=int)

    query = Job.query.filter_by(job_status=JobStatus.ACTIVE)
    if industry_filter:
        query = query.filter(Job.industry.ilike(f'%{industry_filter}%'))
    jobs_to_rank = query.order_by(Job.created_at.desc()).limit(200).all()

    svc = get_matching_service()
    ranked = []
    for j in jobs_to_rank:
        job_dict = {
            'id': j.id,
            'job_title': j.job_title,
            'company_name': j.company_name,
            'required_skills': j.required_skills,
            'preferred_skills': j.preferred_skills,
            'description': j.description,
            'location': j.location,
            'work_mode': j.work_mode,
            'experience_min': j.experience_min,
            'experience_max': j.experience_max,
            'industry': j.industry,
            'salary_min': j.salary_min,
            'salary_max': j.salary_max,
            'salary_currency': j.salary_currency,
            'source_type': j.source_type,
        }
        match = svc.compute_match(profile_dict, job_dict)
        if match['score'] >= min_score:
            ranked.append({'job': j, 'match': match})

    ranked.sort(key=lambda x: x['match']['score'], reverse=True)

    # Simple pagination
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    total = len(ranked)
    page_items = ranked[start:end]

    from app.models.saved_job import SavedJob
    saved_ids = {s.job_id for s in current_user.saved_jobs}

    categories = []
    from app.services.job_service import get_job_categories
    categories = get_job_categories()

    return render_template('seeker/matches.html',
                           ranked=page_items,
                           profile=profile,
                           saved_ids=saved_ids,
                           total=total,
                           page=page,
                           per_page=per_page,
                           industry_filter=industry_filter,
                           min_score=min_score,
                           categories=categories)


@seeker_bp.route('/resume', methods=['GET', 'POST'])
@seeker_required
def resume():
    resumes = Resume.query.filter_by(user_id=current_user.id).order_by(
        Resume.created_at.desc()
    ).all()

    if request.method == 'POST':
        action = request.form.get('action', 'upload')

        if action == 'upload':
            if 'resume_file' not in request.files:
                flash('No file selected.', 'danger')
                return redirect(url_for('seeker.resume'))

            file = request.files['resume_file']
            is_valid, error_msg = validate_pdf_upload(file)
            if not is_valid:
                flash(error_msg, 'danger')
                return redirect(url_for('seeker.resume'))

            # Check file size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)
            if file_size > max_size:
                flash(f'File too large. Maximum size is {max_size // (1024*1024)}MB.', 'danger')
                return redirect(url_for('seeker.resume'))

            stored_name = generate_safe_filename(file.filename, current_user.id)
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, stored_name)
            file.save(file_path)

            # Save record
            resume_obj = Resume(
                user_id=current_user.id,
                original_filename=file.filename[:255],
                stored_filename=stored_name,
                file_path=file_path,
                file_size=file_size,
            )
            db.session.add(resume_obj)
            db.session.flush()

            # Run analysis
            analysis = analyze_resume(file_path, current_user.id)
            resume_obj.analysis_status = analysis['status']
            resume_obj.extracted_text = analysis['text'][:50000] if analysis['text'] else None
            resume_obj.extracted_skills = ', '.join(analysis['skills'])
            resume_obj.extracted_email = analysis.get('email')
            resume_obj.extracted_phone = analysis.get('phone')
            resume_obj.analysis_notes = analysis.get('notes', '')

            db.session.commit()
            flash('Resume uploaded and analyzed. Review the extracted information below.', 'success')
            return redirect(url_for('seeker.resume'))

        elif action == 'select':
            resume_id = request.form.get('resume_id', type=int)
            # Deselect all others
            Resume.query.filter_by(user_id=current_user.id).update({'is_selected': False})
            Resume.query.filter_by(id=resume_id, user_id=current_user.id).update({'is_selected': True})
            db.session.commit()
            flash('Resume set as active.', 'success')
            return redirect(url_for('seeker.resume'))

        elif action == 'delete':
            resume_id = request.form.get('resume_id', type=int)
            r = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
            if r:
                # Delete the file safely
                from app.utils.security import is_safe_path
                if is_safe_path(current_app.config['UPLOAD_FOLDER'], r.file_path):
                    try:
                        os.remove(r.file_path)
                    except OSError:
                        pass
                db.session.delete(r)
                db.session.commit()
                flash('Resume deleted.', 'success')
            return redirect(url_for('seeker.resume'))

    return render_template('seeker/resume.html', resumes=resumes)


@seeker_bp.route('/notifications/mark-read', methods=['POST'])
@seeker_required
def mark_notifications_read():
    mark_all_read(current_user.id)
    return redirect(request.referrer or url_for('seeker.dashboard'))
