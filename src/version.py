"""Version information for AWS Inventory."""
import os

# Default version if not running from a release
__version__ = "development"

def get_version():
    """Get the current version of the application.
    
    Returns:
        str: The version string. Will be 'development' if not running from a release,
             otherwise will be the release version.
    """
    # Check for version file that would be created during release
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return __version__ 