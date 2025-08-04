'''
Web Debug Configuration
'''

# 默认Web服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5001

# 图像压缩配置
JPEG_QUALITY = 70  # JPEG压缩质量 (1-100) - 降低以提高性能
JPEG_QUALITY_OPTIMIZED = 50  # 优化模式下的压缩质量
MAX_IMAGE_WIDTH = 1200  # 图像最大宽度，超过会被缩放 (提高以支持高分辨率设备)
MAX_IMAGE_WIDTH_MOBILE = 800  # 移动设备的最大宽度

# WebSocket配置
CORS_ALLOWED_ORIGINS = "*"  # 允许的跨域来源

# 模板配置
TEMPLATE_FOLDER = "templates"  # 模板文件夹名称

# 调试配置
DEBUG_MODE = False  # Flask调试模式 