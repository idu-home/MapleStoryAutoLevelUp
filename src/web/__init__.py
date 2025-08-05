'''
Web Debug Module for MapleStory Auto Bot
'''

from .server import WebDebugServer
from .config import *
from .utils import *

__all__ = [
    'WebDebugServer',
    'DEFAULT_HOST',
    'DEFAULT_PORT',
    'JPEG_QUALITY',
    'CORS_ALLOWED_ORIGINS',
    'TEMPLATE_FOLDER',
    'DEBUG_MODE',
    'image_to_base64',
    'validate_image'
] 