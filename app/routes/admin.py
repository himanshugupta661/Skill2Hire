"""
Admin routes — dashboard, user management, verification, fraud reports, dataset status.
All endpoints are protected by admin_required decorator (backend enforced).
"""
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, abort, jsonify)
from flask_login import current_user
from extensions import db
from app.utils.decorators import admin_required
from app.models.user import User, UserRole, AccountStatus
from app.models.job import Job, JobStatus
from app.models.employer import Employer, VerificationStatus
from app.models.application import Application
from app.models.verification import VerificationRequest
from app.models.fraud_report import FraudReport, ReportStatus
from app.models.audit_log import AuditLog
from app.services.verification_service import approve_verification, reject_verification
from app.services.analytics_service import (
    get_admin_stats, get_jobs_by_category, get_applications_by_status,
    get_user_role_distribution, get_recent_jobs, get_recent_applications
)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = get_admin_stats()
    category_chart = get_jobs_by_category(10)
    app_status_chart = get_applications_by_status()
    user_chart = get_user_role_distribution()
    recent_jobs = get_recent_jobs(5)
    recent_apps = get_recent_applications(5)
    return render_template('admin/dashboard.html',
                           stats=stats,
                           category_chart=category_chart,
                           app_status_chart=app_status_chart,
                           user_chart=user_chart,
                           recent_jobs=recent_jobs,
                           recent_apps=recent_apps)


@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    role_filter = request.args.get('role', '')
    query = User.query
    if search:
        query = query.filter(
            db.or_(User.full_name.ilike(f'%{search}%'),
                   User.email.ilike(f'%{search}%'))
        )
    if role_filter:
        query = query.filter_by(role=role_filter)
    paginated = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template('admin/users.html',
                           pagination=paginated, users=paginated.items,
                           search=search, role_filter=role_filter,
                           roles=[UserRole.SEEKER, UserRole.EMPLOYER, UserRole.ADMIN])


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", 'danger')
        return redirect(url_for('admin.users'))

    if user.account_status == AccountStatus.ACTIVE:
        user.account_status = AccountStatus.SUSPENDED
        action = 'suspended'
    else:
        user.account_status = AccountStatus.ACTIVE
        action = 'reactivated'

    AuditLog.log(
        action=f'user_{action}',
        entity_type='user', entity_id=user.id,
        description=f'Admin {current_user.email} {action} user {user.email}',
        actor_user_id=current_user.id
    )
    db.session.commit()
    flash(f'User account {action}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/jobs')
@admin_required
def jobs():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    source_filter = request.args.get('source', '')
    query = Job.query
    if search:
        query = query.filter(
            db.or_(Job.job_title.ilike(f'%{search}%'),
                   Job.company_name.ilike(f'%{search}%'))
        )
    if status_filter:
        query = query.filter_by(job_status=status_filter)
    if source_filter:
        query = query.filter_by(source_type=source_filter)
    paginated = query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template('admin/jobs.html',
                           pagination=paginated, jobs=paginated.items,
                           search=search, status_filter=status_filter,
                           source_filter=source_filter)


@admin_bp.route('/jobs/<int:job_id>/suspend', methods=['POST'])
@admin_required
def suspend_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        abort(404)
    job.job_status = JobStatus.SUSPENDED
    AuditLog.log(
        action='job_suspended',
        entity_type='job', entity_id=job_id,
        description=f'Admin suspended job: {job.job_title}',
        actor_user_id=current_user.id
    )
    db.session.commit()
    flash(f'Job "{job.job_title}" has been suspended.', 'warning')
    return redirect(url_for('admin.jobs'))


@admin_bp.route('/employers')
@admin_required
def employers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    query = Employer.query
    if search:
        query = query.filter(Employer.company_name.ilike(f'%{search}%'))
    if status_filter:
        query = query.filter_by(verification_status=status_filter)
    paginated = query.order_by(Employer.created_at.desc()).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template('admin/employers.html',
                           pagination=paginated, employers=paginated.items,
                           search=search, status_filter=status_filter)


@admin_bp.route('/verification-requests')
@admin_required
def verification_requests():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'pending')
    query = VerificationRequest.query
    if status_filter:
        query = query.filter_by(verification_status=status_filter)
    paginated = query.order_by(VerificationRequest.submitted_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/verification_requests.html',
                           pagination=paginated, requests=paginated.items,
                           status_filter=status_filter)


@admin_bp.route('/verification-requests/<int:req_id>/approve', methods=['POST'])
@admin_required
def approve_request(req_id):
    notes = request.form.get('notes', '').strip()
    result = approve_verification(req_id, current_user.id, notes)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('admin.verification_requests'))


@admin_bp.route('/verification-requests/<int:req_id>/reject', methods=['POST'])
@admin_required
def reject_request(req_id):
    reason = request.form.get('reason', '').strip()
    notes = request.form.get('notes', '').strip()
    if not reason:
        flash('A rejection reason is required.', 'danger')
        return redirect(url_for('admin.verification_requests'))
    result = reject_verification(req_id, current_user.id, reason, notes)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    return redirect(url_for('admin.verification_requests'))


@admin_bp.route('/fraud-reports')
@admin_required
def fraud_reports():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = FraudReport.query
    if status_filter:
        query = query.filter_by(report_status=status_filter)
    paginated = query.order_by(FraudReport.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/fraud_reports.html',
                           pagination=paginated, reports=paginated.items,
                           status_filter=status_filter,
                           statuses=[ReportStatus.PENDING, ReportStatus.INVESTIGATING,
                                     ReportStatus.RESOLVED, ReportStatus.DISMISSED])


@admin_bp.route('/fraud-reports/<int:report_id>/update', methods=['POST'])
@admin_required
def update_fraud_report(report_id):
    report = db.session.get(FraudReport, report_id)
    if not report:
        abort(404)
    new_status = request.form.get('status', '')
    notes = request.form.get('notes', '').strip()
    if new_status in [ReportStatus.PENDING, ReportStatus.INVESTIGATING,
                       ReportStatus.RESOLVED, ReportStatus.DISMISSED]:
        report.report_status = new_status
        if new_status == ReportStatus.RESOLVED:
            report.resolved_at = datetime.utcnow()
    if notes:
        existing = report.internal_notes or ''
        report.internal_notes = (
            f"{existing}\n[{current_user.email} {datetime.utcnow().strftime('%Y-%m-%d')}]: {notes}"
        ).strip()
    report.assigned_admin_id = current_user.id
    db.session.commit()
    flash('Fraud report updated.', 'success')
    return redirect(url_for('admin.fraud_reports'))


@admin_bp.route('/dataset-status')
@admin_required
def dataset_status():
    """Dataset import status page."""
    import os, json
    reports_dir = os.path.join(os.getcwd(), 'data', 'reports')
    import_report = {}
    quality_report = {}
    verification_report = {}

    def load_json(filename):
        path = os.path.join(reports_dir, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    import_report = load_json('dataset_import_report.json')
    quality_report = load_json('dataset_quality_report.json')
    verification_report = load_json('dataset_verification_report.json')

    dataset_job_count = Job.query.filter_by(source_type='dataset').count()
    employer_job_count = Job.query.filter_by(source_type='employer').count()

    return render_template('admin/dataset_status.html',
                           import_report=import_report,
                           quality_report=quality_report,
                           verification_report=verification_report,
                           dataset_job_count=dataset_job_count,
                           employer_job_count=employer_job_count)
