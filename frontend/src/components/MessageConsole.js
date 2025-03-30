import React from 'react';

function MessageConsole({ messages, isStreaming, isProcessing, isPaused }) {
  // First, add a console log to verify props are being received
  console.log("MessageConsole props:", { messages, isStreaming, isProcessing, isPaused });
  
  return (
    <div className="message-console">
      <h3>Console</h3>
      <div className="debug-info">
        <small>
          Stream: {isStreaming ? 'Active' : 'Inactive'} | 
          Processing: {isProcessing ? 'Yes' : 'No'} | 
          Paused: {isPaused ? 'Yes' : 'No'}
        </small>
      </div>
      <div className="message-list">
        {Array.isArray(messages) && messages.length > 0 ? (
          messages.map((msg, index) => (
            <div key={index} className="message">{msg}</div>
          ))
        ) : (
          <div className="message">System ready. No messages yet.</div>
        )}
      </div>
    </div>
  );
}

export default MessageConsole; 