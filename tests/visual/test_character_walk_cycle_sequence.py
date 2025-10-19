"""
Visual test for character walk cycle sequence.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pygame
from the_dark_closet.character import Character, CharacterState, CharacterDirection
from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider


class TestCharacterWalkCycleSequence:
    """Test character walk cycle sequence visually."""

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

    def test_walk_cycle_sequence(self):
        """Test complete walk cycle sequence: idle -> walk left -> idle -> walk right -> idle."""
        # Create test game
        config = GameConfig(1024, 768, "Walk Cycle Test", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create character
        character = Character(x=400, y=300)

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Test sequence: idle -> walk left -> idle -> walk right -> idle
        sequence = [
            ("idle", 30),  # Idle for 0.5 seconds
            ("walk_left", 120),  # Walk left for 2 seconds
            ("idle", 30),  # Idle for 0.5 seconds
            ("walk_right", 120),  # Walk right for 2 seconds
            ("idle", 30),  # Idle for 0.5 seconds
        ]

        frame_count = 0

        for phase_name, phase_duration in sequence:
            print(f"Phase: {phase_name} for {phase_duration} frames")

            # Set character state
            if phase_name == "idle":
                character.idle()
            elif phase_name == "walk_left":
                character.walk_left()
            elif phase_name == "walk_right":
                character.walk_right()

            # Run phase
            for frame in range(phase_duration):
                # Update character
                character.update(1.0 / 60.0)  # 60 FPS

                # Move character horizontally during walk phases
                if phase_name == "walk_left":
                    character.move(-2, 0)  # Move left 2 pixels per frame
                elif phase_name == "walk_right":
                    character.move(2, 0)  # Move right 2 pixels per frame

                # Render frame
                surface.fill((18, 22, 30))  # Sky background
                character.draw(surface, camera_x=0, camera_y=0)

                # Save every 10th frame for analysis
                if frame_count % 10 == 0:
                    output_dir = Path("build/test_outputs/walk_cycle")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = (
                        f"walk_cycle_{frame_count:03d}_{phase_name}_{frame:02d}.png"
                    )
                    pygame.image.save(surface, str(output_dir / filename))

                frame_count += 1

        print(f"Generated {frame_count} frames of walk cycle animation")

        # Verify character ended up in expected position
        # Should have moved left 240 pixels, then right 240 pixels, net 0
        assert (
            abs(character.x - 400) < 10
        ), f"Character should be near starting position, got {character.x}"

        # Verify character is in idle state (direction preserved from last action)
        assert character.state == CharacterState.IDLE
        assert (
            character.direction == CharacterDirection.RIGHT
        )  # Last action was walk_right

    def test_walk_cycle_asset_generation(self):
        """Test that walk cycle assets are generated correctly."""
        from the_dark_closet.assets import generate_character_assets

        # Generate assets
        assets_dir = Path("build/test_outputs/walk_cycle_assets")
        asset_paths = generate_character_assets(assets_dir)

        # Check that walk cycle assets were generated
        walk_assets = [key for key in asset_paths.keys() if key.startswith("walk_")]
        assert len(walk_assets) > 0, "Should generate walk cycle assets"

        # Check for left and right walk cycles
        left_walk_assets = [key for key in walk_assets if "left" in key]
        right_walk_assets = [key for key in walk_assets if "right" in key]

        assert (
            len(left_walk_assets) == 4
        ), f"Should have 4 left walk frames, got {len(left_walk_assets)}"
        assert (
            len(right_walk_assets) == 4
        ), f"Should have 4 right walk frames, got {len(right_walk_assets)}"

        # Check that assets exist on disk
        for asset_path in asset_paths.values():
            assert Path(asset_path).exists(), f"Asset should exist: {asset_path}"

        print(f"Generated {len(walk_assets)} walk cycle assets")
        print(f"Left walk assets: {left_walk_assets}")
        print(f"Right walk assets: {right_walk_assets}")

    def test_character_state_transitions(self):
        """Test character state transitions work correctly."""
        character = Character(x=100, y=200)

        # Test state transitions
        assert character.state == CharacterState.IDLE

        character.walk_left()
        assert character.state == CharacterState.WALKING_LEFT
        assert character.direction == CharacterDirection.LEFT

        character.walk_right()
        assert character.state == CharacterState.WALKING_RIGHT
        assert character.direction == CharacterDirection.RIGHT

        character.jump()
        assert character.state == CharacterState.JUMPING

        character.idle()
        assert character.state == CharacterState.IDLE
        assert (
            character.direction == CharacterDirection.RIGHT
        )  # Direction preserved from walk_right

    def test_character_animation_timing(self):
        """Test character animation timing is consistent."""
        character = Character(x=100, y=200)
        character.walk_left()

        # Test animation speed
        initial_frame = character.animation_frame

        # Update with exactly one animation frame duration
        character.update(character.animation_speed)
        assert (
            character.animation_frame
            == (initial_frame + 1) % character.walk_cycle_frames
        )

        # Update with half animation frame duration
        character.update(character.animation_speed / 2)
        assert (
            character.animation_frame
            == (initial_frame + 1) % character.walk_cycle_frames
        )  # Should not advance

        # Update with another half to complete the frame
        character.update(character.animation_speed / 2)
        assert (
            character.animation_frame
            == (initial_frame + 2) % character.walk_cycle_frames
        )
