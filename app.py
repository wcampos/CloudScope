import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from src.models import db, AWSProfile, SchemaVersion
from src import aws_classes as awsc
from src.version import get_version
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from logging.handlers import RotatingFileHandler
from urllib.parse import quote_plus

def get_database_url():
    """Construct database URL from environment variables or return the direct URL if provided"""
    if 'DATABASE_URL' in os.environ:
        return os.environ['DATABASE_URL']
    
    db_user = quote_plus(os.environ.get('DB_USER', 'awsuser'))
    db_pass = quote_plus(os.environ.get('DB_PASSWORD', 'awspass'))
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = os.environ.get('DB_PORT', '5432')
    db_name = os.environ.get('DB_NAME', 'awsprofiles')
    
    return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

app = Flask(__name__)

# Configure logging
log_dir = os.environ.get('LOG_FILE', 'logs/aws_inventory.log').rsplit('/', 1)[0]
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_handler = RotatingFileHandler(
    os.environ.get('LOG_FILE', 'logs/aws_inventory.log'),
    maxBytes=int(os.environ.get('LOG_MAX_BYTES', 10240)),
    backupCount=int(os.environ.get('LOG_BACKUP_COUNT', 10))
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')))
app.logger.addHandler(file_handler)
app.logger.setLevel(getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')))
app.logger.info('AWS Inventory startup')

# Flask configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Database configuration and verification
try:
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    app.logger.info('Database connection successful')
except SQLAlchemyError as e:
    app.logger.error(f'Database connection failed: {str(e)}')
    raise

def handle_aws_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            app.logger.error(f"AWS Profile error in {func.__name__}: {str(e)}")
            flash("Please select an AWS profile first", "warning")
            return redirect(url_for('profiles'))
        except ClientError as e:
            app.logger.error(f"AWS API error in {func.__name__}: {str(e)}")
            error_message = "An error occurred while fetching AWS resources"
            return render_template("error.html.j2", error=error_message)
        except Exception as e:
            app.logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            error_message = "An unexpected error occurred"
            return render_template("error.html.j2", error=error_message)
    wrapper.__name__ = func.__name__
    return wrapper

@app.template_filter('now')
def now_filter(format='%Y'):
    return datetime.now().strftime(format)

@app.template_filter('datetime')
def datetime_filter(value, format_string='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ''
    return value.strftime(format_string)

@app.route("/")
def index():
    active_profile = AWSProfile.get_active_profile()
    return render_template("index.html.j2", active_profile=active_profile)

@app.route("/profiles", methods=['GET'])
def profiles():
    profiles = AWSProfile.query.all()
    return render_template("profiles.html.j2", profiles=profiles)

@app.route("/profiles/add", methods=['POST'])
def add_profile():
    try:
        profile = AWSProfile(
            name=request.form['name'],
            aws_access_key_id=request.form['aws_access_key_id'],
            aws_secret_access_key=request.form['aws_secret_access_key'],
            aws_session_token=request.form.get('aws_session_token'),
            aws_region=request.form['aws_region']
        )
        db.session.add(profile)
        db.session.commit()
        flash('Profile added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding profile: {str(e)}', 'error')
    return redirect(url_for('profiles'))

@app.route("/profiles/<int:profile_id>/delete", methods=['POST'])
def delete_profile(profile_id):
    profile = AWSProfile.query.get_or_404(profile_id)
    try:
        db.session.delete(profile)
        db.session.commit()
        flash('Profile deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting profile: {str(e)}', 'error')
    return redirect(url_for('profiles'))

@app.route("/profiles/set-active", methods=['POST'])
def set_active_profile():
    profile_id = request.form.get('profile_id')
    if profile_id:
        profile = AWSProfile.query.get_or_404(profile_id)
        profile.set_as_active()
        flash('Active profile updated successfully', 'success')
    else:
        AWSProfile.query.update({'is_active': False})
        db.session.commit()
        flash('No profile selected', 'info')
    return redirect(url_for('profiles'))

@app.route("/networks")
@handle_aws_error
def networking():
    return redirect(url_for('dashboard', view='network'))

@app.route("/rds")
@handle_aws_error
def rds():
    return redirect(url_for('dashboard', view='storage'))

@app.route("/s3")
@handle_aws_error
def s3():
    return redirect(url_for('dashboard', view='storage'))

@app.route("/ec2")
@handle_aws_error
def ec2():
    return redirect(url_for('dashboard', view='compute'))

@app.route("/lambda")
@handle_aws_error
def lambdax():
    return redirect(url_for('dashboard', view='services'))

@app.route("/dynamodb")
@handle_aws_error
def dynamodb():
    return redirect(url_for('dashboard', view='storage'))

@app.route("/alb")
@handle_aws_error
def alb():
    return redirect(url_for('dashboard', view='services'))

@app.route("/sgs")
@handle_aws_error
def sgs():
    return redirect(url_for('dashboard', view='network'))

@app.route("/dashboard")
@handle_aws_error
def dashboard():
    aws_services = awsc.CommonAWSServices()
    
    view_type = request.args.get('view', 'all')
    
    if view_type == 'compute':
        resources = aws_services.get_compute_resources()
        title = "Compute Resources"
    elif view_type == 'storage':
        resources = aws_services.get_storage_resources()
        title = "Storage Resources"
    elif view_type == 'network':
        resources = aws_services.get_network_resources()
        title = "Network Resources"
    elif view_type == 'services':
        resources = aws_services.get_service_resources()
        title = "AWS Services"
    else:
        resources = aws_services.get_all_resources()
        title = "All AWS Resources"
    
    return render_template(
        "dashboard.html.j2",
        resources=resources,
        title=title,
        current_view=view_type
    )

@app.route("/settings")
def settings():
    """Display application settings and environment information."""
    db_config = app.config['SQLALCHEMY_DATABASE_URI']
    
    # Parse database URL to get components
    if 'postgresql://' in db_config:
        # Extract host from database URL
        db_host = db_config.split('@')[1].split(':')[0]
        db_port = db_config.split(':')[-1].split('/')[0]
        db_name = db_config.split('/')[-1]
    else:
        # Use environment variables
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'awsprofiles')

    return render_template(
        "settings.html.j2",
        version=get_version(),
        flask_env=os.environ.get('FLASK_ENV', 'production'),
        debug_mode=app.debug,
        db_host=db_host,
        db_port=db_port,
        db_name=db_name
    )

@app.errorhandler(404)
def not_found_error(error):
    return render_template("error.html.j2", error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html.j2", error="Internal server error"), 500

def init_db():
    CURRENT_SCHEMA_VERSION = '1.0.0'  # Update this when making schema changes

    with app.app_context():
        inspector = inspect(db.engine)
        tables_exist = inspector.get_table_names()
        
        # If no tables exist, create everything
        if not tables_exist:
            app.logger.info('No tables found. Creating initial schema...')
            db.create_all()
            version = SchemaVersion(version=CURRENT_SCHEMA_VERSION)
            db.session.add(version)
            db.session.commit()
            app.logger.info(f'Schema version {CURRENT_SCHEMA_VERSION} initialized')
            return

        # If tables exist, check version
        if 'schema_version' in tables_exist:
            current_version = SchemaVersion.get_current_version()
            if current_version != CURRENT_SCHEMA_VERSION:
                app.logger.info(f'Schema version mismatch. Current: {current_version}, Expected: {CURRENT_SCHEMA_VERSION}')
                # Here you would typically run migrations instead of recreating
                # For now, we'll just update the version
                version = SchemaVersion(version=CURRENT_SCHEMA_VERSION)
                db.session.add(version)
                db.session.commit()
                app.logger.info(f'Schema updated to version {CURRENT_SCHEMA_VERSION}')
            else:
                app.logger.info(f'Schema version {CURRENT_SCHEMA_VERSION} already applied')
        else:
            # Schema version table doesn't exist but other tables do
            # This is for existing installations
            app.logger.info('Adding schema version tracking to existing database')
            db.create_all()  # This will only create missing tables
            version = SchemaVersion(version=CURRENT_SCHEMA_VERSION)
            db.session.add(version)
            db.session.commit()
            app.logger.info(f'Schema version {CURRENT_SCHEMA_VERSION} initialized for existing database')

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0')
