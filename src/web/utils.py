'''
Web Debug Utilities
Image processing utilities for web debug server
'''
import cv2
import numpy as np
import base64
from typing import Optional, Tuple

def image_to_base64(image: np.ndarray, quality: int = 85) -> Optional[str]:
    """
    Convert OpenCV image to base64 string
    
    Args:
        image: OpenCV image array
        quality: JPEG compression quality (1-100)
    
    Returns:
        base64 encoded string, returns None if conversion fails
    """
    if image is None:
        return None
        
    try:
        # Ensure image is in BGR format (OpenCV default)
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert to RGB for web display
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', image_rgb, [cv2.IMWRITE_JPEG_QUALITY, quality])
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
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