import cv2
import numpy as np
import datetime

"""
The Display class receives frames and detection data from the Detector process.
It overlays the current timestamp and draws rectangles around detected regions,
applying a Gaussian blur to these areas for emphasis. The processed video is
displayed in a window using OpenCV. The display loop continues until the video
ends or the user presses 'q' to quit. Configuration settings for display options
are loaded from a JSON file.
"""

class Display:
    def __init__(self, input_queue, config):
        self.input_queue = input_queue
        self.config = config
        self.display_video()
        
    def apply_gaussian_blur(self, frame, x, y, w, h):
        # Extract the region
        region = frame[y:y+h, x:x+w]
        
        # Apply Gaussian blur with kernel size from config
        kernel_size = self.config['blur_kernel_size']
        blurred = cv2.GaussianBlur(region, (kernel_size, kernel_size), 0)
        
        # Replace the region with its blurred version
        frame[y:y+h, x:x+w] = blurred
        
        return frame
        
    def display_video(self):
        # Extract config values
        timestamp_config = self.config['timestamp']
        rect_config = self.config['rectangle']
        
        while True:
            # Get frame and detections from the queue
            data = self.input_queue.get()
            
            # Check if the detector has finished
            if data is None:
                print("Display: Received termination signal")
                break
                
            frame, detections = data
            
            # Add current time to the top-left corner
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            position = tuple(timestamp_config['position'])
            font_scale = timestamp_config['font_scale']
            color = tuple(timestamp_config['color'])
            thickness = timestamp_config['thickness']
            
            cv2.putText(frame, current_time, position, 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)
            
            # Draw rectangles around detection areas and blur them
            for (x, y, w, h) in detections:
                # Apply blur to the detection region
                frame = self.apply_gaussian_blur(frame, x, y, w, h)
                
                # Draw rectangle around the blurred region
                cv2.rectangle(
                    frame, 
                    (x, y), 
                    (x + w, y + h), 
                    tuple(rect_config['color']), 
                    rect_config['thickness']
                )
            
            # Display the frame
            cv2.imshow("Video Stream Analytics", frame)
            
            # Break if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        # Close all OpenCV windows
        cv2.destroyAllWindows() 