import React from 'react';

function UploadForm({ 
  fileInputRef,
  uploadVideo,
  isUploading,
  uploadProgress,
  cancelUpload,
  isProcessing,
  processingProgress,
  isStreaming,
  isPaused,
  togglePause,
  connectionStatus,
  handleStopStreaming
}) {
  return (
    <div className="upload-section">
      <h3>Upload Video</h3>
      <form onSubmit={uploadVideo} className="upload-form">
        <input 
          type="file"
          ref={fileInputRef}
          accept="video/*"
          className="file-input"
          disabled={isUploading || isProcessing || isStreaming}
        />
        
        {isUploading && (
          <div className="progress-container">
            <div 
              className="progress-bar" 
              style={{width: `${uploadProgress}%`}}
            ></div>
            <span className="progress-text">{uploadProgress}%</span>
            <button 
              type="button" 
              className="cancel-button" 
              onClick={cancelUpload}
            >
              Cancel
            </button>
          </div>
        )}
        
        {isProcessing && (
          <div className="progress-container">
            <div 
              className="progress-bar processing" 
              style={{width: `${processingProgress}%`}}
            ></div>
            <span className="progress-text">Processing: {processingProgress}%</span>
          </div>
        )}
        
        {isStreaming && (
          <div className="streaming-controls">
            <button 
              type="button" 
              className="pause-button" 
              onClick={togglePause}
            >
              {isPaused ? 'Continue' : 'Pause'}
            </button>
            
            <button 
              type="button" 
              className="stop-button" 
              onClick={handleStopStreaming}
            >
              Stop
            </button>
          </div>
        )}
        
        {!isUploading && !isProcessing && !isStreaming && (
          <button 
            type="submit" 
            className="upload-button"
            disabled={connectionStatus !== 'connected'}
          >
            Process & Stream Video
          </button>
        )}
      </form>
    </div>
  );
}

export default UploadForm; 