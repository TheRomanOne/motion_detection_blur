import React, { useState, useEffect } from 'react';
import './App.css';
import VideoDisplay from './components/VideoDisplay';
import MessageConsole from './components/MessageConsole';
import UploadForm from './components/UploadForm';
import ConnectionStatus from './components/ConnectionStatus';
import useSocket from './hooks/useSocket';
import useFileUpload from './hooks/useFileUpload';

function App() {
  // Local state
  const [config, setConfig] = useState(null);
  
  // Socket-related state and functions from custom hook
  const {
    socket,
    connectionStatus,
    messages,
    addMessage,
    currentFrame,
    isStreaming,
    isProcessing,
    isPaused,
    isTransitioning,
    processingProgress,
    togglePause,
    stopStreaming,
    setIsStreaming,
    setIsProcessing
  } = useSocket('http://localhost:5000', config);
  
  // Handle successful upload
  const handleUploadSuccess = () => {
    setIsProcessing(true);
    setIsStreaming(true);
  };
  
  // File upload logic with custom hook
  const {
    uploadProgress,
    isUploading,
    fileInputRef,
    handleUpload,
    cancelUpload
  } = useFileUpload(config, addMessage, handleUploadSuccess);
  
  useEffect(() => {
    // Fetch configuration from server
    fetch('/api/config')
      .then(response => response.json())
      .then(configData => {
        // Store config for later use
        setConfig(configData);
      })
      .catch(error => {
        console.error("Failed to load configuration:", error);
      });
  }, []);

  // If already streaming, stop it before uploading a new video
  const uploadVideo = (event) => {
    if (isStreaming && socket) {
      socket.emit('stop_streaming');
    }
    handleUpload(event);
  };

  console.log("Rendering App component with states:", { 
    isStreaming, isProcessing, isPaused, currentFrame 
  });

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="logo">
          <h1>Motion Detection</h1>
        </div>
        
        <ConnectionStatus status={connectionStatus} />
        
        <UploadForm 
          fileInputRef={fileInputRef}
          uploadVideo={uploadVideo}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
          cancelUpload={cancelUpload}
          isProcessing={isProcessing}
          processingProgress={processingProgress}
          isStreaming={isStreaming}
          isPaused={isPaused}
          togglePause={togglePause}
          connectionStatus={connectionStatus}
          handleStopStreaming={stopStreaming}
        />
        
        <MessageConsole 
          messages={messages}
          isStreaming={isStreaming}
          isProcessing={isProcessing}
          isPaused={isPaused}
        />
      </div>
      <main className="content">
        <VideoDisplay 
          currentFrame={currentFrame}
          isTransitioning={isTransitioning}
          isUploading={isUploading}
          isProcessing={isProcessing}
          isPaused={isPaused}
        />
      </main>
    </div>
  );
}

export default App; 