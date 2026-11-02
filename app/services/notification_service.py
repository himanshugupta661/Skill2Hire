"""
Notification Service - create and manage in-app notifications.
"""
from extensions import db
from app.models.notification import Notification


def create_notification(user_id: int, title: str, message: str,
                         notification_type: str = 'system',
                         related_entity_type: str = None,
                         related_entity_id: int = None) -> Notification:
    """Create and save a notification. Caller must commit."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.session.add(notif)
    return notif


def get_user_notifications(user_id: int, limit: int = 20):
    return Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()


def get_unread_count(user_id: int) -> int:
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_all_read(user_id: int):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()


def mark_read(notification_id: int, user_id: int) -> bool:
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False
