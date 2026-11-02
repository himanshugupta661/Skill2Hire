"""
API routes — JSON endpoints for interactive frontend features.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from extensions import db
from app.services.job_service import toggle_save_job, is_job_saved
from app.models.notification import Notification
from app.services.notification_service import get_unread_count, mark_read

api_bp = Blueprint('api', __name__)


@api_bp.route('/jobs/<int:job_id>/save', methods=['POST'])
@login_required
def save_job(job_id):
    if not current_user.is_seeker:
        return jsonify({'error': 'Only job seekers can save jobs.'}), 403
    result = toggle_save_job(current_user.id, job_id)
    return jsonify(result)


@api_bp.route('/notifications/unread-count')
@login_required
def unread_notifications_count():
    count = get_unread_count(current_user.id)
    return jsonify({'count': count})


@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    success = mark_read(notif_id, current_user.id)
    return jsonify({'success': success})


@api_bp.route('/jobs/search')
def job_search_api():
    """JSON search endpoint for dynamic job search."""
    from app.services.job_service import search_jobs
    keyword = request.args.get('q', '').strip()
    location = request.args.get('location', '').strip()
    page = request.args.get('page', 1, type=int)

    paginated = search_jobs(
        keyword=keyword or None,
        location=location or None,
        page=page, per_page=10
    )
    jobs_data = [{
        'id': j.id,
        'title': j.job_title,
        'company': j.company_name,
        'location': j.location or '',
        'industry': j.industry or '',
        'employment_type': j.employment_type or '',
        'work_mode': j.work_mode or '',
        'salary_min': j.salary_min,
        'salary_max': j.salary_max,
        'created_at': j.created_at.isoformat() if j.created_at else None,
        'url': f'/jobs/{j.id}',
    } for j in paginated.items]

    return jsonify({
        'jobs': jobs_data,
        'total': paginated.total,
        'pages': paginated.pages,
        'page': page,
    })


@api_bp.route('/stats')
def platform_stats():
    """Public platform statistics."""
    from app.services.job_service import get_platform_stats
    return jsonify(get_platform_stats())
