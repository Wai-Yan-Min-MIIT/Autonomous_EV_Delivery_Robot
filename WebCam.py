import socket
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import cv2
import threading
import base64
import time

# Function to get the Raspberry Pi's IP address
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external server (e.g., Google's DNS) to get the IP
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"  # Fallback to localhost if it fails
    finally:
        s.close()
    return ip_address

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app)

# Global variables for video frame and zthread safety
video_capture = cv2.VideoCapture(0)  # USB webcam
frame = None
lock = threading.Lock()

# Background task to capture video frames
def capture_frames():
    global frame
    while True:
        success, captured_frame = video_capture.read()
        if success:
            # Encode frame as JPEG and convert to base64
            _, buffer = cv2.imencode('.jpg', captured_frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')
            with lock:
                frame = frame_data
        time.sleep(0.03)  # ~30 FPS

# Start the frame capture thread
threading.Thread(target=capture_frames, daemon=True).start()

# Route to serve the webpage with the IP address
@app.route('/')
def index():
    ip_address = get_ip_address()  # Get the current IP address
    return render_template('webcam.html', ip_address=ip_address)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('request_frame')
def handle_request_frame():
    with lock:
        if frame is not None:
            emit('frame', frame)  # Send the latest frame to the client

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)