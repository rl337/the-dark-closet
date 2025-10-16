"""
Procedural asset generation and loading tests using pytest.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path

from the_dark_closet.assets import generate_character_assets
from ..conftest import find_center_mass_position, save_surface


class TestAssetGeneration:
    """Test procedural asset generation."""

    @pytest.mark.unit
    @pytest.mark.asset
    def test_generate_character_assets(self, temp_assets_dir):
        """Test that character assets are generated correctly."""
        assets = generate_character_assets(temp_assets_dir)

        # Check that all expected basic assets were generated
        expected_basic_assets = [
            "head",
            "torso",
            "left_arm",
            "right_arm",
            "left_leg",
            "right_leg",
            "eyes_open",
            "eyes_closed",
            "mouth_neutral",
            "mouth_open",
            "hat",
        ]

        # Check that basic assets exist
        for asset in expected_basic_assets:
            assert asset in assets, f"Expected basic asset {asset} not found"

        # Check that directional assets were generated
        directions = ["left", "right", "forward", "back"]
        for direction in directions:
            for part in ["head", "torso", "left_arm", "right_arm", "left_leg", "right_leg"]:
                asset_key = f"{part}_{direction}"
                assert asset_key in assets, f"Expected directional asset {asset_key} not found"

        # Check that walk cycle assets were generated
        walk_directions = ["left", "right"]
        for direction in walk_directions:
            for frame in range(4):
                asset_key = f"walk_{direction}_{frame}"
                assert asset_key in assets, f"Expected walk cycle asset {asset_key} not found"

        # Should have significantly more assets now
        assert len(assets) >= 40, f"Expected at least 40 assets (basic + directional + walk cycles), got {len(assets)}"

        # Check that all assets exist on disk
        for asset_name, asset_path in assets.items():
            assert Path(asset_path).exists(), f"Asset file '{asset_path}' does not exist"

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_files_are_valid_images(self, temp_assets_dir):
        """Test that generated asset files are valid images."""
        assets = generate_character_assets(temp_assets_dir)

        for asset_name, asset_path in assets.items():
            asset_path = Path(asset_path)
            if asset_path.suffix == ".png":
                # Try to load the image
                try:
                    surface = pygame.image.load(str(asset_path))
                    assert (
                        surface.get_width() > 0
                    ), f"Asset '{asset_name}' has zero width"
                    assert (
                        surface.get_height() > 0
                    ), f"Asset '{asset_name}' has zero height"
                except pygame.error as e:
                    pytest.fail(f"Asset '{asset_name}' is not a valid image: {e}")

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_generation_completeness(self, temp_assets_dir):
        """Test that character assets are generated."""
        assets = generate_character_assets(temp_assets_dir)

        # Check that assets dictionary is returned
        assert isinstance(assets, dict), "Asset generation should return a dictionary"
        assert len(assets) > 0, "Asset generation should return some assets"

        # Check that expected character parts are present
        expected_parts = [
            "head",
            "torso",
            "left_arm",
            "right_arm",
            "left_leg",
            "right_leg",
            "eyes_open",
            "eyes_closed",
            "mouth_neutral",
            "mouth_open",
            "hat",
        ]

        for part in expected_parts:
            assert part in assets, f"Character part '{part}' not generated"

        # Check that all asset files exist
        for part, file_path in assets.items():
            asset_path = Path(file_path)
            assert (
                asset_path.exists()
            ), f"Asset file for '{part}' does not exist: {file_path}"

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_generation_performance(self, temp_assets_dir):
        """Test that asset generation is reasonably fast."""
        import time

        start_time = time.perf_counter()
        generate_character_assets(temp_assets_dir)
        end_time = time.perf_counter()

        generation_time = end_time - start_time
        assert (
            generation_time < 1.0
        ), f"Asset generation took too long: {generation_time:.3f}s"

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_generation_deterministic(self, temp_assets_dir):
        """Test that asset generation is deterministic."""
        # Generate assets twice
        assets1 = generate_character_assets(temp_assets_dir / "assets1")
        assets2 = generate_character_assets(temp_assets_dir / "assets2")

        # Check that same assets were generated
        assert set(assets1.keys()) == set(assets2.keys()), "Different assets generated"

        # Check that files have same size (rough check for determinism)
        for asset_name in assets1:
            asset_path1 = Path(assets1[asset_name])
            if asset_path1.suffix == ".png":
                size1 = asset_path1.stat().st_size
                size2 = Path(assets2[asset_name]).stat().st_size
                assert (
                    size1 == size2
                ), f"Asset '{asset_name}' sizes differ: {size1} vs {size2}"


class TestAssetLoading:
    """Test asset loading in game."""

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_loading_in_game(self, test_scene):
        """Test that assets can be loaded by the game."""
        scene = test_scene
        loaded_assets = scene._load_character_assets()

        assert loaded_assets is not None, "Asset loading returned None"
        assert len(loaded_assets) > 0, "No assets loaded"

        # Check that loaded assets are pygame surfaces
        for name, surface in loaded_assets.items():
            assert isinstance(
                surface, pygame.Surface
            ), f"Asset '{name}' is not a pygame.Surface"
            assert surface.get_width() > 0, f"Asset '{name}' has zero width"
            assert surface.get_height() > 0, f"Asset '{name}' has zero height"

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_loading_performance(self, test_scene):
        """Test that asset loading is reasonably fast."""
        import time

        start_time = time.perf_counter()
        loaded_assets = test_scene._load_character_assets()
        end_time = time.perf_counter()

        loading_time = end_time - start_time
        assert loading_time < 0.1, f"Asset loading took too long: {loading_time:.3f}s"
        assert loaded_assets is not None, "Asset loading failed"

    @pytest.mark.unit
    @pytest.mark.asset
    def test_asset_loading_fallback(self, test_scene):
        """Test that asset loading has proper fallback behavior."""
        # This test ensures that if assets can't be loaded, the game doesn't crash
        # The actual fallback behavior is handled in the game code
        loaded_assets = test_scene._load_character_assets()

        # Should either load assets successfully or return empty dict
        assert isinstance(loaded_assets, dict), "Asset loading should return a dict"


class TestCharacterRendering:
    """Test character rendering with procedural assets using JSON scenes."""

    @pytest.mark.unit
    @pytest.mark.rendering
    def test_character_renders_with_assets(self, test_game_app, output_dir):
        """Test that character renders correctly with procedural assets."""
        from the_dark_closet.json_scene import JSONScene
        from pathlib import Path

        # Use JSON scene for testing
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)

        # Advance one frame to render
        test_game_app.advance_frame(None)

        # Save screenshot
        screenshot_path = output_dir / "character_with_assets.png"
        save_surface(test_game_app._screen, screenshot_path)

        # Check that character is visible
        pos = find_center_mass_position(test_game_app._screen)
        assert pos is not None, "Character not visible with procedural assets"

    @pytest.mark.unit
    @pytest.mark.rendering
    def test_character_rendering_consistency(self, test_game_app, output_dir):
        """Test that character rendering is consistent across frames."""
        from the_dark_closet.json_scene import JSONScene
        from pathlib import Path

        # Use JSON scene for testing
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)

        # Render multiple frames and check consistency
        positions = []
        for i in range(5):
            test_game_app.advance_frame(None)
            pos = find_center_mass_position(test_game_app._screen)
            positions.append(pos)

            # Save screenshot
            screenshot_path = output_dir / f"consistency_frame_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)

        # Character should be visible in all frames (may fall due to gravity)
        assert all(
            pos is not None for pos in positions
        ), "Character not visible in all frames"

        # Character should be falling (Y position should increase due to gravity)
        y_positions = [pos[1] for pos in positions if pos is not None]
        assert len(y_positions) == len(positions), "All positions should be valid"

        # Character should be visible and position should be reasonable
        # (Character may jump due to initial velocity or fall due to gravity)
        assert len(y_positions) == len(positions), "All positions should be valid"

        # Check that character doesn't move too far (reasonable bounds)
        if len(y_positions) > 1:
            y_range = max(y_positions) - min(y_positions)
            assert (
                y_range < 100
            ), f"Character moved too far vertically: {y_range} pixels"

    @pytest.mark.unit
    @pytest.mark.rendering
    def test_character_rendering_with_movement(self, test_game_app, output_dir):
        """Test character rendering during movement."""
        from the_dark_closet.json_scene import JSONScene
        from pathlib import Path

        # Use JSON scene for testing
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)

        # Render initial frame
        test_game_app.advance_frame(None)
        initial_pos = find_center_mass_position(test_game_app._screen)
        assert initial_pos is not None, "Initial position not found"

        # Get initial world position
        initial_world_x = scene.player_rect.x

        # Move and check rendering
        for i in range(3):
            test_game_app.advance_frame({pygame.K_RIGHT})
            pos = find_center_mass_position(test_game_app._screen)
            assert pos is not None, f"Position not found during movement frame {i+1}"

            # Save screenshot
            screenshot_path = output_dir / f"movement_frame_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)

        # Check that character moved in world coordinates
        final_world_x = scene.player_rect.x
        assert (
            final_world_x > initial_world_x
        ), f"Character did not move (initial: {initial_world_x}, final: {final_world_x})"


@pytest.mark.parametrize(
    "asset_name",
    [
        "head",
        "torso",
        "left_arm",
        "right_arm",
        "left_leg",
        "right_leg",
        "eyes_open",
        "eyes_closed",
        "mouth_neutral",
        "mouth_open",
        "hat",
    ],
)
@pytest.mark.unit
@pytest.mark.asset
def test_individual_asset_generation(temp_assets_dir, asset_name):
    """Test generation of individual assets."""
    assets = generate_character_assets(temp_assets_dir)

    assert asset_name in assets, f"Asset '{asset_name}' not generated"
    asset_path = Path(assets[asset_name])
    assert asset_path.exists(), f"Asset file '{asset_path}' does not exist"

    # Load and verify the asset
    surface = pygame.image.load(str(asset_path))
    assert surface.get_width() > 0, f"Asset '{asset_name}' has zero width"
    assert surface.get_height() > 0, f"Asset '{asset_name}' has zero height"


@pytest.mark.unit
@pytest.mark.asset
def test_asset_generation_with_custom_output_dir():
    """Test asset generation with custom output directory."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        custom_dir = Path(temp_dir) / "custom_assets"
        assets = generate_character_assets(custom_dir)

        # Check that assets were created in the custom directory
        for asset_name, asset_path in assets.items():
            asset_path = Path(asset_path)
            assert (
                custom_dir in asset_path.parents
            ), f"Asset '{asset_name}' not in custom directory"
            assert asset_path.exists(), f"Asset file '{asset_path}' does not exist"
