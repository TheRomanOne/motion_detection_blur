import json
import argparse
from multiprocessing import Process, Queue
from streamer import Streamer
from detector import Detector
from display import Display

"""
This script sets up and runs a video processing pipeline using multiprocessing.
It loads configuration settings from a JSON file and initializes three separate
processes: Streamer, Detector, and Display. Each process is responsible for a
specific task in the pipeline: extracting frames from a video, detecting motion,
and displaying the processed video with annotations, respectively. The processes
communicate via queues to pass frames and detection data.
"""

def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Video Stream Analytics System')
    parser.add_argument('--video_path', required=True, help='Path to the video file to process')
    return parser.parse_args()

def run_pipeline(config, video_path):
    # Create communication queues
    frames_queue = Queue()
    detection_queue = Queue()
    
    # Create and start processes with respective configs
    streamer_process = Process(
        target=Streamer, 
        args=(frames_queue, video_path, config['streamer'])
    )
    
    detector_process = Process(
        target=Detector, 
        args=(frames_queue, detection_queue, config['detector'])
    )
    
    display_process = Process(
        target=Display, 
        args=(detection_queue, config['display'])
    )
    
    # Start all processes
    streamer_process.start()
    detector_process.start()
    display_process.start()
    
    # Wait for all processes to finish
    streamer_process.join()
    detector_process.join()
    display_process.join()
    
    print("Video processing completed. All processes terminated.")

if __name__ == "__main__":
    args = parse_arguments()
    config = load_config()
    run_pipeline(config, args.video_path) 