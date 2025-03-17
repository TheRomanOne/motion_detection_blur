import cv2
import numpy as np

"""
The Detector class processes video frames to detect motion. It uses a background
subtractor to identify moving objects and extracts contours to determine regions
of interest. The class includes functionality to merge overlapping bounding boxes
to avoid duplicate detections. Detected regions are sent to the Display process
along with the original frame. Configuration parameters for motion detection are
loaded from a JSON file.
"""

class Detector:
    def __init__(self, input_queue, output_queue, config):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        
        # Create background subtractor with config parameters
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
        self.detect_motion()
        
    def _do_boxes_overlap(self, box1, box2):
        """Check if two bounding boxes overlap."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Calculate the coordinates of box corners
        box1_left, box1_right = x1, x1 + w1
        box1_top, box1_bottom = y1, y1 + h1
        box2_left, box2_right = x2, x2 + w2
        box2_top, box2_bottom = y2, y2 + h2
        
        # Check for overlap
        if (box1_right < box2_left or  # box1 is to the left of box2
            box1_left > box2_right or  # box1 is to the right of box2
            box1_bottom < box2_top or  # box1 is above box2
            box1_top > box2_bottom):   # box1 is below box2
            return False
        return True
    
    def _merge_boxes(self, box1, box2):
        """Merge two overlapping bounding boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        # Find the coordinates of the merged box
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1 + w1, x2 + w2)
        bottom = max(y1 + h1, y2 + h2)
        
        # Calculate width and height of the merged box
        width = right - left
        height = bottom - top
        
        return (left, top, width, height)
    
    def _merge_overlapping_boxes(self, boxes):
        """Merge all overlapping boxes in the list."""
        if not boxes:
            return []
        
        # Keep merging until no more overlaps are found
        merged = True
        while merged:
            merged = False
            result = []
            while boxes:
                current_box = boxes.pop(0)
                
                # Check if current box overlaps with any of the remaining boxes
                i = 0
                while i < len(boxes):
                    if self._do_boxes_overlap(current_box, boxes[i]):
                        # Merge the boxes and remove the second one
                        current_box = self._merge_boxes(current_box, boxes[i])
                        boxes.pop(i)
                        merged = True
                    else:
                        i += 1
                        
                result.append(current_box)
            
            boxes = result
        
        return boxes
        
    def detect_motion(self):
        # Parameters for filtering and sensitivity from config
        min_contour_area = self.config['min_contour_area']
        frames_to_stabilize = self.config['frames_to_stabilize']
        kernel_size = self.config['morph_kernel_size']
        
        frame_count = 0
        
        while True:
            # Get frame from the queue
            frame = self.input_queue.get()
            
            # Check if the streamer has finished
            if frame is None:
                print("Detector: Received termination signal")
                # Pass the termination signal to the display
                self.output_queue.put(None)
                break
            
            # Skip initial frames to allow camera stabilization and background model learning
            frame_count += 1
            if frame_count < frames_to_stabilize:
                self.output_queue.put((frame, []))  # No detections for initial frames
                continue
                
            # Apply background subtraction
            fg_mask = self.bg_subtractor.apply(frame)
            
            # Noise removal with morphological operations
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)  # Remove noise
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel) # Fill holes
            
            # Find contours on mask
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Extract regions with significant motion
            detections = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < min_contour_area:  # Ignore small contours
                    continue
                    
                # Get bounding box coordinates
                (x, y, w, h) = cv2.boundingRect(contour)
                
                # Filtering: ignore detections that are too large (likely false positives)
                if w*h > 0.5 * frame.shape[0] * frame.shape[1]:
                    continue
                    
                detections.append((x, y, w, h))
            
            # Merge overlapping detection boxes
            if detections:
                detections = self._merge_overlapping_boxes(detections)
            
            # Send the original frame and detection regions to Display
            self.output_queue.put((frame, detections)) 