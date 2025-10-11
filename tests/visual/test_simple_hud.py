"""
Simple test to verify HUD rendering.
"""

from __future__ import annotations

import pytest
import pygame
import numpy as np
from pathlib import Path

from ..conftest import save_surface


def test_simple_hud_rendering():
    """Test that HUD text is actually being rendered."""
    from the_dark_closet.rendering_utils import render_hud
    
    # Initialize pygame
    pygame.init()
    
    # Create a test surface
    surface = pygame.Surface((512, 384))
    surface.fill((18, 22, 30))  # Sky color
    
    # Create a font
    font = pygame.font.Font(None, 96)
    
    # Render HUD
    render_hud(surface, font)
    
    # Save the result
    save_surface(surface, Path("build/simple_hud_test.png"))
    
    # Check if the HUD text was rendered by looking for text pixels
    array = pygame.surfarray.array3d(surface)
    
    # Look for the HUD text color (210, 210, 220) in the top-left area
    hud_region = array[:100, :400]
    
    # Count pixels that match the HUD text color
    hud_color = np.array([210, 210, 220])
    hud_pixels = 0
    
    for y in range(hud_region.shape[0]):
        for x in range(hud_region.shape[1]):
            pixel = hud_region[y, x]
            if np.allclose(pixel, hud_color, atol=10):  # Allow some tolerance
                hud_pixels += 1
    
    print(f"HUD text pixels found: {hud_pixels}")
    
    # Should have some HUD text pixels
    assert hud_pixels > 100, f"Expected HUD text pixels, but found only {hud_pixels}"


def test_hud_with_none_font():
    """Test that HUD rendering handles None font gracefully."""
    from the_dark_closet.rendering_utils import render_hud
    
    # Initialize pygame
    pygame.init()
    
    # Create a test surface
    surface = pygame.Surface((512, 384))
    surface.fill((18, 22, 30))  # Sky color
    
    # Render HUD with None font
    render_hud(surface, None)
    
    # Save the result
    save_surface(surface, Path("build/hud_none_font_test.png"))
    
    # Should not crash and should not render any text
    array = pygame.surfarray.array3d(surface)
    
    # Check that the surface is still just the sky color
    sky_color = np.array([18, 22, 30])
    non_sky_pixels = 0
    
    for y in range(array.shape[0]):
        for x in range(array.shape[1]):
            pixel = array[y, x]
            if not np.allclose(pixel, sky_color, atol=5):
                non_sky_pixels += 1
    
    print(f"Non-sky pixels with None font: {non_sky_pixels}")
    
    # Should have very few non-sky pixels (just the character and tiles)
    assert non_sky_pixels < 10000, f"Too many non-sky pixels: {non_sky_pixels} - HUD might be rendering with None font"
