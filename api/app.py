from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from datetime import datetime, UTC
import os
import logging
import json
import boto3
import configparser
from aws_classes import CommonAWSServices
from extensions import db, migrate
from models import AWSProfile, SchemaVersion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:postgres@db:5432/aws_inventory'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)

# Initialize API documentation
api = Api(app, version='1.0', title='CloudScope API',
          description='API for managing AWS profiles and resources',
          prefix='/api',
          doc='/api/docs')

# Create tables within application context
with app.app_context():
    db.create_all()

# Define API models for documentation (input: may include secrets for create)
profile_model = api.model('Profile', {
    'id': fields.Integer(readonly=True, description='Profile ID'),
    'name': fields.String(required=True, description='Profile name'),
    'custom_name': fields.String(description='Custom profile name'),
    'aws_access_key_id': fields.String(required=True, description='AWS access key ID'),
    'aws_secret_access_key': fields.String(required=True, description='AWS secret access key'),
    'aws_session_token': fields.String(description='AWS session token'),
    'aws_region': fields.String(required=True, description='AWS region'),
    'account_number': fields.String(description='AWS account number'),
    'is_active': fields.Boolean(description='Profile active status')
})

# Safe profile model for GET/list responses (no secrets)
profile_safe_model = api.model('ProfileSafe', {
    'id': fields.Integer(readonly=True, description='Profile ID'),
    'name': fields.String(description='Profile name'),
    'custom_name': fields.String(description='Custom profile name'),
    'aws_region': fields.String(description='AWS region'),
    'account_number': fields.String(description='AWS account number'),
    'is_active': fields.Boolean(description='Profile active status'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at'),
})


def _resolve_session_token(data):
    """Resolve aws_session_token from form-like payload (role_type, role_name, etc.)."""
    role_type = data.get('role_type') or 'none'
    session_token = None

    if role_type == 'existing':
        role_name = data.get('role_name')
        if not role_name:
            raise ValueError("Role name is required when using an existing role")
        aws_access_key_id = data.get('aws_access_key_id')
        aws_secret_access_key = data.get('aws_secret_access_key')
        aws_region = data.get('aws_region')
        if not all([aws_access_key_id, aws_secret_access_key, aws_region]):
            raise ValueError("Access key, secret key, and region are required for role assumption")
        temp_session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        sts_client = temp_session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        role_config = {
            "RoleArn": f"arn:aws:iam::{account_id}:role/{role_name}",
            "RoleSessionName": "aws_inventory_session"
        }
        session_token = json.dumps(role_config)

    elif role_type == 'custom':
        raw = data.get('aws_session_token')
        if raw:
            try:
                role_config = json.loads(raw)
                if isinstance(role_config, dict) and 'RoleArn' in role_config:
                    if not role_config['RoleArn'].startswith('arn:aws:iam::'):
                        raise ValueError("Invalid role ARN format")
                    if not role_config.get('RoleSessionName'):
                        role_config['RoleSessionName'] = 'aws_inventory_session'
                    session_token = json.dumps(role_config)
            except json.JSONDecodeError:
                session_token = raw
    else:
        direct_token = data.get('direct_session_token')
        if direct_token:
            session_token = direct_token

    return session_token


def _profile_to_safe_dict(profile):
    """Return profile dict without secrets for API responses."""
    return {
        'id': profile.id,
        'name': profile.name,
        'custom_name': profile.custom_name,
        'aws_region': profile.aws_region,
        'account_number': profile.account_number,
        'is_active': profile.is_active,
        'created_at': profile.created_at,
        'updated_at': profile.updated_at,
    }

credentials_parser = api.model('Credentials', {
    'credentials_text': fields.String(required=True, description='AWS credentials in INI format')
})

# API namespaces
ns_profiles = api.namespace('profiles', description='Profile operations')
ns_resources = api.namespace('resources', description='AWS resource operations')
ns_system = api.namespace('system', description='System operations')

@ns_profiles.route('/')
class ProfileListResource(Resource):
    @ns_profiles.doc('list_profiles')
    @ns_profiles.marshal_list_with(profile_safe_model)
    def get(self):
        """List all profiles (secrets excluded)"""
        return [_profile_to_safe_dict(p) for p in AWSProfile.query.all()]

    @ns_profiles.doc('create_profile')
    @ns_profiles.expect(profile_model)
    @ns_profiles.marshal_with(profile_safe_model, code=201)
    def post(self):
        """Create a new profile (accepts form-like payload with role_type, role_name, etc.)"""
        data = request.json or {}
        name = data.get('name')
        aws_access_key_id = data.get('aws_access_key_id')
        aws_secret_access_key = data.get('aws_secret_access_key')
        aws_region = data.get('aws_region')
        if not name or not aws_access_key_id or not aws_secret_access_key or not aws_region:
            api.abort(400, 'name, aws_access_key_id, aws_secret_access_key, aws_region are required')
        try:
            session_token = _resolve_session_token(data)
        except ValueError as e:
            api.abort(400, str(e))
        profile = AWSProfile(
            name=name,
            custom_name=data.get('custom_name'),
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=session_token,
            aws_region=aws_region
        )
        try:
            account_info = profile.get_account_info()
            if account_info:
                profile.account_number = account_info['account']
        except Exception as e:
            logger.warning("Could not fetch account number for profile %s: %s", name, e)
        db.session.add(profile)
        db.session.commit()
        return _profile_to_safe_dict(profile), 201

@ns_profiles.route('/<int:profile_id>')
@ns_profiles.response(404, 'Profile not found')
class ProfileResource(Resource):
    @ns_profiles.doc('get_profile')
    @ns_profiles.marshal_with(profile_safe_model)
    def get(self, profile_id):
        """Get a profile by ID (secrets excluded)"""
        profile = AWSProfile.query.get_or_404(profile_id)
        return _profile_to_safe_dict(profile)

    @ns_profiles.doc('update_profile')
    @ns_profiles.expect(profile_safe_model)
    @ns_profiles.marshal_with(profile_safe_model)
    def put(self, profile_id):
        """Update a profile (only custom_name and aws_region are updatable)"""
        profile = AWSProfile.query.get_or_404(profile_id)
        data = request.json or {}
        if 'custom_name' in data:
            profile.custom_name = data['custom_name']
        if 'aws_region' in data:
            profile.aws_region = data['aws_region']
        db.session.commit()
        return _profile_to_safe_dict(profile)

    @ns_profiles.doc('delete_profile')
    @ns_profiles.response(204, 'Profile deleted')
    def delete(self, profile_id):
        """Delete a profile"""
        profile = AWSProfile.query.get_or_404(profile_id)
        db.session.delete(profile)
        db.session.commit()
        return '', 204

@ns_profiles.route('/parse')
class ProfileParserResource(Resource):
    @ns_profiles.doc('parse_credentials')
    @ns_profiles.expect(credentials_parser)
    @ns_profiles.marshal_with(profile_safe_model, code=201)
    def post(self):
        """Parse AWS credentials and create a profile"""
        data = request.json
        if not data:
            return {'error': 'Invalid JSON body or missing Content-Type: application/json'}, 400
        credentials_text = (data.get('credentials_text') or '').strip()
        if not credentials_text:
            return {'error': 'No credentials provided'}, 400

        try:
            # Create a ConfigParser with the pasted text
            config = configparser.ConfigParser()
            # Add a default section header if none exists
            if not credentials_text.startswith('['):
                credentials_text = '[default]\n' + credentials_text
            config.read_string(credentials_text)
        except configparser.Error as e:
            logger.warning(f"Credentials parse error: {e}")
            return {'error': f'Invalid credentials format: {str(e)}'}, 400

        if len(config.sections()) == 0:
            return {'error': 'No valid profile found in credentials'}, 400

        profile_name = config.sections()[0]
        profile_data = config[profile_name]
        aws_access_key_id = (profile_data.get('aws_access_key_id') or '').strip()
        aws_secret_access_key = (profile_data.get('aws_secret_access_key') or '').strip()
        if not aws_access_key_id or not aws_secret_access_key:
            return {'error': 'Access key ID and secret access key are required'}, 400

        aws_session_token = (profile_data.get('aws_session_token') or '').strip() or None
        region = (profile_data.get('region') or 'us-east-1').strip()

        name_for_db = profile_name.replace('profile ', '', 1).strip() or 'default'
        if AWSProfile.query.filter_by(name=name_for_db).first():
            return {'error': f'Profile "{name_for_db}" already exists'}, 409

        new_profile = AWSProfile(
            name=name_for_db,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            aws_region=region
        )

        try:
            account_info = new_profile.get_account_info()
            if account_info:
                new_profile.account_number = account_info['account']
        except Exception as e:
            logger.warning(f"Could not fetch account number for profile {profile_name}: {str(e)}")

        try:
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.exception("Failed to save imported profile")
            return {'error': f'Failed to save profile: {str(e)}'}, 500

        return _profile_to_safe_dict(new_profile), 201

@ns_profiles.route('/<int:profile_id>/activate')
class ProfileActivationResource(Resource):
    @ns_profiles.doc('activate_profile')
    @ns_profiles.response(200, 'Profile activated')
    def put(self, profile_id):
        """Activate a profile"""
        profile = AWSProfile.query.get_or_404(profile_id)
        profile.is_active = True
        db.session.commit()
        return {'message': 'Profile activated successfully'}

@ns_profiles.route('/deactivate_all')
class ProfileDeactivateAllResource(Resource):
    @ns_profiles.doc('deactivate_all_profiles')
    @ns_profiles.response(200, 'All profiles deactivated')
    def put(self):
        """Deactivate all profiles"""
        AWSProfile.query.update({AWSProfile.is_active: False})
        db.session.commit()
        return {'message': 'All profiles deactivated successfully'}

@ns_resources.route('/')
class AWSResourcesResource(Resource):
    @ns_resources.doc('get_aws_resources')
    def get(self):
        """Get AWS resources for the active profile"""
        active_profile = AWSProfile.query.filter_by(is_active=True).first()
        if not active_profile:
            api.abort(400, "No active profile found")

        aws_services = CommonAWSServices()
        resources = aws_services.get_all_resources()
        return resources

@app.route('/health')
def health_check():
    """Health check endpoint with database status"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now(UTC).isoformat(),
        'services': {}
    }

    # Check database connection
    try:
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        health_status['services']['database'] = {
            'status': 'healthy',
            'message': 'Connected to PostgreSQL'
        }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['services']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    # Check if any profiles exist (basic data check)
    try:
        profile_count = AWSProfile.query.count()
        health_status['services']['profiles'] = {
            'status': 'healthy',
            'count': profile_count
        }
    except Exception as e:
        health_status['services']['profiles'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    # Check active profile
    try:
        active_profile = AWSProfile.query.filter_by(is_active=True).first()
        health_status['services']['active_profile'] = {
            'status': 'healthy' if active_profile else 'none',
            'name': active_profile.name if active_profile else None
        }
    except Exception as e:
        health_status['services']['active_profile'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 