"""Database models for the CloudScope application."""
from datetime import datetime, UTC
from sqlalchemy import String, DateTime
import boto3
import logging

from extensions import db

class SchemaVersion(db.Model):
    """Model for tracking database schema version."""
    __tablename__ = 'schema_version'
    
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(String(20), nullable=False)
    created_at = db.Column(DateTime, default=lambda: datetime.now(UTC))
    
    @staticmethod
    def get_current_version():
        """Get the current schema version."""
        version = SchemaVersion.query.order_by(SchemaVersion.created_at.desc()).first()
        return version.version if version else None

class AWSProfile(db.Model):
    """Model for AWS profiles."""
    
    __tablename__ = 'aws_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    custom_name = db.Column(db.String(100))
    account_number = db.Column(db.String(12))
    aws_access_key_id = db.Column(db.String(100), nullable=False)
    aws_secret_access_key = db.Column(db.String(100), nullable=False)
    aws_session_token = db.Column(db.Text)
    aws_region = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AWSProfile {self.name}>'

    def to_dict(self):
        """Convert the profile to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'aws_region': self.aws_region,
            'aws_session_token': self.aws_session_token,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def get_active_profile(cls):
        """Get the currently active profile."""
        return cls.query.filter_by(is_active=True).first()

    def set_as_active(self):
        """Set this profile as active and deactivate others."""
        AWSProfile.query.update({'is_active': False})
        self.is_active = True
        db.session.commit()

    def get_account_info(self):
        """Get AWS account information using the profile credentials."""
        try:
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
                region_name=self.aws_region
            )
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            return {
                'account': identity['Account'],
                'arn': identity['Arn'],
                'user_id': identity['UserId']
            }
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None 