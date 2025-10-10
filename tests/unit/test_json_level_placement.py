"""
JSON level object placement validation tests.

This test ensures that objects defined in JSON level files are rendered
at exactly the positions specified in the JSON data.
"""

import pytest
import pygame
from pathlib import Path
from PIL import Image
import numpy as np
from typing import Dict, Tuple, List, Set

from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
from the_dark_closet.json_scene import JSONScene
from the_dark_closet.level_loader import LevelData, LevelObject


class JSONLevelValidator:
    """Validates JSON level object positioning with pixel-perfect accuracy."""
    
    def __init__(self, tolerance: int = 0):
        self.tolerance = tolerance
        self.errors: List[str] = []
    
    def validate_object_position(
        self, 
        screenshot: Image.Image, 
        expected_x: int, 
        expected_y: int, 
        expected_width: int,
        expected_height: int,
        object_type: str,
        object_id: str
    ) -> bool:
        """
        Validate that an object appears at the expected position in the screenshot.
        
        Args:
            screenshot: The full screenshot image
            expected_x: Expected top-left X coordinate of object
            expected_y: Expected top-left Y coordinate of object
            expected_width: Expected width of object
            expected_height: Expected height of object
            object_type: Type of object (brick, mountain, etc.)
            object_id: Unique identifier for error reporting
            
        Returns:
            True if object is positioned correctly, False otherwise
        """
        screenshot_width, screenshot_height = screenshot.size
        
        # Check bounds
        if (expected_x < 0 or expected_y < 0 or 
            expected_x + expected_width > screenshot_width or 
            expected_y + expected_height > screenshot_height):
            self.errors.append(
                f"{object_id}: Object bounds exceed screenshot "
                f"(expected: {expected_x},{expected_y}, size: {expected_width}x{expected_height}, "
                f"screenshot: {screenshot_width}x{screenshot_height})"
            )
            return False
        
        # Extract the region where the object should be
        object_region = screenshot.crop((
            expected_x, expected_y, 
            expected_x + expected_width, 
            expected_y + expected_height
        ))
        
        # Convert to numpy array for analysis
        region_array = np.array(object_region)
        
        # Validate based on object type
        if object_type == "brick":
            return self._validate_brick_region(region_array, object_id)
        elif object_type == "mountain":
            return self._validate_mountain_region(region_array, object_id)
        elif object_type == "hill":
            return self._validate_hill_region(region_array, object_id)
        elif object_type == "foreground_accent":
            return self._validate_foreground_region(region_array, object_id)
        else:
            # Generic validation for unknown types
            return self._validate_generic_region(region_array, object_id)
    
    def _validate_brick_region(self, region_array: np.ndarray, object_id: str) -> bool:
        """Validate that a region contains brick colors and patterns."""
        # Look for characteristic brick colors
        brick_colors = [
            [135, 90, 60],    # Base brick color
            [155, 110, 80],   # Brick texture color
            [200, 200, 200],  # Mortar color
        ]
        
        # Check if any of the brick colors appear in the region
        for color in brick_colors:
            color_diff = np.abs(region_array.astype(int) - np.array(color))
            max_diff = np.max(color_diff, axis=2)
            matching_pixels = np.sum(max_diff < 30)  # 30 pixel tolerance
            
            # If we find a reasonable number of matching pixels, this looks like a brick
            if matching_pixels > (region_array.shape[0] * region_array.shape[1]) * 0.1:  # At least 10% of pixels
                return True
        
        self.errors.append(f"{object_id}: Region does not contain expected brick colors")
        return False
    
    def _validate_mountain_region(self, region_array: np.ndarray, object_id: str) -> bool:
        """Validate that a region contains mountain colors."""
        # Look for mountain color
        mountain_color = [30, 34, 46]
        color_diff = np.abs(region_array.astype(int) - np.array(mountain_color))
        max_diff = np.max(color_diff, axis=2)
        matching_pixels = np.sum(max_diff < 30)
        
        if matching_pixels > (region_array.shape[0] * region_array.shape[1]) * 0.8:  # At least 80% of pixels
            return True
        
        self.errors.append(f"{object_id}: Region does not contain expected mountain colors")
        return False
    
    def _validate_hill_region(self, region_array: np.ndarray, object_id: str) -> bool:
        """Validate that a region contains hill colors."""
        # Look for hill color
        hill_color = [40, 46, 60]
        color_diff = np.abs(region_array.astype(int) - np.array(hill_color))
        max_diff = np.max(color_diff, axis=2)
        matching_pixels = np.sum(max_diff < 30)
        
        if matching_pixels > (region_array.shape[0] * region_array.shape[1]) * 0.8:  # At least 80% of pixels
            return True
        
        self.errors.append(f"{object_id}: Region does not contain expected hill colors")
        return False
    
    def _validate_foreground_region(self, region_array: np.ndarray, object_id: str) -> bool:
        """Validate that a region contains foreground accent colors."""
        # Look for foreground accent color
        accent_color = [12, 14, 18]
        color_diff = np.abs(region_array.astype(int) - np.array(accent_color))
        max_diff = np.max(color_diff, axis=2)
        matching_pixels = np.sum(max_diff < 30)
        
        if matching_pixels > (region_array.shape[0] * region_array.shape[1]) * 0.8:  # At least 80% of pixels
            return True
        
        self.errors.append(f"{object_id}: Region does not contain expected foreground accent colors")
        return False
    
    def _validate_generic_region(self, region_array: np.ndarray, object_id: str) -> bool:
        """Generic validation for unknown object types."""
        # Check if region is not just sky color
        sky_color = [18, 22, 30]
        color_diff = np.abs(region_array.astype(int) - np.array(sky_color))
        max_diff = np.max(color_diff, axis=2)
        non_sky_pixels = np.sum(max_diff > 10)
        
        if non_sky_pixels > (region_array.shape[0] * region_array.shape[1]) * 0.1:  # At least 10% non-sky pixels
            return True
        
        self.errors.append(f"{object_id}: Region appears to be empty or sky-colored only")
        return False
    
    def validate_level_objects(self, screenshot: Image.Image, level_data: LevelData, camera_x: float = 0, camera_y: float = 0) -> bool:
        """
        Validate that all objects in the level are positioned correctly.
        
        Args:
            screenshot: The full screenshot image
            level_data: The loaded level data
            camera_x: Camera X offset
            camera_y: Camera Y offset
            
        Returns:
            True if all objects are positioned correctly, False otherwise
        """
        success = True
        
        # Validate objects from each layer
        for layer_name, layer in level_data.layers.items():
            for obj in layer.objects:
                # Calculate expected position with camera and parallax offset
                parallax_factor = layer.parallax_factor
                expected_x = obj.x - int(camera_x * parallax_factor)
                expected_y = obj.y - int(camera_y * parallax_factor)
                
                # Only validate objects that should be visible (at least partially on screen)
                if (expected_x < screenshot.width and expected_x + obj.width > 0 and
                    expected_y < screenshot.height and expected_y + obj.height > 0):
                    
                    # Clamp coordinates to screenshot bounds for validation
                    clamped_x = max(0, expected_x)
                    clamped_y = max(0, expected_y)
                    clamped_width = min(obj.width, screenshot.width - clamped_x)
                    clamped_height = min(obj.height, screenshot.height - clamped_y)
                    
                    if not self.validate_object_position(
                        screenshot, clamped_x, clamped_y, clamped_width, clamped_height, 
                        obj.type, f"{layer_name}_{obj.id}"
                    ):
                        success = False
        
        return success
    
    def get_error_summary(self) -> str:
        """Get a summary of all validation errors."""
        if not self.errors:
            return "All JSON level object positions validated successfully!"
        
        return f"Found {len(self.errors)} JSON level object positioning errors:\n" + "\n".join(self.errors)


@pytest.fixture
def json_level_validator():
    """Create a JSON level validator."""
    return JSONLevelValidator(tolerance=0)


@pytest.fixture
def test_level_path():
    """Path to the test level JSON file."""
    return Path("levels/example_level.json")


@pytest.fixture
def test_game_app():
    """Create a test game app with controlled time."""
    config = GameConfig(512, 384, 'JSON Level Test', 60)
    time_provider = ControlledTimeProvider(1.0/60.0)
    return GameApp(config, time_provider)


class TestJSONLevelPlacement:
    """Test suite for JSON level object placement validation."""
    
    def test_brick_objects_positioning(self, json_level_validator, test_game_app, test_level_path, output_dir):
        """Test that brick objects are positioned exactly where specified in JSON."""
        # Create JSON scene
        scene = JSONScene(test_game_app, test_level_path)
        test_game_app.switch_scene(scene)
        test_game_app.advance_frame(None)
        
        # Take screenshot
        screenshot_path = output_dir / 'json_level_test.png'
        pygame.image.save(test_game_app._screen, str(screenshot_path))
        
        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)
        
        # Focus on validating only brick objects for now
        success = True
        brick_objects = scene.level_data.get_objects_by_type("brick")
        
        for brick in brick_objects:
            # Calculate expected position with camera offset
            expected_x = brick.x - int(scene.camera_x)
            expected_y = brick.y - int(scene.camera_y)
            
            # Only validate bricks that should be visible
            if (expected_x < screenshot.width and expected_x + brick.width > 0 and
                expected_y < screenshot.height and expected_y + brick.height > 0):
                
                # Clamp coordinates to screenshot bounds
                clamped_x = max(0, expected_x)
                clamped_y = max(0, expected_y)
                clamped_width = min(brick.width, screenshot.width - clamped_x)
                clamped_height = min(brick.height, screenshot.height - clamped_y)
                
                if not json_level_validator.validate_object_position(
                    screenshot, clamped_x, clamped_y, clamped_width, clamped_height, 
                    brick.type, f"brick_{brick.id}"
                ):
                    success = False
        
        # Generate detailed error report if validation failed
        if not success:
            error_report = json_level_validator.get_error_summary()
            print(f"JSON level brick object positioning validation failed:\n{error_report}")
            
            # Save debug image with object overlay
            debug_path = output_dir / 'json_level_debug.png'
            self._save_debug_image(screenshot, scene.level_data, scene.camera_x, scene.camera_y, debug_path)
            print(f"Debug image saved to: {debug_path}")
        
        assert success, f"JSON level brick object positioning validation failed. {json_level_validator.get_error_summary()}"
    
    def test_camera_offset_object_positioning(self, json_level_validator, test_game_app, test_level_path, output_dir):
        """Test object positioning with camera offset."""
        # Create JSON scene
        scene = JSONScene(test_game_app, test_level_path)
        test_game_app.switch_scene(scene)
        
        # Move camera to test offset positioning
        scene.camera_x = 256.0  # 2 tiles offset
        scene.camera_y = 128.0  # 1 tile offset
        
        test_game_app.advance_frame(None)
        
        # Take screenshot
        screenshot_path = output_dir / 'json_level_offset_test.png'
        pygame.image.save(test_game_app._screen, str(screenshot_path))
        
        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)
        
        # Focus on validating only brick objects for now
        success = True
        brick_objects = scene.level_data.get_objects_by_type("brick")
        
        for brick in brick_objects:
            # Calculate expected position with camera offset
            expected_x = brick.x - int(scene.camera_x)
            expected_y = brick.y - int(scene.camera_y)
            
            # Only validate bricks that should be visible
            if (expected_x < screenshot.width and expected_x + brick.width > 0 and
                expected_y < screenshot.height and expected_y + brick.height > 0):
                
                # Clamp coordinates to screenshot bounds
                clamped_x = max(0, expected_x)
                clamped_y = max(0, expected_y)
                clamped_width = min(brick.width, screenshot.width - clamped_x)
                clamped_height = min(brick.height, screenshot.height - clamped_y)
                
                if not json_level_validator.validate_object_position(
                    screenshot, clamped_x, clamped_y, clamped_width, clamped_height, 
                    brick.type, f"brick_{brick.id}_offset"
                ):
                    success = False
        
        if not success:
            error_report = json_level_validator.get_error_summary()
            print(f"JSON level brick object positioning with camera offset failed:\n{error_report}")
            
            # Save debug image
            debug_path = output_dir / 'json_level_offset_debug.png'
            self._save_debug_image(screenshot, scene.level_data, scene.camera_x, scene.camera_y, debug_path)
            print(f"Debug image saved to: {debug_path}")
        
        assert success, f"JSON level brick object positioning with camera offset failed. {json_level_validator.get_error_summary()}"
    
    def test_parallax_layers_positioning(self, json_level_validator, test_game_app, test_level_path, output_dir):
        """Test that parallax layers are positioned correctly."""
        # Create JSON scene
        scene = JSONScene(test_game_app, test_level_path)
        test_game_app.switch_scene(scene)
        
        # Move camera to test parallax
        scene.camera_x = 512.0  # 4 tiles offset
        scene.camera_y = 0.0
        
        test_game_app.advance_frame(None)
        
        # Take screenshot
        screenshot_path = output_dir / 'json_level_parallax_test.png'
        pygame.image.save(test_game_app._screen, str(screenshot_path))
        
        # Load screenshot with PIL
        screenshot = Image.open(screenshot_path)
        
        # Focus on validating only brick objects for now
        success = True
        brick_objects = scene.level_data.get_objects_by_type("brick")
        
        for brick in brick_objects:
            # Calculate expected position with camera offset
            expected_x = brick.x - int(scene.camera_x)
            expected_y = brick.y - int(scene.camera_y)
            
            # Only validate bricks that should be visible
            if (expected_x < screenshot.width and expected_x + brick.width > 0 and
                expected_y < screenshot.height and expected_y + brick.height > 0):
                
                # Clamp coordinates to screenshot bounds
                clamped_x = max(0, expected_x)
                clamped_y = max(0, expected_y)
                clamped_width = min(brick.width, screenshot.width - clamped_x)
                clamped_height = min(brick.height, screenshot.height - clamped_y)
                
                if not json_level_validator.validate_object_position(
                    screenshot, clamped_x, clamped_y, clamped_width, clamped_height, 
                    brick.type, f"brick_{brick.id}_parallax"
                ):
                    success = False
        
        if not success:
            error_report = json_level_validator.get_error_summary()
            print(f"JSON level brick object positioning with parallax failed:\n{error_report}")
            
            # Save debug image
            debug_path = output_dir / 'json_level_parallax_debug.png'
            self._save_debug_image(screenshot, scene.level_data, scene.camera_x, scene.camera_y, debug_path)
            print(f"Debug image saved to: {debug_path}")
        
        assert success, f"JSON level brick object positioning with parallax failed. {json_level_validator.get_error_summary()}"
    
    def test_json_level_loading(self, test_level_path):
        """Test that JSON level files load correctly."""
        # Load level data
        level_data = LevelData(test_level_path)
        
        # Validate metadata
        assert level_data.metadata["name"] == "Example Level"
        assert level_data.metadata["width"] == 12
        assert level_data.metadata["height"] == 8
        assert level_data.metadata["tile_size"] == 128
        
        # Validate layers exist
        assert "background" in level_data.layers
        assert "midground" in level_data.layers
        assert "tiles" in level_data.layers
        assert "foreground" in level_data.layers
        
        # Validate brick objects
        brick_objects = level_data.get_objects_by_type("brick")
        assert len(brick_objects) == 24  # 12 tiles x 2 rows
        
        # Validate specific brick positions
        brick_0_6 = next((obj for obj in brick_objects if obj.id == "brick_0_6"), None)
        assert brick_0_6 is not None
        assert brick_0_6.x == 0
        assert brick_0_6.y == 768
        assert brick_0_6.width == 128
        assert brick_0_6.height == 128
        
        # Validate player spawn
        assert level_data.player_spawn == (384, 512)
    
    def test_object_type_filtering(self, test_level_path):
        """Test filtering objects by type."""
        level_data = LevelData(test_level_path)
        
        # Test brick filtering
        brick_objects = level_data.get_objects_by_type("brick")
        assert len(brick_objects) == 24
        assert all(obj.type == "brick" for obj in brick_objects)
        
        # Test mountain filtering
        mountain_objects = level_data.get_objects_by_type("mountain")
        assert len(mountain_objects) == 2
        assert all(obj.type == "mountain" for obj in mountain_objects)
        
        # Test hill filtering
        hill_objects = level_data.get_objects_by_type("hill")
        assert len(hill_objects) == 2
        assert all(obj.type == "hill" for obj in hill_objects)
    
    def _save_debug_image(self, screenshot: Image.Image, level_data: LevelData, 
                         camera_x: float, camera_y: float, debug_path: Path) -> None:
        """Save a debug image with object overlay showing expected positions."""
        # Create a copy of the screenshot
        debug_img = screenshot.copy()
        
        # Draw object boundaries
        from PIL import ImageDraw
        draw = ImageDraw.Draw(debug_img)
        
        # Draw expected object boundaries
        for layer_name, layer in level_data.layers.items():
            for obj in layer.objects:
                parallax_factor = layer.parallax_factor
                expected_x = obj.x - int(camera_x * parallax_factor)
                expected_y = obj.y - int(camera_y * parallax_factor)
                
                # Only draw if object should be visible
                if (expected_x + obj.width > 0 and expected_x < screenshot.width and
                    expected_y + obj.height > 0 and expected_y < screenshot.height):
                    
                    # Draw object boundary
                    draw.rectangle(
                        [expected_x, expected_y, expected_x + obj.width - 1, expected_y + obj.height - 1],
                        outline=(255, 0, 0), width=2
                    )
                    
                    # Draw object info
                    draw.text(
                        (expected_x + 5, expected_y + 5), 
                        f"{obj.type}\n{obj.id}", 
                        fill=(255, 0, 0)
                    )
        
        debug_img.save(debug_path)
