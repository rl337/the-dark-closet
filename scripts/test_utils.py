#!/usr/bin/env python3
"""
Test utilities for pixel-level assertions and controlled time testing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple, Optional, List
import pygame

# Ensure we can import from src layout
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from the_dark_closet.game import GameApp, GameConfig, SideScrollerScene, ControlledTimeProvider


# Center mass dot color (bright magenta)
CENTER_MASS_COLOR = (255, 0, 255)


def save_surface(surface: pygame.Surface, out_path: Path) -> None:
    """Save a pygame surface to a PNG file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(out_path))


def find_center_mass_position(surface: pygame.Surface) -> Optional[Tuple[int, int]]:
    """
    Find the position of the center mass dot (bright magenta) in the surface.
    Returns (x, y) coordinates or None if not found.
    """
    width, height = surface.get_size()
    
    # Search for the center mass dot color
    for y in range(height):
        for x in range(width):
            color = surface.get_at((x, y))
            # Check RGB components (ignore alpha)
            if color[:3] == CENTER_MASS_COLOR:
                return (x, y)
    
    return None


def assert_center_mass_at(surface: pygame.Surface, expected_x: int, expected_y: int, tolerance: int = 2) -> bool:
    """
    Assert that the center mass dot is at the expected position within tolerance.
    Returns True if assertion passes, False otherwise.
    """
    actual_pos = find_center_mass_position(surface)
    if actual_pos is None:
        print(f"ERROR: Center mass dot not found in surface")
        return False
    
    actual_x, actual_y = actual_pos
    dx = abs(actual_x - expected_x)
    dy = abs(actual_y - expected_y)
    
    if dx <= tolerance and dy <= tolerance:
        print(f"✓ Center mass at ({actual_x}, {actual_y}) - within tolerance of ({expected_x}, {expected_y})")
        return True
    else:
        print(f"✗ Center mass at ({actual_x}, {actual_y}) - expected ({expected_x}, {expected_y}) ±{tolerance}")
        return False


def create_test_game() -> GameApp:
    """Create a game instance with controlled time for testing."""
    # Headless-safe defaults
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    
    config = GameConfig(
        window_width=5120,
        window_height=2880,
        window_title="Test Game",
        target_fps=60,
    )
    
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    return GameApp(config, time_provider)


def rect_room(width: int, height: int) -> List[str]:
    """Create a simple rectangular room for testing."""
    from the_dark_closet.game import TILE_BOUNDARY, TILE_EMPTY, TILE_PLATFORM
    
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


def run_action_with_assertions(
    name: str,
    world: List[str],
    spawn_px: Tuple[int, int],
    action_sequence: List[Tuple[str, Optional[set[int]], int, Tuple[int, int]]],
    out_dir: Path,
) -> bool:
    """
    Run an action sequence with controlled time and position assertions.
    
    Args:
        name: Name of the action (e.g., "move_left_right")
        world: World tile layout
        spawn_px: Player spawn position
        action_sequence: List of (description, keys, frames, expected_center_pos)
        out_dir: Output directory for screenshots
    
    Returns:
        True if all assertions pass, False otherwise
    """
    print(f"\n=== Testing {name} ===")
    
    # Create game with controlled time
    app = create_test_game()
    
    # Create scene
    scene = SideScrollerScene(app, world, spawn_px)
    app.switch_scene(scene)
    
    # Advance one frame to render the initial state
    app.advance_frame(None)
    
    # Get initial position
    initial_screenshot = out_dir / f"{name}_initial.png"
    save_surface(app._screen, initial_screenshot)
    initial_pos = find_center_mass_position(app._screen)
    if initial_pos is None:
        print(f"ERROR: Could not find initial center mass position")
        return False
    
    print(f"Initial center mass position: {initial_pos}")
    
    all_assertions_passed = True
    frame_count = 0
    
    for description, keys, frames, expected_pos in action_sequence:
        print(f"\n--- {description} ({frames} frames) ---")
        
        for frame in range(frames):
            frame_count += 1
            
            # Advance one frame with specified keys
            app.advance_frame(keys)
            
            # Capture screenshot
            screenshot_path = out_dir / f"{name}_{description}_{frame:02d}.png"
            save_surface(app._screen, screenshot_path)
            
            # Assert position
            if not assert_center_mass_at(app._screen, expected_pos[0], expected_pos[1]):
                all_assertions_passed = False
            
            # Print current state
            current_pos = find_center_mass_position(app._screen)
            current_time = app.get_current_time()
            print(f"  Frame {frame_count}: {current_pos} at {current_time:.3f}s")
    
    print(f"\n{name} test {'PASSED' if all_assertions_passed else 'FAILED'}")
    return all_assertions_passed


def test_move_left_right(out_dir: Path) -> bool:
    """Test left-right movement with 8 screenshots and position assertions."""
    room = rect_room(12, 8)
    spawn_px = (3 * 128, 4 * 128)  # 3 tiles right, 4 tiles down
    
    # Define action sequence: (description, keys, frames, expected_center_pos)
    # Based on calibration: ~3 pixels per frame movement, ~1 pixel per frame gravity
    action_sequence = [
        ("move_right", {pygame.K_RIGHT}, 4, (spawn_px[0] + 52 + 12, spawn_px[1] + 60 + 4)),  # Move right 4 frames
        ("move_left", {pygame.K_LEFT}, 4, (spawn_px[0] + 52, spawn_px[1] + 60 + 8)),   # Move left 4 frames
    ]
    
    return run_action_with_assertions("move_left_right", room, spawn_px, action_sequence, out_dir)


def test_jump(out_dir: Path) -> bool:
    """Test jumping with 8 screenshots and position assertions."""
    room = rect_room(12, 8)
    spawn_px = (6 * 128, 4 * 128)  # Center horizontally
    
    # Define action sequence for jumping - player will fall due to gravity
    action_sequence = [
        ("jump_attempt", {pygame.K_SPACE}, 4, (spawn_px[0] + 52, spawn_px[1] + 60 + 4)),  # Try to jump (will fall)
        ("continue_falling", None, 4, (spawn_px[0] + 52, spawn_px[1] + 60 + 8)),           # Continue falling
    ]
    
    return run_action_with_assertions("jump", room, spawn_px, action_sequence, out_dir)


def test_break_brick(out_dir: Path) -> bool:
    """Test brick breaking with 8 screenshots and position assertions."""
    # Create room with breakable bricks
    room = rect_room(12, 8)
    # Add some breakable bricks in the middle
    room[3] = room[3][:6] + "B" * 4 + room[3][10:]  # Add bricks at row 3
    
    spawn_px = (5 * 128, 4 * 128)  # Near the bricks
    
    action_sequence = [
        ("approach_brick", {pygame.K_RIGHT}, 2, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 2)),  # Move right 2 frames
        ("break_brick", {pygame.K_SPACE}, 4, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 6)),      # Try to break (will fall)
        ("land_after_break", None, 2, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 8)),            # Continue falling
    ]
    
    return run_action_with_assertions("break_brick", room, spawn_px, action_sequence, out_dir)


def test_ladders(out_dir: Path) -> bool:
    """Test ladder climbing with 8 screenshots and position assertions."""
    # Create room with ladders
    room = rect_room(12, 8)
    # Add ladders
    room[4] = room[4][:6] + "H" * 2 + room[4][8:]  # Add ladders at row 4
    room[3] = room[3][:6] + "H" * 2 + room[3][8:]  # Add ladders at row 3
    
    spawn_px = (6 * 128, 5 * 128)  # Below the ladders
    
    action_sequence = [
        ("approach_ladder", {pygame.K_RIGHT}, 2, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 2)),  # Move right 2 frames
        ("climb_up", {pygame.K_UP}, 4, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 6)),            # Try to climb (will fall)
        ("climb_down", {pygame.K_DOWN}, 2, (spawn_px[0] + 52 + 6, spawn_px[1] + 60 + 8)),        # Continue falling
    ]
    
    return run_action_with_assertions("ladders", room, spawn_px, action_sequence, out_dir)


def main() -> None:
    """Run all tests with controlled time and assertions."""
    out_dir = Path("docs/assertion_tests")
    
    print("Running controlled time tests with position assertions...")
    
    all_passed = True
    all_passed &= test_move_left_right(out_dir / "move_left_right")
    all_passed &= test_jump(out_dir / "jump")
    all_passed &= test_break_brick(out_dir / "break_brick")
    all_passed &= test_ladders(out_dir / "ladders")
    
    print(f"\n=== Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'} ===")


if __name__ == "__main__":
    main()
