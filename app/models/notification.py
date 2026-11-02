"""
Notification model for in-app notifications.
"""
from datetime import datetime
from extensions import db


class NotificationType:
    APPLICATION_SUBMITTED = 'application_submitted'
    APPLICATION_STATUS = 'application_status'
    VERIFICATION_DECISION = 'verification_decision'
    JOB_CLOSED = 'job_closed'
    FRAUD_REPORT_UPDATE = 'fraud_report_update'
    SYSTEM = 'system'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default=NotificationType.SYSTEM)
    related_entity_type = db.Column(db.String(50))
    related_entity_id = db.Column(db.Integer)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification user={self.user_id} type={self.notification_type} read={self.is_read}>'
