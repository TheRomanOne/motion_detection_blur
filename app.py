import eventlet
eventlet.monkey_patch()

# Import configured modules
from flask import Flask
from flask_socketio import SocketIO

# Import our new modules
from config import logger, load_config, initialize_app_config
from routes import register_routes
from socketio_events import register_socketio_events

# Load application configuration first
app_config = load_config()

# Extract async mode from config
async_mode = app_config['socket'].get('async_mode', 'eventlet')

# Log startup information
logger.info(f"Using {async_mode} mode for Socket.IO")

# Create Flask app
app = Flask(__name__, static_folder='frontend/build', static_url_path='')

# Initialize app configuration
initialize_app_config(app, app_config)

# Initialize SocketIO with config
socketio = SocketIO(app, 
                   cors_allowed_origins=app_config['socket']['cors_allowed_origins'], 
                   async_mode=async_mode,
                   ping_timeout=app_config['socket'].get('ping_timeout', 60),
                   ping_interval=app_config['socket'].get('ping_interval', 25))

# Register routes and socket event handlers
register_routes(app, socketio, app_config)
register_socketio_events(socketio)

if __name__ == '__main__':
    host = app_config['server'].get('host', '0.0.0.0')
    port = app_config['server'].get('port', 5000)
    logger.info(f"Server starting on http://{host}:{port}")
    socketio.run(app, host=host, port=port) 