from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import boto3
import json
import logging
import os
from datetime import datetime, UTC, timedelta
import redis
from aws_classes import CommonAWSServices
from routes import router
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AWS Inventory API",
    description="API for managing AWS resource inventory",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis configuration
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0

# Cache configuration
CACHE_DURATION = 300  # 5 minutes in seconds

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

# Helper functions
def get_aws_session(profile: Profile):
    """Create an AWS session with the given profile"""
    return boto3.Session(
        aws_access_key_id=profile.aws_access_key_id,
        aws_secret_access_key=profile.aws_secret_access_key,
        region_name=profile.aws_region
    )

def get_active_profile():
    """Get the currently active profile from Redis"""
    try:
        active_profile = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('active_profile')
        return json.loads(active_profile) if active_profile else None
    except Exception as e:
        logger.error(f"Error getting active profile: {str(e)}")
        return None

def get_resources_from_cache():
    """Get resources from Redis cache"""
    try:
        timestamp = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('aws_resources_timestamp')
        if not timestamp:
            return None
            
        age = int(datetime.now(UTC).timestamp()) - int(timestamp)
        if age > CACHE_DURATION:
            return None
            
        cached_data = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('aws_resources')
        return json.loads(cached_data) if cached_data else None
    except Exception as e:
        logger.error(f"Error getting cached resources: {str(e)}")
        return None

def cache_resources(resources: Dict[str, List[Dict[str, Any]]]):
    """Cache resources in Redis"""
    try:
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('aws_resources', json.dumps(resources))
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('aws_resources_timestamp', int(datetime.now(UTC).timestamp()))
        logger.debug("Resources cached successfully")
    except Exception as e:
        logger.error(f"Error caching resources: {str(e)}")

# Dependency functions
def get_redis_client():
    """Get Redis client"""
    try:
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
    except Exception as e:
        logger.error(f"Error connecting to Redis: {str(e)}")
        raise

def get_cache_key():
    """Get cache key for resources"""
    return "aws_resources"

def get_cache_timestamp_key():
    """Get cache timestamp key"""
    return "aws_resources_timestamp"

def get_cache_duration():
    """Get cache duration"""
    return CACHE_DURATION

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    """Middleware to handle session cookies"""
    response = await call_next(request)
    
    # Set session cookie if not present
    if not request.cookies.get('session_id'):
        response.set_cookie(
            key='session_id',
            value=str(uuid.uuid4()),
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=timedelta(days=1).total_seconds()
        )
    
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AWS Inventory API"}

# Include routers
app.include_router(router, prefix="/api")

# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}

@app.get("/profiles", response_model=List[Profile])
async def get_profiles():
    """Get all profiles"""
    try:
        profiles = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles')
        return json.loads(profiles) if profiles else []
    except Exception as e:
        logger.error(f"Error getting profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles", response_model=Profile)
async def create_profile(profile: ProfileCreate):
    """Create a new profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profile_dict = profile.dict()
        profile_dict['id'] = len(profiles) + 1
        profiles.append(profile_dict)
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('profiles', json.dumps(profiles))
        return profile_dict
    except Exception as e:
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: int):
    """Get a specific profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: int, profile: ProfileCreate):
    """Update a profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profile_index = next((i for i, p in enumerate(profiles) if p['id'] == profile_id), None)
        if profile_index is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_dict = profile.dict()
        profile_dict['id'] = profile_id
        profiles[profile_index] = profile_dict
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('profiles', json.dumps(profiles))
        return profile_dict
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: int):
    """Delete a profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profiles = [p for p in profiles if p['id'] != profile_id]
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('profiles', json.dumps(profiles))
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profiles/{profile_id}/activate")
async def activate_profile(profile_id: int):
    """Activate a profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Deactivate all profiles
        for p in profiles:
            p['is_active'] = False
        
        # Activate the selected profile
        profile['is_active'] = True
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('profiles', json.dumps(profiles))
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('active_profile', json.dumps(profile))
        return profile
    except Exception as e:
        logger.error(f"Error activating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/profiles/deactivate_all")
async def deactivate_all_profiles():
    """Deactivate all profiles"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        for profile in profiles:
            profile['is_active'] = False
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).set('profiles', json.dumps(profiles))
        redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).delete('active_profile')
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deactivating profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/{profile_id}/account-info", response_model=AccountInfo)
async def get_account_info(profile_id: int):
    """Get AWS account information for a profile"""
    try:
        profiles = json.loads(redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        ).get('profiles') or '[]')
        profile = next((p for p in profiles if p['id'] == profile_id), None)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        session = get_aws_session(Profile(**profile))
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "account": identity['Account'],
            "region": profile['aws_region']
        }
    except Exception as e:
        logger.error(f"Error getting account info: {str(e)}")
        return {
            "account": profile.get('account_number', 'Unknown'),
            "region": profile.get('aws_region', 'Unknown')
        }

@app.get("/resources")
async def get_resources():
    """Get all AWS resources"""
    try:
        # Try to get from cache first
        resources = get_resources_from_cache()
        if resources:
            return resources
            
        # Get active profile
        active_profile = get_active_profile()
        if not active_profile:
            raise HTTPException(status_code=404, detail="No active profile found")
        
        # Create AWS session
        session = get_aws_session(Profile(**active_profile))
        
        # Initialize AWS services
        aws_services = CommonAWSServices(session)
        
        # Get all resources
        resources = aws_services.get_all_resources()
        
        # Cache the results
        cache_resources(resources)
        
        return resources
    except Exception as e:
        logger.error(f"Error getting resources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/parse")
async def parse_credentials(credentials: Dict[str, str]):
    """Parse AWS credentials and create a profile"""
    try:
        credentials_text = credentials.get('credentials_text', '')
        if not credentials_text:
            raise HTTPException(status_code=400, detail="No credentials provided")
        
        # Parse credentials and create profile
        # This is a simplified version - you might want to add more robust parsing
        lines = credentials_text.strip().split('\n')
        profile_data = {}
        
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                profile_data[key.strip()] = value.strip()
        
        if not all(k in profile_data for k in ['aws_access_key_id', 'aws_secret_access_key', 'region']):
            raise HTTPException(status_code=400, detail="Invalid credentials format")
        
        profile = ProfileCreate(
            name=profile_data.get('profile', 'default'),
            aws_access_key_id=profile_data['aws_access_key_id'],
            aws_secret_access_key=profile_data['aws_secret_access_key'],
            aws_region=profile_data['region']
        )
        
        return await create_profile(profile)
    except Exception as e:
        logger.error(f"Error parsing credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 