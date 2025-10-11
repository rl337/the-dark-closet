"""
Test for character rendering quality and proper visual composition.
"""

from __future__ import annotations

import pytest
import pygame
import numpy as np
from pathlib import Path

from ..conftest import save_surface


def test_character_rendering_quality():
    """Test that character rendering shows proper sprites, not just text and lines."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Character Quality Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Render clean scene (no HUD)
    surface = pygame.Surface(app._screen.get_size())
    scene.draw(surface, show_hud=False)
    save_surface(surface, Path("build/character_quality_test.png"))

    # Analyze the rendering
    array = pygame.surfarray.array3d(surface)
    
    # Check for character presence in the center area
    center_x = array.shape[1] // 2
    center_y = array.shape[0] // 2
    character_region = array[
        center_y - 100:center_y + 100,
        center_x - 100:center_x + 100
    ]
    
    # Count non-background pixels (character should be visible)
    sky_color = np.array([18, 22, 30])
    brick_color = np.array([135, 90, 60])
    
    character_pixels = 0
    for y in range(character_region.shape[0]):
        for x in range(character_region.shape[1]):
            pixel = character_region[y, x]
            if not np.allclose(pixel, sky_color, atol=15) and not np.allclose(pixel, brick_color, atol=15):
                character_pixels += 1
    
    print(f"Character pixels in center region: {character_pixels}")
    
    # Check for color diversity (character should have multiple colors)
    unique_colors = len(np.unique(character_region.reshape(-1, 3), axis=0))
    print(f"Unique colors in character region: {unique_colors}")
    
    # Check for proper character proportions (should not be just vertical lines)
    # Look for horizontal vs vertical patterns
    gray_region = np.mean(character_region, axis=2)
    horizontal_edges = np.sum(np.abs(np.diff(gray_region, axis=1)))
    vertical_edges = np.sum(np.abs(np.diff(gray_region, axis=0)))
    edge_ratio = horizontal_edges / (vertical_edges + 1)
    
    print(f"Edge ratio (horizontal/vertical): {edge_ratio:.2f}")
    
    # Character should have:
    # 1. Significant non-background pixels
    # 2. Multiple colors (not just one or two)
    # 3. Balanced edge patterns (not dominated by vertical lines)
    
    assert character_pixels > 500, f"Character region should have significant non-background pixels, found {character_pixels}"
    assert unique_colors > 5, f"Character should have multiple colors, found {unique_colors}"
    assert edge_ratio > 0.5, f"Character should not be dominated by vertical lines, edge ratio: {edge_ratio:.2f}"


def test_level_tile_rendering():
    """Test that level tiles render properly, not as vertical lines."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Tile Rendering Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Render clean scene
    surface = pygame.Surface(app._screen.get_size())
    scene.draw(surface, show_hud=False)
    save_surface(surface, Path("build/tile_rendering_test.png"))

    # Analyze tile rendering
    array = pygame.surfarray.array3d(surface)
    
    # Look for brick tiles in the bottom area
    bottom_region = array[-200:, :]  # Bottom 200 pixels
    
    # Count brick-colored pixels
    brick_color = np.array([135, 90, 60])
    brick_pixels = 0
    
    for y in range(bottom_region.shape[0]):
        for x in range(bottom_region.shape[1]):
            pixel = bottom_region[y, x]
            if np.allclose(pixel, brick_color, atol=15):
                brick_pixels += 1
    
    print(f"Brick pixels in bottom region: {brick_pixels}")
    
    # Check for proper tile patterns (not just vertical lines)
    # Look for horizontal mortar lines
    gray_bottom = np.mean(bottom_region, axis=2)
    
    # Count horizontal lines (mortar lines should be horizontal)
    horizontal_lines = 0
    for y in range(gray_bottom.shape[0] - 1):
        for x in range(gray_bottom.shape[1]):
            if abs(gray_bottom[y, x] - gray_bottom[y + 1, x]) > 20:  # High contrast
                horizontal_lines += 1
    
    # Count vertical lines
    vertical_lines = 0
    for y in range(gray_bottom.shape[0]):
        for x in range(gray_bottom.shape[1] - 1):
            if abs(gray_bottom[y, x] - gray_bottom[y, x + 1]) > 20:  # High contrast
                vertical_lines += 1
    
    line_ratio = horizontal_lines / (vertical_lines + 1)
    print(f"Line ratio (horizontal/vertical): {line_ratio:.2f}")
    
    # Tiles should have:
    # 1. Significant brick pixels
    # 2. Reasonable balance between horizontal and vertical lines (not dominated by vertical)
    
    assert brick_pixels > 1000, f"Should have significant brick pixels, found {brick_pixels}"
    assert line_ratio > 0.3, f"Tiles should not be dominated by vertical lines, ratio: {line_ratio:.2f}"
    
    # Additional check: ensure we have a good variety of colors (not just solid blocks)
    unique_colors = len(np.unique(bottom_region.reshape(-1, 3), axis=0))
    print(f"Unique colors in tile region: {unique_colors}")
    assert unique_colors > 5, f"Tiles should have color variety, found {unique_colors} colors"


def test_overall_visual_composition():
    """Test that the overall visual composition is good."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Visual Composition Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Render clean scene
    surface = pygame.Surface(app._screen.get_size())
    scene.draw(surface, show_hud=False)
    save_surface(surface, Path("build/visual_composition_test.png"))

    # Analyze overall composition
    array = pygame.surfarray.array3d(surface)
    
    # Check color diversity
    unique_colors = len(np.unique(array.reshape(-1, 3), axis=0))
    print(f"Total unique colors: {unique_colors}")
    
    # Check for proper contrast
    gray_image = np.mean(array, axis=2)
    contrast = np.std(gray_image)
    print(f"Overall contrast: {contrast:.2f}")
    
    # Check for visual interest (not too uniform)
    local_variances = []
    for y in range(0, array.shape[0] - 32, 32):
        for x in range(0, array.shape[1] - 32, 32):
            region = gray_image[y:y+32, x:x+32]
            local_variances.append(np.var(region))
    
    avg_local_variance = np.mean(local_variances)
    print(f"Average local variance: {avg_local_variance:.2f}")
    
    # Good composition should have:
    # 1. Multiple colors (not just 2-3)
    # 2. Reasonable contrast
    # 3. Visual interest (not too uniform)
    
    assert unique_colors > 10, f"Should have multiple colors for good composition, found {unique_colors}"
    assert contrast > 40, f"Should have reasonable contrast, found {contrast:.2f}"
    assert avg_local_variance > 100, f"Should have visual interest, local variance: {avg_local_variance:.2f}"
