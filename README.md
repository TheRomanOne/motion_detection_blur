# Motion Detection Web App

A motion detection application that processes a video in real-time to detect motion, annotate it with bounding boxes, and apply a blur effect to the detected areas.

![Motion Detection App Screenshot](https://github.com/TheRomanOne/motion_detection_blur/blob/master/screenshot.png?raw=true)

## Features

- **Motion Detection**: Detects motion in video frames and highlights it with bounding boxes
- **Blurred Annotations**: Applies a blur effect to the content within detected motion areas
- **Real-time Video Streaming**: Upload and stream videos with frame-by-frame processing
- **Interactive Controls**: Pause, resume, and stop streaming with immediate feedback
- **WebSocket Communication**: Bidirectional real-time communication between client and server
- **Configurable Parameters**: Motion detection, blur, and UI parameters can be tuned via a central configuration
- **Progress Tracking**: Real-time progress updates during processing

## Architecture

### Backend

- **Flask**: Web server framework
- **Flask-SocketIO**: WebSocket communication
- **OpenCV**: Video frame processing
- **Multiprocessing**: Parallel processing of video frames
- **Event-driven Communication**: WebSocket events for real-time control

### Frontend

- **React**: UI component library
- **Socket.io Client**: Real-time communication with server
- **Custom Hooks**: State management and business logic
- **CSS**: Styling and animations
- **Responsive UI**: Real-time status updates and controls

## Setup and Installation

### Backend Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the Flask server:
   ```
   cd backend
   python app.py
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. Access the application at http://localhost:3000

## Usage

1. Wait for the "Connected" status in the UI
2. Click "Choose File" to select a video
3. Click "Process & Stream Video" to upload and start processing
4. Use the Pause/Continue and Stop buttons to control the stream
5. View status messages in the console panel
6. The system will automatically show processing progress in real-time

## Configuration

The application's behavior can be customized by modifying the `backend/config.json` file, which includes settings for:

- Server parameters (port, upload limits)
- Motion detection sensitivity 
- Blur effect intensity
- UI appearance
- WebSocket communication
