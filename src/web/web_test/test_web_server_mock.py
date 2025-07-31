#!/usr/bin/env python3
import cv2
import numpy as np
import time
import sys
import os
import threading

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from src.web import WebDebugServer

def create_mock_debug_image(width=800, height=600, frame_count=0):
    """Create mock game window debug image"""
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
    
    # Debug info
    timestamp = time.strftime("%H:%M:%S")
    cv2.putText(image, f"Frame: {frame_count}", (10, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(image, f"Time: {timestamp}", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(image, "Mock Game Window Debug View", (width//2 - 180, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    # Mock attack range box
    attack_x = player_x - 100
    attack_y = player_y - 50
    cv2.rectangle(image, (attack_x, attack_y), (attack_x + 200, attack_y + 100), (0, 0, 255), 2)
    cv2.putText(image, "Attack Range", (attack_x, attack_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    
    return image

def create_mock_route_image(width=400, height=300, frame_count=0):
    """Create mock route map image"""
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
    
    # Add map title and info
    cv2.putText(image, "Mock Route Map View", (width//2 - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(image, f"Player: {current_point}", (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(image, f"Route Progress: {frame_count % len(points)}/{len(points)}", (10, height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    return image

def main():
    """Main function"""
    print("🎮 MapleStory Auto Bot Web Server Verification")
    print("🌐 Using Mock data to quickly verify Web server functionality")
    print("=" * 50)
    
    # Create Web server
    server = WebDebugServer(host='0.0.0.0', port=5001)
    server.start()
    
    print(f"✅ Web server started: {server.get_url()}")
    print("📱 Please open the URL in browser to view Mock debug interface")
    print("🔄 Press Ctrl+C to stop server")
    print("=" * 50)
    print("💡 Mock data description:")
    print("   - Game window: Mock character movement, monsters, UI elements")
    print("   - Route map: Mock paths, player position, action points")
    print("   - Real-time updates: Update images every 0.1 seconds")
    print("=" * 50)
    
    try:
        frame_count = 0
        while True:
            # Create Mock images
            debug_image = create_mock_debug_image(800, 600, frame_count)
            route_image = create_mock_route_image(400, 300, frame_count)
            
            # Update Web server
            server.update_debug_frame(debug_image, route_image)
            
            frame_count += 1
            time.sleep(0.1)  # 10 FPS
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop()
        print("✅ Server stopped")
        print("🎉 Mock verification completed!")

if __name__ == "__main__":
    main() 