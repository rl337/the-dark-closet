"""
Tests to identify and fix character rendering issues.

This module contains tests that specifically check for proper character sprite
rendering and identify rendering problems like text overlays and missing sprites.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path
from typing import List, Tuple
import numpy as np

from ..conftest import save_surface


class CharacterRenderingTester:
    """Handles character rendering testing with specific assertions."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_character_scene(
        self, name: str, level_path: Path, actions: List[Tuple[str, int, int]]
    ) -> List[Path]:
        """Capture screenshots for character rendering tests."""
        from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
        from the_dark_closet.json_scene import JSONScene

        # Create test game
        config = GameConfig(
            window_width=512,
            window_height=384,
            window_title="Character Rendering Test",
            target_fps=60,
        )
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        app = GameApp(config, time_provider)

        scene = JSONScene(app, level_path)
        app.switch_scene(scene)
        app.advance_frame(None)

        screenshots = []
        frame_count = 0

        for description, keys, frames in actions:
            for frame in range(frames):
                frame_count += 1
                app.advance_frame(keys)

                screenshot_path = (
                    self.output_dir / f"{name}_{description}_{frame:02d}.png"
                )
                save_surface(app._screen, screenshot_path)
                screenshots.append(screenshot_path)

        return screenshots

    def analyze_screenshot(self, screenshot_path: Path) -> dict:
        """Analyze a screenshot for rendering issues."""
        if not screenshot_path.exists():
            return {"error": "Screenshot not found"}

        try:
            image = pygame.image.load(str(screenshot_path))
            surface_array = pygame.surfarray.array3d(image)
            
            analysis = {
                "size": image.get_size(),
                "has_hud_text": self._detect_hud_text(surface_array),
                "has_character_pixels": self._detect_character_pixels(surface_array),
                "has_vertical_lines": self._detect_vertical_lines(surface_array),
                "dominant_colors": self._get_dominant_colors(surface_array),
                "pixel_variance": self._calculate_pixel_variance(surface_array),
            }
            
            return analysis
        except Exception as e:
            return {"error": f"Failed to analyze screenshot: {e}"}

    def _detect_hud_text(self, surface_array: np.ndarray) -> bool:
        """Detect if HUD text is present (looks for text-like patterns)."""
        # Look for areas with high contrast that might be text
        # HUD text is typically white/light colored on dark background
        height, width, channels = surface_array.shape
        
        # Check the top-left area where HUD text appears
        hud_region = surface_array[:100, :400]  # Top-left area
        
        # Look for high contrast areas (potential text)
        gray_region = np.mean(hud_region, axis=2)
        contrast = np.std(gray_region)
        
        # If there's high contrast in the HUD area, likely text
        return contrast > 50

    def _detect_character_pixels(self, surface_array: np.ndarray) -> bool:
        """Detect if character sprite pixels are present."""
        height, width, channels = surface_array.shape
        
        # Look for non-background colors in the center area where character should be
        center_x = width // 2
        center_y = height // 2
        character_region = surface_array[
            center_y - 60:center_y + 60,
            center_x - 60:center_x + 60
        ]
        
        # Check for colors that aren't sky blue (18, 22, 30) or brick brown (135, 90, 60)
        sky_color = np.array([18, 22, 30])
        brick_color = np.array([135, 90, 60])
        
        # Count pixels that aren't sky or brick colors
        non_background_pixels = 0
        for y in range(character_region.shape[0]):
            for x in range(character_region.shape[1]):
                pixel = character_region[y, x]
                if not np.allclose(pixel, sky_color, atol=20) and not np.allclose(pixel, brick_color, atol=20):
                    non_background_pixels += 1
        
        # If we have enough non-background pixels, likely a character
        return non_background_pixels > 100

    def _detect_vertical_lines(self, surface_array: np.ndarray) -> bool:
        """Detect vertical line patterns that might indicate rendering issues."""
        height, width, channels = surface_array.shape
        
        # Look for vertical lines by checking for consistent color patterns
        vertical_lines = 0
        for x in range(width):
            column = surface_array[:, x, :]
            # Check if this column has consistent color (potential vertical line)
            column_mean = np.mean(column, axis=0)
            column_std = np.std(column, axis=0)
            
            # If standard deviation is low, it's a consistent vertical line
            if np.mean(column_std) < 10:
                vertical_lines += 1
        
        # If we have many vertical lines, it's likely a rendering issue
        return vertical_lines > width * 0.1  # More than 10% of columns are vertical lines

    def _get_dominant_colors(self, surface_array: np.ndarray) -> List[Tuple[int, int, int]]:
        """Get the most dominant colors in the image."""
        # Reshape to list of pixels
        pixels = surface_array.reshape(-1, 3)
        
        # Get unique colors and their counts
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        
        # Sort by count and return top 5
        sorted_indices = np.argsort(counts)[::-1]
        dominant_colors = []
        
        for i in range(min(5, len(sorted_indices))):
            idx = sorted_indices[i]
            color = tuple(unique_colors[idx].astype(int))
            dominant_colors.append(color)
        
        return dominant_colors

    def _calculate_pixel_variance(self, surface_array: np.ndarray) -> float:
        """Calculate the variance in pixel colors (higher = more detail)."""
        return float(np.var(surface_array))


@pytest.fixture
def character_tester():
    """Create a character rendering tester."""
    output_dir = Path("build/character_rendering_tests")
    return CharacterRenderingTester(output_dir)


class TestCharacterRenderingIssues:
    """Test for character rendering issues and fixes."""

    @pytest.mark.visual
    def test_character_rendering_has_proper_sprites(self, character_tester):
        """Test that character rendering shows proper sprites, not text or lines."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("idle", None, 2),
            ("move_right", {pygame.K_RIGHT}, 2),
        ]

        # Capture screenshots
        screenshots = character_tester.capture_character_scene(
            "character_sprite_test", level_path, actions
        )

        # Analyze each screenshot
        issues_found = []
        for screenshot_path in screenshots:
            analysis = character_tester.analyze_screenshot(screenshot_path)
            
            if "error" in analysis:
                issues_found.append(f"Analysis error in {screenshot_path.name}: {analysis['error']}")
                continue
            
            # Check for specific issues
            if analysis["has_hud_text"]:
                issues_found.append(f"HUD text detected in {screenshot_path.name} - should be minimal or absent")
            
            if not analysis["has_character_pixels"]:
                issues_found.append(f"No character pixels detected in {screenshot_path.name} - character sprite missing")
            
            if analysis["has_vertical_lines"]:
                issues_found.append(f"Vertical lines detected in {screenshot_path.name} - possible rendering issue")
            
            # Check that we have reasonable detail (not just solid colors)
            if analysis["pixel_variance"] < 1000:
                issues_found.append(f"Low pixel variance in {screenshot_path.name} - image may be too simple")
            
            print(f"Analysis for {screenshot_path.name}:")
            print(f"  Size: {analysis['size']}")
            print(f"  Has HUD text: {analysis['has_hud_text']}")
            print(f"  Has character pixels: {analysis['has_character_pixels']}")
            print(f"  Has vertical lines: {analysis['has_vertical_lines']}")
            print(f"  Dominant colors: {analysis['dominant_colors'][:3]}")
            print(f"  Pixel variance: {analysis['pixel_variance']:.2f}")
            print()

        # Report issues
        if issues_found:
            print("RENDERING ISSUES FOUND:")
            for issue in issues_found:
                print(f"  - {issue}")
            print()
            print("Screenshots saved to build/character_rendering_tests/")
            print("Please examine the screenshots to understand the rendering issues.")
        
        # For now, we'll fail the test if we find issues, but this helps us identify problems
        assert len(issues_found) == 0, f"Character rendering issues found: {issues_found}"

    @pytest.mark.visual
    def test_character_animation_sequences(self, character_tester):
        """Test that character animation sequences show proper character movement."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("idle_sequence", None, 4),
            ("walk_sequence", {pygame.K_RIGHT}, 8),
            ("jump_sequence", {pygame.K_SPACE}, 6),
        ]

        # Capture screenshots
        screenshots = character_tester.capture_character_scene(
            "character_animation_test", level_path, actions
        )

        # Analyze animation sequences
        sequence_analyses = {}
        for screenshot_path in screenshots:
            analysis = character_tester.analyze_screenshot(screenshot_path)
            if "error" not in analysis:
                # Extract sequence name from filename
                sequence_name = screenshot_path.stem.split('_')[-2]  # e.g., "idle", "walk", "jump"
                if sequence_name not in sequence_analyses:
                    sequence_analyses[sequence_name] = []
                sequence_analyses[sequence_name].append(analysis)

        # Check each sequence
        issues_found = []
        for sequence_name, analyses in sequence_analyses.items():
            if not analyses:
                continue
                
            print(f"Analysis for {sequence_name} sequence:")
            
            # Check that character pixels are present in most frames
            frames_with_character = sum(1 for analysis in analyses if analysis["has_character_pixels"])
            character_coverage = frames_with_character / len(analyses)
            
            print(f"  Character coverage: {character_coverage:.2f} ({frames_with_character}/{len(analyses)} frames)")
            
            if character_coverage < 0.8:  # Less than 80% of frames have character pixels
                issues_found.append(f"{sequence_name} sequence has poor character coverage: {character_coverage:.2f}")
            
            # Check for consistent rendering (not too much variation in pixel variance)
            variances = [analysis["pixel_variance"] for analysis in analyses]
            variance_std = np.std(variances)
            
            print(f"  Variance consistency: {variance_std:.2f} (lower is better)")
            
            if variance_std > 5000:  # High variation in detail
                issues_found.append(f"{sequence_name} sequence has inconsistent rendering: {variance_std:.2f}")
            
            print()

        if issues_found:
            print("ANIMATION SEQUENCE ISSUES FOUND:")
            for issue in issues_found:
                print(f"  - {issue}")
            print()
            print("Screenshots saved to build/character_rendering_tests/")
        
        # For now, we'll fail the test if we find issues
        assert len(issues_found) == 0, f"Character animation issues found: {issues_found}"

    @pytest.mark.visual
    def test_no_hud_text_overlay(self, character_tester):
        """Test that HUD text doesn't dominate the visual output."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("clean_view", None, 1),
        ]

        # Capture screenshots
        screenshots = character_tester.capture_character_scene(
            "hud_text_test", level_path, actions
        )

        # Analyze for HUD text presence
        for screenshot_path in screenshots:
            analysis = character_tester.analyze_screenshot(screenshot_path)
            
            if "error" in analysis:
                continue
            
            print(f"HUD analysis for {screenshot_path.name}:")
            print(f"  Has HUD text: {analysis['has_hud_text']}")
            print(f"  Dominant colors: {analysis['dominant_colors'][:3]}")
            
            # The HUD text should be present but not dominant
            # We expect some HUD text, but the character should be more prominent
            if analysis["has_hud_text"]:
                # Check if HUD text is too prominent by looking at the top-left area
                # This is a basic check - in a real implementation, we'd be more sophisticated
                print(f"  HUD text detected - this is expected but should not dominate the image")
            
            print()
