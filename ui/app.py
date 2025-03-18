from flask import Flask, render_template, request, flash, redirect, url_for
from flask_restx import Api, Resource, fields
import requests
from datetime import datetime, UTC
import logging
import os
import redis
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Add context processor to make active profile available to all templates
@app.context_processor
def inject_active_profile():
    try:
        profiles = api_request('GET', '/api/profiles')
        active_profile = next((p for p in profiles if p.get('is_active')), None)
        return dict(active_profile=active_profile)
    except Exception as e:
        logger.warning(f"Could not fetch active profile: {str(e)}")
        return dict(active_profile=None)

# Initialize Redis client
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Cache configuration
CACHE_KEY = 'aws_resources_cache'
CACHE_TIMESTAMP_KEY = 'aws_resources_timestamp'
CACHE_DURATION = 300  # 5 minutes in seconds

# Initialize API documentation
api = Api(app, version='1.0', title='AWS Inventory UI',
          description='UI service for managing AWS profiles and resources',
          doc='/ui/docs',
          prefix='/api')

# API service configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://api:5000')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 300))  # 5 minutes default timeout

@app.template_filter('now')
def now_filter(date_format='%Y'):
    """Template filter to format current datetime."""
    return datetime.now(UTC).strftime(date_format)

def api_request(method, endpoint, **kwargs):
    """Helper function to make API requests"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        # Set default timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = API_TIMEOUT
            
        # Ensure endpoint has trailing slash if it's a GET request
        if method == 'GET' and not endpoint.endswith('/'):
            url += '/'
            
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Response text: {e.response.text}")
        raise

# Define namespaces
ns_pages = api.namespace('', description='Page operations')
ns_profiles = api.namespace('profiles', description='Profile operations')
ns_system = api.namespace('system', description='System operations')

@app.route('/')
def index():
    """Get the home page"""
    logger.debug("Handling request for index page")
    try:
        # Get active profile if any
        active_profile = None
        try:
            profiles = api_request('GET', '/api/profiles')
            active_profile = next((p for p in profiles if p.get('is_active')), None)
        except Exception as e:
            logger.warning(f"Could not fetch active profile: {str(e)}")
        
        return render_template('index.html.j2', active_profile=active_profile)
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return render_template('error.html.j2', error=str(e))

@app.route('/loading')
def loading():
    """Show loading page while fetching resources"""
    return render_template('loading.html.j2')

def get_active_profile():
    """Get the currently active profile from the API"""
    try:
        profiles = api_request('GET', '/api/profiles')
        active_profile = next((p for p in profiles if p.get('is_active')), None)
        if active_profile:
            # Get account info for active profile
            try:
                account_info = api_request('GET', f'/api/profiles/{active_profile["id"]}/account-info')
                active_profile['account_info'] = account_info
            except Exception as e:
                logger.warning(f"Could not fetch account info: {str(e)}")
                active_profile['account_info'] = {
                    'account': active_profile.get('account_number', 'Unknown'),
                    'region': active_profile.get('aws_region', 'Unknown')
                }
        return active_profile
    except Exception as e:
        logger.error(f"Error getting active profile: {str(e)}")
        return None

def get_resources_from_cache():
    """Get resources from Redis cache"""
    try:
        # Check if cache exists and is valid
        timestamp = redis_client.get(CACHE_TIMESTAMP_KEY)
        if not timestamp:
            return None
            
        age = int(datetime.now(UTC).timestamp()) - int(timestamp)
        if age > CACHE_DURATION:
            return None
            
        # Get cached data
        cached_data = redis_client.get(CACHE_KEY)
        return json.loads(cached_data) if cached_data else None
    except Exception as e:
        logger.error(f"Error getting cached resources: {str(e)}")
        return None

def get_resources_from_api():
    """Get resources from the API"""
    try:
        return api_request('GET', '/api/resources')
    except Exception as e:
        logger.error(f"Error getting resources from API: {str(e)}")
        return None

def cache_resources(resources):
    """Cache resources in Redis"""
    try:
        # Store resources data
        redis_client.set(CACHE_KEY, json.dumps(resources))
        # Store timestamp
        redis_client.set(CACHE_TIMESTAMP_KEY, int(datetime.now(UTC).timestamp()))
        logger.debug("Resources cached successfully")
    except Exception as e:
        logger.error(f"Error caching resources: {str(e)}")

@app.route('/dashboard')
def dashboard():
    """Dashboard view"""
    try:
        # Get active profile
        active_profile = get_active_profile()
        if not active_profile:
            flash('No active AWS profile found. Please set up a profile first.', 'warning')
            return redirect(url_for('index'))

        # Get account info
        account_info = active_profile.get('account_info', {
            'account': active_profile.get('account_number', 'Unknown'),
            'region': active_profile.get('aws_region', 'Unknown')
        })
        
        # Get resources from cache or API
        resources = get_resources_from_cache()
        if not resources:
            resources = get_resources_from_api()
            if resources:
                cache_resources(resources)

        # Create summary view
        summary = {}
        if resources:
            for service_name, items in resources.items():
                summary[service_name] = len(items)

        # Log all available resource types for debugging
        logger.debug(f"Available resource types: {list(resources.keys()) if resources else []}")

        # Filter resources based on view
        view = request.args.get('view', 'summary')
        if view != 'summary':
            filtered_resources = {}
            if view == 'compute':
                compute_services = ['EC2 Instances', 'EC2 Volumes', 'EC2 AMIs', 'EC2 Snapshots', 
                                  'ECS Clusters', 'ECS Services', 'EKS Clusters', 'Lambda Functions']
                filtered_resources = {k: v for k, v in resources.items() if k in compute_services}
            elif view == 'storage':
                storage_services = ['RDS Instances', 'S3 Buckets', 'DynamoDB Tables']
                filtered_resources = {k: v for k, v in resources.items() if k in storage_services}
            elif view == 'network':
                network_services = ['VPCs', 'Subnets', 'Security Groups', 'Security Group Rules',
                                  'Route53 Hosted Zones', 'SSL Certificates']
                filtered_resources = {k: v for k, v in resources.items() if k in network_services}
            elif view == 'service':
                service_services = ['Load Balancers', 'Target Groups']
                filtered_resources = {k: v for k, v in resources.items() if k in service_services}
                # Log service resources for debugging
                logger.debug(f"Service view resources: {filtered_resources}")
            resources = filtered_resources

        # Log resources for debugging
        logger.debug(f"Resources for view '{view}': {resources}")

        return render_template('dashboard.html.j2', 
                             resources=resources or {},
                             summary=summary,
                             current_view=view,
                             account_info=account_info)
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/profiles')
def profiles():
    """Get the profiles management page"""
    try:
        profiles = api_request('GET', '/api/profiles')
        return render_template('profiles.html.j2', profiles=profiles)
    except requests.exceptions.RequestException as e:
        flash(f"Error: {str(e)}", 'error')
        return render_template('error.html.j2', error=str(e))

@app.route('/profiles/add', methods=['GET', 'POST'])
def add_profile():
    """Add a new profile"""
    if request.method == 'POST':
        try:
            response = api_request('POST', '/api/profiles', json=request.form.to_dict())
            flash('Profile added successfully!', 'success')
            return redirect(url_for('profiles'))
        except requests.exceptions.RequestException as e:
            flash(f"Error: {str(e)}", 'error')
            return render_template('add_profile.html.j2')
    return render_template('add_profile.html.j2')

@app.route('/profiles/<int:profile_id>/edit', methods=['GET', 'POST'])
def edit_profile(profile_id):
    """Edit a profile"""
    if request.method == 'POST':
        try:
            response = api_request('PUT', f'/api/profiles/{profile_id}', 
                                json=request.form.to_dict())
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profiles'))
        except requests.exceptions.RequestException as e:
            flash(f"Error: {str(e)}", 'error')
    
    try:
        profile = api_request('GET', f'/api/profiles/{profile_id}')
        return render_template('edit_profile.html.j2', profile=profile)
    except requests.exceptions.RequestException as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('profiles'))

@app.route('/profiles/<int:profile_id>/delete', methods=['POST'])
def delete_profile(profile_id):
    """Delete a profile"""
    try:
        response = api_request('DELETE', f'/api/profiles/{profile_id}')
        flash('Profile deleted successfully!', 'success')
    except requests.exceptions.RequestException as e:
        flash(f"Error: {str(e)}", 'error')
    return redirect(url_for('profiles'))

@app.route('/set_active_profile', methods=['POST'])
def set_active_profile():
    """Set a profile as active"""
    profile_id = request.form.get('profile_id')
    if not profile_id:
        flash('No profile selected', 'error')
        return redirect(url_for('profiles'))

    try:
        # First, deactivate all profiles
        api_request('PUT', '/api/profiles/deactivate_all')
        
        # Then, activate the selected profile
        api_request('PUT', f'/api/profiles/{profile_id}/activate')
        flash('Profile activated successfully', 'success')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error setting active profile: {str(e)}")
        flash(f'Error activating profile: {str(e)}', 'error')
    
    return redirect(url_for('profiles'))

@app.route('/parse_credentials', methods=['POST'])
def parse_credentials():
    """Parse AWS credentials and create a profile"""
    credentials_text = request.form.get('credentials_text')
    try:
        response = api_request('POST', '/api/profiles/parse', json={'credentials_text': credentials_text})
        flash('Credentials parsed successfully!', 'success')
        return redirect(url_for('profiles'))
    except requests.exceptions.RequestException as e:
        flash(f'Error parsing credentials: {str(e)}', 'error')
        return redirect(url_for('profiles'))

@app.route('/settings')
def settings():
    """Get the settings page"""
    try:
        return render_template('settings.html.j2')
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return render_template('error.html.j2', error=str(e))

@app.route('/health')
def health_check():
    """Check the health status of the UI service"""
    try:
        # Check API health
        api_health = api_request('GET', '/health')
        return {
            'status': 'healthy',
            'api_status': api_health.get('status', 'unknown'),
            'timestamp': datetime.now(UTC).isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(UTC).isoformat()
        }, 500

@app.route('/api/resources/refresh', methods=['POST'])
def refresh_resources():
    """Force refresh of resources cache"""
    try:
        # Fetch fresh resources
        resources = api_request('GET', '/api/resources')
        # Update cache
        update_cache(resources)
        return {'status': 'success', 'message': 'Resources cache refreshed'}
    except Exception as e:
        logger.error(f"Error refreshing resources cache: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500

# Log all registered routes
with app.app_context():
    logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"{rule.endpoint}: {rule.rule}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 