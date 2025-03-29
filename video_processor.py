import os
import base64
import threading
import cv2
import multiprocessing
from multiprocessing import Process, Queue
import logging
from file_manager import cleanup_video_file

logger = logging.getLogger(__name__)

# Global state variables
streaming_active = False
streaming_thread = None
processing_active = False
processing_thread = None
is_paused = False
current_video_path = None

def process_and_stream_video(video_path, app_config, socketio):
    """Process video frames using multiprocessing components and stream to client"""
    global processing_active, streaming_active, is_paused, current_video_path
    
    # Store the video path for cleanup later
    current_video_path = video_path
    
    # Reset state flags
    processing_active = True
    streaming_active = True
    is_paused = False
    
    try:    
        # Get processing configuration
        processing_config = app_config.get('processing', {})
        queue_sizes = processing_config.get('queue_sizes', {})
        progress_reporting = processing_config.get('progress_reporting', {})
        sleep_delays = processing_config.get('sleep_delays', {})
        client_config = app_config.get('client', {}).get('ui', {})
        
        # Create communication queues
        frames_queue = Queue()
        detection_queue = Queue()
        stream_queue = Queue(maxsize=queue_sizes.get('stream_queue', 10))
        
        # Create and start processes with respective configs
        from streamer import Streamer
        from detector import Detector
        from display import Display
        
        streamer_process = Process(
            target=Streamer, 
            args=(frames_queue, video_path, app_config.get('streamer', {}))
        )
        
        detector_process = Process(
            target=Detector, 
            args=(frames_queue, detection_queue, app_config.get('detector', {}))
        )
        
        display_process = Process(
            target=Display, 
            args=(detection_queue, stream_queue, app_config.get('display', {}))
        )
        
        # Function to check if processing should be paused/stopped
        def should_continue():
            return processing_active and (not is_paused)
            
        # Start streaming processed frames to the client
        def stream_frames_to_client():
            frame_count = 0
            socketio.emit('message', {'data': f"Processing and streaming video: {os.path.basename(video_path)}"})
            
            while streaming_active:
                if not is_paused:
                    try:
                        # Non-blocking get with timeout
                        processed_frame = stream_queue.get(timeout=0.5)
                        
                        # Encode frame and send to client
                        encoding_quality = client_config.get('encoding_quality', 85)
                        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), encoding_quality]
                        _, buffer = cv2.imencode('.jpg', processed_frame, encode_param)
                        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send the frame to client if streaming is still active
                        if streaming_active:
                            socketio.emit('frame', {
                                'frame': jpg_as_text,
                                'count': frame_count + 1
                            })
                        
                        frame_count += 1
                        
                        # Report progress periodically
                        ui_update_interval = progress_reporting.get('ui_update_interval', 10)
                        log_interval = progress_reporting.get('log_interval', 50)
                        
                        if frame_count % ui_update_interval == 0:
                            socketio.emit('processing_progress', {
                                'frames': frame_count,
                                'status': 'processing',
                                'progress': min(int(frame_count / 30), 99)  # Approximate progress
                            })
                            
                            if frame_count % log_interval == 0:
                                logger.info(f"Processed and streamed {frame_count} frames")
                    
                    except multiprocessing.queues.Empty:
                        # No frame available, just continue
                        socketio.sleep(sleep_delays.get('empty_queue', 0.01))
                        continue
                    except Exception as e:
                        logger.error(f"Error in streaming: {str(e)}")
                        socketio.emit('message', {'data': f"Error in streaming: {str(e)}"})
                        break
                        
                else:
                    # When paused, just sleep briefly
                    socketio.sleep(sleep_delays.get('paused', 0.1))
                    
                # Brief pause to control streaming rate
                socketio.sleep(sleep_delays.get('frame_processing', 0.05))
        
        # Start the processes
        streamer_process.start()
        detector_process.start()
        display_process.start()
        
        # Start streaming frames in the current thread
        streaming_thread = threading.Thread(target=stream_frames_to_client)
        streaming_thread.daemon = True
        streaming_thread.start()
        
        # Wait for processes to finish (or be terminated)
        streamer_process.join()
        detector_process.join()
        display_process.join()
        
        if processing_active:  # If we weren't interrupted
            socketio.emit('processing_complete', {'frames': 0})  # We don't know exact frame count
            socketio.emit('complete', {'data': 'Finished processing and streaming video'})
            
    except Exception as e:
        logger.error(f"Error in processing and streaming: {str(e)}")
        socketio.emit('message', {'data': f"Error: {str(e)}"})
        processing_active = False
        streaming_active = False
        cleanup_video_file(video_path)
        return
    
    finally:
        # Clean up and reset state
        processing_active = False
        streaming_active = False
        logger.info("Processing and streaming complete") 