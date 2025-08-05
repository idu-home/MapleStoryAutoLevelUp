'''
Web Debug Utilities
Image processing utilities for web debug server
'''
import cv2
import numpy as np
import base64
import time
from typing import Optional, Tuple
from PIL import Image
import io

def image_to_base64(image: np.ndarray, quality: int = 85) -> Optional[str]:
    """
    Convert OpenCV image to base64 string
    
    Args:
        image: OpenCV image array (in BGR format)
        quality: JPEG compression quality (1-100)
    
    Returns:
        base64 encoded string, returns None if conversion fails
    """
    if image is None:
        return None
        
    try:
        # OpenCV images are in BGR format, but web browsers expect RGB
        # Convert BGR to RGB for proper web display
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        # Use PIL for proper RGB JPEG encoding
        pil_image = Image.fromarray(image_rgb)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        jpg_as_text = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{jpg_as_text}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None

def image_to_base64_optimized(image: np.ndarray, quality: int = 60, max_width: int = 800, is_mobile: bool = False) -> Optional[str]:
    """
    Optimized image to base64 conversion with size reduction
    
    Args:
        image: OpenCV image array (in BGR format)
        quality: JPEG compression quality (1-100)
        max_width: Maximum width for resizing
        is_mobile: Whether this is for mobile device (uses higher compression)
    
    Returns:
        base64 encoded string, returns None if conversion fails
    """
    if image is None:
        return None
        
    try:
        # Resize image if too large to reduce transmission time
        h, w = image.shape[:2]
        if w > max_width:
            scale = max_width / w
            new_w = max_width
            new_h = int(h * scale)
            # Use higher quality interpolation for better results on high-DPI displays
            interpolation = cv2.INTER_LANCZOS4 if not is_mobile else cv2.INTER_AREA
            image = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
        
        # Convert BGR to RGB for proper web display
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        # Use PIL for proper RGB JPEG encoding with lower quality for speed
        pil_image = Image.fromarray(image_rgb)
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        jpg_as_text = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{jpg_as_text}"
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        return None



def validate_image(image: np.ndarray) -> bool:
    """
    Validate if image is valid
    
    Args:
        image: Image to validate
    
    Returns:
        Whether the image is valid
    """
    if image is None:
        return False
    
    if not isinstance(image, np.ndarray):
        return False
    
    if len(image.shape) < 2 or len(image.shape) > 3:
        return False
    
    if image.size == 0:
        return False
    
    return True

class PerformanceMonitor:
    """Monitor performance metrics for web transmission"""
    def __init__(self):
        self.frame_times = []
        self.encode_times = []
        self.max_samples = 30  # Keep last 30 samples
        
    def record_frame_time(self, frame_time: float):
        """Record frame processing time"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)
    
    def record_encode_time(self, encode_time: float):
        """Record encoding time"""
        self.encode_times.append(encode_time)
        if len(self.encode_times) > self.max_samples:
            self.encode_times.pop(0)
    
    def get_avg_frame_time(self) -> float:
        """Get average frame time in ms"""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) * 1000 / len(self.frame_times)
    
    def get_avg_encode_time(self) -> float:
        """Get average encode time in ms"""
        if not self.encode_times:
            return 0.0
        return sum(self.encode_times) * 1000 / len(self.encode_times)
    
    def get_fps(self) -> float:
        """Get estimated FPS"""
        avg_time = self.get_avg_frame_time() / 1000.0
        if avg_time <= 0:
            return 0.0
        return 1.0 / avg_time 