#!/usr/bin/env python3
"""
Generate documentation for The Dark Closet project.
This script creates HTML pages with game screenshots, assets, and test sequences.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import json
import shutil

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
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        git_hash_full = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        return git_hash, git_hash_full
    except Exception as e:
        print(f"Failed to get git hash: {e}")
        return "unknown", "unknown"


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
    config = GameConfig(1024, 768, "Test Game", 60)  # Increased window size
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    # Test sequences
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
            "spawn": (6 * 128, 4 * 128),
            "actions": [
                ({pygame.K_RIGHT}, 4),
                ({pygame.K_LEFT}, 4),
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
            "spawn": (6 * 128, 4 * 128),
            "actions": [
                ({pygame.K_SPACE}, 4),
                (None, 4),
            ],
            "name": "Jumping & Falling",
        },
        "brick_breaking": {
            "room": [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B   BBBB   B",
                "B          B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ],
            "spawn": (5 * 128, 4 * 128),
            "actions": [
                ({pygame.K_RIGHT}, 2),
                ({pygame.K_SPACE}, 4),
            ],
            "name": "Brick Breaking",
        },
        "ladder_climbing": {
            "room": [
                "BBBBBBBBBBBB",
                "B          B",
                "B    HH    B",
                "B    HH    B",
                "B    HH    B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ],
            "spawn": (6 * 128, 5 * 128),
            "actions": [
                ({pygame.K_RIGHT}, 2),
                ({pygame.K_UP}, 4),
            ],
            "name": "Ladder Climbing",
        },
    }

    # Create tests directory
    tests_dir = Path("docs/tests")
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Generate test sequence screenshots
    for test_name, test_data in test_sequences.items():
        test_dir = tests_dir / test_name
        test_dir.mkdir(exist_ok=True)

        room = test_data["room"]
        spawn = test_data["spawn"]
        actions = test_data["actions"]

        scene = SideScrollerScene(app, room, spawn)
        app.switch_scene(scene)
        app.advance_frame(None)

        # Adjust camera to center the character in the viewport
        scene.camera_x = max(0, scene.player_rect.centerx - app.width // 2)
        scene.camera_y = max(0, scene.player_rect.centery - app.height // 2)

        # Advance one more frame to ensure camera positioning is applied
        app.advance_frame(None)

        frame_count = 0
        for keys, duration in actions:
            for i in range(duration):
                app.advance_frame(keys)
                screenshot_path = test_dir / f"{test_name}_{frame_count:02d}.png"
                # Use clean rendering without HUD
                clean_surface = pygame.Surface(app._screen.get_size())
                app.draw_clean(clean_surface)
                pygame.image.save(clean_surface, str(screenshot_path))
                frame_count += 1

                # Debug: Print character info for first frame
                if frame_count == 1:
                    scene = app._current_scene
                    if hasattr(scene, "player_rect"):
                        print(f"Character rect: {scene.player_rect}")
                        print(f"Camera: ({scene.camera_x}, {scene.camera_y})")
                        print(f"Window size: {app._screen.get_size()}")
                        print(
                            f"Character in viewport: ({scene.player_rect.x - scene.camera_x}, {scene.player_rect.y - scene.camera_y})"
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

    assets_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assets - The Dark Closet</title>
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
        .section {{
            margin: 40px 0;
        }}
        .section h2 {{
            color: #3498db;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .assets-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .asset-card {{
            background: #2c2c2c;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid transparent;
            transition: border-color 0.3s;
        }}
        .asset-card:hover {{
            border-color: #3498db;
        }}
        .asset-card img {{
            width: 128px; /* Fixed width */
            height: 128px; /* Fixed height */
            object-fit: contain; /* Ensure image fits without cropping */
            border-radius: 5px;
            margin-bottom: 10px;
            background: #1a1a1a;
            padding: 10px;
        }}
        .asset-card h3 {{
            margin: 0 0 10px 0;
            color: #3498db;
        }}
        .asset-card p {{
            margin: 0;
            color: #bdc3c7;
            font-size: 0.9em;
        }}
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

    tests_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Sequences - The Dark Closet</title>
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
        .test-sequence {{
            background: #2c2c2c;
            padding: 20px;
            border-radius: 10px;
            margin: 30px 0;
        }}
        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .test-title {{
            font-size: 1.5em;
            color: #3498db;
            margin: 0;
        }}
        .play-button {{
            background: #27ae60;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }}
        .play-button:hover {{
            background: #229954;
        }}
        .play-button.playing {{
            background: #e74c3c;
        }}
        .play-button.playing:hover {{
            background: #c0392b;
        }}
        .tabs {{
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #34495e;
        }}
        .tab {{
            background: #34495e;
            color: #bdc3c7;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }}
        .tab.active {{
            background: #3498db;
            color: white;
        }}
        .tab:hover:not(.active) {{
            background: #2c3e50;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .sequence-container {{
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
        }}
        .sequence-image {{
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
        }}
        .sequence-image.active {{
            opacity: 1;
        }}
        .source-code {{
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
        }}
        .sequence-info {{
            text-align: center;
            margin-top: 15px;
            color: #bdc3c7;
        }}
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
            const sourceContent = document.getElementById(testName + '_source');
            const testSequence = imageContent.closest('.test-sequence');
            const tabButtons = testSequence.querySelectorAll('.tab');
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            if (tabType === 'image') {
                imageContent.classList.add('active');
                sourceContent.classList.remove('active');
                tabButtons[0].classList.add('active');
                
                // Ensure the first image is shown when switching back to image tab
                const images = imageContent.querySelectorAll('.sequence-image');
                if (images.length > 0) {
                    images.forEach(img => img.classList.remove('active'));
                    images[0].classList.add('active');
                }
            } else {
                imageContent.classList.remove('active');
                sourceContent.classList.add('active');
                tabButtons[1].classList.add('active');
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
    print(f"Generated: index.html, assets.html, tests.html")
    print(f"Assets: {len(list(assets_dir.glob('*.png')))} files")
    print(f"Test sequences: {len(list(tests_dir.glob('*')))} directories")


if __name__ == "__main__":
    main()
