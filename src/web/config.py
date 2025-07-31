'''
Web Debug Configuration
'''

# 默认Web服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5001

# 图像压缩配置
JPEG_QUALITY = 85  # JPEG压缩质量 (1-100)

# WebSocket配置
CORS_ALLOWED_ORIGINS = "*"  # 允许的跨域来源

# 模板配置
TEMPLATE_FOLDER = "templates"  # 模板文件夹名称

# 调试配置
DEBUG_MODE = False  # Flask调试模式 