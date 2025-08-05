# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MapleStoryAutoLevelUp is a computer vision-based auto-leveling bot for MapleStory Artale. The bot uses pure computer vision techniques to detect game elements (player position, monsters, UI elements) and simulates keyboard inputs to control the character.

## Key Development Commands

### Setup and Installation
```bash
# Create virtual environment and install dependencies
make setup

# Manual setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application
```bash
# Run with UI only (default)
python -m src.main
# or
make run

# Run with Web interface only
python -m src.main --mode web --web-port 5000

# Run both UI and Web interface (coexistence mode)
python -m src.main --mode both --web-port 5000 --web-host 0.0.0.0

# Legacy engine-only mode (without UI)
python -m src.engine.MapleStoryAutoLevelUp

# Run with custom config
python -m src.engine.MapleStoryAutoLevelUp --cfg my_config

# Run with web debug viewer (legacy)
python -m src.engine.MapleStoryAutoLevelUp --cfg web_debug
# Then open http://localhost:5001 in browser
```

### Building
```bash
# Build executable (Windows)
./build.bat

# The build uses PyInstaller to create a single executable
```

### Testing and Development
```bash
# Run with disabled controls (for testing)
python -m src.engine.MapleStoryAutoLevelUp --disable_control

# Run with debug logging
python -m src.engine.MapleStoryAutoLevelUp --debug

# Record debug session
python -m src.engine.MapleStoryAutoLevelUp --record
```

### Tools
```bash
# Route recorder for creating new maps
python -m tools.routeRecorder --new_map <map_directory_name>

# Auto dice roller for character creation
python -m tools.AutoDiceRoller --attribute 4,4,13,4

# Monster image downloader
python tools/mob_maker.py
```

## Architecture Overview

### Core Components

**Main Entry Points:**
- `src/main.py` - GUI application entry point using PySide6
- `src/engine/MapleStoryAutoLevelUp.py` - Core bot engine and command-line interface

**State Machine Architecture:**
The bot uses a finite state machine (`src/engine/FiniteStateMachine.py`) with these states:
- `hunting` - Normal combat and movement
- `finding_rune` - Searching for runes when detected
- `near_rune` - Close to rune, preparing to interact
- `solving_rune` - Active rune mini-game solving
- `auxiliary` - Special auxiliary mode
- `patrol` - Simple patrol mode without minimap

**Computer Vision Pipeline:**
1. **Game Window Capture** (`src/input/GameWindowCapturor.py`) - Captures game screen
2. **Player Location Detection** - Uses nametag or party red bar detection
3. **Minimap Processing** - Extracts minimap for global positioning
4. **Monster Detection** - Template matching with multiple modes (color, grayscale, contour-only, template_free)
5. **Route Following** - Color-coded pixel navigation system

**Key Systems:**
- **Health Monitor** (`src/engine/HealthMonitor.py`) - Auto HP/MP potion usage
- **Rune Solver** (`src/engine/RuneSolver.py`) - Automatic rune mini-game solving
- **Alert System** (`src/engine/Alert.py`) - Sound notifications
- **Web Interface** (`src/web_interface/`) - Remote control via web browser
- **Legacy Web Debug Server** (`src/web/`) - Real-time remote monitoring via web interface

### Configuration System

Configuration is layered and hierarchical:
1. `config/config_default.yaml` - Base configuration
2. `config/config_macOS.yaml` - Platform-specific overrides
3. `config/config_custom.yaml` - User customizations
4. `config/config_data.yaml` - Map and monster data

### Asset Organization

**Maps and Routes:**
- `minimaps/` - Map images and route files for navigation
- `maps/` - Legacy full-size maps (deprecated)
- Route files use color-coded pixels for navigation commands

**Monster Detection:**
- `monster/` - Monster template images organized by monster type
- Each monster has multiple animation frames and flipped versions

**UI Assets:**
- `misc/` - UI button templates for different languages
- `rune/` - Rune and arrow detection templates
- `nametag/` - Player nametag templates

## Development Guidelines

### Adding New Maps
1. Use `tools/routeRecorder.py` to record player movement
2. Create map.png and route*.png files in `minimaps/<map_name>/`
3. Register monsters in `config/config_data.yaml`
4. Test with `--cfg custom` configuration

### Monster Detection Modes
- `color` - Most accurate, slowest (full color template matching)
- `grayscale` - Moderate speed and accuracy
- `contour_only` - Fast, good balance (recommended)
- `template_free` - Fastest, detects black pixels as monsters

### Configuration Tips
- Modify `config/config_custom.yaml` for personal settings
- Use web debug mode for real-time monitoring during development
- Enable profiler in config for performance debugging
- Test different monster detection modes for optimal performance

### Multi-Platform Support
- Windows: Full feature support
- macOS: Supported with platform-specific adaptations in `GameWindowCapturorForMac.py`
- The bot automatically detects platform and applies appropriate configurations

### Web Interface Features

The new web interface provides remote control capabilities:

**Startup Modes:**
- `--mode ui` - Traditional PySide6 desktop interface only
- `--mode web` - Web-based interface only (headless)
- `--mode both` - Both UI and web interface running simultaneously

**Web Interface Components:**
- `src/web_interface/server.py` - FastAPI server with REST API and WebSocket
- `src/web_interface/static/` - Frontend HTML/CSS/JavaScript
- Bot control: Start/pause, screenshot, recording
- Real-time status updates via WebSocket
- Responsive design for mobile and desktop access

**API Endpoints:**
- `GET /api/status` - Get current bot status
- `POST /api/start` - Start the bot
- `POST /api/pause` - Pause the bot
- `POST /api/screenshot` - Take screenshot
- `POST /api/record/start` - Start recording
- `POST /api/record/stop` - Stop recording
- `WS /ws` - WebSocket for real-time updates

**Configuration:**
- Web settings in `config/config_default.yaml` under `web_interface` section
- Configurable host, port, image quality, and auto-save settings
- Coexists with existing UI configuration system

**Network Access:**
- Local access: `http://localhost:5000`
- LAN access: `http://192.168.1.x:5000` (when using `--web-host 0.0.0.0`)
- Single-user operation (no multi-user concurrency control yet)

## Important Notes

- This project is for recreational and educational use only
- Does not access game memory - uses pure computer vision
- Requires windowed mode with smallest resolution for optimal detection
- Character must be in a party (shows red health bar) for player detection
- Rune solving is automatic when runes appear
- Bot includes anti-stuck mechanisms and channel changing features
- Web interface coexists with UI - both can control the same bot instance
- Real-time image streaming will be added in Phase 2 of web development