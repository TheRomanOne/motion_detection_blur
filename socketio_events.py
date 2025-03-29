import logging
from video_processor import is_paused, current_video_path, streaming_active, processing_active
from file_manager import cleanup_video_file

logger = logging.getLogger(__name__)

def register_socketio_events(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
        socketio.emit('message', {'data': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")
        global streaming_active, processing_active
        
        import video_processor
        video_processor.streaming_active = False
        video_processor.processing_active = False
        
        # Clean up the video file if it exists
        if video_processor.current_video_path:
            cleanup_video_file(video_processor.current_video_path)
            video_processor.current_video_path = None
    
    @socketio.on('stop_streaming')
    def handle_stop_streaming():
        import video_processor
        
        video_processor.streaming_active = False
        video_processor.processing_active = False
        video_processor.is_paused = False
        
        # Clean up the video file if it exists
        if video_processor.current_video_path:
            cleaned_up = cleanup_video_file(video_processor.current_video_path)
            video_processor.current_video_path = None  # Reset the path
            message = 'Video file deleted. ' if cleaned_up else ''
            socketio.emit('message', {'data': f'Stopping video processing and streaming... {message}'})
        else:
            socketio.emit('message', {'data': 'Stopping video processing and streaming...'})
        
        socketio.emit('stream_stopped', {'reset': True})
        logger.info("Stopping video processing and streaming")
    
    @socketio.on('pause_streaming')
    def handle_pause_streaming():
        import video_processor
        
        if not video_processor.streaming_active:
            socketio.emit('message', {'data': 'No active stream to pause'})
            return
            
        video_processor.is_paused = True
        socketio.emit('message', {'data': 'Stream paused'})
        socketio.emit('stream_paused', {})
        logger.info("Streaming paused")
    
    @socketio.on('resume_streaming')
    def handle_resume_streaming():
        import video_processor
        
        if not video_processor.streaming_active:
            socketio.emit('message', {'data': 'No active stream to resume'})
            return
            
        video_processor.is_paused = False
        socketio.emit('message', {'data': 'Stream resumed'})
        socketio.emit('stream_resumed', {})
        logger.info("Streaming resumed") 