#!/usr/bin/env python3
import sys
import os

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

def test_imports():
    """Test module imports"""
    print("🧪 Testing module imports...")
    
    try:
        from src.web import WebDebugServer
        print("✅ WebDebugServer import successful")
    except Exception as e:
        print(f"❌ WebDebugServer import failed: {e}")
        return False
    
    try:
        from src.web import image_to_base64, validate_image
        print("✅ Utility functions import successful")
    except Exception as e:
        print(f"❌ Utility functions import failed: {e}")
        return False
    
    try:
        from src.web import DEFAULT_HOST, DEFAULT_PORT, JPEG_QUALITY
        print("✅ Configuration constants import successful")
    except Exception as e:
        print(f"❌ Configuration constants import failed: {e}")
        return False
    
    return True

def test_server_creation():
    """Test server creation"""
    print("\n🧪 Testing server creation...")
    
    try:
        from src.web import WebDebugServer
        server = WebDebugServer(host='127.0.0.1', port=5002)
        print("✅ Server creation successful")
        return server
    except Exception as e:
        print(f"❌ Server creation failed: {e}")
        return None

def test_image_utils():
    """Test image utility functions"""
    print("\n🧪 Testing image utility functions...")
    
    try:
        import cv2
        import numpy as np
        from src.web import image_to_base64, validate_image
        
        # Create test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # Red image
        
        # Test image validation
        if validate_image(test_image):
            print("✅ Image validation function normal")
        else:
            print("❌ Image validation function abnormal")
            return False
        
        # Test Base64 conversion
        b64_result = image_to_base64(test_image)
        if b64_result and b64_result.startswith("data:image/jpeg;base64,"):
            print("✅ Base64 conversion function normal")
        else:
            print("❌ Base64 conversion function abnormal")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Image utility functions test failed: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.web import DEFAULT_HOST, DEFAULT_PORT, JPEG_QUALITY
        
        print(f"✅ Default host: {DEFAULT_HOST}")
        print(f"✅ Default port: {DEFAULT_PORT}")
        print(f"✅ JPEG quality: {JPEG_QUALITY}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Web Module Function Verification")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Module import test failed")
        return 1
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration test failed")
        return 1
    
    # Test image utilities
    if not test_image_utils():
        print("\n❌ Image utilities test failed")
        return 1
    
    # Test server creation
    server = test_server_creation()
    if server is None:
        print("\n❌ Server creation test failed")
        return 1
    
    print("\n🎉 All tests passed!")
    print("💡 Now you can run the following commands for full testing:")
    print("   python src/web/test/quick_test_web.py")
    print("   python src/web/test/test_web_server_mock.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 