#!/usr/bin/env python3
"""
Calibrate movement tests to understand actual player movement behavior.
"""

from __future__ import annotations

import os
from pathlib import Path

# Ensure we can import from src layout
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame
from test_utils import create_test_game, save_surface, find_center_mass_position, rect_room
from the_dark_closet.game import SideScrollerScene


def calibrate_movement() -> None:
    """Calibrate movement to understand actual behavior."""
    print("Calibrating movement behavior...")
    
    # Create game
    app = create_test_game()
    
    # Create a simple room with platforms
    room = rect_room(10, 6)
    spawn_px = (4 * 128, 2 * 128)  # Start on a platform
    
    # Create scene
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)
    
    # Advance one frame to render initial state
    app.advance_frame(None)
    
    # Get initial position
    initial_pos = find_center_mass_position(app._screen)
    print(f"Initial position: {initial_pos}")
    
    # Test right movement
    print("\n--- Testing right movement ---")
    for i in range(8):
        app.advance_frame({pygame.K_RIGHT})
        pos = find_center_mass_position(app._screen)
        time = app.get_current_time()
        print(f"Frame {i+1}: {pos} at {time:.3f}s")
        
        # Save screenshot
        save_surface(app._screen, Path(f"calibrate_right_{i+1:02d}.png"))
    
    # Reset and test left movement
    print("\n--- Testing left movement ---")
    app = create_test_game()
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)
    app.advance_frame(None)
    
    for i in range(8):
        app.advance_frame({pygame.K_LEFT})
        pos = find_center_mass_position(app._screen)
        time = app.get_current_time()
        print(f"Frame {i+1}: {pos} at {time:.3f}s")
        
        # Save screenshot
        save_surface(app._screen, Path(f"calibrate_left_{i+1:02d}.png"))
    
    # Reset and test jump
    print("\n--- Testing jump ---")
    app = create_test_game()
    scene = SideScrollerScene(app, room, spawn_px)
    app.switch_scene(scene)
    app.advance_frame(None)
    
    for i in range(8):
        app.advance_frame({pygame.K_SPACE})
        pos = find_center_mass_position(app._screen)
        time = app.get_current_time()
        print(f"Frame {i+1}: {pos} at {time:.3f}s")
        
        # Save screenshot
        save_surface(app._screen, Path(f"calibrate_jump_{i+1:02d}.png"))


if __name__ == "__main__":
    calibrate_movement()
