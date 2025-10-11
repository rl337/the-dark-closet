"""
Debug rendering test to understand what's being rendered.
"""

from __future__ import annotations

import pygame
from pathlib import Path

from ..conftest import save_surface


def test_debug_rendering():
    """Debug test to see what's actually being rendered."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Debug Rendering Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Capture regular rendering
    regular_surface = pygame.Surface(app._screen.get_size())
    app._current_scene.draw(regular_surface, show_hud=True)
    save_surface(regular_surface, Path("build/debug_regular.png"))

    # Capture clean rendering
    clean_surface = pygame.Surface(app._screen.get_size())
    app._current_scene.draw(clean_surface, show_hud=False)
    save_surface(clean_surface, Path("build/debug_clean.png"))

    # Compare the two
    print("Regular rendering saved to build/debug_regular.png")
    print("Clean rendering saved to build/debug_clean.png")

    # Check if they're different
    regular_array = pygame.surfarray.array3d(regular_surface)
    clean_array = pygame.surfarray.array3d(clean_surface)

    different_pixels = 0
    for y in range(regular_array.shape[0]):
        for x in range(regular_array.shape[1]):
            if not (regular_array[y, x] == clean_array[y, x]).all():
                different_pixels += 1

    print(f"Different pixels between regular and clean: {different_pixels}")

    # The clean version should have fewer different pixels (no HUD text)
    assert (
        different_pixels < 1000
    ), f"Too many different pixels: {different_pixels} - HUD might not be disabled properly"
