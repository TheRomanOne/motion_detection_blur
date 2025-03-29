import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

function App() {
  const [socket, setSocket] = useState(null);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const fileInputRef = useRef(null);
  const uploadXHR = useRef(null);
  const [config, setConfig] = useState(null);
  
  useEffect(() => {
    // First fetch configuration from server
    fetch('/api/config')
      .then(response => response.json())
      .then(config => {
        // Store config for later use
        setConfig(config);
        
        // Connect to the WebSocket server with config values
        const newSocket = io('http://localhost:5000', {
          transports: config.websocket.transports || ['websocket', 'polling'],
          reconnection: config.websocket.reconnection,
          reconnectionAttempts: config.websocket.reconnection_attempts,
          reconnectionDelay: config.websocket.reconnection_delay,
        });
        
        console.log("Attempting to connect to WebSocket server...");

        newSocket.on('connect', () => {
          console.log("Successfully connected to WebSocket server!");
          setConnectionStatus('connected');
          addMessage('Connected to server');
        });

        newSocket.on('disconnect', () => {
          setConnectionStatus('disconnected');
          addMessage('Disconnected from server');
          setIsStreaming(false);
          setIsProcessing(false);
          setIsTransitioning(false);
        });

        newSocket.on('connect_error', (error) => {
          console.error("Socket.IO connection error:", error);
          setConnectionStatus('error');
          addMessage(`Connection error: ${error.message}`);
        });

        newSocket.on('message', (data) => {
          addMessage(data.data);
          
          if (data.data === 'Stopping video processing and streaming...') {
            setIsTransitioning(false);
            setIsStreaming(false);
            setIsProcessing(false);
            setIsPaused(false);
          }
          if (data.data.includes('Video processing complete')) {
            setIsProcessing(false);
            setProcessingProgress(100);
          }
        });

        newSocket.on('frame', (data) => {
          setCurrentFrame(`data:image/jpeg;base64,${data.frame}`);
          setIsStreaming(true);
          setIsTransitioning(false);
          console.log("Received frame, streaming state:", true);
        });

        newSocket.on('error', (data) => {
          addMessage(`Error: ${data.data}`);
          setIsTransitioning(false);
          setIsUploading(false);
        });

        newSocket.on('complete', (data) => {
          addMessage('Stream ended: ' + data.data);
          setIsStreaming(false);
          setIsTransitioning(false);
        });
        
        newSocket.on('processing_progress', (data) => {
          if (data.progress) {
            setProcessingProgress(data.progress);
          } else {
            // Fallback for older server versions without progress percentage
            setProcessingProgress(prev => Math.min(prev + 5, 95));
          }
          
          if (data.frames % 200 === 0) {
            addMessage(`Processed ${data.frames} frames so far...`);
          }
        });
        
        newSocket.on('processing_complete', (data) => {
          setProcessingProgress(100);
          setIsProcessing(false);
          addMessage(`Processing complete: ${data.frames} total frames`);
        });

        // Add new event listeners for pause/resume
        newSocket.on('stream_paused', () => {
          setIsPaused(true);
        });
        
        newSocket.on('stream_resumed', () => {
          setIsPaused(false);
        });

        // Add new event handler in useEffect socket setup
        newSocket.on('stream_stopped', (data) => {
          // Reset all states to allow a new upload
          setIsStreaming(false);
          setIsProcessing(false);
          setIsPaused(false);
          setCurrentFrame(null);
          setProcessingProgress(0);
          setIsTransitioning(false);
          
          if (data.reset) {
            addMessage('Ready for a new video upload');
          }
        });

        setSocket(newSocket);

        // No need to check for frames since we're not saving them anymore
        addMessage('Ready to process and stream videos');
      })
      .catch(error => {
        console.error("Failed to load configuration:", error);
        // Fall back to defaults
        // ...
      });

    // Clean up on unmount
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, []);

  const addMessage = (message) => {
    setMessages(prevMessages => {
      const newMessages = [...prevMessages, message];
      const maxMessages = config?.ui?.max_messages || 100;
      if (newMessages.length > maxMessages) {
        return newMessages.slice(newMessages.length - maxMessages);
      }
      return newMessages;
    });
  };

  const uploadVideo = (event) => {
    event.preventDefault();
    
    const file = fileInputRef.current.files[0];
    if (!file) {
      addMessage('Please select a video file first');
      return;
    }
    
    // Check file size using config
    const maxSize = (config?.upload?.max_file_size_mb || 500) * 1024 * 1024;
    if (file.size > maxSize) {
      addMessage(`File too large. Maximum size is ${config?.upload?.max_file_size_mb || 500}MB. Your file is ${Math.round(file.size / (1024 * 1024))}MB`);
      return;
    }
    
    // Check file type
    const fileType = file.type;
    if (!fileType.match('video.*')) {
      addMessage('Please select a valid video file');
      return;
    }
    
    // If already streaming, stop it
    if (isStreaming) {
      socket.emit('stop_streaming');
    }
    
    // Create FormData
    const formData = new FormData();
    formData.append('video', file);
    
    setIsUploading(true);
    setUploadProgress(0);
    addMessage(`Uploading video: ${file.name} (${Math.round(file.size / (1024 * 1024))} MB)`);
    
    // Upload the file with progress tracking
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const progressPercent = Math.round((event.loaded / event.total) * 100);
        setUploadProgress(progressPercent);
        
        const notificationInterval = config?.upload?.progress_notification_interval || 25;
        if (progressPercent % notificationInterval === 0) {
          addMessage(`Upload progress: ${progressPercent}%`);
        }
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          setIsUploading(false);
          addMessage('Upload complete! Processing and streaming video...');
          setIsProcessing(true);
          setIsStreaming(true);
          setProcessingProgress(0);
        } catch (error) {
          setIsUploading(false);
          addMessage(`Upload error: Could not parse server response`);
          console.error("Server response parsing error:", error);
        }
      } else {
        setIsUploading(false);
        addMessage(`Upload failed: Server returned ${xhr.status} ${xhr.statusText}`);
        console.error("Server response:", xhr.responseText);
      }
    });
    
    xhr.addEventListener('error', () => {
      setIsUploading(false);
      addMessage('Upload failed due to network error. Please try again.');
      console.error("XHR error during upload");
    });
    
    xhr.addEventListener('timeout', () => {
      setIsUploading(false);
      addMessage('Upload timed out. Please try a smaller file or check your connection.');
    });
    
    // Set timeout from config
    xhr.timeout = config?.upload?.timeout_ms || 300000;
    
    xhr.open('POST', '/api/upload_video', true);
    xhr.send(formData);
    
    // Store the XHR reference so we can abort it if needed
    uploadXHR.current = xhr;
  };
  
  const cancelUpload = () => {
    // Implementation for canceling upload
    addMessage('Upload canceled');
    setIsUploading(false);
    // You would need to abort the XHR request here
  };
  
  const stopProcessing = () => {
    if (socket && isProcessing) {
      socket.emit('stop_processing');
      addMessage('Stopping video processing...');
    }
  };

  // Get button text based on state
  const getButtonText = () => {
    if (isTransitioning) {
      return isStreaming ? 'Stopping Stream...' : 'Starting Stream...';
    }
    return isStreaming ? 'Stop Stream' : 'Start Stream';
  };

  // Add new function to toggle pause state
  const togglePause = () => {
    if (!socket || !isStreaming) return;
    
    if (isPaused) {
      socket.emit('resume_streaming');
      addMessage('Resuming stream...');
    } else {
      socket.emit('pause_streaming');
      addMessage('Pausing stream...');
    }
  };

  // Add this function to help with debugging
  const resetAllStates = () => {
    console.log("Resetting all states to allow new upload");
    setIsStreaming(false);
    setIsProcessing(false);
    setIsPaused(false);
    setCurrentFrame(null);
    setProcessingProgress(0);
    setIsTransitioning(false);
  };

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="logo">
          <h1>Vision Stream</h1>
        </div>
        <div className={`connection-badge ${connectionStatus}`}>
          <div className="connection-dot"></div>
          <span>{connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}</span>
        </div>
        
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
                  onClick={() => {
                    socket.emit('stop_streaming');
                    addMessage('Stopping video processing and streaming...');
                    // Reset frontend state immediately for better responsiveness
                    setIsStreaming(false);
                    setIsProcessing(false);
                    setIsPaused(false);
                  }}
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
        
        <div className="message-console">
          <h3>Console</h3>
          <div className="debug-info">
            <small>Stream: {isStreaming ? 'Active' : 'Inactive'} | Processing: {isProcessing ? 'Yes' : 'No'} | Paused: {isPaused ? 'Yes' : 'No'}</small>
          </div>
          <div className="message-list">
            {messages.length === 0 ? (
              <div className="message">System ready. No messages yet.</div>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className="message">{msg}</div>
              ))
            )}
          </div>
        </div>
      </div>
      <main className="content">
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
                  <p>Upload a video to start processing and streaming</p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App; 