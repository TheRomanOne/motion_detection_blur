import React from 'react';

function VideoDisplay({ currentFrame, isTransitioning, isUploading, isProcessing, isPaused }) {
  return (
    <div className={`video-container ${isPaused ? 'paused' : ''}`}>
      {currentFrame ? (
        <img src={currentFrame} alt="Live stream" className="stream-image" />
      ) : (
        <div className="placeholder">
          {isTransitioning ? (
            <div className="loading-animation">
              <div className="loading-spinner"></div>
              <p>Starting stream...</p>
            </div>
          ) : isUploading ? (
            <div className="loading-animation">
              <div className="loading-spinner"></div>
              <p>Uploading video...</p>
            </div>
          ) : isProcessing ? (
            <div className="loading-animation">
              <div className="loading-spinner"></div>
              <p>{isPaused ? 'Processing paused' : 'Processing and streaming video...'}</p>
            </div>
          ) : (
            <div className="stream-placeholder">
              <span className="placeholder-icon">📹</span>
              <p>Upload a video</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default VideoDisplay; 