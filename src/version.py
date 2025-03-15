"""Version information for the AWS Inventory application."""
import os
import subprocess

def get_version():
    """Get the current version of the application.
    
    Returns:
        str: The version string. If running in development mode, returns 'development'.
        If in production and git is available, returns the git commit hash.
        Otherwise, returns 'unknown'.
    """
    if os.environ.get('FLASK_ENV') == 'development':
        return 'development'
    
    try:
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
        return git_hash.decode('utf-8').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 'unknown' 