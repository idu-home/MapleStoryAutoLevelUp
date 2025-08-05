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
from .config import DEFAULT_HOST, DEFAULT_PORT, JPEG_QUALITY, JPEG_QUALITY_OPTIMIZED, MAX_IMAGE_WIDTH, MAX_IMAGE_WIDTH_MOBILE, CORS_ALLOWED_ORIGINS, TEMPLATE_FOLDER, DEBUG_MODE
from .utils import image_to_base64, image_to_base64_optimized, validate_image, PerformanceMonitor

# Import project logger
try:
    from src.utils.logger import logger
except ImportError:
    # Fallback to standard logging if project logger not available
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
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        self.use_optimized_encoding = True  # Use optimized encoding by default
        
        # Adaptive frame rate limiting
        self.last_frame_time = 0
        self.target_fps = 15  # Target FPS
        self.min_frame_interval = 1.0 / self.target_fps
        self.adaptive_quality = True  # Enable adaptive quality based on performance
        self.current_quality = JPEG_QUALITY_OPTIMIZED
        
        # Performance tracking for adaptive behavior
        self.recent_frame_times = []
        self.performance_check_interval = 10  # Check every 10 frames
        
        # Client device tracking
        self.connected_clients = {}  # Track client info for optimization
        
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
                'alert_active': self.alert_status,
                'performance': {
                    'avg_frame_time_ms': round(self.performance_monitor.get_avg_frame_time(), 2),
                    'avg_encode_time_ms': round(self.performance_monitor.get_avg_encode_time(), 2),
                    'estimated_fps': round(self.performance_monitor.get_fps(), 1),
                    'optimized_encoding': self.use_optimized_encoding
                }
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
        
        @self.app.route('/api/toggle_optimization', methods=['POST'])
        def toggle_optimization():
            """Toggle optimized encoding mode"""
            try:
                self.use_optimized_encoding = not self.use_optimized_encoding
                logger.info(f"Toggled optimized encoding: {self.use_optimized_encoding}")
                
                return jsonify({
                    'success': True,
                    'optimized_encoding': self.use_optimized_encoding
                })
                
            except Exception as e:
                logger.error(f"Error toggling optimization: {e}")
                return jsonify({'error': str(e)}), 500
            
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to debug server')
            emit('status', {'message': 'Connected to debug server'})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            from flask import request
            logger.info('Client disconnected from debug server')
            # Clean up client info
            if request.sid in self.connected_clients:
                del self.connected_clients[request.sid]
        
        @self.socketio.on('client_info')
        def handle_client_info(data):
            """Handle client device information for optimization"""
            from flask import request
            self.connected_clients[request.sid] = data
            logger.info(f'Client info received: {data}')
            
    def _image_to_base64(self, image):
        """Convert OpenCV image to base64 string with adaptive quality"""
        start_time = time.time()
        
        # Use adaptive quality if enabled
        quality = self.current_quality if self.adaptive_quality else JPEG_QUALITY_OPTIMIZED
        
        if self.use_optimized_encoding:
            # Check if any connected clients are mobile devices
            is_mobile = any(client.get('is_mobile', False) for client in self.connected_clients.values())
            max_width = MAX_IMAGE_WIDTH_MOBILE if is_mobile else MAX_IMAGE_WIDTH
            result = image_to_base64_optimized(image, quality, max_width, is_mobile)
        else:
            result = image_to_base64(image, JPEG_QUALITY)
        
        encode_time = time.time() - start_time
        self.performance_monitor.record_encode_time(encode_time)
        
        # Track performance for adaptive adjustments
        self.recent_frame_times.append(encode_time)
        if len(self.recent_frame_times) > self.performance_check_interval:
            self.recent_frame_times.pop(0)
        
        # Adaptive quality adjustment
        if self.adaptive_quality and len(self.recent_frame_times) >= self.performance_check_interval:
            avg_encode_time = sum(self.recent_frame_times) / len(self.recent_frame_times)
            if avg_encode_time > 0.05:  # If encoding takes more than 50ms
                self.current_quality = max(20, self.current_quality - 5)  # Reduce quality
                logger.debug(f"Reducing quality to {self.current_quality} due to slow encoding")
            elif avg_encode_time < 0.02 and self.current_quality < JPEG_QUALITY_OPTIMIZED:  # If very fast
                self.current_quality = min(JPEG_QUALITY_OPTIMIZED, self.current_quality + 5)  # Increase quality
                logger.debug(f"Increasing quality to {self.current_quality}")
        
        return result
        
    def update_debug_frame(self, debug_frame, route_frame=None, alert_status=False, sound_command=None):
        """Update debug images and alert status"""
        # Check if server is running
        if not self.is_running:
            logger.debug("[WebDebugServer] Server not running, skipping frame update")
            return
            
        frame_start_time = time.time()
        
        # Debug logging for frame updates
        if hasattr(self, '_last_debug_frame_valid') and self._last_debug_frame_valid != (debug_frame is not None):
            logger.info(f"[WebDebugServer] Frame validity changed: "
                       f"debug_frame={'valid' if debug_frame is not None else 'None'}, "
                       f"route_frame={'valid' if route_frame is not None else 'None'}")
            self._last_debug_frame_valid = debug_frame is not None
        
        # Adaptive rate limiting based on performance
        current_interval = self.min_frame_interval
        if self.adaptive_quality:
            avg_encode_time = self.performance_monitor.get_avg_encode_time() / 1000.0
            if avg_encode_time > 0.05:  # If encoding is slow
                current_interval = max(self.min_frame_interval * 2, avg_encode_time * 2)  # Reduce frame rate
            elif avg_encode_time < 0.02:  # If encoding is fast
                current_interval = self.min_frame_interval * 0.8  # Slightly increase frame rate
        
        if frame_start_time - self.last_frame_time < current_interval:
            return
        
        # Validate images
        debug_valid = validate_image(debug_frame)
        route_valid = validate_image(route_frame)
        
        if not debug_valid and not route_valid:
            if hasattr(self, '_last_validation_warn_time') and time.time() - self._last_validation_warn_time > 5:
                logger.warning(f"[WebDebugServer] No valid frames to send: "
                             f"debug_valid={debug_valid}, route_valid={route_valid}")
                self._last_validation_warn_time = time.time()
            return
            
        with self.frame_lock:
            self.latest_debug_frame = debug_frame.copy() if debug_valid else None
            self.latest_route_frame = route_frame.copy() if route_valid else None
        
        with self.alert_lock:
            self.alert_status = alert_status
            
        # Send updates via WebSocket only if there are connected clients
        try:
            # Send debug frame update
            if debug_valid:
                debug_b64 = self._image_to_base64(debug_frame)
                if debug_b64:
                    self.socketio.emit('debug_frame_update', {
                        'debug_frame': debug_b64,
                        'timestamp': frame_start_time,
                        'quality': self.current_quality,
                        'performance': {
                            'encode_time_ms': round(self.performance_monitor.get_avg_encode_time(), 2),
                            'frame_time_ms': round((time.time() - frame_start_time) * 1000, 2)
                        }
                    })
                    if hasattr(self, '_last_debug_frame_valid') and not self._last_debug_frame_valid:
                        logger.info(f"[WebDebugServer] Debug frame emission resumed")
                
            # Send route frame update
            if route_valid:
                route_b64 = self._image_to_base64(route_frame)
                if route_b64:
                    self.socketio.emit('route_frame_update', {
                        'route_frame': route_b64,
                        'timestamp': frame_start_time
                    })
            
            # Send alert status update
            self.socketio.emit('alert_status_update', {
                'alert_active': self.alert_status,
                'timestamp': frame_start_time
            })
            
            # Send sound command if provided
            if sound_command:
                self.socketio.emit('sound_command', {
                    'command': sound_command,
                    'timestamp': frame_start_time
                })
                
        except Exception as e:
            logger.warning(f"Failed to emit websocket updates: {e}")
        
        # Record performance metrics
        frame_time = time.time() - frame_start_time
        self.performance_monitor.record_frame_time(frame_time)
        self.last_frame_time = frame_start_time
            
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