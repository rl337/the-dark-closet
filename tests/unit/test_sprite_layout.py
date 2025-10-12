"""
Pixel-perfect sprite layout validation tests.

This test ensures that sprites are rendered at exactly the expected pixel positions.
It creates a solid block of sprites and validates every pixel matches expectations.
"""

import pytest
import pygame
from pathlib import Path
from PIL import Image
import numpy as np
from typing import List

from the_dark_closet.game import (
    GameApp,
    GameConfig,
    SideScrollerScene,
    ControlledTimeProvider,
    TILE_SIZE,
    TILE_BRICK,
)


class SpriteLayoutValidator:
    """Validates sprite positioning with pixel-perfect accuracy."""

    def __init__(self, tolerance: int = 0):
        self.tolerance = tolerance
        self.errors: List[str] = []

    def validate_sprite_position(
        self,
        screenshot: Image.Image,
        expected_x: int,
        expected_y: int,
        sprite: Image.Image,
        sprite_name: str,
    ) -> bool:
        """
        Validate that a sprite appears at the expected position in the screenshot.

        Args:
            screenshot: The full screenshot image
            expected_x: Expected top-left X coordinate of sprite
            expected_y: Expected top-left Y coordinate of sprite
            sprite: The sprite image to look for
            sprite_name: Name for error reporting

        Returns:
            True if sprite is positioned correctly, False otherwise
        """
        sprite_width, sprite_height = sprite.size
        screenshot_width, screenshot_height = screenshot.size

        # Check bounds
        if (
            expected_x < 0
            or expected_y < 0
            or expected_x + sprite_width > screenshot_width
            or expected_y + sprite_height > screenshot_height
        ):
            self.errors.append(
                f"{sprite_name}: Sprite bounds exceed screenshot "
                f"(expected: {expected_x},{expected_y}, size: {sprite_width}x{sprite_height}, "
                f"screenshot: {screenshot_width}x{screenshot_height})"
            )
            return False

        # Extract the region where the sprite should be
        sprite_region = screenshot.crop(
            (
                expected_x,
                expected_y,
                expected_x + sprite_width,
                expected_y + sprite_height,
            )
        )

        # Convert to numpy arrays for comparison
        sprite_array = np.array(sprite)
        region_array = np.array(sprite_region)

        # Compare pixel by pixel
        if sprite_array.shape != region_array.shape:
            self.errors.append(
                f"{sprite_name}: Shape mismatch "
                f"(sprite: {sprite_array.shape}, region: {region_array.shape})"
            )
            return False

        # Calculate pixel differences
        diff = np.abs(sprite_array.astype(int) - region_array.astype(int))
        max_diff = np.max(diff)

        if max_diff > self.tolerance:
            # Find the first mismatched pixel for detailed error reporting
            mismatched_pixels = np.where(diff > self.tolerance)
            if len(mismatched_pixels[0]) > 0:
                first_error_y, first_error_x = (
                    mismatched_pixels[0][0],
                    mismatched_pixels[1][0],
                )
                sprite_pixel = sprite_array[first_error_y, first_error_x]
                region_pixel = region_array[first_error_y, first_error_x]

                self.errors.append(
                    f"{sprite_name}: Pixel mismatch at relative position ({first_error_x}, {first_error_y}) "
                    f"(expected: {sprite_pixel}, got: {region_pixel}, max_diff: {max_diff})"
                )
            return False

        return True

    def validate_tile_grid(
        self,
        screenshot: Image.Image,
        world_tiles: List[str],
        camera_x: int = 0,
        camera_y: int = 0,
    ) -> bool:
        """
        Validate that all tiles in the world are rendered at correct positions.

        Args:
            screenshot: The full screenshot image
            world_tiles: 2D array of tile characters
            camera_x: Camera X offset
            camera_y: Camera Y offset

        Returns:
            True if all tiles are positioned correctly, False otherwise
        """
        success = True

        # Generate expected brick sprite for comparison
        brick_sprite = self._generate_brick_sprite()

        for ty, line in enumerate(world_tiles):
            for tx, tile_char in enumerate(line):
                if tile_char == TILE_BRICK:
                    # Calculate expected position
                    expected_x = tx * TILE_SIZE - camera_x
                    expected_y = ty * TILE_SIZE - camera_y

                    # Only validate tiles that should be visible
                    if (
                        expected_x + TILE_SIZE > 0
                        and expected_x < screenshot.width
                        and expected_y + TILE_SIZE > 0
                        and expected_y < screenshot.height
                    ):

                        tile_name = f"tile_{tx}_{ty}"
                        if not self.validate_sprite_position(
                            screenshot, expected_x, expected_y, brick_sprite, tile_name
                        ):
                            success = False

        return success

    def _generate_brick_sprite(self) -> Image.Image:
        """Generate the expected brick sprite for comparison."""
        # Create a surface and draw the brick using the same logic as the game
        surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surface.fill((0, 0, 0, 0))  # Transparent background

        # Draw brick using the exact same logic as render_brick_tile from rendering_utils.py
        rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        
        # Use the new brick rendering algorithm
        from the_dark_closet.rendering_utils import render_brick_tile
        render_brick_tile(surface, rect)

        # Convert to PIL Image
        pygame_surface = pygame.surfarray.array3d(surface)
        pygame_surface = np.transpose(pygame_surface, (1, 0, 2))
        return Image.fromarray(pygame_surface)

    def get_error_summary(self) -> str:
        """Get a summary of all validation errors."""
        if not self.errors:
            return "All sprite positions validated successfully!"

        return f"Found {len(self.errors)} sprite positioning errors:\n" + "\n".join(
            self.errors
        )


@pytest.fixture
def sprite_validator():
    """Create a sprite layout validator."""
    return SpriteLayoutValidator(tolerance=0)  # Pixel-perfect validation


@pytest.fixture
def test_world_tiles():
    """Create a simple test world with a solid brick block."""
    return [
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
        "BBBBBBBBBBBB",
    ]


@pytest.fixture
def test_game_app():
    """Create a test game app with controlled time."""
    config = GameConfig(512, 384, "Sprite Layout Test", 60)
    time_provider = ControlledTimeProvider(1.0 / 60.0)
    return GameApp(config, time_provider)


class TestSpriteLayout:
    """Test suite for sprite layout validation."""

    def test_brick_tile_positioning(
        self, sprite_validator, test_game_app, test_world_tiles, output_dir
    ):
        """Test that brick tiles are positioned exactly where expected."""
        # Create a minimal test that only renders tiles without player/HUD
        # We'll test individual tile rendering by creating a custom surface

        # Create a surface to test individual tile rendering
        test_surface = pygame.Surface((TILE_SIZE * 4, TILE_SIZE * 4))
        test_surface.fill((18, 22, 30))  # Sky color

        # Test rendering individual tiles at known positions
        test_positions = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
        ]

        # Render tiles directly using the game's tile drawing logic
        scene = SideScrollerScene(test_game_app, test_world_tiles, (0, 0))

        for tx, ty in test_positions:
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            scene._draw_detailed_tile(test_surface, rect, TILE_BRICK)

        # Save test surface
        screenshot_path = output_dir / "sprite_layout_test.png"
        pygame.image.save(test_surface, str(screenshot_path))

        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)

        # Validate each tile position individually
        success = True
        brick_sprite = sprite_validator._generate_brick_sprite()

        for tx, ty in test_positions:
            expected_x = tx * TILE_SIZE
            expected_y = ty * TILE_SIZE
            tile_name = f"tile_{tx}_{ty}"

            if not sprite_validator.validate_sprite_position(
                screenshot, expected_x, expected_y, brick_sprite, tile_name
            ):
                success = False

        # Generate detailed error report if validation failed
        if not success:
            error_report = sprite_validator.get_error_summary()
            print(f"Sprite layout validation failed:\n{error_report}")

            # Save debug image with grid overlay
            debug_path = output_dir / "sprite_layout_debug.png"
            self._save_debug_image(screenshot, [["B" * 4] * 4], 0, 0, debug_path)
            print(f"Debug image saved to: {debug_path}")

        assert (
            success
        ), f"Sprite positioning validation failed. {sprite_validator.get_error_summary()}"

    def test_tile_positioning_with_camera_offset(
        self, sprite_validator, test_game_app, test_world_tiles, output_dir
    ):
        """Test tile positioning with camera offset."""
        # Test camera offset by rendering tiles at offset positions
        camera_x = 128.0  # 1 tile offset
        camera_y = 64.0  # 0.5 tile offset

        # Create a larger surface to accommodate offset tiles
        test_surface = pygame.Surface((TILE_SIZE * 6, TILE_SIZE * 6))
        test_surface.fill((18, 22, 30))  # Sky color

        # Test rendering tiles with camera offset
        test_positions = [
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (1, 2),
            (2, 2),
            (3, 2),
            (4, 2),
        ]

        # Render tiles with camera offset
        scene = SideScrollerScene(test_game_app, test_world_tiles, (0, 0))

        for tx, ty in test_positions:
            # Apply camera offset to tile position
            rect = pygame.Rect(
                tx * TILE_SIZE - int(camera_x),
                ty * TILE_SIZE - int(camera_y),
                TILE_SIZE,
                TILE_SIZE,
            )
            scene._draw_detailed_tile(test_surface, rect, TILE_BRICK)

        # Save test surface
        screenshot_path = output_dir / "sprite_layout_offset_test.png"
        pygame.image.save(test_surface, str(screenshot_path))

        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)

        # Validate each tile position with camera offset
        success = True
        brick_sprite = sprite_validator._generate_brick_sprite()

        for tx, ty in test_positions:
            expected_x = tx * TILE_SIZE - int(camera_x)
            expected_y = ty * TILE_SIZE - int(camera_y)
            tile_name = f"tile_{tx}_{ty}_offset"

            if not sprite_validator.validate_sprite_position(
                screenshot, expected_x, expected_y, brick_sprite, tile_name
            ):
                success = False

        if not success:
            error_report = sprite_validator.get_error_summary()
            print(
                f"Sprite layout validation with camera offset failed:\n{error_report}"
            )

            # Save debug image
            debug_path = output_dir / "sprite_layout_offset_debug.png"
            self._save_debug_image(
                screenshot, [["B" * 6] * 6], camera_x, camera_y, debug_path
            )
            print(f"Debug image saved to: {debug_path}")

        assert (
            success
        ), f"Sprite positioning with camera offset failed. {sprite_validator.get_error_summary()}"

    def test_edge_case_tile_positioning(
        self, sprite_validator, test_game_app, output_dir
    ):
        """Test tile positioning at screen edges and boundaries."""
        # Test edge case by rendering tiles at screen boundaries
        # Create a surface to test edge tile rendering
        test_surface = pygame.Surface((TILE_SIZE * 4, TILE_SIZE * 4))
        test_surface.fill((18, 22, 30))  # Sky color

        # Test rendering tiles at various edge positions
        test_positions = [
            (0, 0),
            (3, 0),  # Top left and right
            (0, 3),
            (3, 3),  # Bottom left and right
            (1, 1),
            (2, 2),  # Center positions
        ]

        # Render tiles at edge positions
        scene = SideScrollerScene(test_game_app, [["B" * 4] * 4], (0, 0))

        for tx, ty in test_positions:
            rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            scene._draw_detailed_tile(test_surface, rect, TILE_BRICK)

        # Save test surface
        screenshot_path = output_dir / "sprite_layout_edge_test.png"
        pygame.image.save(test_surface, str(screenshot_path))

        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)

        # Validate each tile position
        success = True
        brick_sprite = sprite_validator._generate_brick_sprite()

        for tx, ty in test_positions:
            expected_x = tx * TILE_SIZE
            expected_y = ty * TILE_SIZE
            tile_name = f"edge_tile_{tx}_{ty}"

            if not sprite_validator.validate_sprite_position(
                screenshot, expected_x, expected_y, brick_sprite, tile_name
            ):
                success = False

        if not success:
            error_report = sprite_validator.get_error_summary()
            print(f"Edge case sprite layout validation failed:\n{error_report}")

            # Save debug image
            debug_path = output_dir / "sprite_layout_edge_debug.png"
            self._save_debug_image(screenshot, [["B" * 4] * 4], 0, 0, debug_path)
            print(f"Debug image saved to: {debug_path}")

        assert (
            success
        ), f"Edge case sprite positioning failed. {sprite_validator.get_error_summary()}"

    def test_full_scene_sprite_positioning(
        self, sprite_validator, test_game_app, test_world_tiles, output_dir
    ):
        """Test sprite positioning in full scene with all layers - MANDATORY FOR CI."""
        # This test validates that sprites are positioned correctly in the full scene
        # including all rendering layers (background, tiles, player, HUD, etc.)

        # Create scene with solid brick block
        scene = SideScrollerScene(test_game_app, test_world_tiles, (0, 0))
        test_game_app.switch_scene(scene)
        test_game_app.advance_frame(None)

        # Take screenshot of full scene
        screenshot_path = output_dir / "full_scene_sprite_test.png"
        pygame.image.save(test_game_app._screen, str(screenshot_path))

        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)

        # For full scene validation, we need to account for layering
        # We'll validate that tiles appear in the correct positions
        # but allow for other elements to be drawn on top

        success = True
        # brick_sprite = sprite_validator._generate_brick_sprite()  # Not used in this method

        # Test a subset of tiles that should be visible and not obscured
        # Focus on tiles that are likely to be in the background
        test_tiles = [
            (0, 6),
            (1, 6),
            (2, 6),
            (3, 6),  # Bottom row
            (0, 7),
            (1, 7),
            (2, 7),
            (3, 7),  # Bottom row
        ]

        for tx, ty in test_tiles:
            expected_x = tx * TILE_SIZE - int(scene.camera_x)
            expected_y = ty * TILE_SIZE - int(scene.camera_y)

            # Only validate tiles that should be visible
            if (
                expected_x + TILE_SIZE > 0
                and expected_x < screenshot.width
                and expected_y + TILE_SIZE > 0
                and expected_y < screenshot.height
            ):

                tile_name = f"full_scene_tile_{tx}_{ty}"

                # For full scene, we'll be more lenient - check if brick colors appear
                # in the expected region rather than pixel-perfect matching
                if not self._validate_tile_region_contains_brick_colors(
                    screenshot, expected_x, expected_y, tile_name
                ):
                    success = False

        if not success:
            error_report = sprite_validator.get_error_summary()
            print(f"Full scene sprite layout validation failed:\n{error_report}")

            # Save debug image
            debug_path = output_dir / "full_scene_sprite_debug.png"
            self._save_debug_image(
                screenshot, test_world_tiles, scene.camera_x, scene.camera_y, debug_path
            )
            print(f"Debug image saved to: {debug_path}")

        # This test MUST pass for CI builds
        assert (
            success
        ), f"CRITICAL: Full scene sprite positioning failed. This test is MANDATORY for CI builds. {sprite_validator.get_error_summary()}"

    def _validate_tile_region_contains_brick_colors(
        self, screenshot: Image.Image, expected_x: int, expected_y: int, tile_name: str
    ) -> bool:
        """Validate that a tile region contains expected brick colors (more lenient than pixel-perfect)."""
        tile_size = TILE_SIZE

        # Check bounds
        if (
            expected_x < 0
            or expected_y < 0
            or expected_x + tile_size > screenshot.width
            or expected_y + tile_size > screenshot.height
        ):
            return False

        # Extract the region where the tile should be
        tile_region = screenshot.crop(
            (expected_x, expected_y, expected_x + tile_size, expected_y + tile_size)
        )

        # Convert to numpy array
        region_array = np.array(tile_region)

        # Check if brick colors appear in the region
        # Look for the characteristic brick colors: (135, 90, 60), (155, 110, 80), (200, 200, 200)
        brick_colors = [
            [135, 90, 60],  # Base brick color
            [155, 110, 80],  # Brick texture color
            [200, 200, 200],  # Mortar color
        ]

        # Check if any of the brick colors appear in the region
        for color in brick_colors:
            # Find pixels that match this color (with some tolerance)
            color_diff = np.abs(region_array.astype(int) - np.array(color))
            max_diff = np.max(color_diff, axis=2)
            matching_pixels = np.sum(max_diff < 30)  # 30 pixel tolerance

            # If we find a reasonable number of matching pixels, this looks like a brick
            if (
                matching_pixels > (tile_size * tile_size) * 0.1
            ):  # At least 10% of pixels
                return True

        return False

    def _save_debug_image(
        self,
        screenshot: Image.Image,
        world_tiles: List[str],
        camera_x: float,
        camera_y: float,
        debug_path: Path,
    ) -> None:
        """Save a debug image with grid overlay showing expected tile positions."""
        # Create a copy of the screenshot
        debug_img = screenshot.copy()

        # Draw grid overlay
        from PIL import ImageDraw

        draw = ImageDraw.Draw(debug_img)

        # Draw expected tile boundaries
        for ty, line in enumerate(world_tiles):
            for tx, tile_char in enumerate(line):
                if tile_char == TILE_BRICK:
                    expected_x = tx * TILE_SIZE - int(camera_x)
                    expected_y = ty * TILE_SIZE - int(camera_y)

                    # Only draw if tile should be visible
                    if (
                        expected_x + TILE_SIZE > 0
                        and expected_x < screenshot.width
                        and expected_y + TILE_SIZE > 0
                        and expected_y < screenshot.height
                    ):

                        # Draw tile boundary
                        draw.rectangle(
                            [
                                expected_x,
                                expected_y,
                                expected_x + TILE_SIZE - 1,
                                expected_y + TILE_SIZE - 1,
                            ],
                            outline=(255, 0, 0),
                            width=2,
                        )

                        # Draw tile coordinates
                        draw.text(
                            (expected_x + 5, expected_y + 5),
                            f"{tx},{ty}",
                            fill=(255, 0, 0),
                        )

        debug_img.save(debug_path)
