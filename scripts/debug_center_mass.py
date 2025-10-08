#!/usr/bin/env python3
"""
Debug script to check if the center mass dot is being rendered correctly.
"""

from __future__ import annotations

from pathlib import Path

# Ensure we can import from src layout
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from test_utils import (
    create_test_game,
    save_surface,
    find_center_mass_position,
    rect_room,
)
from the_dark_closet.game import SideScrollerScene


def debug_center_mass() -> None:
    """Debug the center mass dot rendering."""
    print("Debugging center mass dot...")

    # Create game
    app = create_test_game()

    # Create a simple room
    room = rect_room(8, 6)
    spawn_px = (3 * 128, 2 * 128)  # Higher up to avoid falling

    # Create scene
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)

    # Take initial screenshot
    save_surface(app._screen, Path("debug_initial.png"))

    # Check for center mass
    pos = find_center_mass_position(app._screen)
    print(f"Center mass position: {pos}")

    # Print player rect info
    print(f"Player rect: {scene.player_rect}")
    print(f"Player center: {scene.player_rect.center}")

    # Check a few pixels around the expected center
    center_x, center_y = scene.player_rect.center
    print(f"Checking pixels around ({center_x}, {center_y}):")

    for dy in range(-5, 6):
        for dx in range(-5, 6):
            x, y = center_x + dx, center_y + dy
            if 0 <= x < app._screen.get_width() and 0 <= y < app._screen.get_height():
                color = app._screen.get_at((x, y))
                if color[:3] == (255, 0, 255):  # Bright magenta RGB
                    print(f"  Found magenta at ({x}, {y}): {color}")
                elif color[:3] != (0, 0, 0):  # Not black
                    print(f"  Color at ({x}, {y}): {color}")


if __name__ == "__main__":
    debug_center_mass()
