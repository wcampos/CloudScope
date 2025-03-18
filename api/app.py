from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from datetime import datetime, UTC
import os
import logging
import boto3
import configparser
from aws_classes import CommonAWSServices
from extensions import db, migrate
from models import AWSProfile, SchemaVersion
from utils import DateTimeEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure JSON encoder
app.json_encoder = DateTimeEncoder

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
api = Api(app, version='1.0', title='AWS Inventory API',
          description='API for managing AWS profiles and resources',
          prefix='/api',
          doc='/api/docs')

# Create tables within application context
with app.app_context():
    db.create_all()

# Define API models for documentation
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
    @ns_profiles.marshal_list_with(profile_model)
    def get(self):
        """List all profiles"""
        return AWSProfile.query.all()

    @ns_profiles.doc('create_profile')
    @ns_profiles.expect(profile_model)
    @ns_profiles.marshal_with(profile_model, code=201)
    def post(self):
        """Create a new profile"""
        data = request.json
        profile = AWSProfile(**data)
        db.session.add(profile)
        db.session.commit()
        return profile, 201

@ns_profiles.route('/<int:profile_id>')
@ns_profiles.response(404, 'Profile not found')
class ProfileResource(Resource):
    @ns_profiles.doc('get_profile')
    @ns_profiles.marshal_with(profile_model)
    def get(self, profile_id):
        """Get a profile by ID"""
        profile = AWSProfile.query.get_or_404(profile_id)
        return profile

    @ns_profiles.doc('update_profile')
    @ns_profiles.expect(profile_model)
    @ns_profiles.marshal_with(profile_model)
    def put(self, profile_id):
        """Update a profile"""
        profile = AWSProfile.query.get_or_404(profile_id)
        data = request.json
        for key, value in data.items():
            setattr(profile, key, value)
        db.session.commit()
        return profile

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
    @ns_profiles.marshal_with(profile_model, code=201)
    def post(self):
        """Parse AWS credentials and create a profile"""
        data = request.json
        credentials_text = data.get('credentials_text')
        if not credentials_text:
            return {'error': 'No credentials provided'}, 400

        # Create a ConfigParser with the pasted text
        config = configparser.ConfigParser()
        
        # Add a default section header if none exists
        if not credentials_text.strip().startswith('['):
            credentials_text = '[default]\n' + credentials_text
        
        # Parse the credentials text
        config.read_string(credentials_text)

        # Get the first section (profile) name
        if len(config.sections()) == 0:
            return {'error': 'No valid profile found in credentials'}, 400
        
        profile_name = config.sections()[0]
        profile_data = config[profile_name]

        # Extract required fields
        aws_access_key_id = profile_data.get('aws_access_key_id')
        aws_secret_access_key = profile_data.get('aws_secret_access_key')
        if not aws_access_key_id or not aws_secret_access_key:
            return {'error': 'Access key ID and secret access key are required'}, 400

        # Extract optional fields
        aws_session_token = profile_data.get('aws_session_token')
        region = profile_data.get('region', 'us-east-1')

        # Create new profile in database
        new_profile = AWSProfile(
            name=profile_name.replace('profile ', ''),  # Remove 'profile ' prefix if present
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            aws_region=region
        )

        # Try to get account number
        try:
            account_info = new_profile.get_account_info()
            if account_info:
                new_profile.account_number = account_info['account']
        except Exception as e:
            logger.warning(f"Could not fetch account number for profile {profile_name}: {str(e)}")

        db.session.add(new_profile)
        db.session.commit()

        return new_profile, 201

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
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now(UTC).isoformat()
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 