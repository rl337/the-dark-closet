#!/usr/bin/env python3
"""
Debug script to check if advance_frame is working correctly.
"""

from __future__ import annotations

import os
from pathlib import Path

# Ensure we can import from src layout
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame
from test_utils import create_test_game, save_surface, rect_room
from the_dark_closet.game import SideScrollerScene


def debug_advance_frame() -> None:
    """Debug the advance_frame method."""
    print("Debugging advance_frame...")
    
    # Create game
    app = create_test_game()
    
    # Create a simple room
    room = rect_room(8, 6)
    spawn_px = (3 * 128, 2 * 128)  # Higher up to avoid falling
    
    # Create scene
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)
    
    # Take screenshot before advance_frame
    save_surface(app._screen, Path("debug_before_advance.png"))
    print("Screenshot taken before advance_frame")
    
    # Advance one frame
    app.advance_frame(None)
    
    # Take screenshot after advance_frame
    save_surface(app._screen, Path("debug_after_advance.png"))
    print("Screenshot taken after advance_frame")
    
    # Check for center mass dot
    from test_utils import find_center_mass_position
    pos = find_center_mass_position(app._screen)
    print(f"Center mass position after advance: {pos}")
    
    # Check a few pixels in the player area
    player_screen_rect = scene.player_rect.move(-int(scene.camera_x), -int(scene.camera_y))
    print(f"Player screen rect: {player_screen_rect}")
    
    print("Checking pixels in player area after advance:")
    for y in range(player_screen_rect.top, player_screen_rect.bottom, 20):
        for x in range(player_screen_rect.left, player_screen_rect.right, 20):
            if 0 <= x < app._screen.get_width() and 0 <= y < app._screen.get_height():
                color = app._screen.get_at((x, y))
                if color[:3] != (18, 22, 30):  # Not sky color
                    print(f"  Color at ({x}, {y}): {color}")


if __name__ == "__main__":
    debug_advance_frame()
