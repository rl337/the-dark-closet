"""
Test specifically for HUD rendering issues.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path
import numpy as np

from ..conftest import save_surface


def test_hud_text_detection():
    """Test that HUD text can be detected and disabled."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Initialize pygame
    pygame.init()

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="HUD Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Debug: Check if font is initialized
    print(f"Scene HUD font: {scene.hud_font}")
    print(f"Font is None: {scene.hud_font is None}")

    # Test 1: Regular rendering with HUD
    regular_surface = pygame.Surface(app._screen.get_size())
    scene.draw(regular_surface, show_hud=True)
    save_surface(regular_surface, Path("build/hud_test_regular.png"))

    # Test 2: Clean rendering without HUD
    clean_surface = pygame.Surface(app._screen.get_size())
    scene.draw(clean_surface, show_hud=False)
    save_surface(clean_surface, Path("build/hud_test_clean.png"))

    # Analyze both images for HUD text
    def detect_hud_text(surface):
        """Detect if HUD text is present in the image."""
        array = pygame.surfarray.array3d(surface)
        
        # Look at the top-left area where HUD text appears
        hud_region = array[:100, :400]  # Top-left area
        
        # Convert to grayscale
        gray_region = np.mean(hud_region, axis=2)
        
        # Look for high contrast areas (text typically has high contrast)
        contrast = np.std(gray_region)
        
        # Look for horizontal text patterns
        horizontal_edges = np.sum(np.abs(np.diff(gray_region, axis=1)))
        vertical_edges = np.sum(np.abs(np.diff(gray_region, axis=0)))
        
        # Text typically has more horizontal than vertical edges
        text_ratio = horizontal_edges / (vertical_edges + 1)
        
        # If contrast is high and text ratio is high, likely HUD text
        has_hud_text = contrast > 40 and text_ratio > 2.0
        
        return has_hud_text, contrast, text_ratio

    # Analyze both images
    regular_has_hud, regular_contrast, regular_ratio = detect_hud_text(regular_surface)
    clean_has_hud, clean_contrast, clean_ratio = detect_hud_text(clean_surface)

    print(f"Regular rendering:")
    print(f"  Has HUD text: {regular_has_hud}")
    print(f"  Contrast: {regular_contrast:.2f}")
    print(f"  Text ratio: {regular_ratio:.2f}")
    
    print(f"Clean rendering:")
    print(f"  Has HUD text: {clean_has_hud}")
    print(f"  Contrast: {clean_contrast:.2f}")
    print(f"  Text ratio: {clean_ratio:.2f}")

    # The regular version should have HUD text, clean should not
    assert regular_has_hud, "Regular rendering should have HUD text"
    assert not clean_has_hud, f"Clean rendering should not have HUD text (contrast: {clean_contrast:.2f}, ratio: {clean_ratio:.2f})"

    # The clean version should have lower contrast in the HUD area
    assert clean_contrast < regular_contrast, f"Clean rendering should have lower contrast than regular (clean: {clean_contrast:.2f}, regular: {regular_contrast:.2f})"


def test_character_rendering_consistency():
    """Test that character rendering is consistent between frames."""
    from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
    from the_dark_closet.json_scene import JSONScene

    # Create test game
    config = GameConfig(
        window_width=512,
        window_height=384,
        window_title="Character Consistency Test",
        target_fps=60,
    )
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    app = GameApp(config, time_provider)

    level_path = Path("levels/visual_test_simple.json")
    scene = JSONScene(app, level_path)
    app.switch_scene(scene)
    app.advance_frame(None)

    # Capture multiple frames
    frames = []
    for i in range(3):
        app.advance_frame(None)
        surface = pygame.Surface(app._screen.get_size())
        scene.draw(surface, show_hud=False)
        frames.append(surface)
        save_surface(surface, Path(f"build/consistency_test_frame_{i:02d}.png"))

    # Compare frames for consistency
    frame_arrays = [pygame.surfarray.array3d(frame) for frame in frames]
    
    # All frames should be identical (no randomness)
    for i in range(1, len(frame_arrays)):
        different_pixels = 0
        for y in range(frame_arrays[0].shape[0]):
            for x in range(frame_arrays[0].shape[1]):
                if not (frame_arrays[0][y, x] == frame_arrays[i][y, x]).all():
                    different_pixels += 1
        
        print(f"Different pixels between frame 0 and frame {i}: {different_pixels}")
        
        # Should be identical (or very close due to floating point precision)
        assert different_pixels < 100, f"Frame {i} differs from frame 0 by {different_pixels} pixels - rendering is not consistent"
