'''
Web Debug Server
Flask-based web server for real-time debug image streaming
'''
import os
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
import logging
from .config import DEFAULT_HOST, DEFAULT_PORT, JPEG_QUALITY, CORS_ALLOWED_ORIGINS, TEMPLATE_FOLDER, DEBUG_MODE
from .utils import image_to_base64, validate_image

logger = logging.getLogger(__name__)

class WebDebugServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        # Set template folder path
        template_dir = os.path.join(os.path.dirname(__file__), TEMPLATE_FOLDER)
        self.app = Flask(__name__, template_folder=template_dir)
        self.socketio = SocketIO(self.app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)
        self.server_thread = None
        self.is_running = False
        
        # Store latest debug images
        self.latest_debug_frame = None
        self.latest_route_frame = None
        self.frame_lock = threading.Lock()
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('debug_viewer.html')
            
        @self.app.route('/api/status')
        def status():
            return jsonify({
                'status': 'running',
                'has_debug_frame': self.latest_debug_frame is not None,
                'has_route_frame': self.latest_route_frame is not None
            })
            
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to debug server')
            emit('status', {'message': 'Connected to debug server'})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from debug server')
            
    def _image_to_base64(self, image):
        """Convert OpenCV image to base64 string"""
        return image_to_base64(image, JPEG_QUALITY)
        
    def update_debug_frame(self, debug_frame, route_frame=None):
        """Update debug images"""
        # Validate images
        if not validate_image(debug_frame) and not validate_image(route_frame):
            return
            
        with self.frame_lock:
            self.latest_debug_frame = debug_frame.copy() if validate_image(debug_frame) else None
            self.latest_route_frame = route_frame.copy() if validate_image(route_frame) else None
            
        # Send updates via WebSocket
        if validate_image(debug_frame):
            debug_b64 = self._image_to_base64(debug_frame)
            if debug_b64:
                self.socketio.emit('debug_frame_update', {
                    'debug_frame': debug_b64,
                    'timestamp': time.time()
                })
            
        if validate_image(route_frame):
            route_b64 = self._image_to_base64(route_frame)
            if route_b64:
                self.socketio.emit('route_frame_update', {
                    'route_frame': route_b64,
                    'timestamp': time.time()
                })
            
    def start(self):
        """Start Web server"""
        if self.is_running:
            logger.warning("Web server is already running")
            return
            
        def run_server():
            try:
                logger.info(f"Starting web debug server on http://{self.host}:{self.port}")
                self.socketio.run(self.app, host=self.host, port=self.port, debug=DEBUG_MODE)
            except Exception as e:
                logger.error(f"Failed to start web server: {e}")
                
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
        
    def stop(self):
        """Stop Web server"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("Stopping web debug server")
        
        # Close socketio
        try:
            self.socketio.stop()
        except:
            pass
            
        # Wait for thread to end
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
            
    def get_url(self):
        """Get server URL"""
        return f"http://{self.host}:{self.port}" 