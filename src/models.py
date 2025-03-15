from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SchemaVersion(db.Model):
    """Model for tracking database schema version."""
    __tablename__ = 'schema_version'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_current_version():
        """Get the current schema version."""
        version = SchemaVersion.query.order_by(SchemaVersion.created_at.desc()).first()
        return version.version if version else None

class AWSProfile(db.Model):
    __tablename__ = 'aws_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    aws_access_key_id = db.Column(db.String(100), nullable=False)
    aws_secret_access_key = db.Column(db.String(100), nullable=False)
    aws_session_token = db.Column(db.Text, nullable=True)
    aws_region = db.Column(db.String(50), nullable=False, default='us-east-1')
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AWSProfile {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'aws_region': self.aws_region,
            'aws_session_token': self.aws_session_token,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def get_active_profile():
        return AWSProfile.query.filter_by(is_active=True).first()

    def set_as_active(self):
        AWSProfile.query.update({'is_active': False})
        self.is_active = True
        db.session.commit() 