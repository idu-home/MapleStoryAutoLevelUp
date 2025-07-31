#!/usr/bin/env python3
import cv2
import numpy as np
import time
import sys
import os

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from src.web import WebDebugServer

def create_simple_mock_image(width=800, height=600, frame_count=0):
    """Create simple mock image"""
    # Create gradient background
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            image[y, x] = [
                int(255 * x / width),  # B
                int(255 * y / height), # G
                int(255 * (x + y) / (width + height))  # R
            ]
    
    # Add moving circle
    center_x = width // 2 + int(100 * np.sin(frame_count * 0.1))
    center_y = height // 2 + int(50 * np.cos(frame_count * 0.1))
    cv2.circle(image, (center_x, center_y), 30, (255, 255, 0), -1)
    
    # Add text
    timestamp = time.strftime("%H:%M:%S")
    cv2.putText(image, f"Mock Frame {frame_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(image, f"Time: {timestamp}", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return image

def main():
    print("🚀 Quick Web Server Test")
    print("🌐 Starting server...")
    
    # Start server
    server = WebDebugServer(host='0.0.0.0', port=5001)
    server.start()
    
    print(f"✅ Server started: {server.get_url()}")
    print("📱 Open the URL in browser to see the effect")
    print("⏱️  Will run for 10 seconds then auto-stop")
    
    try:
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:  # Run for 10 seconds
            # Create mock images
            debug_image = create_simple_mock_image(800, 600, frame_count)
            route_image = create_simple_mock_image(400, 300, frame_count)
            
            # Update server
            server.update_debug_frame(debug_image, route_image)
            
            frame_count += 1
            time.sleep(0.1)
            
        print(f"✅ Test completed, sent {frame_count} frames")
        
    except KeyboardInterrupt:
        print("\n🛑 User interrupted")
    finally:
        server.stop()
        print("✅ Server stopped")

if __name__ == "__main__":
    main() 