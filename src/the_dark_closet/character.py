"""
Character composite object for The Dark Closet.

This module provides a Character class that manages its own position, state,
and rendering. The character is a composite object with body parts positioned
relative to its central position.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import pygame

from .assets import generate_character_assets


class CharacterState(Enum):
    """Character animation states."""

    IDLE = "idle"
    WALKING_LEFT = "walking_left"
    WALKING_RIGHT = "walking_right"
    JUMPING = "jumping"
    FALLING = "falling"


class CharacterDirection(Enum):
    """Character facing directions."""

    FORWARD = "forward"  # Facing camera
    LEFT = "left"  # Facing left
    RIGHT = "right"  # Facing right
    BACK = "back"  # Facing away from camera


class Character:
    """
    A composite character object that manages its own position, state, and rendering.

    The character consists of multiple body parts (head, torso, arms, legs) that are
    positioned relative to the character's central position. The character manages
    its own animation state and can be told to perform actions like walking or jumping.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: int = 104,
        height: int = 120,
        assets_dir: Optional[Path] = None,
    ):
        """
        Initialize the character.

        Args:
            x: Initial x position
            y: Initial y position
            width: Character width in pixels
            height: Character height in pixels
            assets_dir: Directory containing character assets
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Character state
        self.state = CharacterState.IDLE
        self.direction = CharacterDirection.FORWARD
        self.animation_frame = 0
        self.animation_timer = 0.0

        # Animation settings
        self.animation_speed = 0.1  # Seconds per frame
        self.walk_cycle_frames = 4  # Number of frames in walk cycle

        # Load character assets
        if assets_dir is None:
            assets_dir = Path("build/generated_assets")
        self._load_assets(assets_dir)

        # Character parts positioning (relative to character center)
        self._part_offsets = {
            "torso": (0, 10),
            "head": (0, -20),
            "left_arm": (-30, 5),
            "right_arm": (30, 5),
            "left_leg": (-15, 35),
            "right_leg": (15, 35),
        }

        # Facial feature offsets (relative to head)
        self._facial_offsets = {
            "eyes": (0, -5),
            "mouth": (0, 5),
        }

    def _load_assets(self, assets_dir: Path) -> None:
        """Load character assets from the assets directory."""
        try:
            asset_paths = generate_character_assets(assets_dir)
            self._assets = {}

            for asset_name, asset_path in asset_paths.items():
                if Path(asset_path).exists():
                    self._assets[asset_name] = pygame.image.load(asset_path)
                else:
                    print(f"Warning: Asset not found: {asset_path}")

        except Exception as e:
            print(f"Failed to load character assets: {e}")
            self._assets = {}

    def get_rect(self) -> pygame.Rect:
        """Get the character's bounding rectangle."""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def get_center(self) -> Tuple[float, float]:
        """Get the character's center position."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def set_position(self, x: float, y: float) -> None:
        """Set the character's position."""
        self.x = x
        self.y = y

    def move(self, dx: float, dy: float) -> None:
        """Move the character by the given offset."""
        self.x += dx
        self.y += dy

    def set_state(self, state: CharacterState) -> None:
        """Set the character's animation state."""
        if self.state != state:
            self.state = state
            self.animation_frame = 0
            self.animation_timer = 0.0

    def set_direction(self, direction: CharacterDirection) -> None:
        """Set the character's facing direction."""
        self.direction = direction

    def walk_left(self) -> None:
        """Start walking left."""
        self.set_state(CharacterState.WALKING_LEFT)
        self.set_direction(CharacterDirection.LEFT)

    def walk_right(self) -> None:
        """Start walking right."""
        self.set_state(CharacterState.WALKING_RIGHT)
        self.set_direction(CharacterDirection.RIGHT)

    def jump(self) -> None:
        """Start jumping."""
        self.set_state(CharacterState.JUMPING)

    def idle(self) -> None:
        """Set character to idle state."""
        self.set_state(CharacterState.IDLE)
        # Don't reset direction - keep current direction

    def update(self, delta_time: float) -> None:
        """Update character animation."""
        self.animation_timer += delta_time

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0

            if self.state in [
                CharacterState.WALKING_LEFT,
                CharacterState.WALKING_RIGHT,
            ]:
                # Cycle through walk animation frames
                self.animation_frame = (
                    self.animation_frame + 1
                ) % self.walk_cycle_frames
            elif self.state == CharacterState.IDLE:
                # Idle animation (subtle breathing or blinking)
                self.animation_frame = (self.animation_frame + 1) % 2

    def draw(
        self, surface: pygame.Surface, camera_x: float = 0.0, camera_y: float = 0.0
    ) -> None:
        """
        Draw the character on the given surface.

        Args:
            surface: Pygame surface to draw on
            camera_x: Camera x offset
            camera_y: Camera y offset
        """
        if not self._assets:
            # Fallback: draw a simple rectangle
            rect = self.get_rect()
            rect.x -= int(camera_x)
            rect.y -= int(camera_y)
            pygame.draw.rect(surface, (220, 80, 80), rect)
            return

        # Calculate character center for positioning
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2

        # Draw character parts
        self._draw_body_parts(surface, center_x, center_y, camera_x, camera_y)

        # Draw facial features
        self._draw_facial_features(surface, center_x, center_y, camera_x, camera_y)

        # Draw center mass dot for debugging
        self._draw_center_mass_dot(surface, center_x, center_y, camera_x, camera_y)

    def _draw_body_parts(
        self,
        surface: pygame.Surface,
        center_x: float,
        center_y: float,
        camera_x: float,
        camera_y: float,
    ) -> None:
        """Draw the character's body parts."""
        # Calculate scaling factor
        scale_x = self.width / 256.0
        scale_y = self.height / 256.0

        # Draw body parts in order (back to front)
        parts_order = [
            "left_leg",
            "right_leg",
            "torso",
            "left_arm",
            "right_arm",
            "head",
        ]

        for part in parts_order:
            # Get the asset for this part and direction
            asset = self._get_directional_asset(part)
            if asset is None:
                continue

            # Scale the asset
            scaled_asset = pygame.transform.scale(
                asset, (int(256 * scale_x), int(256 * scale_y))
            )

            # Position the part relative to character center
            base_offset_x, base_offset_y = self._part_offsets[part]

            # Add walk cycle animation offsets
            walk_offset_x, walk_offset_y = self._get_walk_cycle_offset(part)
            final_offset_x = float(base_offset_x) + walk_offset_x
            final_offset_y = float(base_offset_y) + walk_offset_y

            part_x = center_x + final_offset_x - scaled_asset.get_width() // 2
            part_y = center_y + final_offset_y - scaled_asset.get_height() // 2

            # Apply camera offset
            part_x -= camera_x
            part_y -= camera_y

            # Blit the asset
            surface.blit(scaled_asset, (int(part_x), int(part_y)))

    def _draw_facial_features(
        self,
        surface: pygame.Surface,
        center_x: float,
        center_y: float,
        camera_x: float,
        camera_y: float,
    ) -> None:
        """Draw the character's facial features."""
        # Calculate scaling factor
        scale_x = self.width / 256.0
        scale_y = self.height / 256.0

        # Head position
        head_offset_x, head_offset_y = self._part_offsets["head"]
        head_x = center_x + head_offset_x
        head_y = center_y + head_offset_y

        # Draw eyes
        if "eyes_open" in self._assets:
            eyes_asset = self._get_directional_asset("eyes_open")
            if eyes_asset:
                scaled_eyes = pygame.transform.scale(
                    eyes_asset, (int(256 * scale_x), int(256 * scale_y))
                )
                eyes_offset_x, eyes_offset_y = self._facial_offsets["eyes"]
                eyes_x = head_x + eyes_offset_x - scaled_eyes.get_width() // 2
                eyes_y = head_y + eyes_offset_y - scaled_eyes.get_height() // 2

                # Apply camera offset
                eyes_x -= camera_x
                eyes_y -= camera_y

                surface.blit(scaled_eyes, (int(eyes_x), int(eyes_y)))

        # Draw mouth
        if "mouth_neutral" in self._assets:
            mouth_asset = self._get_directional_asset("mouth_neutral")
            if mouth_asset:
                scaled_mouth = pygame.transform.scale(
                    mouth_asset, (int(256 * scale_x), int(256 * scale_y))
                )
                mouth_offset_x, mouth_offset_y = self._facial_offsets["mouth"]
                mouth_x = head_x + mouth_offset_x - scaled_mouth.get_width() // 2
                mouth_y = head_y + mouth_offset_y - scaled_mouth.get_height() // 2

                # Apply camera offset
                mouth_x -= camera_x
                mouth_y -= camera_y

                surface.blit(scaled_mouth, (int(mouth_x), int(mouth_y)))

    def _get_directional_asset(self, part: str) -> Optional[pygame.Surface]:
        """
        Get the appropriate asset for a body part based on current direction and state.
        """
        # Always use directional assets based on current direction
        direction_str = self.direction.value
        directional_asset_key = f"{part}_{direction_str}"
        if directional_asset_key in self._assets:
            return self._assets[directional_asset_key]

        # Fallback to basic asset
        return self._assets.get(part)

    def _get_walk_cycle_offset(self, part: str) -> Tuple[float, float]:
        """Get walk cycle animation offset for a body part."""
        if self.state not in [
            CharacterState.WALKING_LEFT,
            CharacterState.WALKING_RIGHT,
        ]:
            return (0, 0)

        # Calculate walk cycle offset based on animation frame
        import math

        walk_cycle_progress = self.animation_frame / self.walk_cycle_frames
        walk_offset = 3 * math.sin(walk_cycle_progress * 2 * math.pi)

        # Apply different offsets to different body parts for realistic walking
        if part in ["left_arm", "right_arm"]:
            # Arms swing opposite to each other
            if part == "left_arm":
                return (0, walk_offset)
            else:  # right_arm
                return (0, -walk_offset)
        elif part in ["left_leg", "right_leg"]:
            # Legs alternate
            if part == "left_leg":
                return (0, walk_offset)
            else:  # right_leg
                return (0, -walk_offset)
        else:
            # Head and torso have subtle movement
            return (0, walk_offset * 0.3)

    def _draw_center_mass_dot(
        self,
        surface: pygame.Surface,
        center_x: float,
        center_y: float,
        camera_x: float,
        camera_y: float,
    ) -> None:
        """Draw the center mass dot for debugging."""
        dot_x = center_x - 4 - camera_x
        dot_y = center_y - 4 - camera_y
        dot_rect = pygame.Rect(int(dot_x), int(dot_y), 8, 8)
        pygame.draw.rect(surface, (255, 0, 255), dot_rect)  # Bright magenta
