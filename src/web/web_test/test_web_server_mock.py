#!/usr/bin/env python3
'''
Web test server with rune alert scenarios
Provides mock data for testing alert functionality
'''
# Standard import
import time
import sys
import os
import threading
import argparse

# Library import
import cv2
import numpy as np

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

# Local import
from src.web import WebDebugServer
from src.utils.common import load_yaml

class RuneAlertScenario:
    """Rune alert scenario manager"""
    
    def __init__(self):
        # Load config (no need for alert manager since sounds are played in frontend)
        self.cfg = load_yaml("config/config_default.yaml")
        
        self.scenarios = {
            'normal': self.normal_scenario,
            'rune_detected': self.rune_detected_scenario,
            'rune_solving': self.rune_solving_scenario,
            'rune_solved': self.rune_solved_scenario,
            'rune_timeout': self.rune_timeout_scenario,
            'bot_stopped': self.bot_stopped_scenario,
            'demo_cycle': self.demo_cycle_scenario
        }
        self.current_scenario = 'normal'
        self.scenario_start_time = time.time()
        self.frame_count = 0
        self.alert_status = False
        self.last_alert_status = False  # Track previous status for transitions
        
    def normal_scenario(self, frame_count):
        """Normal hunting scenario - no rune"""
        self.alert_status = False
        return "Normal Hunting", "No rune detected"
    
    def rune_detected_scenario(self, frame_count):
        """Rune detected scenario - alert should be active"""
        self.alert_status = True
        return "Rune Detected!", "Alert: Rune has appeared!"
    
    def rune_solving_scenario(self, frame_count):
        """Rune solving scenario - alert should be active"""
        self.alert_status = True
        return "Solving Rune", "Alert: Solving rune puzzle..."
    
    def rune_solved_scenario(self, frame_count):
        """Rune solved scenario - alert should stop and play solved sound"""
        # Only show solved for a short time, then return to normal
        if frame_count < 30:  # 3 seconds at 10 FPS
            self.alert_status = False
            return "Rune Solved!", "Success: Rune puzzle completed!"
        else:
            self.current_scenario = 'normal'
            return "Normal Hunting", "No rune detected"
    
    def rune_timeout_scenario(self, frame_count):
        """Rune timeout scenario - alert should stop"""
        # Show timeout for a short time, then return to normal
        if frame_count < 20:  # 2 seconds at 10 FPS
            self.alert_status = False
            return "Rune Timeout", "Warning: Rune solving timeout"
        else:
            self.current_scenario = 'normal'
            return "Normal Hunting", "No rune detected"
    
    def bot_stopped_scenario(self, frame_count):
        """Bot stopped scenario - alert should be active"""
        self.alert_status = True
        return "Bot Stopped", "Alert: Bot has been stopped!"
    
    def demo_cycle_scenario(self, frame_count):
        """Demo cycle through all scenarios"""
        cycle_duration = 100  # 10 seconds per scenario at 10 FPS
        scenario_index = (frame_count // cycle_duration) % 6
        
        scenarios = ['normal', 'rune_detected', 'rune_solving', 'rune_solved', 'rune_timeout', 'bot_stopped']
        self.current_scenario = scenarios[scenario_index]
        
        # Call the appropriate scenario function
        return self.scenarios[self.current_scenario](frame_count % cycle_duration)
    
    def get_alert_status(self):
        """Get current alert status"""
        return self.alert_status
    
    def update_alert_sound(self):
        """Update alert sound based on status changes"""
        # Check if alert status changed
        if self.alert_status != self.last_alert_status:
            if self.alert_status:
                # Alert just became active
                if 'rune' in self.current_scenario:
                    print("🔊 Started rune alert sound (frontend)")
                elif 'bot_stopped' in self.current_scenario:
                    print("🛑 Played bot stopped alert sound (frontend)")
            else:
                # Alert just became inactive
                if 'rune' in self.current_scenario:
                    print("🔇 Stopped rune alert sound (frontend)")
                
                # Play solved sound for rune_solved scenario
                if self.current_scenario == 'rune_solved':
                    print("✅ Played rune solved sound (frontend)")
            
            self.last_alert_status = self.alert_status
    
    def get_sound_command(self):
        """Get sound command for frontend"""
        # Check if alert status changed
        if self.alert_status != self.last_alert_status:
            if self.alert_status:
                if 'rune' in self.current_scenario:
                    return "start_rune_alert"
                elif 'bot_stopped' in self.current_scenario:
                    return "play_bot_stopped_alert"
            else:
                if 'rune' in self.current_scenario:
                    return "stop_rune_alert"
                if self.current_scenario == 'rune_solved':
                    return "play_rune_solved_alert"
        
        # Also send initial command when scenario starts
        if self.frame_count == 0:
            if self.alert_status:
                if 'rune' in self.current_scenario:
                    return "start_rune_alert"
                elif 'bot_stopped' in self.current_scenario:
                    return "play_bot_stopped_alert"
        
        return None
    
    def set_scenario(self, scenario_name):
        """Set the current scenario"""
        if scenario_name in self.scenarios:
            self.current_scenario = scenario_name
            self.frame_count = 0
            self.scenario_start_time = time.time()
            print(f"🎯 Scenario changed to: {scenario_name}")
        else:
            print(f"❌ Unknown scenario: {scenario_name}")
            print(f"Available scenarios: {list(self.scenarios.keys())}")
    
    def cleanup(self):
        """Clean up resources"""
        pass

def create_mock_debug_image(width=800, height=600, frame_count=0, scenario_manager=None):
    """Create mock game window debug image with rune alert scenarios"""
    # Create base image
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Mock game background (sky gradient)
    for y in range(height // 2):
        blue_intensity = int(100 + 155 * y / (height // 2))
        image[y, :] = [blue_intensity, blue_intensity, 255]
    
    # Mock ground
    for y in range(height // 2, height):
        green_intensity = int(50 + 100 * (y - height // 2) / (height // 2))
        image[y, :] = [0, green_intensity, 0]
    
    # Mock character (moving circle)
    player_x = width // 2 + int(100 * np.sin(frame_count * 0.1))
    player_y = height // 2
    cv2.circle(image, (player_x, player_y), 25, (255, 255, 0), -1)  # Yellow character
    
    # Mock monster (red square)
    monster_x = player_x + 150
    monster_y = player_y + 50
    cv2.rectangle(image, (monster_x-20, monster_y-20), (monster_x+20, monster_y+20), (0, 0, 255), -1)
    
    # Mock UI elements
    # HP bar
    hp_percent = 0.7 + 0.3 * np.sin(frame_count * 0.05)
    hp_width = int(200 * hp_percent)
    cv2.rectangle(image, (10, 10), (210, 30), (0, 0, 0), -1)  # Background
    cv2.rectangle(image, (10, 10), (10 + hp_width, 30), (0, 255, 0), -1)  # HP bar
    cv2.putText(image, f"HP: {int(hp_percent*100)}%", (15, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # MP bar
    mp_percent = 0.5 + 0.5 * np.sin(frame_count * 0.03)
    mp_width = int(200 * mp_percent)
    cv2.rectangle(image, (10, 35), (210, 55), (0, 0, 0), -1)  # Background
    cv2.rectangle(image, (10, 35), (10 + mp_width, 55), (255, 0, 255), -1)  # MP bar
    cv2.putText(image, f"MP: {int(mp_percent*100)}%", (15, 47), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Minimap
    minimap_size = 120
    minimap_x = width - minimap_size - 10
    minimap_y = 10
    cv2.rectangle(image, (minimap_x, minimap_y), (minimap_x + minimap_size, minimap_y + minimap_size), (255, 255, 255), 2)
    cv2.circle(image, (minimap_x + minimap_size//2, minimap_y + minimap_size//2), 4, (255, 255, 0), -1)  # Player position
    
    # Rune Alert Scenario Display
    if scenario_manager:
        title, message = scenario_manager.scenarios[scenario_manager.current_scenario](frame_count)
        
        # Scenario title (top center)
        cv2.putText(image, title, (width//2 - 150, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Alert status indicator
        if scenario_manager.get_alert_status():
            # Red alert background
            cv2.rectangle(image, (width//2 - 200, 90), (width//2 + 200, 130), (0, 0, 100), -1)
            cv2.putText(image, "🔊 ALERT ACTIVE", (width//2 - 80, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        else:
            # Gray normal background
            cv2.rectangle(image, (width//2 - 200, 90), (width//2 + 200, 130), (50, 50, 50), -1)
            cv2.putText(image, "🔇 Alert Disabled", (width//2 - 80, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        
        # Scenario message
        cv2.putText(image, message, (width//2 - 150, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # Current scenario info
        cv2.putText(image, f"Scenario: {scenario_manager.current_scenario}", (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Debug info
    timestamp = time.strftime("%H:%M:%S")
    cv2.putText(image, f"Frame: {frame_count}", (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(image, f"Time: {timestamp}", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Mock attack range box
    attack_x = player_x - 100
    attack_y = player_y - 50
    cv2.rectangle(image, (attack_x, attack_y), (attack_x + 200, attack_y + 100), (0, 0, 255), 2)
    cv2.putText(image, "Attack Range", (attack_x, attack_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    # Add rune-related visual elements based on scenario
    if scenario_manager:
        if 'rune' in scenario_manager.current_scenario:
            # Draw rune icon near player
            rune_x = player_x + 80
            rune_y = player_y - 60
            cv2.circle(image, (rune_x, rune_y), 20, (255, 0, 255), -1)  # Purple rune
            cv2.putText(image, "RUNE", (rune_x - 20, rune_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            if scenario_manager.current_scenario == 'rune_solving':
                # Draw arrow puzzle
                arrow_x = width // 2
                arrow_y = height // 2 + 100
                for i in range(4):
                    x = arrow_x - 150 + i * 100
                    cv2.rectangle(image, (x-30, arrow_y-30), (x+30, arrow_y+30), (255, 255, 0), 2)
                    cv2.putText(image, "↑", (x-5, arrow_y+5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    return image

def create_mock_route_image(width=400, height=300, frame_count=0, scenario_manager=None):
    """Create mock route map image with rune alert scenarios"""
    # Create map background
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = [30, 30, 30]  # Dark gray background
    
    # Draw route path
    points = []
    for i in range(15):
        x = int(width * 0.1 + (width * 0.8) * i / 14)
        y = int(height * 0.5 + 60 * np.sin(i * 0.8 + frame_count * 0.1))
        points.append((x, y))
    
    # Draw route lines
    for i in range(len(points) - 1):
        cv2.line(image, points[i], points[i+1], (0, 255, 0), 3)
    
    # Add current player position
    current_point = points[frame_count % len(points)]
    cv2.circle(image, current_point, 8, (255, 255, 0), -1)  # Yellow player position
    
    # Add action points (color coded)
    for i in range(0, len(points), 3):
        if i < len(points):
            cv2.circle(image, points[i], 12, (255, 0, 0), -1)  # Blue action point
            cv2.putText(image, f"A{i//3+1}", (points[i][0]-8, points[i][1]+4), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    # Add rune locations based on scenario
    if scenario_manager and 'rune' in scenario_manager.current_scenario:
        # Add rune locations on the map
        for i in range(2, len(points), 4):
            if i < len(points):
                rune_point = points[i]
                cv2.circle(image, rune_point, 15, (255, 0, 255), -1)  # Purple rune
                cv2.putText(image, "RUNE", (rune_point[0]-15, rune_point[1]+5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    # Add map title and info
    cv2.putText(image, "Mock Route Map View", (width//2 - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, f"Player: {current_point}", (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(image, f"Route Progress: {frame_count % len(points)}/{len(points)}", (10, height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # Add alert status to route map
    if scenario_manager:
        alert_text = "🔊 ALERT" if scenario_manager.get_alert_status() else "🔇 Normal"
        alert_color = (0, 255, 255) if scenario_manager.get_alert_status() else (200, 200, 200)
        cv2.putText(image, alert_text, (width - 120, height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, alert_color, 1)
    
    return image

def print_scenario_help():
    """Print help information for scenarios"""
    print("🎯 Available Rune Alert Scenarios:")
    print("  normal        - Normal hunting (no alert)")
    print("  rune_detected - Rune detected (alert active)")
    print("  rune_solving  - Solving rune puzzle (alert active)")
    print("  rune_solved   - Rune solved (alert stops, plays solved sound)")
    print("  rune_timeout  - Rune timeout (alert stops)")
    print("  bot_stopped   - Bot stopped (alert active)")
    print("  demo_cycle    - Cycle through all scenarios automatically")
    print("")
    print("💡 Usage:")
    print("  python test_web_server_mock.py --scenario rune_detected")
    print("  python test_web_server_mock.py --scenario demo_cycle")
    print("")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='MapleStory Auto Bot Web Server with Rune Alert Scenarios')
    parser.add_argument('--scenario', default='demo_cycle', 
                       choices=['normal', 'rune_detected', 'rune_solving', 'rune_solved', 'rune_timeout', 'bot_stopped', 'demo_cycle'],
                       help='Rune alert scenario to test')
    parser.add_argument('--port', type=int, default=5001, help='Web server port')
    parser.add_argument('--host', default='0.0.0.0', help='Web server host')
    
    args = parser.parse_args()
    
    print("🎮 MapleStory Auto Bot Web Server with Rune Alert Scenarios")
    print("🌐 Using Mock data to test and demonstrate alert functionality")
    print("=" * 60)
    
    # Create scenario manager
    scenario_manager = RuneAlertScenario()
    scenario_manager.set_scenario(args.scenario)
    
    # Create Web server
    server = WebDebugServer(host=args.host, port=args.port)
    server.start()
    
    print(f"✅ Web server started: {server.get_url()}")
    print(f"🎯 Current scenario: {args.scenario}")
    print("📱 Please open the URL in browser to view Mock debug interface")
    print("🔄 Press Ctrl+C to stop server")
    print("=" * 60)
    print("💡 Rune Alert Features:")
    print("   - Visual alert indicators in game window")
    print("   - Alert status in route map")
    print("   - Real-time scenario transitions")
    print("   - WebSocket alert status updates")
    print("=" * 60)
    print("🎵 Alert Sound Testing:")
    print("   - Rune detection: Continuous beeping sound")
    print("   - Rune solved: Success chime")
    print("   - Bot stopped: Warning tone")
    print("=" * 60)
    
    try:
        frame_count = 0
        while True:
            # Create Mock images with scenario
            debug_image = create_mock_debug_image(800, 600, frame_count, scenario_manager)
            route_image = create_mock_route_image(400, 300, frame_count, scenario_manager)
            
            # Update alert sound based on scenario
            scenario_manager.update_alert_sound()
            
            # Get sound command for frontend
            sound_command = scenario_manager.get_sound_command()
            
            # Update Web server with alert status and sound command
            alert_status = scenario_manager.get_alert_status()
            server.update_debug_frame(debug_image, route_image, alert_status, sound_command)
            
            frame_count += 1
            time.sleep(0.1)  # 10 FPS
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop()
        scenario_manager.cleanup()
        print("✅ Server stopped")
        print("🎉 Rune alert scenario testing completed!")

if __name__ == "__main__":
    print_scenario_help()
    main() 