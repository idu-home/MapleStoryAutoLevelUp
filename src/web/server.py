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
        self.bot = None  # Will be set when server starts
        # Set template folder path
        template_dir = os.path.join(os.path.dirname(__file__), TEMPLATE_FOLDER)
        # Set static folder to the same as template folder for CSS/JS files
        self.app = Flask(__name__, template_folder=template_dir, static_folder=template_dir, static_url_path='/static')
        
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
        
        # Add explicit static file serving for templates directory
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory(template_dir, filename)
        logger.info(f"Static files served from: {template_dir}")
        self.socketio = SocketIO(self.app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)
        self.server_thread = None
        self.is_running = False
        
        # Store latest debug images
        self.latest_debug_frame = None
        self.latest_route_frame = None
        self.frame_lock = threading.Lock()
        
        
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
            return render_template('index.html')
            
        @self.app.route('/api/status')
        def status():
            bot_status = 'unknown'
            bot_state = 'unknown'
            
            if self.bot:
                if hasattr(self.bot, 'is_terminated') and self.bot.is_terminated:
                    bot_status = 'stopped'
                elif hasattr(self.bot, 'thread_auto_bot') and self.bot.thread_auto_bot and self.bot.thread_auto_bot.is_alive():
                    bot_status = 'running'
                else:
                    bot_status = 'paused'
                    
                # Get current FSM state if available
                if hasattr(self.bot, 'fsm') and self.bot.fsm and hasattr(self.bot.fsm, 'state') and self.bot.fsm.state:
                    bot_state = self.bot.fsm.state.name
            
            # Get HP/MP/EXP data if available
            hp_percent = None
            mp_percent = None
            exp_percent = None
            
            if self.bot and hasattr(self.bot, 'health_monitor') and self.bot.health_monitor:
                hp_percent = getattr(self.bot.health_monitor, 'hp_percent', None)
                mp_percent = getattr(self.bot.health_monitor, 'mp_percent', None) 
                exp_percent = getattr(self.bot.health_monitor, 'exp_percent', None)
                    
            # Build performance data safely
            performance_data = {
                'optimized_encoding': self.use_optimized_encoding
            }
            
            try:
                if hasattr(self, 'performance_monitor') and self.performance_monitor:
                    performance_data.update({
                        'avg_frame_time_ms': round(self.performance_monitor.get_avg_frame_time(), 2),
                        'avg_encode_time_ms': round(self.performance_monitor.get_avg_encode_time(), 2),
                        'estimated_fps': round(self.performance_monitor.get_fps(), 1),
                    })
            except Exception as e:
                logger.warning(f"Error getting performance data: {e}")
            
            return jsonify({
                'status': 'running',
                'bot_status': bot_status,
                'bot_state': bot_state,
                'has_debug_frame': self.latest_debug_frame is not None,
                'has_route_frame': self.latest_route_frame is not None,
                'performance': performance_data,
                'health_stats': {
                    'hp_percent': hp_percent,
                    'mp_percent': mp_percent,
                    'exp_percent': exp_percent
                }
            })
            
        
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

        @self.app.route('/api/bot/stop', methods=['POST'])
        def stop_bot():
            """Stop the bot"""
            try:
                if not self.bot:
                    return jsonify({'error': 'Bot instance not available'}), 400
                
                # Stop the bot
                self.bot.pause()
                logger.info("Bot stopped via web interface")
                
                return jsonify({
                    'success': True,
                    'message': 'Bot stopped successfully'
                })
                
            except Exception as e:
                logger.error(f"Error stopping bot: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/history')
        def exp_history():
            """Get EXP gain history data for charts"""
            try:
                from src.utils.exp_tracker import exp_tracker
                
                # Get hours parameter, default to 1 hour
                hours_back = request.args.get('hours', default=1, type=int)
                hours_back = max(1, min(24, hours_back))  # Limit between 1-24 hours
                
                # Get minute-by-minute data
                data = exp_tracker.get_exp_per_minute_data(hours_back)
                
                # Get statistics
                stats = exp_tracker.get_statistics(hours_back)
                
                return jsonify({
                    'success': True,
                    'data': data,
                    'statistics': stats,
                    'hours_back': hours_back
                })
                
            except Exception as e:
                logger.error(f"Error getting EXP history: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/stats')
        def exp_stats():
            """Get EXP statistics for different time periods"""
            try:
                from src.utils.exp_tracker import exp_tracker
                
                # Get stats for different periods
                stats_1h = exp_tracker.get_statistics(1)
                stats_3h = exp_tracker.get_statistics(3) 
                stats_6h = exp_tracker.get_statistics(6)
                stats_24h = exp_tracker.get_statistics(24)
                
                current_exp = exp_tracker.get_current_exp()
                
                return jsonify({
                    'success': True,
                    'current_exp_percent': current_exp,
                    'periods': {
                        '1h': stats_1h,
                        '3h': stats_3h,
                        '6h': stats_6h,
                        '24h': stats_24h
                    }
                })
                
            except Exception as e:
                logger.error(f"Error getting EXP statistics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/reset', methods=['POST'])
        def reset_exp_data():
            """Reset EXP tracking data"""
            try:
                from src.utils.exp_tracker import exp_tracker
                
                exp_tracker.clear_data()
                logger.info("EXP tracking data reset via web interface")
                
                return jsonify({
                    'success': True,
                    'message': 'EXP tracking data reset successfully'
                })
                
            except Exception as e:
                logger.error(f"Error resetting EXP data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/snapshots')
        def exp_snapshots():
            """Get raw snapshot data for debugging"""
            try:
                from src.utils.exp_tracker import exp_tracker
                
                hours_back = request.args.get('hours', default=1, type=int)
                hours_back = max(1, min(24, hours_back))
                
                snapshots = exp_tracker.get_snapshots_raw(hours_back)
                
                return jsonify({
                    'success': True,
                    'snapshots': snapshots,
                    'count': len(snapshots),
                    'hours_back': hours_back
                })
                
            except Exception as e:
                logger.error(f"Error getting EXP snapshots: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/debug')
        def exp_debug():
            """Debug EXP tracking system"""
            try:
                from src.utils.exp_tracker import exp_tracker
                
                with exp_tracker.data_lock:
                    debug_info = {
                        'current_exp_percent': exp_tracker.current_exp_percent,
                        'last_snapshot_time': exp_tracker.last_snapshot_time,
                        'last_update_time': exp_tracker.last_update_time,
                        'snapshot_count': len(exp_tracker.snapshots),
                        'recent_snapshots': [
                            snapshot.to_dict() 
                            for snapshot in list(exp_tracker.snapshots)[-5:]  # 最近5个
                        ]
                    }
                
                return jsonify({
                    'success': True,
                    'debug_info': debug_info,
                    'timestamp': time.time()
                })
                
            except Exception as e:
                logger.error(f"Error getting EXP debug info: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/exp/generate_test_data', methods=['POST'])
        def generate_test_data():
            """Generate test EXP data for debugging"""
            try:
                from src.utils.exp_tracker import exp_tracker
                import random
                
                # Generate test snapshots
                current_time = time.time()
                base_exp = 10.0
                
                for i in range(10):  # Generate 10 test snapshots
                    timestamp = current_time - (10 - i) * 60  # 每分钟一个快照
                    exp_percent = base_exp + (i * random.uniform(0.5, 2.0))  # 模拟增长
                    
                    # Manually create snapshot (for testing)
                    from src.utils.exp_tracker import ExpSnapshot
                    snapshot = ExpSnapshot(timestamp, exp_percent)
                    exp_tracker.snapshots.append(snapshot)
                
                exp_tracker.current_exp_percent = exp_percent
                exp_tracker.last_snapshot_time = current_time
                
                logger.info(f"Generated {len(exp_tracker.snapshots)} test EXP snapshots")
                
                return jsonify({
                    'success': True,
                    'message': f'Generated {len(exp_tracker.snapshots)} test snapshots',
                    'snapshots_count': len(exp_tracker.snapshots)
                })
                
            except Exception as e:
                logger.error(f"Error generating test data: {e}")
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
        
    def _setup_status_broadcast(self):
        """Set up periodic bot status broadcasting via WebSocket"""
        import threading
        
        def broadcast_status():
            while self.is_running:
                try:
                    if self.bot:
                        # Get bot status
                        bot_status = 'unknown'
                        bot_state = 'unknown'
                        
                        if hasattr(self.bot, 'is_terminated') and self.bot.is_terminated:
                            bot_status = 'stopped'
                        elif hasattr(self.bot, 'thread_auto_bot') and self.bot.thread_auto_bot and self.bot.thread_auto_bot.is_alive():
                            bot_status = 'running'
                        else:
                            bot_status = 'paused'
                            
                        # Get current FSM state if available
                        if hasattr(self.bot, 'fsm') and self.bot.fsm and hasattr(self.bot.fsm, 'state') and self.bot.fsm.state:
                            bot_state = self.bot.fsm.state.name
                        
                        # Get HP/MP/EXP data
                        hp_percent = None
                        mp_percent = None
                        exp_percent = None
                        
                        if hasattr(self.bot, 'health_monitor') and self.bot.health_monitor:
                            hp_percent = getattr(self.bot.health_monitor, 'hp_percent', None)
                            mp_percent = getattr(self.bot.health_monitor, 'mp_percent', None)
                            exp_percent = getattr(self.bot.health_monitor, 'exp_percent', None)
                        
                        # Get EXP tracking info
                        exp_debug_info = None
                        try:
                            from src.utils.exp_tracker import exp_tracker
                            with exp_tracker.data_lock:
                                exp_debug_info = {
                                    'snapshot_count': len(exp_tracker.snapshots),
                                    'last_snapshot_time': exp_tracker.last_snapshot_time,
                                    'current_exp': exp_tracker.current_exp_percent
                                }
                        except Exception as e:
                            logger.debug(f"Error getting EXP debug info for broadcast: {e}")
                        
                        # Broadcast status update via WebSocket
                        self.socketio.emit('bot_status_update', {
                            'bot_status': bot_status,
                            'bot_state': bot_state,
                            'timestamp': time.time(),
                            'health_stats': {
                                'hp_percent': hp_percent,
                                'mp_percent': mp_percent,
                                'exp_percent': exp_percent
                            },
                            'exp_debug_info': exp_debug_info
                        })
                    
                    time.sleep(1)  # Check every 1 second
                except Exception as e:
                    logger.warning(f"Error in status broadcast: {e}")
                    time.sleep(5)  # Wait longer on error
        
        # Start status broadcast thread
        self.status_thread = threading.Thread(target=broadcast_status, daemon=True)
        self.status_thread.start()
        
    def update_debug_frame(self, debug_frame, route_frame=None):
        """Update debug images"""
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
            
            
                
        except Exception as e:
            logger.warning(f"Failed to emit websocket updates: {e}")
        
        # Record performance metrics
        frame_time = time.time() - frame_start_time
        self.performance_monitor.record_frame_time(frame_time)
        self.last_frame_time = frame_start_time
            
    def start(self, bot):
        """Start Web server"""
        if self.is_running:
            logger.warning("Web server is already running")
            return
        
        # Set bot instance
        self.bot = bot
        
        # Set up periodic status broadcast
        self._setup_status_broadcast()
            
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