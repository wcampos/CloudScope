from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
import json
import logging
from datetime import datetime, UTC
import redis
from aws_classes import CommonAWSServices
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Helper functions
def get_session_id(request: Request):
    """Get or create a session ID from the request"""
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

# Redis client dependency
def get_redis_client():
    try:
        client = redis.Redis(
            host='redis',
            port=6379,
            db=0,
            decode_responses=True
        )
        return client
    except Exception as e:
        logger.error(f"Error connecting to Redis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")

# Cache key dependencies
def get_cache_key(session_id: str = Depends(get_session_id)):
    return f"aws_resources:{session_id}"

def get_cache_timestamp_key(session_id: str = Depends(get_session_id)):
    return f"aws_resources_timestamp:{session_id}"

def get_cache_duration():
    return 300  # 5 minutes in seconds

# Pydantic models
class ProfileBase(BaseModel):
    name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    account_number: Optional[str] = None
    is_active: bool = False

class ProfileCreate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: int

    class Config:
        from_attributes = True

class AccountInfo(BaseModel):
    account: str
    region: str

class ResourceCount(BaseModel):
    service: str
    count: int

class CredentialsInput(BaseModel):
    credentials_text: str

class CredentialsResponse(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

# Helper functions
def get_aws_session(profile: Profile):
    """Create an AWS session with the given profile"""
    return boto3.Session(
        aws_access_key_id=profile.aws_access_key_id,
        aws_secret_access_key=profile.aws_secret_access_key,
        region_name=profile.aws_region
    )

def get_active_profile(redis_client: redis.Redis):
    """Get the currently active profile from Redis"""
    try:
        active_profile = redis_client.get('active_profile')
        return json.loads(active_profile) if active_profile else None
    except Exception as e:
        logger.error(f"Error getting active profile: {str(e)}")
        return None

def get_resources_from_cache(redis_client: redis.Redis, session_id: str, cache_key: str, cache_timestamp_key: str, cache_duration: int):
    """Get resources from Redis cache for a specific session"""
    try:
        cached_data = redis_client.get(cache_key)
        cached_timestamp = redis_client.get(cache_timestamp_key)
        
        if cached_data and cached_timestamp:
            timestamp = float(cached_timestamp)
            if datetime.now(UTC).timestamp() - timestamp < cache_duration:
                return json.loads(cached_data)
        return None
    except Exception as e:
        logger.error(f"Error getting resources from cache: {str(e)}")
        return None

def cache_resources(redis_client: redis.Redis, session_id: str, resources: Dict[str, Any], cache_key: str, cache_timestamp_key: str):
    """Cache resources in Redis for a specific session"""
    try:
        redis_client.set(cache_key, json.dumps(resources))
        redis_client.set(cache_timestamp_key, str(datetime.now(UTC).timestamp()))
    except Exception as e:
        logger.error(f"Error caching resources: {str(e)}")

# API endpoints
@router.get("/profiles", response_model=List[Profile])
async def get_profiles(redis_client: redis.Redis = Depends(get_redis_client)):
    """Get all AWS profiles"""
    try:
        profiles = redis_client.get('aws_profiles')
        return json.loads(profiles) if profiles else []
    except Exception as e:
        logger.error(f"Error getting profiles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get profiles")

@router.post("/profiles", response_model=Profile)
async def create_profile(profile: ProfileCreate, redis_client: redis.Redis = Depends(get_redis_client)):
    """Create a new AWS profile"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        profile_dict = profile.dict()
        profile_dict['id'] = len(profiles) + 1
        profiles.append(profile_dict)
        redis_client.set('aws_profiles', json.dumps(profiles))
        return profile_dict
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create profile")

@router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: int, redis_client: redis.Redis = Depends(get_redis_client)):
    """Get a specific AWS profile"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@router.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: int, profile: ProfileCreate, redis_client: redis.Redis = Depends(get_redis_client)):
    """Update an AWS profile"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        profile_index = next((i for i, p in enumerate(profiles) if p['id'] == profile_id), None)
        if profile_index is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_dict = profile.dict()
        profile_dict['id'] = profile_id
        profiles[profile_index] = profile_dict
        redis_client.set('aws_profiles', json.dumps(profiles))
        return profile_dict
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int, redis_client: redis.Redis = Depends(get_redis_client)):
    """Delete an AWS profile"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        profiles = [p for p in profiles if p['id'] != profile_id]
        redis_client.set('aws_profiles', json.dumps(profiles))
        return {"message": "Profile deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete profile")

@router.post("/profiles/{profile_id}/activate")
async def activate_profile(profile_id: int, redis_client: redis.Redis = Depends(get_redis_client)):
    """Activate an AWS profile"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Deactivate all profiles
        for p in profiles:
            p['is_active'] = False
        
        # Activate the selected profile
        profile['is_active'] = True
        redis_client.set('aws_profiles', json.dumps(profiles))
        redis_client.set('active_profile', json.dumps(profile))
        return {"message": "Profile activated successfully"}
    except Exception as e:
        logger.error(f"Error activating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to activate profile")

@router.post("/profiles/deactivate-all")
async def deactivate_all_profiles(redis_client: redis.Redis = Depends(get_redis_client)):
    """Deactivate all AWS profiles"""
    try:
        profiles = json.loads(redis_client.get('aws_profiles') or '[]')
        for profile in profiles:
            profile['is_active'] = False
        redis_client.set('aws_profiles', json.dumps(profiles))
        redis_client.delete('active_profile')
        return {"message": "All profiles deactivated successfully"}
    except Exception as e:
        logger.error(f"Error deactivating profiles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to deactivate profiles")

@router.get("/profiles/account-info", response_model=AccountInfo)
async def get_account_info(redis_client: redis.Redis = Depends(get_redis_client)):
    """Get account information for the active profile"""
    try:
        active_profile = get_active_profile(redis_client)
        if not active_profile:
            raise HTTPException(status_code=404, detail="No active profile found")
        
        session = get_aws_session(Profile(**active_profile))
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "account": identity['Account'],
            "region": active_profile['aws_region']
        }
    except Exception as e:
        logger.error(f"Error getting account info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get account info")

@router.post("/profiles/parse", response_model=CredentialsResponse)
async def parse_credentials(credentials: CredentialsInput):
    """Parse AWS credentials from text input"""
    try:
        lines = credentials.credentials_text.strip().split('\n')
        credentials_dict = {}
        
        # Map of possible key variations to standardized keys
        key_mapping = {
            'aws_access_key_id': ['aws_access_key_id', 'access_key_id', 'access_key'],
            'aws_secret_access_key': ['aws_secret_access_key', 'secret_access_key', 'secret_key'],
            'aws_region': ['aws_region', 'region']
        }
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if '=' in line:
                key, value = [part.strip() for part in line.split('=', 1)]
            else:
                continue
            
            # Remove quotes if present
            value = value.strip('"\'')
            
            # Map the key to a standard format
            for standard_key, variations in key_mapping.items():
                if key.lower() in [v.lower() for v in variations]:
                    credentials_dict[standard_key] = value
                    break
        
        # Check for required fields and provide specific error messages
        missing_fields = []
        if 'aws_access_key_id' not in credentials_dict:
            missing_fields.append('AWS Access Key ID')
        if 'aws_secret_access_key' not in credentials_dict:
            missing_fields.append('AWS Secret Access Key')
        if 'aws_region' not in credentials_dict:
            missing_fields.append('AWS Region')
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required credentials: {', '.join(missing_fields)}"
            )
        
        return {
            "aws_access_key_id": credentials_dict['aws_access_key_id'],
            "aws_secret_access_key": credentials_dict['aws_secret_access_key'],
            "aws_region": credentials_dict['aws_region']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing credentials: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to parse credentials. Please ensure the format is correct with each credential on a new line using 'key=value' format."
        )

@router.delete("/session")
async def delete_session(
    redis_client: redis.Redis = Depends(get_redis_client),
    session_id: str = Depends(get_session_id)
):
    """Delete the current session and its cached data"""
    try:
        cache_key = get_cache_key(session_id)
        cache_timestamp_key = get_cache_timestamp_key(session_id)
        redis_client.delete(cache_key, cache_timestamp_key)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")

@router.get("/resources")
async def get_resources(
    redis_client: redis.Redis = Depends(get_redis_client),
    session_id: str = Depends(get_session_id),
    cache_key: str = Depends(get_cache_key),
    cache_timestamp_key: str = Depends(get_cache_timestamp_key),
    cache_duration: int = Depends(get_cache_duration)
):
    """Get AWS resources for the active profile"""
    try:
        # Try to get resources from cache
        cached_resources = get_resources_from_cache(
            redis_client, session_id, cache_key, cache_timestamp_key, cache_duration
        )
        if cached_resources:
            return cached_resources
        
        # If not in cache, get active profile and fetch resources
        active_profile = get_active_profile(redis_client)
        if not active_profile:
            raise HTTPException(status_code=404, detail="No active profile found")
        
        session = get_aws_session(Profile(**active_profile))
        aws_services = CommonAWSServices(session)
        resources = aws_services.get_all_resources()
        
        # Cache the resources
        cache_resources(redis_client, session_id, resources, cache_key, cache_timestamp_key)
        
        return resources
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get resources") 