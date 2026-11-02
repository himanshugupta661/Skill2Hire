"""
Audit Log model for administrative and application events.
Does NOT log passwords, tokens, or sensitive personal data.
"""
from datetime import datetime
from extensions import db


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), index=True)
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    actor = db.relationship('User', foreign_keys=[actor_user_id])

    @classmethod
    def log(cls, action, entity_type=None, entity_id=None, description=None,
             actor_user_id=None, ip_address=None):
        from extensions import db
        entry = cls(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address
        )
        db.session.add(entry)
        # Note: caller is responsible for committing the session

    def __repr__(self):
        return f'<AuditLog action={self.action} entity={self.entity_type}:{self.entity_id}>'
