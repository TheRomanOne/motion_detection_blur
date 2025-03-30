import React from 'react';

function ConnectionStatus({ status }) {
  return (
    <div className={`connection-badge ${status}`}>
      <div className="connection-dot"></div>
      <span>{status === 'connected' ? 'Connected' : 'Disconnected'}</span>
    </div>
  );
}

export default ConnectionStatus; 