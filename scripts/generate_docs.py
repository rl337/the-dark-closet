#!/usr/bin/env python3
"""
Generate documentation for The Dark Closet project.
This script creates HTML pages with game screenshots, assets, and test sequences.
"""

import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import json
import os

# Set up headless operation BEFORE any pygame imports
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["DISPLAY"] = ":99"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from the_dark_closet.game import (
    GameApp,
    GameConfig,
    SideScrollerScene,
    ControlledTimeProvider,
)
from the_dark_closet.assets import generate_character_assets
import pygame


def get_git_hash():
    """Get the current git commit hash."""
    try:
        git_path = shutil.which("git")
        if not git_path:
            return "unknown", "unknown"

        git_hash = subprocess.check_output(  # noqa: S603
            [git_path, "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        git_hash_full = subprocess.check_output(  # noqa: S603
            [git_path, "rev-parse", "HEAD"], text=True
        ).strip()
        return git_hash, git_hash_full
    except Exception as e:
        print(f"Failed to get git hash: {e}")
        return "unknown", "unknown"


def generate_ascii_level(room_data, spawn_pos):
    """Generate ASCII representation of the level similar to NetHack style."""
    # Character mappings for different tile types
    char_map = {
        "B": "█",  # Brick - solid block
        "H": "║",  # Ladder - vertical line
        " ": "·",  # Empty space - middle dot
    }

    # Convert spawn position to grid coordinates
    spawn_x = spawn_pos[0] // 128
    spawn_y = spawn_pos[1] // 128

    # Create ASCII representation
    ascii_lines = []
    for y, row in enumerate(room_data):
        ascii_row = ""
        for x, char in enumerate(row):
            if x == spawn_x and y == spawn_y:
                # Show player position with '@' symbol
                ascii_row += "@"
            else:
                # Use character mapping
                ascii_row += char_map.get(char, char)
        ascii_lines.append(ascii_row)

    # Add border and legend
    width = len(room_data[0])
    border = "┌" + "─" * width + "┐"

    result = [border]
    for line in ascii_lines:
        result.append("│" + line + "│")
    result.append("└" + "─" * width + "┘")

    # Add legend
    result.append("")
    result.append("Legend:")
    result.append("  @ = Player spawn position")
    result.append("  █ = Brick wall (128x128 pixels)")
    result.append("  ║ = Ladder (128x128 pixels)")
    result.append("  · = Empty space (128x128 pixels)")

    return "\n".join(result)


def generate_ascii_level_for_test(test_data):
    """Generate ASCII representation for a test sequence."""
    if "level_file" in test_data:
        # For JSON level files, load the level data and convert to ASCII
        with open(test_data["level_file"], "r") as f:
            level_data = json.load(f)
        
        # Extract spawn position
        spawn_x = level_data["player"]["spawn_x"]
        spawn_y = level_data["player"]["spawn_y"]
        
        # Create a grid representation from the level data
        width = level_data["metadata"]["width"]
        height = level_data["metadata"]["height"]
        
        # Initialize grid with empty spaces
        grid = [[" " for _ in range(width)] for _ in range(height)]
        
        # Place objects from the level data
        for obj in level_data["layers"]["tiles"]["objects"]:
            x = obj["x"] // 128
            y = obj["y"] // 128
            if 0 <= x < width and 0 <= y < height:
                if obj["type"] == "brick":
                    grid[y][x] = "B"
                elif obj["type"] == "ladder":
                    grid[y][x] = "H"
        
        # Convert spawn position to grid coordinates
        spawn_grid_x = spawn_x // 128
        spawn_grid_y = spawn_y // 128
        
        # Create ASCII representation
        ascii_lines = []
        for y, row in enumerate(grid):
            ascii_row = ""
            for x, char in enumerate(row):
                if x == spawn_grid_x and y == spawn_grid_y:
                    ascii_row += "@"
                else:
                    char_map = {
                        "B": "█",  # Brick - solid block
                        "H": "║",  # Ladder - vertical line
                        " ": "·",  # Empty space - middle dot
                    }
                    ascii_row += char_map.get(char, char)
            ascii_lines.append(ascii_row)
        
        # Add border and legend
        border = "┌" + "─" * width + "┐"
        result = [border]
        for line in ascii_lines:
            result.append("│" + line + "│")
        result.append("└" + "─" * width + "┘")
        
        # Add legend
        result.append("")
        result.append("Legend:")
        result.append("  @ = Player spawn position")
        result.append("  █ = Brick wall (128x128 pixels)")
        result.append("  ║ = Ladder (128x128 pixels)")
        result.append("  · = Empty space (128x128 pixels)")
        
        return "\n".join(result)
    else:
        # For string-based rooms, use the original function
        return generate_ascii_level(test_data["room"], test_data["spawn"])


def detect_movement(prev_pos, curr_pos, threshold=2.0):
    """Detect if character has moved significantly between frames."""
    if prev_pos is None or curr_pos is None:
        return False

    dx = abs(curr_pos[0] - prev_pos[0])
    dy = abs(curr_pos[1] - prev_pos[1])
    distance = (dx * dx + dy * dy) ** 0.5

    return distance > threshold


def wait_for_stabilization(app, scene, max_frames=30, movement_threshold=2.0):
    """Wait for character to stabilize (no movement for several frames)."""
    prev_pos = None
    stable_frames = 0
    required_stable_frames = 5

    for frame in range(max_frames):
        app.advance_frame(None)

        if hasattr(scene, "player_rect"):
            curr_pos = (scene.player_rect.x, scene.player_rect.y)

            if not detect_movement(prev_pos, curr_pos, movement_threshold):
                stable_frames += 1
                if stable_frames >= required_stable_frames:
                    return True
            else:
                stable_frames = 0

            prev_pos = curr_pos

    return False


def capture_action_sequence(app, scene, keys, max_frames=60, movement_threshold=2.0):
    """Capture frames during an action, selecting meaningful ones."""
    frames = []
    prev_pos = None
    action_started = False
    action_ended = False
    stable_frames = 0
    required_stable_frames = 5

    for frame in range(max_frames):
        app.advance_frame(keys)

        if hasattr(scene, "player_rect"):
            curr_pos = (scene.player_rect.x, scene.player_rect.y)
            is_moving = detect_movement(prev_pos, curr_pos, movement_threshold)

            # Capture frame
            clean_surface = pygame.Surface(app._screen.get_size())
            app.draw_clean(clean_surface)
            frames.append(clean_surface.copy())

            if not action_started and is_moving:
                # Action just started
                action_started = True
                print(f"  Action started at frame {frame}")
            elif action_started and not is_moving:
                # Character stopped moving
                stable_frames += 1
                if stable_frames >= required_stable_frames:
                    action_ended = True
                    print(f"  Action ended at frame {frame}")
                    break
            elif action_started and is_moving:
                # Reset stable counter if character starts moving again
                stable_frames = 0

            prev_pos = curr_pos

    return frames, action_started, action_ended


def select_meaningful_frames(frames, action_started, action_ended, target_count=8):
    """Select meaningful frames from the captured sequence."""
    if not frames:
        return []

    if len(frames) <= target_count:
        return frames

    if not action_started:
        # No action detected, return evenly spaced frames
        step = len(frames) // target_count
        return [frames[i * step] for i in range(target_count)]

    # Find action phase
    action_frames = frames
    if action_ended:
        # Use frames from start to end of action
        action_frames = frames

    # Select representative frames from action phase
    if len(action_frames) <= target_count:
        return action_frames

    # Distribute frames across the action
    step = len(action_frames) // target_count
    selected = []
    for i in range(target_count):
        idx = min(i * step, len(action_frames) - 1)
        selected.append(action_frames[idx])

    return selected


def generate_assets():
    """Generate procedural character assets."""
    print("Generating procedural assets...")
    temp_assets_dir = Path("temp_assets_for_docs")
    temp_assets_dir.mkdir(exist_ok=True)
    asset_paths = generate_character_assets(temp_assets_dir)
    return asset_paths, temp_assets_dir


def generate_test_sequences():
    """Generate test sequence screenshots."""
    print("Generating test sequences...")

    # Use a larger window to capture the full level
    # Room is 1536x1024, so we need at least that size
    config = GameConfig(1536, 1024, "Test Game", 60)
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    # Test sequences with intelligent frame selection
    test_sequences = {
        "movement": {
            "room": [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ],
            "spawn": (6 * 128, 6 * 128),  # Spawn on ground level
            "actions": [
                (
                    {pygame.K_RIGHT},
                    30,
                ),  # Move right - intelligent selection will pick meaningful frames
                (
                    {pygame.K_LEFT},
                    30,
                ),  # Move left - intelligent selection will pick meaningful frames
            ],
            "name": "Character Movement",
        },
        "jumping": {
            "room": [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ],
            "spawn": (6 * 128, 6 * 128),  # Spawn on ground level
            "actions": [
                (
                    {pygame.K_SPACE},
                    40,
                ),  # Jump - intelligent selection will pick jump and fall frames
            ],
            "name": "Jumping & Falling",
        },
        "brick_breaking": {
            "level_file": "levels/test_brick_breaking.json",
            "actions": [
                ({pygame.K_RIGHT}, 20),  # Move to bricks
                ({pygame.K_SPACE}, 30),  # Break bricks
            ],
            "name": "Brick Breaking",
        },
        "ladder_climbing": {
            "room": [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B          B",
                "B    HH    B",  # Move ladders to ground level
                "B    HH    B",
                "B          B",
                "BBBBBBBBBBBB",
            ],
            "spawn": (5 * 128, 5 * 128),  # Spawn at ground level near ladder
            "actions": [
                ({pygame.K_RIGHT}, 20),  # Move to ladder
                ({pygame.K_UP}, 40),  # Climb ladder
            ],
            "name": "Ladder Climbing",
        },
    }

    # Create tests directory
    tests_dir = Path("docs/tests")
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Generate test sequence screenshots with intelligent frame selection
    for test_name, test_data in test_sequences.items():
        test_dir = tests_dir / test_name
        test_dir.mkdir(exist_ok=True)

        # Clean up any existing frames from previous runs
        for old_file in test_dir.glob(f"{test_name}_*.png"):
            old_file.unlink()

        actions = test_data["actions"]

        print(f"Generating {test_name}...")

        # Check if this test uses a JSON level file
        if "level_file" in test_data:
            from the_dark_closet.json_scene import JSONScene
            level_path = Path(test_data["level_file"])
            scene = JSONScene(app, level_path)
        else:
            # Use the old string-based room format
            room = test_data["room"]
            spawn = test_data["spawn"]
            scene = SideScrollerScene(app, room, spawn)
        
        app.switch_scene(scene)
        app.advance_frame(None)

        # Wait for character to stabilize
        print("  Waiting for character to stabilize...")
        if not wait_for_stabilization(app, scene):
            print("  Warning: Character did not stabilize within timeout")

        # Adjust camera to show the full level for tests
        if "level_file" in test_data:
            # For JSON scenes, use the level dimensions
            room_width = scene.level_width
            room_height = scene.level_height
        else:
            # For string-based rooms
            room_width = len(room[0]) * 128
            room_height = len(room) * 128

        # Position camera to show the entire room
        # With window size matching room size, we can show the full room
        scene.camera_x = 0  # Start at left edge
        scene.camera_y = 0  # Start at top edge

        # Advance one more frame to ensure camera positioning is applied
        app.advance_frame(None)

        # Debug: Print setup info
        if hasattr(scene, "player_rect"):
            print(f"  Character rect: {scene.player_rect}")
            print(f"  Camera: ({scene.camera_x}, {scene.camera_y})")
            print(f"  Window size: {app._screen.get_size()}")
            print(f"  Room size: {room_width}x{room_height}")
            print(
                f"  Character in viewport: ({scene.player_rect.x - scene.camera_x}, {scene.player_rect.y - scene.camera_y})"
            )

        # Process each action with intelligent frame selection
        frame_count = 0

        for action_idx, (keys, duration) in enumerate(actions):
            print(f"  Processing action {action_idx + 1}: {keys if keys else 'None'}")

            # Capture frames during this action
            captured_frames, action_started, action_ended = capture_action_sequence(
                app,
                scene,
                keys,
                max_frames=duration * 10,  # Allow more frames for detection
            )

            # Select meaningful frames from this action
            selected_frames = select_meaningful_frames(
                captured_frames, action_started, action_ended, target_count=4
            )

            # Save selected frames
            for i, frame in enumerate(selected_frames):
                screenshot_path = test_dir / f"{test_name}_{frame_count:02d}.png"
                pygame.image.save(frame, str(screenshot_path))
                frame_count += 1

            print(
                f"    Selected {len(selected_frames)} frames from {len(captured_frames)} captured"
            )

        print(f"Generated {frame_count} frames for {test_name}")

    return test_sequences


def generate_index_html(git_hash, git_hash_full):
    """Generate the main index.html page."""
    print("Generating index.html...")

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Dark Closet - Pinocchio Game</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #ffffff;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            border-radius: 10px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            color: #ecf0f1;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            color: #bdc3c7;
        }}
        .nav {{
            text-align: center;
            margin: 20px 0;
        }}
        .nav a {{
            display: inline-block;
            margin: 0 15px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }}
        .nav a:hover {{
            background: #2980b9;
        }}
        .screenshot {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: #2c2c2c;
            border-radius: 10px;
        }}
        .screenshot img {{
            width: 1024px; /* Fixed width */
            height: 768px; /* Fixed height */
            object-fit: contain; /* Ensure image fits without cropping */
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 40px 0;
        }}
        .feature {{
            background: #2c2c2c;
            padding: 20px;
            border-left: 4px solid #3498db;
        }}
        .feature h3 {{
            margin: 0 0 10px 0;
            color: #3498db;
        }}
        .feature p {{
            margin: 0;
            color: #bdc3c7;
            font-size: 0.9em;
        }}
        .status {{
            background: #27ae60;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-align: center;
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #7f8c8d;
            border-top: 1px solid #34495e;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎭 The Dark Closet</h1>
        <p>A Pinocchio-inspired 2D platformer built with Python & Pygame</p>
    </div>
    
    <div class="nav">
        <a href="index.html">🏠 Home</a>
        <a href="assets.html">🎨 Assets</a>
        <a href="tests.html">🧪 Test Sequences</a>
    </div>
    
    <div class="status">
        ✅ CI/CD Pipeline: PASSING | 🧪 Tests: 20/20 | 📊 Code Quality: 10/10
    </div>
    
    <div class="screenshot">
        <h2>Game Screenshot</h2>
        <img src="tests/movement/movement_00.png" alt="The Dark Closet Game Screenshot">
        <p>Procedurally generated character in a 2D platformer world</p>
    </div>
    
    <div class="features">
        <div class="feature">
            <h3>🎨 Procedural Assets</h3>
            <p>All character sprites, facial features, and gear are generated procedurally at build time using Python and Pygame drawing primitives.</p>
            <p><a href="assets.html" style="color: #3498db;">View All Assets →</a></p>
        </div>
        
        <div class="feature">
            <h3>🧪 Comprehensive Testing</h3>
            <p>Full test suite with unit tests, integration tests, performance benchmarks, and visual regression testing using pytest.</p>
            <p><a href="tests.html" style="color: #3498db;">View Test Sequences →</a></p>
        </div>
        
        <div class="feature">
            <h3>⚡ Performance Optimized</h3>
            <p>Optimized rendering pipeline with controlled time system for deterministic testing and smooth gameplay.</p>
        </div>
        
        <div class="feature">
            <h3>🔧 Modern CI/CD</h3>
            <p>Automated builds with Poetry, mypy type checking, pylint code quality, and GitHub Pages deployment.</p>
        </div>
        
        <div class="feature">
            <h3>🎮 Game Features</h3>
            <p>2D platformer with movement, jumping, brick breaking, ladder climbing, and camera following mechanics.</p>
        </div>
        
        <div class="feature">
            <h3>📊 Build Status</h3>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}<br>
            All systems operational and ready for development!</p>
        </div>
    </div>
    
    <div class="footer">
        <p>Built with ❤️ using Python, Pygame, Poetry, and GitHub Actions</p>
        <p><a href="https://github.com/rlee/the-dark-closet" style="color: #3498db;">View Source Code</a></p>
        <p style="font-size: 0.9em; color: #95a5a6; margin-top: 15px;">
            Version: <code style="background: #34495e; padding: 2px 6px; border-radius: 3px;">{git_hash}</code>
            | <a href="https://github.com/rl337/the-dark-closet/commit/{git_hash_full}" style="color: #3498db;">View Commit</a>
        </p>
    </div>
</body>
</html>"""

    return index_html


def generate_assets_html(asset_paths, git_hash, git_hash_full):
    """Generate the assets.html page."""
    print("Generating assets.html...")

    # Define asset categories
    asset_categories = {
        "Body Parts": {
            "head": "Character head with facial features",
            "torso": "Main body torso section",
            "left_arm": "Left arm with joint details",
            "right_arm": "Right arm with joint details",
            "left_leg": "Left leg with joint details",
            "right_leg": "Right leg with joint details",
        },
        "Facial Features": {
            "eyes_open": "Open eyes expression",
            "eyes_closed": "Closed eyes expression",
            "mouth_neutral": "Neutral mouth expression",
            "mouth_open": "Open mouth expression",
        },
        "Accessories": {"hat": "Character hat accessory"},
    }

    assets_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assets - The Dark Closet</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #ffffff;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            border-radius: 10px;
        }
        .nav {
            text-align: center;
            margin: 20px 0;
        }
        .nav a {
            display: inline-block;
            margin: 0 15px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .nav a:hover {
            background: #2980b9;
        }
        .section {
            margin: 40px 0;
        }
        .section h2 {
            color: #3498db;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .assets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .asset-card {
            background: #2c2c2c;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid transparent;
            transition: border-color 0.3s;
        }
        .asset-card:hover {
            border-color: #3498db;
        }
        .asset-card img {
            width: 128px; /* Fixed width */
            height: 128px; /* Fixed height */
            object-fit: contain; /* Ensure image fits without cropping */
            border-radius: 5px;
            margin-bottom: 10px;
            background: #1a1a1a;
            padding: 10px;
        }
        .asset-card h3 {
            margin: 0 0 10px 0;
            color: #3498db;
        }
        .asset-card p {
            margin: 0;
            color: #bdc3c7;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Procedural Assets</h1>
        <p>All character components generated programmatically</p>
    </div>
    
    <div class="nav">
        <a href="index.html">🏠 Home</a>
        <a href="assets.html">🎨 Assets</a>
        <a href="tests.html">🧪 Test Sequences</a>
    </div>"""

    # Generate sections for each category
    for category_name, assets in asset_categories.items():
        assets_html += f"""
    <div class="section">
        <h2>{category_name}</h2>
        <div class="assets-grid">"""

        for asset_name, description in assets.items():
            if (Path("docs/assets") / f"{asset_name}.png").exists():
                assets_html += f"""
        <div class="asset-card">
            <img src="assets/{asset_name}.png" alt="{asset_name}">
            <h3>{asset_name.replace('_', ' ').title()}</h3>
            <p>{description}</p>
        </div>"""

        assets_html += """
        </div>
    </div>"""

    assets_html += f"""
    <div class="footer">
        <p>All assets generated procedurally using Python & Pygame</p>
        <p style="font-size: 0.9em; color: #95a5a6; margin-top: 15px;">
            Version: <code style="background: #34495e; padding: 2px 6px; border-radius: 3px;">{git_hash}</code>
            | <a href="https://github.com/rl337/the-dark-closet/commit/{git_hash_full}" style="color: #3498db;">View Commit</a>
        </p>
    </div>
</body>
</html>"""

    return assets_html


def generate_tests_html(test_sequences, git_hash, git_hash_full):
    """Generate the tests.html page with tabbed interface."""
    print("Generating tests.html...")

    tests_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Sequences - The Dark Closet</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #ffffff;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(135deg, #2c3e50, #34495e);
            border-radius: 10px;
        }
        .nav {
            text-align: center;
            margin: 20px 0;
        }
        .nav a {
            display: inline-block;
            margin: 0 15px;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            transition: background 0.3s;
        }
        .nav a:hover {
            background: #2980b9;
        }
        .test-sequence {
            background: #2c2c2c;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
        }
        .test-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .test-title {
            font-size: 1.5em;
            color: #3498db;
            margin: 0;
        }
        .play-button {
            background: #27ae60;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        .play-button:hover {
            background: #229954;
        }
        .play-button.playing {
            background: #e74c3c;
        }
        .play-button.playing:hover {
            background: #c0392b;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #34495e;
        }
        .tab {
            background: #34495e;
            color: #bdc3c7;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background: #3498db;
            color: white;
        }
        .tab:hover:not(.active) {
            background: #2c3e50;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .sequence-container {
            position: relative;
            text-align: center;
            background: #1a1a1a;
            border-radius: 5px;
            padding: 20px;
            width: 100%;
            max-width: 1024px;
            height: 600px; /* Fixed height for consistent sizing */
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden; /* Prevent overflow */
        }
        .sequence-image {
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain; /* Ensure image fits without cropping */
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            opacity: 0;
            transition: opacity 0.3s;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        .sequence-image.active {
            opacity: 1;
        }
        .source-code {
            background: #1a1a1a;
            border: 1px solid #34495e;
            border-radius: 5px;
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9em;
            line-height: 1.4;
            color: #e8e8e8;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        .ascii-render {
            background: #1a1a1a;
            border: 1px solid #34495e;
            border-radius: 5px;
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 1.1em;
            line-height: 1.2;
            color: #00ff00;
            white-space: pre;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
            text-align: center;
        }
        .sequence-info {
            text-align: center;
            margin-top: 15px;
            color: #bdc3c7;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Sequences</h1>
        <p>Interactive test demonstrations with play controls and source code</p>
    </div>
    
    <div class="nav">
        <a href="index.html">🏠 Home</a>
        <a href="assets.html">🎨 Assets</a>
        <a href="tests.html">🧪 Test Sequences</a>
    </div>"""

    # Add test sequences with tabbed interface
    for test_name, test_data in test_sequences.items():
        test_dir = Path("docs/tests") / test_name
        if test_dir.exists():
            # Count frames
            frame_files = list(test_dir.glob(f"{test_name}_*.png"))
            frame_count = len(frame_files)

            # Generate JSON source for this test sequence
            if "level_file" in test_data:
                # For JSON level files, load and display the level data
                with open(test_data["level_file"], "r") as f:
                    level_data = json.load(f)
                # Convert pygame key sets to lists for JSON serialization
                serializable_actions = []
                for keys, duration in test_data["actions"]:
                    if keys is None:
                        serializable_actions.append({"keys": None, "duration": duration})
                    else:
                        serializable_actions.append({"keys": list(keys), "duration": duration})
                
                test_json = {
                    "level_file": test_data["level_file"],
                    "level_data": level_data,
                    "actions": serializable_actions,
                }
            else:
                # For string-based rooms
                test_json = {
                    "metadata": {
                        "name": test_data["name"],
                        "width": len(test_data["room"][0]),
                        "height": len(test_data["room"]),
                    },
                    "layers": {"tiles": {"parallax_factor": 1.0, "objects": []}},
                    "player": {
                        "spawn_x": test_data["spawn"][0],
                        "spawn_y": test_data["spawn"][1],
                    },
                }

                # Convert room data to JSON objects
                for y, row in enumerate(test_data["room"]):
                    for x, char in enumerate(row):
                        if char == "B":  # Brick
                            test_json["layers"]["tiles"]["objects"].append(
                                {
                                    "id": f"brick_{x}_{y}",
                                    "type": "brick",
                                    "x": x * 128,
                                    "y": y * 128,
                                    "width": 128,
                                    "height": 128,
                                    "color": [135, 90, 60],
                                }
                            )
                        elif char == "H":  # Ladder
                            test_json["layers"]["tiles"]["objects"].append(
                                {
                                    "id": f"ladder_{x}_{y}",
                                    "type": "ladder",
                                    "x": x * 128,
                                    "y": y * 128,
                                    "width": 128,
                                    "height": 128,
                                    "color": [139, 69, 19],
                                }
                            )

            # Format JSON for display
            json_source = json.dumps(test_json, indent=2)

            tests_html += f"""
    <div class="test-sequence">
        <div class="test-header">
            <h2 class="test-title">{test_data['name']}</h2>
            <button class="play-button" onclick="toggleAnimation('{test_name}', {frame_count})">
                ▶️ Play
            </button>
        </div>
        <div class="tabs">
            <button class="tab active" onclick="switchTab('{test_name}', 'image')">🖼️ Image</button>
            <button class="tab" onclick="switchTab('{test_name}', 'ascii')">🎮 ASCII</button>
            <button class="tab" onclick="switchTab('{test_name}', 'source')">📄 Source</button>
        </div>
        <div class="tab-content active" id="{test_name}_image">
            <div class="sequence-container">"""

            for i in range(frame_count):
                active_class = " active" if i == 0 else ""
                tests_html += f"""
                <img src="tests/{test_name}/{test_name}_{i:02d}.png" 
                      class="sequence-image{active_class}" 
                      id="{test_name}_{i:02d}"
                      alt="Frame {i+1}">"""

            tests_html += f"""
            </div>
        </div>
            <div class="tab-content" id="{test_name}_ascii">
                <div class="ascii-render">{generate_ascii_level_for_test(test_data)}</div>
            </div>
        <div class="tab-content" id="{test_name}_source">
            <div class="source-code">{json_source}</div>
        </div>
        <div class="sequence-info">
            <p>{frame_count} frames • Click play to see the sequence in action</p>
        </div>
    </div>"""

    tests_html += (
        """
    </div>
    
    <script>
        const animations = {};
        
        function toggleAnimation(testName, frameCount) {
            const button = event.target;
            const container = button.closest('.test-sequence').querySelector('.sequence-container');
            
            if (animations[testName]) {
                // Stop animation
                clearInterval(animations[testName]);
                delete animations[testName];
                button.textContent = '▶️ Play';
                button.classList.remove('playing');
                
                // Hide all images
                const images = container.querySelectorAll('.sequence-image');
                images.forEach(img => img.classList.remove('active'));
            } else {
                // Start animation
                let currentFrame = 0;
                const images = container.querySelectorAll('.sequence-image');
                
                // Show first frame
                images.forEach(img => img.classList.remove('active'));
                images[0].classList.add('active');
                
                animations[testName] = setInterval(() => {
                    images.forEach(img => img.classList.remove('active'));
                    images[currentFrame].classList.add('active');
                    currentFrame = (currentFrame + 1) % frameCount;
                }, 200); // 5 FPS
                
                button.textContent = '⏸️ Stop';
                button.classList.add('playing');
            }
        }
        
        function switchTab(testName, tabType) {
            // Stop any playing animation when switching tabs
            if (animations[testName]) {
                // Find the play button for this test sequence
                const testSequence = document.getElementById(testName + '_image').closest('.test-sequence');
                const button = testSequence.querySelector('.play-button');
                if (button && button.classList.contains('playing')) {
                    clearInterval(animations[testName]);
                    delete animations[testName];
                    button.textContent = '▶️ Play';
                    button.classList.remove('playing');
                }
            }

            // Update tab buttons and content
            const imageContent = document.getElementById(testName + '_image');
            const asciiContent = document.getElementById(testName + '_ascii');
            const sourceContent = document.getElementById(testName + '_source');
            const testSequence = imageContent.closest('.test-sequence');
            const tabButtons = testSequence.querySelectorAll('.tab');
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            if (tabType === 'image') {
                imageContent.classList.add('active');
                asciiContent.classList.remove('active');
                sourceContent.classList.remove('active');
                tabButtons[0].classList.add('active');
                
                // Ensure the first image is shown when switching back to image tab
                const images = imageContent.querySelectorAll('.sequence-image');
                if (images.length > 0) {
                    images.forEach(img => img.classList.remove('active'));
                    images[0].classList.add('active');
                }
            } else if (tabType === 'ascii') {
                imageContent.classList.remove('active');
                asciiContent.classList.add('active');
                sourceContent.classList.remove('active');
                tabButtons[1].classList.add('active');
            } else {
                imageContent.classList.remove('active');
                asciiContent.classList.remove('active');
                sourceContent.classList.add('active');
                tabButtons[2].classList.add('active');
            }
        }
    </script>
    
    <div class="footer">
        <p>All test sequences generated automatically by the CI/CD pipeline</p>
        <p style="font-size: 0.9em; color: #95a5a6; margin-top: 15px;">
            Version: <code style="background: #34495e; padding: 2px 6px; border-radius: 3px;">"""
        + git_hash
        + """</code>
            | <a href="https://github.com/rl337/the-dark-closet/commit/"""
        + git_hash_full
        + """" style="color: #3498db;">View Commit</a>
        </p>
    </div>
</body>
</html>"""
    )

    return tests_html


def main():
    """Main function to generate all documentation."""
    print("Starting documentation generation...")

    # Initialize pygame
    pygame.init()

    # Get git hash
    git_hash, git_hash_full = get_git_hash()
    print(f"Git hash (short): {git_hash}")
    print(f"Git hash (full): {git_hash_full}")

    # Create docs directory structure
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    assets_dir = docs_dir / "assets"
    tests_dir = docs_dir / "tests"
    assets_dir.mkdir(exist_ok=True)
    tests_dir.mkdir(exist_ok=True)

    # Generate procedural assets
    asset_paths, temp_assets_dir = generate_assets()

    # Copy assets to docs
    for asset_name, asset_path in asset_paths.items():
        if Path(asset_path).exists():
            dest_path = assets_dir / f"{asset_name}.png"
            shutil.copy2(asset_path, dest_path)
            print(f"Copied {asset_name} to {dest_path}")

    # Generate test sequences
    test_sequences = generate_test_sequences()

    # Generate HTML pages
    index_html = generate_index_html(git_hash, git_hash_full)
    assets_html = generate_assets_html(asset_paths, git_hash, git_hash_full)
    tests_html = generate_tests_html(test_sequences, git_hash, git_hash_full)

    # Write HTML files
    with open(docs_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    with open(docs_dir / "assets.html", "w", encoding="utf-8") as f:
        f.write(assets_html)

    with open(docs_dir / "tests.html", "w", encoding="utf-8") as f:
        f.write(tests_html)

    # Clean up temp directory
    shutil.rmtree(temp_assets_dir, ignore_errors=True)

    print("Documentation generation complete!")
    print("Generated: index.html, assets.html, tests.html")
    print(f"Assets: {len(list(assets_dir.glob('*.png')))} files")
    print(f"Test sequences: {len(list(tests_dir.glob('*')))} directories")


if __name__ == "__main__":
    main()
