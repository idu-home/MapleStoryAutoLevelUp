'''
Alert system for MapleStory Auto Bot
Handles sound alerts for various events like rune detection
'''
# Standard import
import os
import time
import threading
import logging
from pathlib import Path

# Library import
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available, sound alerts will be disabled")

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False

# Local import
from src.utils.logger import logger

class Alert:
    '''
    Manages sound alerts for the bot
    '''
    def __init__(self, cfg):
        self.cfg = cfg
        self.is_rune_alert_active = False
        self.rune_alert_thread = None
        self.alert_lock = threading.Lock()
        
        # Initialize sound system
        self._init_sound_system()
        
        # Load alert sounds
        self._load_alert_sounds()
        
    def _init_sound_system(self):
        '''Initialize the sound system based on available libraries'''
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                self.sound_system = "pygame"
                logger.info("Sound system initialized with pygame")
            except Exception as e:
                logger.warning(f"Failed to initialize pygame mixer: {e}")
                self.sound_system = None
        elif WINSOUND_AVAILABLE:
            self.sound_system = "winsound"
            logger.info("Sound system initialized with winsound")
        else:
            self.sound_system = None
            logger.warning("No sound system available, alerts will be silent")
    
    def _load_alert_sounds(self):
        '''Load alert sound files'''
        self.alert_sounds = {}
        
        if not self.sound_system:
            return
            
        # Define sound file paths
        sound_files = {
            'rune_detected': 'media/rune_alert.wav',
            'rune_solved': 'media/rune_solved.wav',
            'bot_stopped': 'media/bot_stopped.wav'
        }
        
        for alert_type, file_path in sound_files.items():
            if os.path.exists(file_path):
                if self.sound_system == "pygame":
                    try:
                        self.alert_sounds[alert_type] = pygame.mixer.Sound(file_path)
                        logger.info(f"Loaded sound: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load sound {file_path}: {e}")
                else:
                    self.alert_sounds[alert_type] = file_path
            else:
                logger.warning(f"Sound file not found: {file_path}")
    
    def play_sound(self, alert_type, repeat=False):
        '''
        Play a sound alert
        
        Args:
            alert_type (str): Type of alert ('rune_detected', 'rune_solved', 'bot_stopped')
            repeat (bool): Whether to repeat the sound
        '''
        if not self.sound_system or alert_type not in self.alert_sounds:
            return
            
        try:
            if self.sound_system == "pygame":
                sound = self.alert_sounds[alert_type]
                if repeat:
                    sound.play(-1)  # -1 means loop indefinitely
                else:
                    sound.play()
            elif self.sound_system == "winsound":
                sound_file = self.alert_sounds[alert_type]
                if repeat:
                    # For winsound, we need to implement looping manually
                    def play_loop():
                        while True:
                            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                            time.sleep(0.1)  # Small delay between loops
                    
                    thread = threading.Thread(target=play_loop, daemon=True)
                    thread.start()
                else:
                    winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                    
            logger.info(f"Playing {alert_type} alert")
            
        except Exception as e:
            logger.error(f"Failed to play sound {alert_type}: {e}")
    
    def stop_sound(self, alert_type):
        '''Stop a specific sound alert'''
        if not self.sound_system or alert_type not in self.alert_sounds:
            return
            
        try:
            if self.sound_system == "pygame":
                sound = self.alert_sounds[alert_type]
                sound.stop()
            # For winsound, stopping is handled by the thread termination
            
            logger.info(f"Stopped {alert_type} alert")
            
        except Exception as e:
            logger.error(f"Failed to stop sound {alert_type}: {e}")
    
    def start_rune_alert(self):
        '''Start the rune detection alert'''
        with self.alert_lock:
            if not self.is_rune_alert_active:
                self.is_rune_alert_active = True
                self.play_sound('rune_detected', repeat=True)
                logger.info("Started rune detection alert")
    
    def stop_rune_alert(self):
        '''Stop the rune detection alert'''
        with self.alert_lock:
            if self.is_rune_alert_active:
                self.is_rune_alert_active = False
                self.stop_sound('rune_detected')
                logger.info("Stopped rune detection alert")
    
    def play_rune_solved_alert(self):
        '''Play rune solved alert'''
        self.play_sound('rune_solved', repeat=False)
    
    def play_bot_stopped_alert(self):
        '''Play bot stopped alert'''
        self.play_sound('bot_stopped', repeat=False)
    
    def is_rune_alert_playing(self):
        '''Check if rune alert is currently playing'''
        with self.alert_lock:
            return self.is_rune_alert_active
    
    def cleanup(self):
        '''Clean up resources'''
        self.stop_rune_alert()
        if self.sound_system == "pygame":
            try:
                pygame.mixer.quit()
            except:
                pass 