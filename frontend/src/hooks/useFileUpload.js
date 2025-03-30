import { useState, useRef, useCallback } from 'react';

function useFileUpload(config, addMessage, onUploadSuccess) {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const uploadXHR = useRef(null);
  
  const uploadFile = useCallback((file) => {
    if (!file) {
      addMessage('Please select a video file first');
      return false;
    }
    
    // Check file size using config
    const maxSize = (config?.upload?.max_file_size_mb || 500) * 1024 * 1024;
    if (file.size > maxSize) {
      addMessage(`File too large. Maximum size is ${config?.upload?.max_file_size_mb || 500}MB. Your file is ${Math.round(file.size / (1024 * 1024))}MB`);
      return false;
    }
    
    // Check file type
    const fileType = file.type;
    if (!fileType.match('video.*')) {
      addMessage('Please select a valid video file');
      return false;
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
          onUploadSuccess();
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
    
    return true;
  }, [config, addMessage, onUploadSuccess]);
  
  const handleUpload = useCallback((event) => {
    event.preventDefault();
    const file = fileInputRef.current.files[0];
    return uploadFile(file);
  }, [uploadFile]);
  
  const cancelUpload = useCallback(() => {
    if (uploadXHR.current) {
      uploadXHR.current.abort();
    }
    addMessage('Upload canceled');
    setIsUploading(false);
  }, [addMessage]);
  
  return {
    uploadProgress,
    isUploading,
    fileInputRef,
    handleUpload,
    cancelUpload
  };
}

export default useFileUpload; 