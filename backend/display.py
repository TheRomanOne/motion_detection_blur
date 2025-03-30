import cv2
import numpy as np
import datetime
import os
import shutil
import logging
import json

logger = logging.getLogger(__name__)

"""
The Display class receives frames and detection data from the Detector process.
It overlays the current timestamp and draws rectangles around detected regions,
applying a Gaussian blur to these areas for emphasis. Instead of displaying the
video, it saves each processed frame to the 'frames' directory. The processing
continues until the video ends or the user presses 'q' to quit. Configuration
settings for display options are loaded from a JSON file.
"""

class Display:
    """
    Handles frame processing, visualization, and optional saving.
    """
    def __init__(self, detection_queue=None, stream_queue=None, config=None):
        """
        Initialize the display processor with configuration
        
        Args:
            detection_queue: Queue to receive frames and detections from
            stream_queue: Queue to send processed frames for streaming
            config: Dictionary with display configuration parameters
                   If None, will attempt to load from config.json
        """
        # Store the queues
        self.detection_queue = detection_queue
        self.stream_queue = stream_queue
        self.config = config
            
        # Validate that required keys exist
        required_keys = ['blur_kernel_size', 'rectangle', 'timestamp']
        missing_keys = [key for key in required_keys if key not in self.config]
        
        if missing_keys:
            logger.error(f"Missing required configuration keys: {missing_keys}")
            raise ValueError(f"Missing required configuration keys: {missing_keys}")
                            
        logger.debug(f"Display initialized with config: {self.config}")
            
        # If queues are provided, start processing in a separate thread
        if self.detection_queue is not None and self.stream_queue is not None:
            self.start_processing()
            
    def set_config(self, config):
        """Update processing configuration"""
        self.config.update(config)
        logger.debug(f"Display config updated: {self.config}")
        
        # Re-validate configuration after update
        required_keys = ['blur_kernel_size', 'rectangle', 'timestamp']
        missing_keys = [key for key in required_keys if key not in self.config]
        
        if missing_keys:
            logger.error(f"Missing required configuration keys after update: {missing_keys}")
            raise ValueError(f"Missing required configuration keys after update: {missing_keys}")
    
    def apply_gaussian_blur(self, frame, x, y, w, h, kernel_size):
        """Apply Gaussian blur to a region of the frame"""
        # Extract the region
        region = frame[y:y+h, x:x+w]
        
        # Apply Gaussian blur
        blurred_region = cv2.GaussianBlur(region, (kernel_size, kernel_size), 0)
        
        # Replace the region in the original frame
        frame[y:y+h, x:x+w] = blurred_region
        
        return frame
    
    def process_frame(self, frame, detections=None):
        """
        Process a single frame with detections
        
        Args:
            frame: The video frame to process
            detections: List of (x, y, w, h) detection tuples
            timestamp: Optional timestamp string, if None current time is used
        
        Returns:
            Processed frame
        """
        if detections is None:
            detections = []
            
        # Apply blur and draw rectangles for each detection
        for x, y, w, h in detections:
            # Apply blur to detected regions
            frame = self.apply_gaussian_blur(frame, x, y, w, h, self.config['blur_kernel_size'])
            
            # Draw rectangle
            cv2.rectangle(
                frame, 
                (x, y), 
                (x + w, y + h), 
                tuple(self.config['rectangle']['color']), 
                self.config['rectangle']['thickness']
            )
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        cv2.putText(
            frame, 
            timestamp, 
            tuple(self.config['timestamp']['position']), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            self.config['timestamp']['font_scale'], 
            tuple(self.config['timestamp']['color']), 
            self.config['timestamp']['thickness']
        )
        
        return frame 
    
    def start_processing(self):
        """Start processing frames from detection queue and sending to stream queue"""
        while True:
            try:
                # Get frame and detections from queue
                frame_data = self.detection_queue.get()
                
                # Check if it's a termination signal
                if frame_data is None:
                    break
                    
                frame, detections = frame_data
                
                # Process the frame
                processed_frame = self.process_frame(frame, detections)
                
                # Send to stream queue if it exists
                if self.stream_queue is not None:
                    self.stream_queue.put(processed_frame)
                    
            except Exception as e:
                logger.error(f"Error in display processing: {str(e)}")
                break
                
        logger.info("Display processing stopped") 