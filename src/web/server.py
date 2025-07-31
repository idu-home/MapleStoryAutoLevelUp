'''
Web Debug Server
Flask-based web server for real-time debug image streaming
'''
import os
import cv2
import numpy as np
from flask import Flask, render_template, jsonify, request, send_from_directory
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
        
        # Add static file serving for media files
        media_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'media')
        if os.path.exists(media_dir):
            # Create a route to serve media files
            @self.app.route('/media/<path:filename>')
            def serve_media(filename):
                return send_from_directory(media_dir, filename)
            logger.info(f"Media files served from: {media_dir}")
        else:
            logger.warning(f"Media directory not found: {media_dir}")
        self.socketio = SocketIO(self.app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)
        self.server_thread = None
        self.is_running = False
        
        # Store latest debug images
        self.latest_debug_frame = None
        self.latest_route_frame = None
        self.frame_lock = threading.Lock()
        
        # Store alert status
        self.alert_status = False
        self.alert_lock = threading.Lock()
        
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
                'has_route_frame': self.latest_route_frame is not None,
                'alert_active': self.alert_status
            })
            
        @self.app.route('/api/trigger_alert', methods=['POST'])
        def trigger_alert():
            """Trigger alert event via API"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                alert_type = data.get('type')
                if not alert_type:
                    return jsonify({'error': 'No alert type specified'}), 400
                
                # Map alert types to sound commands
                sound_commands = {
                    'rune_detected': 'start_rune_alert',
                    'rune_solved': 'play_rune_solved_alert',
                    'rune_stop': 'stop_rune_alert',
                    'bot_stopped': 'play_bot_stopped_alert'
                }
                
                if alert_type not in sound_commands:
                    return jsonify({'error': f'Unknown alert type: {alert_type}'}), 400
                
                sound_command = sound_commands[alert_type]
                
                # Update alert status based on type
                with self.alert_lock:
                    if alert_type == 'rune_detected':
                        self.alert_status = True
                    elif alert_type == 'rune_solved' or alert_type == 'rune_stop':
                        self.alert_status = False
                
                # Send sound command via WebSocket
                self.socketio.emit('sound_command', {
                    'command': sound_command,
                    'timestamp': time.time()
                })
                
                # Send alert status update
                self.socketio.emit('alert_status_update', {
                    'alert_active': self.alert_status,
                    'timestamp': time.time()
                })
                
                logger.info(f"Triggered alert: {alert_type} -> {sound_command}")
                
                return jsonify({
                    'success': True,
                    'alert_type': alert_type,
                    'sound_command': sound_command,
                    'alert_active': self.alert_status
                })
                
            except Exception as e:
                logger.error(f"Error triggering alert: {e}")
                return jsonify({'error': str(e)}), 500
            
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
        
    def update_debug_frame(self, debug_frame, route_frame=None, alert_status=False, sound_command=None):
        """Update debug images and alert status"""
        # Validate images
        if not validate_image(debug_frame) and not validate_image(route_frame):
            return
            
        with self.frame_lock:
            self.latest_debug_frame = debug_frame.copy() if validate_image(debug_frame) else None
            self.latest_route_frame = route_frame.copy() if validate_image(route_frame) else None
        
        with self.alert_lock:
            self.alert_status = alert_status
            
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
        
        # Send alert status update
        self.socketio.emit('alert_status_update', {
            'alert_active': self.alert_status,
            'timestamp': time.time()
        })
        
        # Send sound command if provided
        if sound_command:
            self.socketio.emit('sound_command', {
                'command': sound_command,
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