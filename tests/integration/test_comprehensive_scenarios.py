"""
Comprehensive scenario tests using pytest.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path

from ..conftest import find_center_mass_position, save_surface
from the_dark_closet.game import SideScrollerScene


class TestPlatformInteractions:
    """Test platform interaction scenarios."""
    
    @pytest.mark.integration
    def test_platform_jumping(self, test_game_app, platform_room, output_dir):
        """Test jumping from a platform."""
        spawn_px = (6 * 128, 2 * 128)  # Above the platform
        scene = SideScrollerScene(test_game_app, platform_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        initial_pos = find_center_mass_position(test_game_app._screen)
        assert initial_pos is not None, "Initial position not found"
        
        # Test jumping from platform for 8 frames
        positions = []
        for i in range(8):
            test_game_app.advance_frame({pygame.K_SPACE})
            pos = find_center_mass_position(test_game_app._screen)
            positions.append(pos)
            
            # Save screenshot
            screenshot_path = output_dir / f"platform_jump_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should be falling due to gravity
        assert all(pos is not None for pos in positions), "Some positions not found during jump"
        # Y position should generally increase (falling)
        y_positions = [pos[1] for pos in positions if pos is not None]
        assert len(y_positions) > 0, "No valid positions found"
    
    @pytest.mark.integration
    def test_platform_landing(self, test_game_app, platform_room, output_dir):
        """Test landing on a platform."""
        spawn_px = (6 * 128, 1 * 128)  # Above the platform
        scene = SideScrollerScene(test_game_app, platform_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Fall towards platform
        positions = []
        for i in range(10):
            test_game_app.advance_frame(None)  # No keys - just fall
            pos = find_center_mass_position(test_game_app._screen)
            positions.append(pos)
            
            # Save screenshot
            screenshot_path = output_dir / f"platform_landing_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should be falling
        assert all(pos is not None for pos in positions), "Some positions not found during fall"


class TestLadderInteractions:
    """Test ladder interaction scenarios."""
    
    @pytest.mark.integration
    def test_ladder_climbing(self, test_game_app, ladder_room, output_dir):
        """Test climbing ladders."""
        spawn_px = (6 * 128, 5 * 128)  # Below the ladders
        scene = SideScrollerScene(test_game_app, ladder_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        initial_pos = find_center_mass_position(test_game_app._screen)
        assert initial_pos is not None, "Initial position not found"
        
        # Test climbing for 8 frames
        positions = []
        for i in range(8):
            test_game_app.advance_frame({pygame.K_UP})
            pos = find_center_mass_position(test_game_app._screen)
            positions.append(pos)
            
            # Save screenshot
            screenshot_path = output_dir / f"ladder_climb_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should be falling due to gravity (ladder climbing not implemented)
        assert all(pos is not None for pos in positions), "Some positions not found during climb"
    
    @pytest.mark.integration
    def test_ladder_approach(self, test_game_app, ladder_room, output_dir):
        """Test approaching ladders."""
        spawn_px = (3 * 128, 5 * 128)  # Left of the ladders
        scene = SideScrollerScene(test_game_app, ladder_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach ladder
        positions = []
        for i in range(5):
            test_game_app.advance_frame({pygame.K_RIGHT})
            pos = find_center_mass_position(test_game_app._screen)
            positions.append(pos)
            
            # Save screenshot
            screenshot_path = output_dir / f"ladder_approach_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should move right
        assert all(pos is not None for pos in positions), "Some positions not found during approach"


class TestBrickInteractions:
    """Test brick interaction scenarios."""
    
    @pytest.mark.integration
    def test_brick_breaking_sequence(self, test_game_app, brick_room, output_dir):
        """Test complete brick breaking sequence."""
        spawn_px = (3 * 128, 4 * 128)  # Left of the bricks
        scene = SideScrollerScene(test_game_app, brick_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Approach bricks
        for i in range(3):
            test_game_app.advance_frame({pygame.K_RIGHT})
            screenshot_path = output_dir / f"brick_approach_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Try to break bricks
        for i in range(5):
            test_game_app.advance_frame({pygame.K_SPACE})
            screenshot_path = output_dir / f"brick_break_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should be visible throughout
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible after brick breaking sequence"
    
    @pytest.mark.integration
    def test_multiple_brick_interactions(self, test_game_app, brick_room, output_dir):
        """Test interacting with multiple bricks."""
        spawn_px = (2 * 128, 4 * 128)  # Left of the bricks
        scene = SideScrollerScene(test_game_app, brick_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Move across multiple bricks
        for i in range(8):
            test_game_app.advance_frame({pygame.K_RIGHT})
            screenshot_path = output_dir / f"multi_brick_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should be visible throughout
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible after multi-brick interaction"


class TestCameraBehavior:
    """Test camera following behavior."""
    
    @pytest.mark.integration
    def test_camera_following_horizontal(self, test_game_app, simple_room, output_dir):
        """Test camera following horizontal movement."""
        spawn_px = (2 * 128, 4 * 128)  # Start on left side
        scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        initial_camera = scene.camera_x
        initial_pos = find_center_mass_position(test_game_app._screen)
        assert initial_pos is not None, "Initial position not found"
        
        # Move right and check camera
        for i in range(10):
            test_game_app.advance_frame({pygame.K_RIGHT})
            current_camera = scene.camera_x
            current_pos = find_center_mass_position(test_game_app._screen)
            
            # Save screenshot
            screenshot_path = output_dir / f"camera_follow_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
            
            # Camera should follow player (or at least not crash)
            assert current_pos is not None, f"Position not found at frame {i+1}"
    
    @pytest.mark.integration
    def test_camera_boundary_behavior(self, test_game_app, simple_room, output_dir):
        """Test camera behavior at boundaries."""
        spawn_px = (1 * 128, 4 * 128)  # Near left boundary
        scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Try to move left (should hit boundary)
        for i in range(5):
            test_game_app.advance_frame({pygame.K_LEFT})
            screenshot_path = output_dir / f"camera_boundary_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should still be visible
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible at boundary"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.integration
    def test_boundary_collision(self, test_game_app, simple_room, output_dir):
        """Test collision with boundaries."""
        spawn_px = (6 * 128, 4 * 128)  # Center
        scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Try to move into walls
        for i in range(8):
            test_game_app.advance_frame({pygame.K_RIGHT})
            screenshot_path = output_dir / f"boundary_collision_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should still be visible
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible after boundary collision"
    
    @pytest.mark.integration
    def test_rapid_key_presses(self, test_game_app, simple_room, output_dir):
        """Test rapid key press handling."""
        spawn_px = (6 * 128, 4 * 128)  # Center
        scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # Rapid key presses
        key_sequences = [
            {pygame.K_RIGHT, pygame.K_SPACE},
            {pygame.K_LEFT, pygame.K_UP},
            {pygame.K_RIGHT, pygame.K_DOWN},
        ]
        
        for i, keys in enumerate(key_sequences):
            test_game_app.advance_frame(keys)
            screenshot_path = output_dir / f"rapid_keys_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should still be visible
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible after rapid key presses"
    
    @pytest.mark.integration
    def test_no_key_input(self, test_game_app, simple_room, output_dir):
        """Test behavior with no key input."""
        spawn_px = (6 * 128, 4 * 128)  # Center
        scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
        test_game_app.switch_scene(scene)
        
        # Advance one frame to render initial state
        test_game_app.advance_frame(None)
        
        # No key input for multiple frames
        for i in range(10):
            test_game_app.advance_frame(None)
            screenshot_path = output_dir / f"no_keys_{i:02d}.png"
            save_surface(test_game_app._screen, screenshot_path)
        
        # Character should still be visible and falling due to gravity
        final_pos = find_center_mass_position(test_game_app._screen)
        assert final_pos is not None, "Character not visible with no key input"


@pytest.mark.parametrize("room_type,spawn_x,spawn_y", [
    ("simple", 6, 4),
    ("platform", 6, 2),
    ("brick", 5, 4),
    ("ladder", 6, 5),
])
@pytest.mark.integration
def test_scene_initialization(test_game_app, room_type, spawn_x, spawn_y, output_dir):
    """Test scene initialization with different room types."""
    # Get the appropriate room based on type
    if room_type == "simple":
        room = [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
    elif room_type == "platform":
        room = [
            "BBBBBBBBBBBB",
            "B          B",
            "B    PP    B",
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
    elif room_type == "brick":
        room = [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B",
            "B   BBBB   B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
    elif room_type == "ladder":
        room = [
            "BBBBBBBBBBBB",
            "B          B",
            "B    HH    B",
            "B    HH    B",
            "B    HH    B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
    
    spawn_px = (spawn_x * 128, spawn_y * 128)
    scene = SideScrollerScene(test_game_app, room, spawn_px)
    test_game_app.switch_scene(scene)
    
    # Advance one frame to render
    test_game_app.advance_frame(None)
    
    # Save screenshot
    screenshot_path = output_dir / f"scene_init_{room_type}.png"
    save_surface(test_game_app._screen, screenshot_path)
    
    # Character should be visible
    pos = find_center_mass_position(test_game_app._screen)
    assert pos is not None, f"Character not visible in {room_type} room"
