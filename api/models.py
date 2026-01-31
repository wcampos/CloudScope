"""Database models for the CloudScope application."""
from datetime import datetime, UTC
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
import boto3
import logging

from database import Base

logger = logging.getLogger(__name__)


class SchemaVersion(Base):
    """Model for tracking database schema version."""
    __tablename__ = "schema_version"

    id = Column(Integer, primary_key=True)
    version = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class AWSProfile(Base):
    """Model for AWS profiles."""

    __tablename__ = "aws_profiles"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    custom_name = Column(String(100))
    account_number = Column(String(12))
    aws_access_key_id = Column(String(100), nullable=False)
    aws_secret_access_key = Column(String(100), nullable=False)
    aws_session_token = Column(Text)
    aws_region = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<AWSProfile {self.name}>"

    def to_dict(self) -> dict:
        """Convert the profile to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "aws_region": self.aws_region,
            "aws_session_token": self.aws_session_token,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_account_info(self) -> dict | None:
        """Get AWS account information using the profile credentials."""
        try:
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
                region_name=self.aws_region,
            )
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()
            return {
                "account": identity["Account"],
                "arn": identity["Arn"],
                "user_id": identity["UserId"],
            }
        except Exception as e:
            logger.error("Error getting account info: %s", e)
            return None
