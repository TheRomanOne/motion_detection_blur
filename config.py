import os
import json
import logging

# Set up logging with appropriate level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Disable verbose socket.io and engineio logs
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

def load_config(config_path='config.json'):
    """Load configuration from a JSON file"""
    with open(config_path, 'r') as f:
        config = json.load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config

def create_upload_directory(app):
    """Create necessary upload directories"""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    logger.info(f"Created upload directory: {app.config['UPLOAD_FOLDER']}")

def initialize_app_config(app, config):
    """Initialize Flask app configuration from the loaded config"""
    # Configure upload settings
    app.config['MAX_CONTENT_LENGTH'] = config['server']['max_content_length'] * 1024 * 1024  # Convert MB to bytes
    app.config['UPLOAD_FOLDER'] = config['server']['upload_folder']
    
    # Create necessary directories
    create_upload_directory(app) 