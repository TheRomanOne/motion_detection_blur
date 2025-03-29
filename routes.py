from flask import send_from_directory, jsonify, request
import os
import logging
from file_manager import cleanup_video_file, generate_unique_filename, is_valid_video_format
import video_processor

logger = logging.getLogger(__name__)

def register_routes(app, socketio, app_config):
    """Register all API routes"""
    
    @app.route('/')
    def index():
        """Serve the static React app"""
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/api/upload_video', methods=['POST'])
    def upload_video():
        # Check if there's a file in the request
        if 'video' not in request.files:
            logger.warning("No video file in upload request")
            return jsonify({'status': 'error', 'message': 'No video file provided'}), 400
            
        file = request.files['video']
        
        # Check if the file is selected
        if file.filename == '':
            logger.warning("Empty filename in upload request")
            return jsonify({'status': 'error', 'message': 'No video file selected'}), 400
            
        # Check if processing is already happening
        if video_processor.processing_active or video_processor.streaming_active:
            logger.warning("Attempted upload while processing is active")
            return jsonify({'status': 'error', 'message': 'Video processing already in progress'}), 409
        
        try:
            # Get valid video formats from config
            valid_formats = app_config['server'].get('valid_video_formats', ['.mp4', '.avi', '.mov', '.mkv'])
            
            # Validate file format
            if not is_valid_video_format(file.filename, valid_formats):
                file_ext = os.path.splitext(file.filename)[1].lower()
                logger.warning(f"Unsupported file format: {file_ext}")
                return jsonify({'status': 'error', 'message': 'Unsupported video format'}), 400
                
            # Generate a unique filename
            unique_filename = generate_unique_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Save the uploaded file
            file.save(filepath)
            logger.info(f"Video uploaded to {filepath}")
            
            # Start processing and streaming in background
            socketio.start_background_task(
                    video_processor.process_and_stream_video, 
                    filepath, 
                    app_config, 
                    socketio
                )
            
            return jsonify({
                'status': 'success', 
                'message': 'Video upload successful, processing and streaming started',
                'filename': unique_filename
            })
        except Exception as e:
            logger.error(f"Error during upload: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Upload error: {str(e)}'}), 500
    
    # Add a new endpoint to expose configuration to frontend
    @app.route('/api/config', methods=['GET'])
    def get_frontend_config():
        """Provide the frontend with necessary configuration values"""
        # Only expose what the frontend needs
        frontend_config = {
            'upload': app_config.get('client', {}).get('upload', {}),
            'ui': app_config.get('client', {}).get('ui', {}),
            'websocket': app_config.get('client', {}).get('websocket', {})
        }
        return jsonify(frontend_config)
