import cv2
import time
import logging

logger = logging.getLogger(__name__)

# The Streamer class is responsible for reading a video file frame by frame and
# sending each frame to the Detector process. It uses OpenCV to handle video
# capture and applies a small delay between frames to manage the flow of data
# through the pipeline. If the video cannot be opened or ends, it signals the
# other processes to terminate by sending a None value through the queue.

class Streamer:
    def __init__(self, output_queue, video_path, config):
        self.output_queue = output_queue
        self.video_path = video_path
        self.config = config
        self.process_video()
        
    def process_video(self):
        # Open the video
        try:
            cap = cv2.VideoCapture(self.video_path)
            
            if not cap.isOpened():
                logger.error(f"Error: Could not open video at {self.video_path}")
                # Signal other processes to terminate by sending None
                self.output_queue.put(None)
                return
                
            # Process frame by frame
            frame_count = 0
            while True:
                ret, frame = cap.read()
                
                # If frame is read correctly, ret is True
                if not ret:
                    logger.info(f"End of video stream after {frame_count} frames")
                    # Signal other processes to terminate by sending None
                    self.output_queue.put(None)
                    break
                    
                # Send the frame to the detector
                self.output_queue.put(frame)
                frame_count += 1
                
                # Small delay to prevent overwhelming the queue
                time.sleep(self.config.get('sleep_delay', 0.01))
                
        except Exception as e:
            logger.error(f"Error in video streaming: {str(e)}")
            # Signal error to other processes
            self.output_queue.put(None)
        finally:
            # Always release the video capture object
            if 'cap' in locals() and cap is not None:
                cap.release()
                logger.info("Video capture released") 