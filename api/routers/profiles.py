"""Profile API routes."""
import configparser
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from helpers.profile_helpers import resolve_session_token
from models import AWSProfile
from schemas import (
    ConfigParse,
    CredentialsParse,
    MessageResponse,
    ProfileCreate,
    ProfileFromRole,
    ProfileResponse,
    ProfileUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["profiles"])
DbSession = Annotated[Session, Depends(get_db)]


def _profile_to_response(profile: AWSProfile) -> ProfileResponse:
    return ProfileResponse.model_validate(profile)


@router.get("", response_model=list[ProfileResponse])
@router.get("/", response_model=list[ProfileResponse])
def list_profiles(db: DbSession) -> list[ProfileResponse]:
    """List all profiles (secrets excluded)."""
    profiles = db.query(AWSProfile).all()
    return [_profile_to_response(p) for p in profiles]


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(body: ProfileCreate, db: DbSession) -> ProfileResponse:
    """Create a new profile."""
    try:
        session_token = resolve_session_token(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    is_first = db.query(AWSProfile).count() == 0
    profile = AWSProfile(
        name=body.name,
        custom_name=body.custom_name,
        aws_access_key_id=body.aws_access_key_id,
        aws_secret_access_key=body.aws_secret_access_key,
        aws_session_token=session_token,
        aws_region=body.aws_region,
        is_active=is_first,
    )
    try:
        account_info = profile.get_account_info()
        if account_info:
            profile.account_number = account_info["account"]
    except Exception as e:
        logger.warning("Could not fetch account number for profile %s: %s", body.name, e)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: DbSession) -> ProfileResponse:
    """Get a profile by ID (secrets excluded)."""
    profile = db.get(AWSProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return _profile_to_response(profile)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: int, body: ProfileUpdate, db: DbSession) -> ProfileResponse:
    """Update a profile (only custom_name and aws_region)."""
    profile = db.get(AWSProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    if body.custom_name is not None:
        profile.custom_name = body.custom_name
    if body.aws_region is not None:
        profile.aws_region = body.aws_region
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, db: DbSession) -> None:
    """Delete a profile."""
    profile = db.get(AWSProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()


@router.post("/parse", response_model=ProfileResponse, status_code=201)
def parse_credentials(body: CredentialsParse, db: DbSession) -> ProfileResponse:
    """Parse AWS credentials (INI format) and create a profile."""
    credentials_text = (body.credentials_text or "").strip()
    if not credentials_text:
        raise HTTPException(status_code=400, detail="No credentials provided")

    try:
        config = configparser.ConfigParser()
        if not credentials_text.startswith("["):
            credentials_text = "[default]\n" + credentials_text
        config.read_string(credentials_text)
    except configparser.Error as e:
        logger.warning("Credentials parse error: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid credentials format: {e}") from e

    if len(config.sections()) == 0:
        raise HTTPException(status_code=400, detail="No valid profile found in credentials")

    profile_name = config.sections()[0]
    profile_data = config[profile_name]
    aws_access_key_id = (profile_data.get("aws_access_key_id") or "").strip()
    aws_secret_access_key = (profile_data.get("aws_secret_access_key") or "").strip()
    if not aws_access_key_id or not aws_secret_access_key:
        raise HTTPException(
            status_code=400,
            detail="Access key ID and secret access key are required",
        )

    aws_session_token = (profile_data.get("aws_session_token") or "").strip() or None
    region = (profile_data.get("region") or "us-east-1").strip()
    name_for_db = profile_name.replace("profile ", "", 1).strip() or "default"

    if db.query(AWSProfile).filter(AWSProfile.name == name_for_db).first():
        raise HTTPException(
            status_code=409,
            detail=f'Profile "{name_for_db}" already exists. Delete it first or use credentials with a different profile name.',
        )

    is_first = db.query(AWSProfile).count() == 0
    new_profile = AWSProfile(
        name=name_for_db,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_session_token=aws_session_token,
        aws_region=region,
        is_active=is_first,
    )
    try:
        account_info = new_profile.get_account_info()
        if account_info:
            new_profile.account_number = account_info["account"]
    except Exception as e:
        logger.warning("Could not fetch account number for profile %s: %s", profile_name, e)

    try:
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
    except Exception as e:
        db.rollback()
        logger.exception("Failed to save imported profile")
        raise HTTPException(status_code=500, detail=f"Failed to save profile: {e}") from e

    return _profile_to_response(new_profile)


def _create_profile_from_source(
    db: Session,
    source: AWSProfile,
    name: str,
    role_arn: str,
    region: str | None = None,
) -> AWSProfile:
    """Create a profile that uses source's credentials and assumes the given role."""
    role_config = {
        "RoleArn": role_arn,
        "RoleSessionName": "aws_inventory_session",
    }
    session_token = json.dumps(role_config)
    is_first = db.query(AWSProfile).count() == 0
    profile = AWSProfile(
        name=name,
        aws_access_key_id=source.aws_access_key_id,
        aws_secret_access_key=source.aws_secret_access_key,
        aws_session_token=session_token,
        aws_region=region or source.aws_region,
        is_active=is_first,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/parse_config", response_model=list[ProfileResponse])
def parse_config(body: ConfigParse, db: DbSession) -> list[ProfileResponse]:
    """Parse ~/.aws/config format and create one or more profiles (role-assuming from existing profiles)."""
    config_text = (body.config_text or "").strip()
    if not config_text:
        raise HTTPException(status_code=400, detail="No config provided")

    try:
        config = configparser.ConfigParser()
        config.read_string(config_text)
    except configparser.Error as e:
        logger.warning("Config parse error: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid config format: {e}") from e

    created: list[ProfileResponse] = []
    errors: list[str] = []

    for section in config.sections():
        # Section can be [profile name] or [default]
        profile_name = section.replace("profile ", "", 1).strip() if section.lower().startswith("profile ") else section
        if not profile_name:
            profile_name = "default"
        data = config[section]
        role_arn = (data.get("role_arn") or "").strip()
        source_profile = (data.get("source_profile") or "").strip()
        region = (data.get("region") or "us-east-1").strip()

        if not role_arn or not source_profile:
            continue  # Skip sections without role_arn + source_profile (no credentials in config)

        source = db.query(AWSProfile).filter(AWSProfile.name == source_profile).first()
        if not source:
            errors.append(f'Profile "{profile_name}": source_profile "{source_profile}" not found in CloudScope.')
            continue
        if db.query(AWSProfile).filter(AWSProfile.name == profile_name).first():
            errors.append(f'Profile "{profile_name}" already exists.')
            continue

        try:
            new_profile = _create_profile_from_source(db, source, profile_name, role_arn, region)
            created.append(_profile_to_response(new_profile))
        except Exception as e:
            db.rollback()
            errors.append(f'Profile "{profile_name}": {e}')
            logger.exception("Failed to create profile from config section %s", section)

    if not created and errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    if errors:
        logger.warning("Config import partial errors: %s", errors)
    return created


@router.post("/from_role", response_model=ProfileResponse, status_code=201)
def create_profile_from_role(body: ProfileFromRole, db: DbSession) -> ProfileResponse:
    """Create a new profile that uses an existing profile's credentials and assumes an AWS role (existing or custom)."""
    source = db.get(AWSProfile, body.source_profile_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source profile not found")

    if body.role_type == "existing":
        if not (body.role_name or "").strip():
            raise HTTPException(status_code=400, detail="Role name is required for existing role")
        try:
            import boto3
            session = boto3.Session(
                aws_access_key_id=source.aws_access_key_id,
                aws_secret_access_key=source.aws_secret_access_key,
                region_name=source.aws_region,
            )
            account_id = session.client("sts").get_caller_identity()["Account"]
            role_arn = f"arn:aws:iam::{account_id}:role/{body.role_name.strip()}"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Cannot resolve account for source profile: {e}") from e
        session_token = json.dumps({"RoleArn": role_arn, "RoleSessionName": "aws_inventory_session"})
    else:
        if not (body.aws_session_token or "").strip():
            raise HTTPException(status_code=400, detail="Role configuration (JSON) is required for custom role")
        raw = body.aws_session_token.strip()
        try:
            role_config = json.loads(raw)
            if not isinstance(role_config, dict) or "RoleArn" not in role_config:
                raise ValueError("JSON must include RoleArn")
            if not role_config["RoleArn"].startswith("arn:aws:iam::"):
                raise ValueError("Invalid RoleArn format")
            role_config.setdefault("RoleSessionName", "aws_inventory_session")
            session_token = json.dumps(role_config)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}") from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    is_first = db.query(AWSProfile).count() == 0
    profile = AWSProfile(
        name=body.name.strip(),
        aws_access_key_id=source.aws_access_key_id,
        aws_secret_access_key=source.aws_secret_access_key,
        aws_session_token=session_token,
        aws_region=source.aws_region,
        is_active=is_first,
    )
    if db.query(AWSProfile).filter(AWSProfile.name == profile.name).first():
        raise HTTPException(status_code=409, detail=f'Profile "{profile.name}" already exists.')
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _profile_to_response(profile)


@router.put("/deactivate_all", response_model=MessageResponse)
def deactivate_all_profiles(db: DbSession) -> MessageResponse:
    """Deactivate all profiles."""
    db.query(AWSProfile).update({AWSProfile.is_active: False})
    db.commit()
    return MessageResponse(message="All profiles deactivated successfully")


@router.put("/{profile_id}/activate", response_model=MessageResponse)
def activate_profile(profile_id: int, db: DbSession) -> MessageResponse:
    """Activate a profile."""
    profile = db.get(AWSProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.query(AWSProfile).update({AWSProfile.is_active: False})
    profile.is_active = True
    db.commit()
    return MessageResponse(message="Profile activated successfully")
