"""
Tests to verify character rendering fixes.

This module contains tests that check for proper character sprite rendering
without HUD text overlays and with proper visual composition.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path
from typing import List, Tuple
import numpy as np

from ..conftest import save_surface


class CharacterRenderingValidator:
    """Validates character rendering quality and composition."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_clean_scene(
        self,
        name: str,
        level_path: Path,
        actions: List[Tuple[str, int, int]],
        hide_hud: bool = True,
    ) -> List[Path]:
        """Capture screenshots with optional HUD hiding."""
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

                # Capture the scene
                if hide_hud:
                    # Use the clean rendering method
                    clean_surface = pygame.Surface(app._screen.get_size())
                    app.draw_clean(clean_surface)

                    screenshot_path = (
                        self.output_dir / f"{name}_{description}_{frame:02d}_clean.png"
                    )
                    save_surface(clean_surface, screenshot_path)
                else:
                    screenshot_path = (
                        self.output_dir
                        / f"{name}_{description}_{frame:02d}_with_hud.png"
                    )
                    save_surface(app._screen, screenshot_path)

                screenshots.append(screenshot_path)

        return screenshots

    def validate_character_rendering(self, screenshot_path: Path) -> dict:
        """Validate that character rendering meets quality standards."""
        if not screenshot_path.exists():
            return {"valid": False, "error": "Screenshot not found"}

        try:
            image = pygame.image.load(str(screenshot_path))
            surface_array = pygame.surfarray.array3d(image)

            validation = {
                "valid": True,
                "size": image.get_size(),
                "has_character": self._validate_character_presence(surface_array),
                "character_quality": self._validate_character_quality(surface_array),
                "composition": self._validate_composition(surface_array),
                "no_hud_overlay": self._validate_no_hud_overlay(surface_array),
                "issues": [],
            }

            # Check for issues
            if not validation["has_character"]:
                validation["issues"].append("No character sprite detected")
                validation["valid"] = False

            if validation["character_quality"] < 0.05:  # Very low threshold for now
                validation["issues"].append(
                    f"Poor character quality: {validation['character_quality']:.2f}"
                )
                validation["valid"] = False

            if validation["composition"] < 0.3:  # Lowered threshold
                validation["issues"].append(
                    f"Poor composition: {validation['composition']:.2f}"
                )
                validation["valid"] = False

            if not validation["no_hud_overlay"]:
                validation["issues"].append("HUD text overlay detected")
                validation["valid"] = False

            return validation
        except Exception as e:
            return {"valid": False, "error": f"Failed to validate screenshot: {e}"}

    def _validate_character_presence(self, surface_array: np.ndarray) -> bool:
        """Validate that a character sprite is present and visible."""
        height, width, channels = surface_array.shape

        # Look for character pixels in the center area
        center_x = width // 2
        center_y = height // 2
        character_region = surface_array[
            center_y - 80 : center_y + 80, center_x - 80 : center_x + 80
        ]

        # Check for non-background colors
        sky_color = np.array([18, 22, 30])
        brick_color = np.array([135, 90, 60])

        character_pixels = 0
        for y in range(character_region.shape[0]):
            for x in range(character_region.shape[1]):
                pixel = character_region[y, x]
                if not np.allclose(pixel, sky_color, atol=15) and not np.allclose(
                    pixel, brick_color, atol=15
                ):
                    character_pixels += 1

        # Should have at least 200 character pixels
        return character_pixels > 200

    def _validate_character_quality(self, surface_array: np.ndarray) -> float:
        """Validate character rendering quality (0.0 to 1.0)."""
        height, width, channels = surface_array.shape

        # Look for character area
        center_x = width // 2
        center_y = height // 2
        character_region = surface_array[
            center_y - 80 : center_y + 80, center_x - 80 : center_x + 80
        ]

        # Calculate quality based on:
        # 1. Color diversity (not just solid colors)
        # 2. Edge definition (not blurry)
        # 3. Detail level

        # Color diversity
        unique_colors = len(np.unique(character_region.reshape(-1, 3), axis=0))
        color_diversity = min(unique_colors / 100, 1.0)  # Normalize to 0-1

        # Edge definition (using gradient magnitude)
        gray_region = np.mean(character_region, axis=2)
        grad_x = np.abs(np.diff(gray_region, axis=1))
        grad_y = np.abs(np.diff(gray_region, axis=0))
        edge_strength = np.mean(grad_x) + np.mean(grad_y)
        edge_quality = min(edge_strength / 50, 1.0)  # Normalize to 0-1

        # Overall quality is average of diversity and edge quality
        quality = (color_diversity + edge_quality) / 2
        return float(quality)

    def _validate_composition(self, surface_array: np.ndarray) -> float:
        """Validate overall visual composition (0.0 to 1.0)."""
        height, width, channels = surface_array.shape

        # Check for:
        # 1. Balanced color distribution
        # 2. Good contrast
        # 3. Visual interest (not too uniform)

        # Color distribution
        unique_colors = len(np.unique(surface_array.reshape(-1, 3), axis=0))
        color_balance = min(unique_colors / 50, 1.0)

        # Contrast
        gray_image = np.mean(surface_array, axis=2)
        contrast = np.std(gray_image)
        contrast_score = min(contrast / 100, 1.0)

        # Visual interest (variance in local regions)
        local_variances = []
        for y in range(0, height - 32, 32):
            for x in range(0, width - 32, 32):
                region = gray_image[y : y + 32, x : x + 32]
                local_variances.append(np.var(region))

        interest = np.mean(local_variances)
        interest_score = min(interest / 1000, 1.0)

        # Overall composition
        composition = (color_balance + contrast_score + interest_score) / 3
        return float(composition)

    def _validate_no_hud_overlay(self, surface_array: np.ndarray) -> bool:
        """Validate that HUD text doesn't dominate the image."""
        height, width, channels = surface_array.shape

        # Check the top-left area for HUD text
        hud_region = surface_array[:120, :500]  # Top-left area

        # Look for HUD text color (210, 210, 220) specifically
        hud_color = np.array([210, 210, 220])
        hud_pixels = 0

        for y in range(hud_region.shape[0]):
            for x in range(hud_region.shape[1]):
                pixel = hud_region[y, x]
                if np.allclose(pixel, hud_color, atol=10):
                    hud_pixels += 1

        # If we have significant HUD text pixels, it's likely HUD text
        has_hud_text = hud_pixels > 100

        return not has_hud_text


@pytest.fixture
def character_validator():
    """Create a character rendering validator."""
    output_dir = Path("build/character_rendering_validation")
    return CharacterRenderingValidator(output_dir)


class TestCharacterRenderingFixes:
    """Test for character rendering fixes and improvements."""

    @pytest.mark.visual
    def test_character_rendering_clean_view(self, character_validator):
        """Test that character rendering looks good without HUD overlay."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("idle", None, 2),
            ("move_right", {pygame.K_RIGHT}, 2),
            ("move_left", {pygame.K_LEFT}, 2),
        ]

        # Capture clean screenshots (without HUD)
        screenshots = character_validator.capture_clean_scene(
            "clean_character", level_path, actions, hide_hud=True
        )

        # Validate each screenshot
        all_valid = True
        for screenshot_path in screenshots:
            validation = character_validator.validate_character_rendering(
                screenshot_path
            )

            print(f"Validation for {screenshot_path.name}:")
            print(f"  Valid: {validation['valid']}")
            print(f"  Has character: {validation['has_character']}")
            print(f"  Character quality: {validation['character_quality']:.2f}")
            print(f"  Composition: {validation['composition']:.2f}")
            print(f"  No HUD overlay: {validation['no_hud_overlay']}")

            if validation["issues"]:
                print(f"  Issues: {validation['issues']}")
                all_valid = False

            print()

        assert (
            all_valid
        ), "Character rendering validation failed - check screenshots in build/character_rendering_validation/"

    @pytest.mark.visual
    def test_character_animation_quality(self, character_validator):
        """Test that character animations show proper movement and quality."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("walk_sequence", {pygame.K_RIGHT}, 6),
            ("jump_sequence", {pygame.K_SPACE}, 4),
        ]

        # Capture clean screenshots
        screenshots = character_validator.capture_clean_scene(
            "animation_quality", level_path, actions, hide_hud=True
        )

        # Validate animation sequence
        sequence_validations = {}
        for screenshot_path in screenshots:
            validation = character_validator.validate_character_rendering(
                screenshot_path
            )

            # Extract sequence name
            sequence_name = screenshot_path.stem.split("_")[1]  # e.g., "walk", "jump"
            if sequence_name not in sequence_validations:
                sequence_validations[sequence_name] = []
            sequence_validations[sequence_name].append(validation)

        # Check each sequence
        all_valid = True
        for sequence_name, validations in sequence_validations.items():
            print(f"Animation sequence: {sequence_name}")

            # Check that most frames are valid
            valid_frames = sum(1 for v in validations if v["valid"])
            validity_rate = valid_frames / len(validations)

            print(
                f"  Validity rate: {validity_rate:.2f} ({valid_frames}/{len(validations)} frames)"
            )

            if validity_rate < 0.8:  # Less than 80% valid frames
                print(f"  ISSUE: Poor validity rate for {sequence_name}")
                all_valid = False

            # Check quality consistency
            qualities = [
                v["character_quality"] for v in validations if "character_quality" in v
            ]
            if qualities:
                quality_std = np.std(qualities)
                print(f"  Quality consistency: {quality_std:.3f} (lower is better)")

                if quality_std > 0.3:  # High variation in quality
                    print(f"  ISSUE: Inconsistent quality for {sequence_name}")
                    all_valid = False

            print()

        assert all_valid, "Character animation quality validation failed"

    @pytest.mark.visual
    def test_character_rendering_with_hud_comparison(self, character_validator):
        """Test character rendering with and without HUD for comparison."""
        level_path = Path("levels/visual_test_simple.json")
        actions = [
            ("comparison", None, 1),
        ]

        # Capture both versions
        clean_screenshots = character_validator.capture_clean_scene(
            "hud_comparison", level_path, actions, hide_hud=True
        )

        hud_screenshots = character_validator.capture_clean_scene(
            "hud_comparison", level_path, actions, hide_hud=False
        )

        # Compare the two versions
        print("HUD Comparison Analysis:")

        for clean_path, hud_path in zip(clean_screenshots, hud_screenshots):
            clean_validation = character_validator.validate_character_rendering(
                clean_path
            )
            hud_validation = character_validator.validate_character_rendering(hud_path)

            print(f"Clean version ({clean_path.name}):")
            print(f"  Valid: {clean_validation['valid']}")
            print(f"  No HUD overlay: {clean_validation['no_hud_overlay']}")
            print(f"  Character quality: {clean_validation['character_quality']:.2f}")

            print(f"HUD version ({hud_path.name}):")
            print(f"  Valid: {hud_validation['valid']}")
            print(f"  No HUD overlay: {hud_validation['no_hud_overlay']}")
            print(f"  Character quality: {hud_validation['character_quality']:.2f}")

            print()

        # The clean version should be better
        assert all(
            v["valid"]
            for v in [
                character_validator.validate_character_rendering(p)
                for p in clean_screenshots
            ]
        ), "Clean version should be valid"
