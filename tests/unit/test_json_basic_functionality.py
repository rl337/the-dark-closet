"""
JSON-based basic functionality tests using pytest.

These tests use JSON level files instead of hardcoded room layouts.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path

from ..conftest import find_center_mass_position, assert_center_mass_at, save_surface
from the_dark_closet.json_scene import JSONScene


class TestJSONMovement:
    """Test basic movement functionality using JSON levels."""
    
    @pytest.mark.unit
    def test_move_right(self, test_game_app, output_dir):
        """Test right movement with position assertions using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        
        # Test right movement for 4 frames
        for i in range(4):
            test_game_app.advance_frame({pygame.K_RIGHT})
            
            # Save screenshot
            screenshot_path = output_dir / f"json_move_right_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character moved in world coordinates
        final_world_x = scene.player_rect.x
        assert final_world_x > initial_world_x, f"Character did not move right (initial: {initial_world_x}, final: {final_world_x})"
        
        # Check that character is still visible (camera following)
        assert assert_center_mass_at(test_game_app._screen, 252, 192), "Character not visible after movement"
    
    @pytest.mark.unit
    def test_move_left(self, test_game_app, output_dir):
        """Test left movement with position assertions using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        
        # Test left movement for 4 frames
        for i in range(4):
            test_game_app.advance_frame({pygame.K_LEFT})
            
            # Save screenshot
            screenshot_path = output_dir / f"json_move_left_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character moved in world coordinates
        final_world_x = scene.player_rect.x
        assert final_world_x < initial_world_x, f"Character did not move left (initial: {initial_world_x}, final: {final_world_x})"
        
        # Check that character is still visible (camera following)
        assert assert_center_mass_at(test_game_app._screen, 252, 192), "Character not visible after movement"
    
    @pytest.mark.unit
    def test_combined_movement(self, test_game_app, output_dir):
        """Test combined movement using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Get initial position
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        
        # Move right then left
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
        
        for i in range(2):
            test_game_app.advance_frame({pygame.K_LEFT})
        
        # Save final screenshot
        screenshot_path = output_dir / "json_combined_movement.png"
        save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character is back near starting position
        final_world_x = scene.player_rect.x
        assert abs(final_world_x - initial_world_x) < 10, f"Character not back near start (initial: {initial_world_x}, final: {final_world_x})"
        
        # Check that character is still visible
        assert assert_center_mass_at(test_game_app._screen, 252, 192), "Character not visible after movement"


class TestJSONJumping:
    """Test jumping functionality using JSON levels."""
    
    @pytest.mark.unit
    def test_jump_attempt(self, test_game_app, output_dir):
        """Test jump attempt using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        initial_world_y = scene.player_rect.y
        
        # Test jump for 4 frames
        for i in range(4):
            test_game_app.advance_frame({pygame.K_SPACE})
            
            # Save screenshot
            screenshot_path = output_dir / f"json_jump_attempt_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character jumped (moved up in world coordinates)
        final_world_y = scene.player_rect.y
        assert final_world_y < initial_world_y, f"Character did not jump (initial: {initial_world_y}, final: {final_world_y})"
        
        # Check that character is still visible (position changes during jump due to camera following)
        assert assert_center_mass_at(test_game_app._screen, 252, 188), "Character not visible after jump"
    
    @pytest.mark.unit
    def test_continue_falling(self, test_game_app, output_dir):
        """Test falling after jump using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # First jump to get off the ground and wait for peak
        test_game_app.advance_frame({pygame.K_SPACE})
        # Wait more frames for character to reach peak of jump and start falling
        # Jump speed 420, gravity 1200 = ~21 frames to peak at 60fps
        for _ in range(25):
            test_game_app.advance_frame(None)
        
        # Verify character is actually falling (positive velocity)
        assert scene.player_velocity_y > 0, f"Character not falling yet (velocity: {scene.player_velocity_y})"
        
        initial_world_y = scene.player_rect.y
        
        # Test falling for 4 frames
        for i in range(4):
            test_game_app.advance_frame(None)  # No keys pressed
            
            # Save screenshot
            screenshot_path = output_dir / f"json_continue_falling_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character fell (moved down in world coordinates)
        final_world_y = scene.player_rect.y
        assert final_world_y > initial_world_y, f"Character did not fall (initial: {initial_world_y}, final: {final_world_y})"
        
        # Check that character is still visible
        assert assert_center_mass_at(test_game_app._screen, 252, 188), "Character not visible after falling"


class TestJSONBrickBreaking:
    """Test brick breaking functionality using JSON levels."""
    
    @pytest.mark.unit
    def test_approach_brick(self, test_game_app, output_dir):
        """Test approaching breakable brick using JSON level."""
        level_path = Path("levels/test_brick_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        
        # Move towards brick
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
            
            # Save screenshot
            screenshot_path = output_dir / f"json_approach_brick_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character moved towards brick
        final_world_x = scene.player_rect.x
        assert final_world_x > initial_world_x, f"Character did not move towards brick (initial: {initial_world_x}, final: {final_world_x})"
        
        # Check that character is still visible
        assert assert_center_mass_at(test_game_app._screen, 252, 192), "Character not visible after approaching brick"
    
    @pytest.mark.unit
    def test_break_brick(self, test_game_app, output_dir):
        """Test breaking brick using JSON level."""
        level_path = Path("levels/test_brick_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        initial_world_y = scene.player_rect.y
        
        # Move towards brick and break it
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
        
        for i in range(4):
            test_game_app.advance_frame({pygame.K_SPACE})
            
            # Save screenshot
            screenshot_path = output_dir / f"json_break_brick_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character moved and jumped
        final_world_x = scene.player_rect.x
        final_world_y = scene.player_rect.y
        assert final_world_x > initial_world_x, f"Character did not move towards brick (initial: {initial_world_x}, final: {final_world_x})"
        assert final_world_y < initial_world_y, f"Character did not jump (initial: {initial_world_y}, final: {final_world_y})"
        
        # Check that character is still visible (position changes during jump due to camera following)
        assert assert_center_mass_at(test_game_app._screen, 252, 188), "Character not visible after breaking brick"


class TestJSONCharacterRendering:
    """Test character rendering using JSON levels."""
    
    @pytest.mark.unit
    def test_character_visible(self, test_game_app, output_dir):
        """Test that character is visible using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Save screenshot
        screenshot_path = output_dir / "json_character_visible.png"
        save_surface(test_game_app._screen, screenshot_path)
        
        # Check that character is visible (center mass dot should be present)
        pos = find_center_mass_position(test_game_app._screen)
        assert pos is not None, "Character not visible (no center mass dot found)"
    
    @pytest.mark.unit
    def test_character_moves(self, test_game_app, output_dir):
        """Test that character moves using JSON level."""
        level_path = Path("levels/test_simple_room.json")
        scene = JSONScene(test_game_app, level_path)
        test_game_app.switch_scene(scene)
        
        # Get initial world position
        test_game_app.advance_frame(None)
        initial_world_x = scene.player_rect.x
        
        # Move character
        test_game_app.advance_frame({pygame.K_RIGHT})
        final_world_x = scene.player_rect.x
        
        # Character should have moved in world coordinates
        assert final_world_x > initial_world_x, f"Character did not move (initial: {initial_world_x}, final: {final_world_x})"
        
        # Character should still be visible (camera follows)
        assert assert_center_mass_at(test_game_app._screen, 252, 192), "Character not visible after movement"


@pytest.mark.parametrize("keys,expected_movement", [
    ({pygame.K_RIGHT}, "right"),
    ({pygame.K_LEFT}, "left"),
    ({pygame.K_SPACE}, "jump"),
])
def test_movement_parametrized(test_game_app, keys, expected_movement, output_dir):
    """Parametrized movement test using JSON level."""
    level_path = Path("levels/test_simple_room.json")
    scene = JSONScene(test_game_app, level_path)
    test_game_app.switch_scene(scene)
    
    # Advance one frame to render initial state
    test_game_app.advance_frame(None)
    initial_world_x = scene.player_rect.x
    initial_world_y = scene.player_rect.y
    
    # Test movement for 4 frames
    for i in range(4):
        test_game_app.advance_frame(keys)
    
    # Save final screenshot
    screenshot_path = output_dir / f"json_parametrized_{keys}_{0:02d}.png"
    save_surface(test_game_app._screen, screenshot_path)
    
    # Check movement based on expected type
    final_world_x = scene.player_rect.x
    final_world_y = scene.player_rect.y
    
    if expected_movement == "right":
        assert final_world_x > initial_world_x, f"Character did not move right (initial: {initial_world_x}, final: {final_world_x})"
    elif expected_movement == "left":
        assert final_world_x < initial_world_x, f"Character did not move left (initial: {initial_world_x}, final: {final_world_x})"
    elif expected_movement == "jump":
        assert final_world_y < initial_world_y, f"Character did not jump (initial: {initial_world_y}, final: {final_world_y})"
    
    # Check that character is still visible (position changes during jump due to camera following)
    if expected_movement == "jump":
        assert assert_center_mass_at(test_game_app._screen, 252, 188), f"Character not visible after {expected_movement}"
    else:
        assert assert_center_mass_at(test_game_app._screen, 252, 192), f"Character not visible after {expected_movement}"
