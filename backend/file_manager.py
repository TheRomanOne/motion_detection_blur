import os
import uuid
import logging

logger = logging.getLogger(__name__)

def cleanup_video_file(file_path):
    """Delete a temporary video file if it exists"""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted temporary video file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting video file {file_path}: {str(e)}")
            return False
    return False

def generate_unique_filename(original_filename):
    """Generate a unique filename for uploaded video"""
    file_ext = os.path.splitext(original_filename)[1].lower()
    unique_filename = f"{str(uuid.uuid4())}{file_ext}"
    return unique_filename

def is_valid_video_format(filename, valid_formats=None):
    """Check if file has a valid video extension based on config"""
    if valid_formats is None:
        valid_formats = ['.mp4', '.avi', '.mov', '.mkv']
        
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in valid_formats 