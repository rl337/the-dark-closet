"""
Visual showcase test for the new character composite object system.
This test generates screenshots that will be published to GitHub Pages.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pygame
from the_dark_closet.character import Character, CharacterState, CharacterDirection
from the_dark_closet.game import GameApp, GameConfig, ControlledTimeProvider


class TestCharacterShowcase:
    """Visual showcase for the new character system."""

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

    def test_character_directions_showcase(self):
        """Showcase character in different directions."""
        # Create test game
        config = GameConfig(1024, 768, "Character Directions Showcase", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Test different directions
        directions = [
            (CharacterDirection.FORWARD, "forward"),
            (CharacterDirection.LEFT, "left"),
            (CharacterDirection.RIGHT, "right"),
            (CharacterDirection.BACK, "back"),
        ]

        for i, (direction, name) in enumerate(directions):
            # Create character
            character = Character(x=400, y=300)
            character.set_direction(direction)
            character.idle()

            # Render
            surface.fill((18, 22, 30))  # Sky background
            character.draw(surface, camera_x=0, camera_y=0)

            # Save screenshot
            output_dir = Path("build/test_outputs/character_showcase")
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"character_direction_{name}.png"
            pygame.image.save(surface, str(output_dir / filename))
            print(f"Generated: {filename}")

    def test_character_states_showcase(self):
        """Showcase character in different states."""
        # Create test game
        config = GameConfig(1024, 768, "Character States Showcase", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Test different states
        states = [
            (CharacterState.IDLE, "idle"),
            (CharacterState.WALKING_LEFT, "walking_left"),
            (CharacterState.WALKING_RIGHT, "walking_right"),
            (CharacterState.JUMPING, "jumping"),
        ]

        for i, (state, name) in enumerate(states):
            # Create character
            character = Character(x=400, y=300)
            character.set_state(state)

            if state == CharacterState.WALKING_LEFT:
                character.set_direction(CharacterDirection.LEFT)
            elif state == CharacterState.WALKING_RIGHT:
                character.set_direction(CharacterDirection.RIGHT)
            else:
                character.set_direction(CharacterDirection.FORWARD)

            # Render
            surface.fill((18, 22, 30))  # Sky background
            character.draw(surface, camera_x=0, camera_y=0)

            # Save screenshot
            output_dir = Path("build/test_outputs/character_showcase")
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"character_state_{name}.png"
            pygame.image.save(surface, str(output_dir / filename))
            print(f"Generated: {filename}")

    def test_character_walk_cycle_showcase(self):
        """Showcase character walk cycle animation."""
        # Create test game
        config = GameConfig(1024, 768, "Character Walk Cycle Showcase", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Test walk cycles for both directions
        for direction_name, direction in [
            ("left", CharacterDirection.LEFT),
            ("right", CharacterDirection.RIGHT),
        ]:
            character = Character(x=400, y=300)
            character.set_direction(direction)

            if direction_name == "left":
                character.walk_left()
            else:
                character.walk_right()

            # Generate walk cycle frames
            for frame in range(8):  # 2 complete cycles
                # Update character animation
                character.update(1.0 / 60.0)  # 60 FPS

                # Move character horizontally
                if direction_name == "left":
                    character.move(-3, 0)  # Move left
                else:
                    character.move(3, 0)  # Move right

                # Render
                surface.fill((18, 22, 30))  # Sky background
                character.draw(surface, camera_x=0, camera_y=0)

                # Save every frame
                output_dir = Path("build/test_outputs/character_showcase")
                output_dir.mkdir(parents=True, exist_ok=True)
                filename = f"character_walk_{direction_name}_{frame:02d}.png"
                pygame.image.save(surface, str(output_dir / filename))
                print(f"Generated: {filename}")

    def test_character_composite_parts_showcase(self):
        """Showcase individual character parts and their positioning."""
        # Create test game
        config = GameConfig(1024, 768, "Character Parts Showcase", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Create character
        character = Character(x=400, y=300)
        character.idle()

        # Render character with all parts
        surface.fill((18, 22, 30))  # Sky background
        character.draw(surface, camera_x=0, camera_y=0)

        # Save screenshot
        output_dir = Path("build/test_outputs/character_showcase")
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = "character_composite_parts.png"
        pygame.image.save(surface, str(output_dir / filename))
        print(f"Generated: {filename}")

    def test_character_movement_showcase(self):
        """Showcase character movement across the screen."""
        # Create test game
        config = GameConfig(1024, 768, "Character Movement Showcase", 60)
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        GameApp(config, time_provider)  # Initialize pygame

        # Create test surface
        surface = pygame.Surface((1024, 768))

        # Create character
        character = Character(x=100, y=300)

        # Movement sequence: idle -> walk right -> idle -> walk left -> idle
        sequence = [
            ("idle", 30, 0, 0),
            ("walk_right", 60, 3, 0),  # Move right
            ("idle", 30, 0, 0),
            ("walk_left", 60, -3, 0),  # Move left
            ("idle", 30, 0, 0),
        ]

        frame_count = 0
        for phase_name, duration, dx, dy in sequence:
            print(f"Phase: {phase_name} for {duration} frames")

            # Set character state
            if phase_name == "idle":
                character.idle()
            elif phase_name == "walk_left":
                character.walk_left()
            elif phase_name == "walk_right":
                character.walk_right()

            # Run phase
            for frame in range(duration):
                # Update character
                character.update(1.0 / 60.0)  # 60 FPS

                # Move character
                character.move(dx, dy)

                # Render frame
                surface.fill((18, 22, 30))  # Sky background
                character.draw(surface, camera_x=0, camera_y=0)

                # Save every 5th frame for the showcase
                if frame_count % 5 == 0:
                    output_dir = Path("build/test_outputs/character_showcase")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"character_movement_{frame_count:03d}_{phase_name}.png"
                    pygame.image.save(surface, str(output_dir / filename))
                    print(f"Generated: {filename}")

                frame_count += 1

    def test_character_asset_generation_showcase(self):
        """Showcase the generated character assets."""
        from the_dark_closet.assets import generate_character_assets

        # Generate assets
        assets_dir = Path("build/test_outputs/character_showcase_assets")
        asset_paths = generate_character_assets(assets_dir)

        print(f"Generated {len(asset_paths)} character assets:")

        # Categorize assets
        basic_assets = [
            k
            for k in asset_paths.keys()
            if not any(
                x in k for x in ["_left", "_right", "_forward", "_back", "walk_"]
            )
        ]
        directional_assets = [
            k
            for k in asset_paths.keys()
            if any(x in k for x in ["_left", "_right", "_forward", "_back"])
            and not k.startswith("walk_")
        ]
        walk_cycle_assets = [k for k in asset_paths.keys() if k.startswith("walk_")]

        print(f"  Basic assets: {len(basic_assets)}")
        print(f"  Directional assets: {len(directional_assets)}")
        print(f"  Walk cycle assets: {len(walk_cycle_assets)}")

        # Verify all assets exist
        for asset_name, asset_path in asset_paths.items():
            assert Path(asset_path).exists(), f"Asset should exist: {asset_path}"

        print("All character assets generated successfully!")
