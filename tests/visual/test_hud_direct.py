"""
Direct test for HUD text rendering.
"""

from __future__ import annotations

import pytest
import pygame
import numpy as np
from pathlib import Path

from ..conftest import save_surface


def test_direct_hud_check():
    """Directly check for HUD text pixels."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Direct HUD Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Render with HUD
    surface = pygame.Surface(app._screen.get_size())
    scene.draw(surface, show_hud=True)
    save_surface(surface, Path("build/direct_hud_test.png"))

    # Look for HUD text color (210, 210, 220) directly
    array = pygame.surfarray.array3d(surface)
    hud_color = np.array([210, 210, 220])
    
    # Count pixels that match the HUD text color
    hud_pixels = 0
    hud_locations = []
    
    for y in range(array.shape[0]):
        for x in range(array.shape[1]):
            pixel = array[y, x]
            if np.allclose(pixel, hud_color, atol=10):  # Allow some tolerance
                hud_pixels += 1
                hud_locations.append((x, y))
    
    print(f"HUD text pixels found: {hud_pixels}")
    print(f"HUD locations (first 10): {hud_locations[:10]}")
    
    # Check the top-left area specifically
    top_left_region = array[:150, :500]
    top_left_hud_pixels = 0
    
    for y in range(top_left_region.shape[0]):
        for x in range(top_left_region.shape[1]):
            pixel = top_left_region[y, x]
            if np.allclose(pixel, hud_color, atol=10):
                top_left_hud_pixels += 1
    
    print(f"HUD pixels in top-left region: {top_left_hud_pixels}")
    
    # Should have HUD text pixels
    assert hud_pixels > 100, f"Expected HUD text pixels, but found only {hud_pixels}"
    assert top_left_hud_pixels > 50, f"Expected HUD text in top-left region, but found only {top_left_hud_pixels}"


def test_hud_vs_no_hud_difference():
    """Test that there's a clear difference between HUD and no-HUD rendering."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="HUD Difference Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Render with HUD
    hud_surface = pygame.Surface(app._screen.get_size())
    scene.draw(hud_surface, show_hud=True)
    save_surface(hud_surface, Path("build/hud_difference_with.png"))

    # Render without HUD
    no_hud_surface = pygame.Surface(app._screen.get_size())
    scene.draw(no_hud_surface, show_hud=False)
    save_surface(no_hud_surface, Path("build/hud_difference_without.png"))

    # Compare the two surfaces
    hud_array = pygame.surfarray.array3d(hud_surface)
    no_hud_array = pygame.surfarray.array3d(no_hud_surface)
    
    different_pixels = 0
    for y in range(hud_array.shape[0]):
        for x in range(hud_array.shape[1]):
            if not np.array_equal(hud_array[y, x], no_hud_array[y, x]):
                different_pixels += 1
    
    print(f"Different pixels between HUD and no-HUD: {different_pixels}")
    
    # Should have some differences (HUD text)
    assert different_pixels > 100, f"Expected differences between HUD and no-HUD rendering, but found only {different_pixels} pixels"
