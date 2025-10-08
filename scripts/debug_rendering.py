#!/usr/bin/env python3
"""
Debug script to check what's being rendered on screen.
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


def debug_rendering() -> None:
    """Debug what's being rendered on screen."""
    print("Debugging rendering...")
    
    # Create game
    app = create_test_game()
    
    # Create a simple room
    room = rect_room(8, 6)
    spawn_px = (3 * 128, 2 * 128)  # Higher up to avoid falling
    
    # Create scene
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)
    
    # Take initial screenshot
    save_surface(app._screen, Path("debug_rendering.png"))
    
    # Print scene info
    print(f"Scene world size: {scene.world_width_px}x{scene.world_height_px}")
    print(f"Player rect: {scene.player_rect}")
    print(f"Player center: {scene.player_rect.center}")
    print(f"Camera: ({scene.camera_x}, {scene.camera_y})")
    
    # Check if player is in view
    player_screen_rect = scene.player_rect.move(-int(scene.camera_x), -int(scene.camera_y))
    print(f"Player screen rect: {player_screen_rect}")
    
    # Check a few pixels in the player area
    print("Checking pixels in player area:")
    for y in range(player_screen_rect.top, player_screen_rect.bottom, 10):
        for x in range(player_screen_rect.left, player_screen_rect.right, 10):
            if 0 <= x < app._screen.get_width() and 0 <= y < app._screen.get_height():
                color = app._screen.get_at((x, y))
                if color[:3] != (18, 22, 30):  # Not sky color
                    print(f"  Color at ({x}, {y}): {color}")
    
    # Check center area specifically
    center_x, center_y = player_screen_rect.center
    print(f"Checking center area around ({center_x}, {center_y}):")
    for dy in range(-10, 11, 2):
        for dx in range(-10, 11, 2):
            x, y = center_x + dx, center_y + dy
            if 0 <= x < app._screen.get_width() and 0 <= y < app._screen.get_height():
                color = app._screen.get_at((x, y))
                if color[:3] != (18, 22, 30):  # Not sky color
                    print(f"  Color at ({x}, {y}): {color}")


if __name__ == "__main__":
    debug_rendering()
