const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Create a WebSocket proxy for Socket.IO
  const socketProxy = createProxyMiddleware('/socket.io', {
    target: 'http://localhost:5000',
    ws: true,
    changeOrigin: true,
    logLevel: 'debug',
  });

  // Create a proxy for API requests
  const apiProxy = createProxyMiddleware('/api', {
    target: 'http://localhost:5000',
    changeOrigin: true,
    logLevel: 'debug',
    // Increase timeout for large uploads
    proxyTimeout: 300000,
    timeout: 300000,
  });

  app.use(socketProxy);
  app.use(apiProxy);
}; 