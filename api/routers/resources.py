"""AWS resources API routes. Resources are cached in Redis; refresh only on page load or Refresh Cache."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from aws_classes import CommonAWSServices
from cache import get_cached_resources, invalidate_resources, set_cached_resources
from database import get_db
from models import AWSProfile

router = APIRouter(prefix="/resources", tags=["resources"])
DbSession = Annotated[Session, Depends(get_db)]


def _fetch_and_cache(profile: AWSProfile) -> dict:
    """Fetch resources from AWS and store in Redis."""
    aws_services = CommonAWSServices(profile)
    data = aws_services.get_all_resources()
    set_cached_resources(profile.id, data)
    return data


@router.get("")
def get_aws_resources(db: DbSession) -> dict:
    """Get AWS resources for the active profile. Serves from Redis cache when available."""
    active_profile = db.query(AWSProfile).filter(AWSProfile.is_active.is_(True)).first()
    if not active_profile:
        raise HTTPException(status_code=400, detail="No active profile found")
    cached = get_cached_resources(active_profile.id)
    if cached is not None:
        return cached
    return _fetch_and_cache(active_profile)


@router.post("/refresh")
def refresh_aws_resources(db: DbSession) -> dict:
    """Refresh resources from AWS and update Redis cache. Call when user clicks Refresh Cache."""
    active_profile = db.query(AWSProfile).filter(AWSProfile.is_active.is_(True)).first()
    if not active_profile:
        raise HTTPException(status_code=400, detail="No active profile found")
    invalidate_resources(active_profile.id)
    return _fetch_and_cache(active_profile)
