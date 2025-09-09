'''
Alert system for MapleStory Auto Bot
Handles push notifications for various events like rune detection
'''
# Standard import
import threading
import logging
import requests
from datetime import datetime
import sys
import os

# Handle imports for both direct execution and module import
if __name__ == '__main__':
    # Direct execution: add parent directory to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

try:
    from src.utils.logger import logger
except ImportError:
    # Fallback to basic logging if logger module not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Default ntfy configuration
DEFAULT_NTFY_SERVER = 'https://ntfy.sh'
DEFAULT_NTFY_TOPIC = 'weiwei-maple-bot'
DEFAULT_NTFY_PRIORITY = 'default'
DEFAULT_NTFY_TAGS = 'maple_story,bot'

class Alert:
    '''
    Manages push notifications for the bot
    '''
    def __init__(self, cfg):
        self.cfg = cfg
        self.is_rune_alert_active = False
        self.rune_alert_thread = None
        self.is_other_player_alert_active = False
        self.other_player_alert_thread = None
        self.other_player_first_detected_time = None
        self.minimap_detection_failed = False
        self.t_minimap_detection_failed = None
        self.t_last_minimap_alert = None
        self.minimap_alert_thread = None
        self.minimap_alert_stop_event = None
        self.alert_lock = threading.Lock()
        
        # Initialize ntfy system
        self._init_ntfy_system()
        
    def _init_ntfy_system(self):
        '''Initialize the ntfy notification system'''
        self.alert_enabled = self.cfg.get('alert', {}).get('enable', False)
        self.ntfy_enabled = self.alert_enabled
        
        if self.ntfy_enabled:
            # Hardcoded ntfy settings
            self.ntfy_server = DEFAULT_NTFY_SERVER
            self.ntfy_topic = DEFAULT_NTFY_TOPIC
            self.ntfy_priority = DEFAULT_NTFY_PRIORITY
            self.ntfy_tags = DEFAULT_NTFY_TAGS
            logger.info(f"ntfy notification system initialized - Topic: {self.ntfy_topic}")
        else:
            logger.info("ntfy notifications disabled")
    
    def _send_ntfy_notification(self, title, message, priority=None, tags=None):
        '''Send a notification via ntfy.sh'''
        if not self.ntfy_enabled:
            return
            
        try:
            ntfy_url = f"{self.ntfy_server}/{self.ntfy_topic}"
            
            # Remove emojis from title for headers (HTTP headers have encoding limitations)
            clean_title = title.encode('ascii', 'ignore').decode('ascii').strip() if title else ''
            
            headers = {
                'Title': clean_title,
                'Priority': priority or self.ntfy_priority,
                'Tags': tags or self.ntfy_tags
            }
            
            # Include original title with emojis in the message body
            full_message = f"{title}\n{message}" if title != clean_title else message
            
            response = requests.post(
                ntfy_url, 
                data=full_message.encode('utf-8'), 
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"ntfy notification sent: {title}")
                return True
            else:
                logger.error(f"ntfy notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send ntfy notification: {e}")
            return False
    
    def start_rune_alert(self):
        '''Start the rune detection alert'''
        with self.alert_lock:
            if not self.is_rune_alert_active and self.alert_enabled:
                self.is_rune_alert_active = True
                
                # Send immediate notification
                self._send_ntfy_notification(
                    title="🔮 Rune Detected!",
                    message=f"A rune has been detected at {datetime.now().strftime('%H:%M:%S')}. The bot is now solving it.",
                    priority="high",
                    tags="rune,alert,urgent"
                )
                
                # Start periodic notifications for persistent rune alert
                def periodic_alert():
                    count = 1
                    while self.is_rune_alert_active:
                        import time
                        time.sleep(10)  # Wait 10 seconds between notifications
                        if self.is_rune_alert_active:
                            count += 1
                            self._send_ntfy_notification(
                                title="🔮 Rune Still Active",
                                message=f"Rune solving in progress... ({count * 10}s elapsed)",
                                priority="default"
                            )
                
                self.rune_alert_thread = threading.Thread(target=periodic_alert, daemon=True)
                self.rune_alert_thread.start()
                
                logger.info("Started rune detection alert")
    
    def stop_rune_alert(self):
        '''Stop the rune detection alert'''
        with self.alert_lock:
            if self.is_rune_alert_active:
                self.is_rune_alert_active = False
                logger.info("Stopped rune detection alert")
    
    def update_other_player_status(self, player_count):
        '''Update other player status and handle alerts'''
        import time
        
        with self.alert_lock:
            if player_count > 0:
                # Other player detected
                if self.other_player_first_detected_time is None:
                    # First detection
                    self.other_player_first_detected_time = time.time()
                    self._start_other_player_alert()
            else:
                # No other player detected
                if self.other_player_first_detected_time is not None:
                    # Player disappeared
                    self.other_player_first_detected_time = None
                    self._stop_other_player_alert()
    
    def _start_other_player_alert(self):
        '''Internal method to start the other player detection alert'''
        if not self.is_other_player_alert_active and self.alert_enabled:
            self.is_other_player_alert_active = True
            
            # Send immediate notification
            self._send_ntfy_notification(
                title="👤 Other Player Detected!",
                message=f"Another player has been detected on the map at {datetime.now().strftime('%H:%M:%S')}. Monitoring for 10+ seconds...",
                priority="default",
                tags="other_player,alert"
            )
            
            # Start periodic notifications after 10 seconds
            def periodic_alert():
                import time
                time.sleep(10)  # Wait 10 seconds before first notification
                count = 1
                while self.is_other_player_alert_active:
                    if self.is_other_player_alert_active:
                        self._send_ntfy_notification(
                            title="👤 Other Player Still Present",
                            message=f"Other player has been on the map for {(count * 10) + 10} seconds. Consider changing channels.",
                            priority="default",
                            tags="other_player,persistent"
                        )
                        count += 1
                    time.sleep(10)  # Wait 10 seconds between notifications
            
            self.other_player_alert_thread = threading.Thread(target=periodic_alert, daemon=True)
            self.other_player_alert_thread.start()
            
            logger.info("Started other player detection alert")
    
    def _stop_other_player_alert(self):
        '''Internal method to stop the other player detection alert'''
        if self.is_other_player_alert_active:
            self.is_other_player_alert_active = False
            logger.info("Stopped other player detection alert")
    
    def stop_other_player_alert(self):
        '''Public method to stop the other player detection alert'''
        with self.alert_lock:
            self.other_player_first_detected_time = None
            self._stop_other_player_alert()
    
    def play_rune_solved_alert(self):
        '''Send rune solved notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="✅ Rune Solved!",
                message=f"Rune successfully solved at {datetime.now().strftime('%H:%M:%S')}. Bot continuing normal operation.",
                priority="default",
                tags="rune,success"
            )
    
    def play_bot_stopped_alert(self):
        '''Send bot stopped notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⛔ Bot Stopped",
                message=f"MapleStory bot has stopped at {datetime.now().strftime('%H:%M:%S')}. Please check the application.",
                priority="urgent",
                tags="bot,stopped,urgent"
            )
        # Stop other player alert when bot is stopped
        self.stop_other_player_alert()
    
    def play_bot_started_alert(self):
        '''Send bot started notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="🚀 Bot Started",
                message=f"MapleStory bot has started at {datetime.now().strftime('%H:%M:%S')}. Beginning auto-leveling session.",
                priority="default",
                tags="bot,started"
            )
    
    def play_bot_paused_alert(self):
        '''Send bot paused notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⏸️ Bot Paused",
                message=f"MapleStory bot has been paused at {datetime.now().strftime('%H:%M:%S')}. Waiting for resume command.",
                priority="default",
                tags="bot,paused"
            )
        # Stop other player alert when bot is paused
        self.stop_other_player_alert()
    
    def send_player_stuck_alert(self, stuck_duration):
        '''Send player stuck notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⚠️ Player Stuck",
                message=f"Player has been stuck for {stuck_duration:.1f} seconds. Bot is attempting recovery actions.",
                priority="high",
                tags="player,stuck,warning"
            )
    
    def send_rune_activated_alert(self):
        '''Send rune mini-game activated notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="🎯 Rune Activated!",
                message="Rune mini-game has started. Bot is now solving the arrows.",
                priority="high",
                tags="rune,minigame,progress"
            )
    
    def send_rune_located_alert(self):
        '''Send rune located notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="📍 Rune Located!",
                message="Rune found on screen. Bot is moving to interact with it.",
                priority="default",
                tags="rune,found,progress"
            )
    
    def send_rune_search_warning_alert(self, elapsed_time, remaining_time):
        '''Send rune search taking long warning'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="🔍 Rune Search Taking Long",
                message=f"Still searching for rune after {elapsed_time:.1f}s. {remaining_time:.1f}s remaining before timeout.",
                priority="default",
                tags="rune,search,warning"
            )
    
    def send_rune_search_timeout_alert(self, elapsed_time):
        '''Send rune search timeout notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⏰ Rune Search Timeout",
                message=f"Could not locate rune after {elapsed_time:.1f} seconds. Returning to normal hunting...",
                priority="high",
                tags="rune,timeout,failure"
            )
    
    def send_rune_warning_detected_alert(self):
        '''Send rune warning message detected notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⚠️ Rune Warning Detected",
                message="Game is showing 'Please solve rune before hunting' message. Bot has stopped attacking and is focusing on rune.",
                priority="high",
                tags="rune,warning,game_message"
            )
    
    def send_rune_interaction_start_alert(self):
        '''Send rune interaction started notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="🔧 Interacting with Rune",
                message="Bot is now attempting to trigger the rune. Getting into position...",
                priority="default",
                tags="rune,interaction,progress"
            )
    
    def send_rune_interaction_timeout_alert(self, elapsed_time):
        '''Send rune interaction timeout notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⏰ Rune Interaction Timeout",
                message=f"Failed to activate rune after {elapsed_time:.1f} seconds. Returning to search mode...",
                priority="high",
                tags="rune,timeout,warning"
            )
    
    def send_rune_interaction_warning_alert(self, remaining_time):
        '''Send rune interaction taking long warning'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="⚠️ Rune Interaction Taking Long",
                message=f"Still trying to activate rune. {remaining_time:.1f}s remaining before timeout.",
                priority="default",
                tags="rune,warning,progress"
            )
    
    def send_rune_interaction_attempts_alert(self, attempts):
        '''Send multiple rune interaction attempts notification'''
        if False:  # Debug alerts disabled by default
            self._send_ntfy_notification(
                title="🔄 Multiple Rune Attempts",
                message=f"Made {attempts} attempts to activate rune. Still trying...",
                priority="low",
                tags="rune,attempts,debug"
            )
    
    def send_minimap_detection_failed_alert(self, duration):
        '''Send minimap detection failure notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="🗺️ Minimap Detection Failed",
                message=f"Unable to detect minimap for {duration:.1f} seconds. Bot may not function correctly.",
                priority="high",
                tags="minimap,detection,failure,warning"
            )
    
    def send_minimap_detection_recovered_alert(self):
        '''Send minimap detection recovery notification'''
        if self.alert_enabled:
            self._send_ntfy_notification(
                title="✅ Minimap Detection Recovered",
                message="Minimap detection is working again. Bot should function normally now.",
                priority="default",
                tags="minimap,detection,recovery,success"
            )
    
    def update_minimap_detection_status(self, is_detected):
        '''
        Update minimap detection status and handle alerts
        
        Args:
            is_detected (bool): True if minimap was successfully detected, False otherwise
        '''
        import time
        
        with self.alert_lock:
            if is_detected:
                # Minimap detection successful
                if self.minimap_detection_failed:
                    # Was in failure state, now recovered
                    self._stop_minimap_alert_timer()
                    
                    if self.alert_enabled and self.t_last_minimap_alert is not None:
                        # Only send recovery alert if we previously sent a failure alert
                        self.send_minimap_detection_recovered_alert()
                        logger.info("[Minimap Alert] Detection recovered - recovery alert sent")
                    
                    # Reset all tracking state
                    self.minimap_detection_failed = False
                    self.t_minimap_detection_failed = None
                    self.t_last_minimap_alert = None
                    logger.debug("[Minimap Alert] Reset minimap detection failure tracking")
            else:
                # Minimap detection failed
                if not self.minimap_detection_failed:
                    # First time detection failed - start timer
                    self.minimap_detection_failed = True
                    self.t_minimap_detection_failed = time.time()
                    self.t_last_minimap_alert = None
                    logger.debug("[Minimap Alert] Started tracking minimap detection failure")
                    
                    # Start alert timer
                    if self.alert_enabled:
                        self._start_minimap_alert_timer()
                # If already in failure state, do nothing - timer is already running
    
    def _start_minimap_alert_timer(self):
        '''Start the minimap alert timer thread'''
        if self.minimap_alert_thread is not None:
            return  # Timer already running
        
        import threading
        self.minimap_alert_stop_event = threading.Event()
        self.minimap_alert_thread = threading.Thread(target=self._minimap_alert_worker)
        self.minimap_alert_thread.daemon = True
        self.minimap_alert_thread.start()
        logger.debug("[Minimap Alert] Started alert timer thread")
    
    def _stop_minimap_alert_timer(self):
        '''Stop the minimap alert timer thread'''
        if self.minimap_alert_thread is not None:
            self.minimap_alert_stop_event.set()
            self.minimap_alert_thread.join(timeout=1.0)
            self.minimap_alert_thread = None
            self.minimap_alert_stop_event = None
            logger.debug("[Minimap Alert] Stopped alert timer thread")
    
    def _minimap_alert_worker(self):
        '''Worker thread for minimap alert timing'''
        import time
        
        timeout_threshold = self.cfg.get("minimap", {}).get("detection_failure_timeout", 10.0)
        repeat_interval = self.cfg.get("minimap", {}).get("alert_repeat_interval", 10.0)
        
        # Wait for initial timeout
        if self.minimap_alert_stop_event.wait(timeout_threshold):
            return  # Stopped before timeout
        
        # Send initial alert
        with self.alert_lock:
            if self.minimap_detection_failed and self.t_minimap_detection_failed is not None:
                failure_duration = time.time() - self.t_minimap_detection_failed
                self.send_minimap_detection_failed_alert(failure_duration)
                self.t_last_minimap_alert = time.time()
                logger.warning(f"[Minimap Alert] Detection failed for {failure_duration:.1f}s - initial alert sent")
        
        # Send repeat alerts
        while not self.minimap_alert_stop_event.wait(repeat_interval):
            with self.alert_lock:
                if self.minimap_detection_failed and self.t_minimap_detection_failed is not None:
                    failure_duration = time.time() - self.t_minimap_detection_failed
                    self.send_minimap_detection_failed_alert(failure_duration)
                    self.t_last_minimap_alert = time.time()
                    logger.warning(f"[Minimap Alert] Detection still failed for {failure_duration:.1f}s - repeat alert sent")
                else:
                    break  # No longer in failure state
    
    def is_rune_alert_playing(self):
        '''Check if rune alert is currently active'''
        with self.alert_lock:
            return self.is_rune_alert_active
    
    def is_alert_enabled(self):
        '''Check if alert system is enabled'''
        return self.alert_enabled
    
    def cleanup(self):
        '''Clean up resources'''
        self.stop_rune_alert()
        self.stop_other_player_alert()
        self._stop_minimap_alert_timer()
        


def main():
    '''
    Test function for Alert system
    Usage: python -m src.engine.Alert
    '''
    import time
    
    print("🧪 Testing ntfy Alert System")
    print("=" * 50)
    
    # Create minimal test configuration
    test_cfg = {
        'alert': {
            'enable': True
        }
    }
    
    print(f"📱 ntfy server: {DEFAULT_NTFY_SERVER}")
    print(f"📢 ntfy topic: {DEFAULT_NTFY_TOPIC}")
    print(f"🏷️  ntfy tags: {DEFAULT_NTFY_TAGS}")
    print()
    
    # Initialize Alert system
    try:
        alert = Alert(test_cfg)
        print("✅ Alert system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Alert system: {e}")
        return
    
    # Test different alert types
    test_cases = [
        ("Bot Started", alert.play_bot_started_alert),
        ("Bot Paused", alert.play_bot_paused_alert),
        ("Bot Stopped", alert.play_bot_stopped_alert),
        ("Player Stuck", lambda: alert.send_player_stuck_alert(15.3)),
        ("Rune Solved", alert.play_rune_solved_alert),
        ("Rune Detection Start", alert.start_rune_alert),
        ("Rune Activated", alert.send_rune_activated_alert),
        ("Rune Located", alert.send_rune_located_alert),
        ("Rune Warning Detected", alert.send_rune_warning_detected_alert),
        ("Rune Interaction Start", alert.send_rune_interaction_start_alert),
        ("Other Player Detection", lambda: alert.update_other_player_status(1)),
        ("Other Player Disappears", lambda: alert.update_other_player_status(0)),
    ]
    
    for description, method in test_cases:
        print(f"\n🔔 Testing: {description}")
        try:
            method()
            print("✅ Notification sent successfully")
            
            if description == "Rune Detection Start":
                print("⏳ Rune alert active for 5 seconds...")
                time.sleep(5)
                alert.stop_rune_alert()
                print("🛑 Rune alert stopped")
                
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
        
        time.sleep(1)  # Small delay between tests
    
    
    # Cleanup
    alert.cleanup()
    print("✅ Alert system cleaned up")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed! Check your ntfy app/web interface for notifications.")
    print(f"📱 Subscribe to topic: {DEFAULT_NTFY_TOPIC}")
    print(f"🌐 Web interface: {DEFAULT_NTFY_SERVER}/{DEFAULT_NTFY_TOPIC}")


if __name__ == '__main__':
    main() 