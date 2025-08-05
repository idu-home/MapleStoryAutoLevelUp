'''
Web Debug Configuration
'''

# Default Web server configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5001

# Image compression configuration
JPEG_QUALITY = 70  # JPEG compression quality (1-100) - reduced for better performance
JPEG_QUALITY_OPTIMIZED = 50  # Optimized mode compression quality
MAX_IMAGE_WIDTH = 1200  # Maximum image width, will be scaled if exceeded (increased to support high-resolution devices)
MAX_IMAGE_WIDTH_MOBILE = 800  # Maximum width for mobile devices

# WebSocket configuration
CORS_ALLOWED_ORIGINS = "*"  # Allowed cross-origin sources

# Template configuration
TEMPLATE_FOLDER = "templates"  # Template folder name

# Debug configuration
DEBUG_MODE = False  # Flask debug mode 