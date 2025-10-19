"""
Test character walk cycle functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pygame
from the_dark_closet.character import Character, CharacterState, CharacterDirection


class TestCharacterWalkCycle:
    """Test character walk cycle functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Set up headless operation
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        os.environ["DISPLAY"] = ":99"

        # Initialize pygame
        pygame.init()

    def teardown_method(self):
        """Clean up after test."""
        pygame.quit()

    def test_character_initialization(self):
        """Test character initializes correctly."""
        character = Character(x=100, y=200)

        assert character.x == 100
        assert character.y == 200
        assert character.state == CharacterState.IDLE
        assert character.direction == CharacterDirection.FORWARD
        assert character.animation_frame == 0

    def test_character_walk_left(self):
        """Test character walking left."""
        character = Character(x=100, y=200)

        character.walk_left()

        assert character.state == CharacterState.WALKING_LEFT
        assert character.direction == CharacterDirection.LEFT

    def test_character_walk_right(self):
        """Test character walking right."""
        character = Character(x=100, y=200)

        character.walk_right()

        assert character.state == CharacterState.WALKING_RIGHT
        assert character.direction == CharacterDirection.RIGHT

    def test_character_jump(self):
        """Test character jumping."""
        character = Character(x=100, y=200)

        character.jump()

        assert character.state == CharacterState.JUMPING

    def test_character_idle(self):
        """Test character returning to idle."""
        character = Character(x=100, y=200)

        # Start walking
        character.walk_left()
        assert character.state == CharacterState.WALKING_LEFT

        # Return to idle
        character.idle()
        assert character.state == CharacterState.IDLE
        assert (
            character.direction == CharacterDirection.LEFT
        )  # Direction should be preserved

    def test_character_animation_update(self):
        """Test character animation updates correctly."""
        character = Character(x=100, y=200)
        character.walk_left()

        # Update animation
        character.update(0.1)  # 0.1 seconds

        # Should advance to next frame
        assert character.animation_frame == 1

        # Update again
        character.update(0.1)
        assert character.animation_frame == 2

    def test_character_walk_cycle_loops(self):
        """Test walk cycle loops correctly."""
        character = Character(x=100, y=200)
        character.walk_left()

        # Advance through all frames
        for i in range(5):  # More than the cycle length
            character.update(0.1)

        # Should loop back to 0
        assert character.animation_frame == 1  # 5 % 4 = 1

    def test_character_positioning(self):
        """Test character positioning methods."""
        character = Character(x=100, y=200)

        # Test get_rect
        rect = character.get_rect()
        assert rect.x == 100
        assert rect.y == 200
        assert rect.width == 104
        assert rect.height == 120

        # Test get_center
        center_x, center_y = character.get_center()
        assert center_x == 152  # 100 + 104/2
        assert center_y == 260  # 200 + 120/2

        # Test set_position
        character.set_position(300, 400)
        assert character.x == 300
        assert character.y == 400

        # Test move
        character.move(50, -25)
        assert character.x == 350
        assert character.y == 375

    def test_character_rendering(self):
        """Test character can be rendered without errors."""
        character = Character(x=100, y=200)

        # Create a test surface
        surface = pygame.Surface((800, 600))

        # Render character (should not raise exceptions)
        character.draw(surface, camera_x=0, camera_y=0)

        # Character should be visible (not just transparent)
        # Check that some pixels were drawn
        pixels = pygame.surfarray.array3d(surface)
        has_content = pixels.any()
        assert has_content

    def test_character_walk_cycle_rendering(self):
        """Test walk cycle rendering produces different frames."""
        character = Character(x=100, y=200)
        character.walk_left()

        # Create test surface
        surface = pygame.Surface((800, 600))

        # Render first frame
        character.draw(surface, camera_x=0, camera_y=0)
        frame1_pixels = pygame.surfarray.array3d(surface).copy()

        # Advance animation
        character.update(0.1)
        character.draw(surface, camera_x=0, camera_y=0)
        frame2_pixels = pygame.surfarray.array3d(surface)

        # Frames should be different (walk cycle animation)
        frames_different = not (frame1_pixels == frame2_pixels).all()
        assert frames_different, "Walk cycle frames should be different"

    def test_character_directional_assets(self):
        """Test character uses different assets for different directions."""
        character = Character(x=100, y=200)

        # Test left direction
        character.set_direction(CharacterDirection.LEFT)
        character.idle()  # Set to idle state

        surface = pygame.Surface((800, 600))
        character.draw(surface, camera_x=0, camera_y=0)
        left_pixels = pygame.surfarray.array3d(surface).copy()

        # Test right direction
        character.set_direction(CharacterDirection.RIGHT)
        surface.fill((0, 0, 0))  # Clear surface
        character.draw(surface, camera_x=0, camera_y=0)
        right_pixels = pygame.surfarray.array3d(surface)

        # Directions should produce different renders
        directions_different = not (left_pixels == right_pixels).all()
        assert (
            directions_different
        ), "Left and right directions should produce different renders"
