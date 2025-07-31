'''
Web Debug Launcher
Standalone launcher for web debug server
'''
import sys
import os
import argparse
from typing import Optional

def add_src_to_path():
    """Add src directory to Python path"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

def launch_web_debug(host: str = "0.0.0.0", port: int = 5001, 
                    config_file: Optional[str] = None) -> None:
    """
    Launch Web debug server
    
    Args:
        host: Server address
        port: Server port
        config_file: Configuration file path
    """
    add_src_to_path()
    
    from .server import WebDebugServer
    
    print(f"🌐 Starting Web debug server...")
    print(f"📍 Address: {host}:{port}")
    if config_file:
        print(f"⚙️  Config file: {config_file}")
    
    # Create and start server
    server = WebDebugServer(host=host, port=port)
    server.start()
    
    print(f"✅ Web server started: {server.get_url()}")
    print("📱 Please open the URL in browser to view debug interface")
    print("🔄 Press Ctrl+C to stop server")
    
    try:
        # Keep server running
        while server.is_running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop()
        print("✅ Server stopped")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Web debug server launcher")
    parser.add_argument("--host", default="0.0.0.0", help="Server address")
    parser.add_argument("--port", type=int, default=5001, help="Server port")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    launch_web_debug(host=args.host, port=args.port, config_file=args.config)

if __name__ == "__main__":
    main() 