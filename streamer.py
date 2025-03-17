import cv2
import time

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
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video at {self.video_path}")
            # Signal other processes to terminate by sending None
            self.output_queue.put(None)
            return
            
        # Process frame by frame
        while True:
            ret, frame = cap.read()
            
            # If frame is read correctly, ret is True
            if not ret:
                print("End of video stream")
                # Signal other processes to terminate by sending None
                self.output_queue.put(None)
                break
                
            # Send the frame to the detector
            self.output_queue.put(frame)
            
            # Small delay to prevent overwhelming the queue
            time.sleep(self.config['sleep_delay'])
            
        # Release the video capture object
        cap.release() 