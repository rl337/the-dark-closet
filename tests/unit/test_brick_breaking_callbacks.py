"""
Test brick breaking callbacks and object deactivation.
"""

import pytest
import pygame
from pathlib import Path

from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider
from the_dark_closet.json_scene import JSONScene
from the_dark_closet.level_loader import LevelObject


class TestBrickBreakingCallbacks:
    """Test brick breaking callback system."""

    def test_brick_breaking_callback_system(self):
        """Test that brick breaking triggers callbacks and deactivates objects."""
        # Set up headless operation
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        os.environ["DISPLAY"] = ":99"

        # Create test game
        config = GameConfig(512, 384, "Brick Breaking Test", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        app = GameApp(config, time_provider)

        # Load the brick breaking test level
        level_path = Path("levels/test_brick_breaking.json")
        scene = JSONScene(app, level_path)
        app.switch_scene(scene)
        app.advance_frame(None)

        # Get initial brick count
        initial_bricks = [obj for obj in scene.level_data.get_objects_by_type("brick") if obj.is_active()]
        initial_count = len(initial_bricks)
        
        print(f"Initial brick count: {initial_count}")

        # Set up callback tracking
        broken_bricks = []
        
        def on_break_callback(brick):
            broken_bricks.append(brick.id)
            print(f"Brick {brick.id} was broken!")
        
        # Register callbacks for all breakable bricks
        for brick in initial_bricks:
            if "breakable" in brick.id:
                brick.register_callback("OnBreak", on_break_callback)

        # Test the collision detection directly by manually positioning the character
        # to collide with a breakable brick while moving upward
        breakable_brick = next((obj for obj in initial_bricks if "breakable" in obj.id), None)
        assert breakable_brick is not None, "Should have at least one breakable brick"
        
        brick_rect = breakable_brick.get_rect()
        print(f"Breakable brick at: {brick_rect}")
        
        # Position character to collide with the brick from below
        scene.player_rect.x = brick_rect.x + brick_rect.width // 2  # Center horizontally
        scene.player_rect.y = brick_rect.bottom - 10  # Just below the brick
        scene.player_velocity_y = -5  # Moving upward
        scene.on_ground = False  # Not on ground
        
        print(f"Positioned player at: {scene.player_rect}, velocity_y={scene.player_velocity_y}")
        
        # Call the collision detection directly
        scene._check_collisions()
        
        # Check results
        final_bricks = [obj for obj in scene.level_data.get_objects_by_type("brick") if obj.is_active()]
        final_count = len(final_bricks)
        
        print(f"Final brick count: {final_count}")
        print(f"Broken bricks: {broken_bricks}")

        # Assertions
        assert final_count < initial_count, f"Expected some bricks to be broken, but count went from {initial_count} to {final_count}"
        assert len(broken_bricks) > 0, f"Expected OnBreak callbacks to be triggered, but none were called"
        
        # Verify that broken bricks are inactive
        for brick_id in broken_bricks:
            brick = next((obj for obj in scene.level_data.get_objects_by_type("brick") if obj.id == brick_id), None)
            assert brick is not None, f"Could not find brick {brick_id}"
            assert not brick.is_active(), f"Brick {brick_id} should be inactive after breaking"

    def test_object_callback_registration(self):
        """Test that object callbacks can be registered and triggered."""
        # Create a test object
        obj_data = {
            "id": "test_brick",
            "type": "brick",
            "x": 0,
            "y": 0,
            "width": 128,
            "height": 128,
            "color": [135, 90, 60]
        }
        
        obj = LevelObject(obj_data)
        
        # Test callback registration and triggering
        callback_called = False
        callback_args = None
        
        def test_callback(*args, **kwargs):
            nonlocal callback_called, callback_args
            callback_called = True
            callback_args = (args, kwargs)
        
        # Register callback
        obj.register_callback("OnBreak", test_callback)
        
        # Trigger callback
        result = obj.trigger_callback("OnBreak", "test_arg", key="test_value")
        
        # Verify callback was called
        assert callback_called, "Callback should have been called"
        assert callback_args == (("test_arg",), {"key": "test_value"}), f"Callback args mismatch: {callback_args}"
        assert result is None, "Callback should return None by default"

    def test_object_deactivation(self):
        """Test that objects can be deactivated."""
        # Create a test object
        obj_data = {
            "id": "test_brick",
            "type": "brick",
            "x": 0,
            "y": 0,
            "width": 128,
            "height": 128,
            "color": [135, 90, 60]
        }
        
        obj = LevelObject(obj_data)
        
        # Initially active
        assert obj.is_active(), "Object should be active initially"
        
        # Deactivate
        obj.deactivate()
        
        # Should be inactive
        assert not obj.is_active(), "Object should be inactive after deactivation"
