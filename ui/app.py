from flask import Flask, render_template, request, flash, redirect, url_for
from flask_restx import Api, Resource, fields
import requests
from datetime import datetime, UTC
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Initialize API documentation
api = Api(app, version='1.0', title='AWS Inventory UI',
          description='UI service for managing AWS profiles and resources',
          doc='/ui/docs',
          prefix='/api')

# API service configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://api:5000')

@app.template_filter('now')
def now_filter(date_format='%Y'):
    """Template filter to format current datetime."""
    return datetime.now(UTC).strftime(date_format)

def api_request(method, endpoint, **kwargs):
    """Helper function to make API requests"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
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
        return render_template('index.html.j2')
    except Exception as e:
        logger.error(f"Error rendering index page: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return render_template('error.html.j2', error=str(e))

@app.route('/dashboard')
def dashboard():
    """Get the dashboard page"""
    try:
        resources = api_request('GET', '/api/resources')
        profiles = api_request('GET', '/api/profiles')
        current_view = request.args.get('view', 'all')
        
        # Filter resources based on the selected view
        if current_view != 'all':
            filtered_resources = {}
            for service_name, items in resources.items():
                # Map services to their categories
                service_categories = {
                    'compute': ['ec2', 'lambda', 'ecs', 'eks'],
                    'storage': ['s3', 'ebs', 'efs', 'rds'],
                    'network': ['vpc', 'subnet', 'security_group', 'route_table', 'internet_gateway', 'nat_gateway'],
                    'services': ['alb', 'dynamodb', 'cloudwatch', 'iam']
                }
                
                # Check if the service belongs to the selected category
                if any(category in service_name.lower() for category in service_categories.get(current_view, [])):
                    filtered_resources[service_name] = items
            
            resources = filtered_resources
        
        return render_template('dashboard.html.j2',
                            resources=resources,
                            profiles=profiles,
                            current_view=current_view,
                            title='Dashboard')
    except requests.exceptions.RequestException as e:
        flash(f"Error: {str(e)}", 'error')
        return render_template('error.html.j2', error=str(e))

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

# Log all registered routes
with app.app_context():
    logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.debug(f"{rule.endpoint}: {rule.rule}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 