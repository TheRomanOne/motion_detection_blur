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
        
        import video_processor
        import multiprocessing
        
        # Set flags to stop processing
        video_processor.streaming_active = False
        video_processor.processing_active = False
        video_processor.is_paused = False
        
        # Give a short delay for processes to finish naturally
        socketio.sleep(0.5)
        
        # Terminate any lingering child processes
        active_children = multiprocessing.active_children()
        if active_children:
            for child in active_children:
                try:
                    child.terminate()
                    socketio.sleep(0.1)  # Small delay for cleanup
                except:
                    pass  # Ignore errors during termination
        
        # Clean up the video file if it exists
        if video_processor.current_video_path:
            cleanup_video_file(video_processor.current_video_path)
            video_processor.current_video_path = None
        
        logger.info("All processes terminated after client disconnect")
    
    @socketio.on('stop_streaming')
    def handle_stop_streaming():
        import video_processor
        import multiprocessing
        
        try:
            # Set flags to stop processing
            video_processor.streaming_active = False
            video_processor.processing_active = False
            video_processor.is_paused = False
            
            # Give a short delay for processes to finish naturally
            socketio.sleep(0.5)
            
            # Terminate any lingering child processes
            active_children = multiprocessing.active_children()
            if active_children:
                for child in active_children:
                    try:
                        child.terminate()
                        socketio.sleep(0.1)  # Small delay for cleanup
                    except Exception as e:
                        logger.error(f"Error terminating child process: {str(e)}")
            
            # Clean up the video file if it exists
            if video_processor.current_video_path:
                cleaned_up = cleanup_video_file(video_processor.current_video_path)
                video_processor.current_video_path = None  # Reset the path
                message = 'Video file deleted. ' if cleaned_up else ''
                try:
                    socketio.emit('message', {'data': f'Stopping video processing and streaming... {message}'})
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
            else:
                try:
                    socketio.emit('message', {'data': 'Stopping video processing and streaming...'})
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
            
            try:
                socketio.emit('stream_stopped', {'reset': True})
            except Exception as e:
                logger.error(f"Error sending stream_stopped event: {str(e)}")
            
            logger.info("Stopping video processing and streaming")
        except Exception as e:
            logger.error(f"Error in stop_streaming handler: {str(e)}")
            # Make sure flags are set to stop processing even if errors occur
            video_processor.streaming_active = False
            video_processor.processing_active = False
            video_processor.is_paused = False
    
    @socketio.on('pause_streaming')
    def handle_pause_streaming():
        import video_processor
        
        if not video_processor.streaming_active:
            socketio.emit('message', {'data': 'No active stream to pause'})
            return
            
        video_processor.is_paused = True
        socketio.emit('stream_paused', {})
        logger.info("Streaming paused")
    
    @socketio.on('resume_streaming')
    def handle_resume_streaming():
        import video_processor
        
        if not video_processor.streaming_active:
            socketio.emit('message', {'data': 'No active stream to resume'})
            return
            
        video_processor.is_paused = False
        socketio.emit('stream_resumed', {})
        logger.info("Streaming resumed") 