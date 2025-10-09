"""
Basic functionality tests using pytest.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path

from ..conftest import find_center_mass_position, assert_center_mass_at, save_surface
from the_dark_closet.game import SideScrollerScene


class TestMovement:
    """Test basic movement functionality."""
    
    @pytest.mark.unit
    def test_move_right(self, test_scene, output_dir):
        """Test right movement with position assertions."""
        app = test_scene.app
        
        # Advance one frame to render initial state
        app.advance_frame(None)
        
        # Test right movement for 4 frames
        for i in range(4):
            app.advance_frame({pygame.K_RIGHT})
            
            # Save screenshot
            screenshot_path = output_dir / f"move_right_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(app._screen, 444, 571), f"Frame {i+1}: Wrong position"
    
    @pytest.mark.unit
    def test_move_left(self, test_scene, output_dir):
        """Test left movement with position assertions."""
        app = test_scene.app
        
        # Advance one frame to render initial state
        app.advance_frame(None)
        
        # Test left movement for 4 frames
        for i in range(4):
            app.advance_frame({pygame.K_LEFT})
            
            # Save screenshot
            screenshot_path = output_dir / f"move_left_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(app._screen, 432, 580), f"Frame {i+1}: Wrong position"
    
    @pytest.mark.unit
    def test_combined_movement(self, test_scene, output_dir):
        """Test combined left-right movement."""
        app = test_scene.app
        
        # Advance one frame to render initial state
        app.advance_frame(None)
        
        # Move right then left
        for i in range(4):
            app.advance_frame({pygame.K_RIGHT})
            screenshot_path = output_dir / f"combined_right_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
        
        for i in range(4):
            app.advance_frame({pygame.K_LEFT})
            screenshot_path = output_dir / f"combined_left_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
        
        # Final position should be back to start
        assert assert_center_mass_at(app._screen, 432, 580), "Final position incorrect"


class TestJumping:
    """Test jumping functionality."""
    
    @pytest.mark.unit
    def test_jump_attempt(self, test_scene, output_dir):
        """Test jump attempt (player falls due to gravity)."""
        app = test_scene.app
        
        # Advance one frame to render initial state
        app.advance_frame(None)
        
        # Test jump attempt for 4 frames
        for i in range(4):
            app.advance_frame({pygame.K_SPACE})
            
            # Save screenshot
            screenshot_path = output_dir / f"jump_attempt_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(app._screen, 813, 571), f"Frame {i+1}: Wrong position"
    
    @pytest.mark.unit
    def test_continue_falling(self, test_scene, output_dir):
        """Test continued falling after jump attempt."""
        app = test_scene.app
        
        # Advance one frame to render initial state
        app.advance_frame(None)
        
        # Jump attempt first
        for i in range(4):
            app.advance_frame({pygame.K_SPACE})
        
        # Continue falling
        for i in range(4):
            app.advance_frame(None)
            
            # Save screenshot
            screenshot_path = output_dir / f"continue_falling_{i:02d}.png"
            save_surface(app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(app._screen, 813, 580), f"Frame {i+1}: Wrong position"


class TestBrickBreaking:
    """Test brick breaking functionality."""
    
    @pytest.mark.unit
    def test_approach_brick(self, test_game_app, brick_room, output_dir):
        """Test approaching breakable bricks."""
        spawn_px = (5 * 128, 4 * 128)  # Near the bricks
        scene = SideScrollerScene(test_game_app, brick_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach brick for 2 frames
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
            
            # Save screenshot
            screenshot_path = output_dir / f"approach_brick_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 1:  # Final frame
                assert assert_center_mass_at(test_game_app._screen, 694, 569), f"Frame {i+1}: Wrong position"
    
    @pytest.mark.unit
    def test_break_brick(self, test_game_app, brick_room, output_dir):
        """Test brick breaking attempt."""
        spawn_px = (5 * 128, 4 * 128)  # Near the bricks
        scene = SideScrollerScene(test_game_app, brick_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach brick first
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
        
        # Try to break brick for 4 frames
        for i in range(4):
            test_game_app.advance_frame({pygame.K_SPACE})
            
            # Save screenshot
            screenshot_path = output_dir / f"break_brick_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(test_game_app._screen, 694, 575), f"Frame {i+1}: Wrong position"


class TestLadderClimbing:
    """Test ladder climbing functionality."""
    
    @pytest.mark.unit
    def test_approach_ladder(self, test_game_app, ladder_room, output_dir):
        """Test approaching ladders."""
        spawn_px = (6 * 128, 5 * 128)  # Below the ladders
        scene = SideScrollerScene(test_game_app, ladder_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach ladder for 2 frames
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
            
            # Save screenshot
            screenshot_path = output_dir / f"approach_ladder_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 1:  # Final frame
                assert assert_center_mass_at(test_game_app._screen, 822, 697), f"Frame {i+1}: Wrong position"
    
    @pytest.mark.unit
    def test_climb_ladder(self, test_game_app, ladder_room, output_dir):
        """Test ladder climbing attempt."""
        spawn_px = (6 * 128, 5 * 128)  # Below the ladders
        scene = SideScrollerScene(test_game_app, ladder_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach ladder first
        for i in range(2):
            test_game_app.advance_frame({pygame.K_RIGHT})
        
        # Try to climb for 4 frames
        for i in range(4):
            test_game_app.advance_frame({pygame.K_UP})
            
            # Save screenshot
            screenshot_path = output_dir / f"climb_ladder_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
            
            # Check position (based on calibration data)
            if i == 3:  # Final frame
                assert assert_center_mass_at(test_game_app._screen, 822, 703), f"Frame {i+1}: Wrong position"


class TestCharacterRendering:
    """Test character rendering functionality."""
    
    @pytest.mark.unit
    @pytest.mark.rendering
    def test_character_visible(self, test_scene):
        """Test that character is visible and renders correctly."""
        app = test_scene.app
        
        # Advance one frame to render
        app.advance_frame(None)
        
        # Check that center mass dot is present (indicates character is rendering)
        pos = find_center_mass_position(app._screen)
        assert pos is not None, "Character not visible (no center mass dot found)"
    
    @pytest.mark.unit
    @pytest.mark.rendering
    def test_character_moves(self, test_scene):
        """Test that character moves when keys are pressed."""
        app = test_scene.app
        
        # Get initial position
        app.advance_frame(None)
        initial_pos = find_center_mass_position(app._screen)
        assert initial_pos is not None, "Initial position not found"
        
        # Move right
        app.advance_frame({pygame.K_RIGHT})
        moved_pos = find_center_mass_position(app._screen)
        assert moved_pos is not None, "Position after movement not found"
        
        # Position should have changed
        assert moved_pos != initial_pos, "Character did not move"


@pytest.mark.parametrize("keys,expected_final_pos", [
    ({pygame.K_RIGHT}, (444, 571)),
    ({pygame.K_LEFT}, (432, 580)),
    ({pygame.K_SPACE}, (813, 571)),
])
@pytest.mark.unit
def test_movement_parametrized(test_scene, keys, expected_final_pos, output_dir):
    """Parametrized test for different movement types."""
    app = test_scene.app
    
    # Advance one frame to render initial state
    app.advance_frame(None)
    
    # Move for 4 frames
    for i in range(4):
        app.advance_frame(keys)
        
        # Save screenshot
        screenshot_path = output_dir / f"parametrized_{keys}_{i:02d}.png"
        save_surface(app._screen, screenshot_path)
    
    # Check final position
    assert assert_center_mass_at(app._screen, expected_final_pos[0], expected_final_pos[1]), \
        f"Final position incorrect for keys {keys}"
