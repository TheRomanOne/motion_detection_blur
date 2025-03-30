import { useState, useEffect, useCallback } from 'react';
import io from 'socket.io-client';

function useSocket(serverUrl, config) {
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [isStopping, setIsStopping] = useState(false);
  
  // Helper function to add a message to the message list
  const addMessage = useCallback((message) => {
    setMessages(prevMessages => {
      const newMessages = [...prevMessages, message];
      const maxMessages = config?.ui?.max_messages || 100;
      if (newMessages.length > maxMessages) {
        return newMessages.slice(newMessages.length - maxMessages);
      }
      return newMessages;
    });
  }, [config]);
  
  // Connect to websocket and setup event handlers
  useEffect(() => {
    if (!config) return; // Wait for config to be loaded
    
    const newSocket = io(serverUrl, {
      transports: config.websocket.transports,
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
      if (!isStopping) {
        setIsStreaming(true);
        setIsTransitioning(false);
        console.log("Received frame, streaming state:", true);
      }
    });

    newSocket.on('error', (data) => {
      addMessage(`Error: ${data.data}`);
      setIsTransitioning(false);
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

    newSocket.on('stream_paused', () => {
      setIsPaused(true);
    });
    
    newSocket.on('stream_resumed', () => {
      setIsPaused(false);
    });

    newSocket.on('stream_stopped', (data) => {
      // Clear the safety timeout if it exists
      if (window.lastStopTimeout) {
        clearTimeout(window.lastStopTimeout);
        window.lastStopTimeout = null;
      }
      
      // Reset all states to allow a new upload
      setIsStreaming(false);
      setIsProcessing(false);
      setIsPaused(false);
      setCurrentFrame(null);
      setProcessingProgress(0);
      setIsTransitioning(false);
      setIsStopping(false);
      
      if (data.reset) {
        addMessage('Ready for a new video upload');
      }
    });

    setSocket(newSocket);
    addMessage('Ready to process and stream videos');

    // Clean up on unmount
    return () => {
      if (newSocket) {
        newSocket.disconnect();
      }
    };
  }, [serverUrl, config, addMessage]);
  
  // Function to toggle pause state
  const togglePause = useCallback(() => {
    if (!socket || !isStreaming) return;
    
    if (isPaused) {
      socket.emit('resume_streaming');
      addMessage('Resuming stream');
    } else {
      socket.emit('pause_streaming');
      addMessage('Pausing stream');
    }
  }, [socket, isStreaming, isPaused, addMessage]);
  
  // Function to stop streaming
  const stopStreaming = useCallback(() => {
    if (!socket) return;
    
    setIsStopping(true);
    socket.emit('stop_streaming');
    addMessage('Stopping video processing and streaming...');
    setIsStreaming(false);
    setIsProcessing(false);
    setIsPaused(false);
    
    // Add a safety timeout to ensure UI resets even if socket completion event isn't received
    const safetyTimeout = setTimeout(() => {
      setIsStopping(false);
      setCurrentFrame(null);
      setProcessingProgress(0);
      setIsTransitioning(false);
      addMessage('Stream stopped (timeout)');
    }, 5000);  // 5 second timeout
    
    // Store the timeout ID so it can be cleared if normal completion occurs
    window.lastStopTimeout = safetyTimeout;
  }, [socket, addMessage]);
  
  // Function to stop processing
  const stopProcessing = useCallback(() => {
    if (!socket || !isProcessing) return;
    
    socket.emit('stop_processing');
    addMessage('Stopping video processing...');
  }, [socket, isProcessing, addMessage]);
  
  // Return everything the components will need
  return {
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
    stopProcessing,
    setIsStreaming,
    setIsProcessing,
    setIsTransitioning
  };
}

export default useSocket; 