"""Pydantic schemas for API request/response."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# --- Profile ---

class ProfileBase(BaseModel):
    """Base profile fields (input)."""
    name: str
    custom_name: str | None = None
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    role_type: Literal["none", "existing", "custom"] = "none"
    role_name: str | None = None
    direct_session_token: str | None = None
    aws_session_token: str | None = None


class ProfileCreate(ProfileBase):
    """Schema for creating a profile."""
    pass


class ProfileUpdate(BaseModel):
    """Schema for updating a profile (only safe fields)."""
    custom_name: str | None = None
    aws_region: str | None = None


class ProfileResponse(BaseModel):
    """Profile response (no secrets)."""
    id: int
    name: str
    custom_name: str | None
    aws_region: str
    account_number: str | None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CredentialsParse(BaseModel):
    """Body for paste-credentials import."""
    credentials_text: str = Field(..., min_length=1)


class ConfigParse(BaseModel):
    """Body for paste config (~/.aws/config) import."""
    config_text: str = Field(..., min_length=1)


class ProfileFromRole(BaseModel):
    """Body for creating a profile that assumes a role using an existing profile's credentials."""
    source_profile_id: int
    name: str
    role_type: Literal["existing", "custom"]
    role_name: str | None = None
    aws_session_token: str | None = None  # JSON for custom role


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
