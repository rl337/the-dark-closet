#!/usr/bin/env python3
"""
Test script demonstrating controlled time advancement for precise testing.
This allows us to advance time frame by frame and capture screenshots at exact moments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple, Optional

# Ensure we can import from src layout
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame

from the_dark_closet.game import (
    GameApp,
    GameConfig,
    SideScrollerScene,
    TILE_BOUNDARY,
    TILE_EMPTY,
    TILE_PLATFORM,
    TILE_SIZE,
    ControlledTimeProvider,
)


def save_surface(surface: pygame.Surface, out_path: Path) -> None:
    """Save a pygame surface to a PNG file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(out_path))


def rect_room(width: int, height: int) -> List[str]:
    """Create a simple rectangular room for testing."""
    rows: List[str] = []

    # Top boundary
    rows.append(TILE_BOUNDARY * width)

    # Middle rows (empty space)
    for _ in range(height - 2):
        row = TILE_BOUNDARY + TILE_EMPTY * (width - 2) + TILE_BOUNDARY
        rows.append(row)

    # Bottom boundary with some platforms
    bottom_row = TILE_BOUNDARY
    for i in range(1, width - 1):
        if i % 3 == 0:
            bottom_row += TILE_PLATFORM
        else:
            bottom_row += TILE_BOUNDARY
    bottom_row += TILE_BOUNDARY
    rows.append(bottom_row)

    return rows


def test_controlled_movement(out_dir: Path) -> None:
    """Test controlled time advancement with precise movement tracking."""
    print("Testing controlled time advancement...")

    # Headless-safe defaults
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    # Create game with controlled time
    config = GameConfig(
        window_width=5120,
        window_height=2880,
        window_title="Controlled Time Test",
        target_fps=60,
    )

    # Use controlled time provider
    time_provider = ControlledTimeProvider(1.0 / 60.0)  # 60 FPS
    app = GameApp(config, time_provider)

    # Create a simple test room
    room = rect_room(12, 8)
    spawn_px = (3 * TILE_SIZE, 4 * TILE_SIZE)  # Start in middle-left

    # Switch to side scroller scene
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)

    # Test sequence: move right for 10 frames, then jump
    frames_to_capture: List[Tuple[int, str, Optional[set[int]]]] = []

    # Frame 0: Initial position
    frames_to_capture.append((0, "initial", None))

    # Frames 1-10: Move right
    for i in range(1, 11):
        frames_to_capture.append((i, f"move_right_{i}", {pygame.K_RIGHT}))

    # Frames 11-15: Jump
    for i in range(11, 16):
        frames_to_capture.append((i, f"jump_{i}", {pygame.K_SPACE}))

    # Frames 16-20: Move left
    for i in range(16, 21):
        frames_to_capture.append((i, f"move_left_{i}", {pygame.K_LEFT}))

    # Execute the controlled sequence
    out_dir.mkdir(parents=True, exist_ok=True)

    for frame_num, name, keys in frames_to_capture:
        # Advance exactly one frame with the specified keys
        app.advance_frame(keys)

        # Capture screenshot
        screenshot_path = out_dir / f"controlled_{name}.png"
        save_surface(app._screen, screenshot_path)

        # Print current state for debugging
        if hasattr(scene, "player_rect"):
            player_pos = (scene.player_rect.x, scene.player_rect.y)
            current_time = app.get_current_time()
            print(
                f"Frame {frame_num}: {name} - Player at {player_pos}, Time: {current_time:.3f}s"
            )

    print(f"Controlled time test completed. Screenshots saved to {out_dir}")


def test_frame_by_frame_analysis(out_dir: Path) -> None:
    """Test frame-by-frame analysis for pixel-level verification."""
    print("Testing frame-by-frame analysis...")

    # Headless-safe defaults
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"

    # Create game with controlled time
    config = GameConfig(
        window_width=5120,
        window_height=2880,
        window_title="Frame Analysis Test",
        target_fps=60,
    )

    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    # Create a simple test room
    room = rect_room(10, 6)
    spawn_px = (2 * TILE_SIZE, 3 * TILE_SIZE)

    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)

    # Analyze player movement pixel by pixel
    initial_pos = scene.player_rect.center
    print(f"Initial player position: {initial_pos}")

    # Move right for 5 frames and track position
    positions = []
    for i in range(6):  # 0 to 5
        app.advance_frame({pygame.K_RIGHT} if i > 0 else None)
        pos = scene.player_rect.center
        positions.append(pos)

        # Save screenshot for analysis
        screenshot_path = out_dir / f"analysis_frame_{i:02d}.png"
        save_surface(app._screen, screenshot_path)

        print(
            f"Frame {i}: Player at {pos}, moved {pos[0] - initial_pos[0]} pixels right"
        )

    # Verify movement is consistent
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        print(f"Movement from frame {i-1} to {i}: {dx} pixels")

    print(f"Frame analysis completed. Screenshots saved to {out_dir}")


def main() -> None:
    """Run controlled time tests."""
    out_dir = Path("docs/controlled_time_tests")

    # Run tests
    test_controlled_movement(out_dir / "movement")
    test_frame_by_frame_analysis(out_dir / "analysis")

    print("All controlled time tests completed!")


if __name__ == "__main__":
    main()
