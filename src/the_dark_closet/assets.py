"""
Procedural asset generation for Pinocchio-inspired character sprites.
Generates all character parts programmatically at build time.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Tuple, Optional

import pygame


class PinocchioAssetGenerator:
    """Generates Pinocchio-inspired character assets procedurally."""

    def __init__(self, canvas_size: Tuple[int, int] = (256, 256)):
        self.canvas_size = canvas_size
        self.width, self.height = canvas_size

        # Pinocchio-inspired color palette
        self.colors = {
            "skin": (255, 220, 177),  # Warm skin tone
            "skin_shadow": (220, 180, 140),  # Darker skin for shadows
            "wood": (139, 69, 19),  # Wood brown
            "wood_light": (160, 82, 45),  # Lighter wood
            "wood_dark": (101, 67, 33),  # Darker wood
            "hat": (139, 0, 0),  # Red hat
            "hat_band": (255, 215, 0),  # Gold band
            "shirt": (70, 130, 180),  # Blue shirt
            "pants": (34, 139, 34),  # Green pants
            "shoes": (25, 25, 25),  # Black shoes
            "eyes": (0, 0, 0),  # Black eyes
            "mouth": (220, 20, 60),  # Red mouth
            "nose": (255, 182, 193),  # Pink nose
            "hair": (101, 67, 33),  # Brown hair
        }

        # Character proportions (Pinocchio-inspired)
        self.proportions = {
            "head_radius": 40,
            "torso_width": 60,
            "torso_height": 80,
            "arm_length": 50,
            "arm_width": 20,
            "leg_length": 60,
            "leg_width": 25,
            "hand_size": 15,
            "foot_size": 20,
        }

    def create_surface(self) -> pygame.Surface:
        """Create a transparent surface for drawing."""
        surface = pygame.Surface(self.canvas_size, pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Transparent background
        return surface

    def draw_circle_with_shading(
        self,
        surface: pygame.Surface,
        center: Tuple[int, int],
        radius: int,
        color: Tuple[int, int, int],
        shadow_color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """Draw a circle with subtle shading."""
        if shadow_color is None:
            shadow_color = tuple(max(0, c - 30) for c in color)  # type: ignore

        # Main circle
        pygame.draw.circle(surface, color, center, radius)

        # Highlight
        highlight_center = (center[0] - radius // 3, center[1] - radius // 3)
        highlight_radius = radius // 3
        highlight_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.circle(surface, highlight_color, highlight_center, highlight_radius)

        # Shadow
        shadow_center = (center[0] + radius // 4, center[1] + radius // 4)
        shadow_radius = radius // 2
        assert shadow_color is not None  # We set it above if it was None
        pygame.draw.circle(surface, shadow_color, shadow_center, shadow_radius)

    def draw_ellipse_with_shading(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        color: Tuple[int, int, int],
        shadow_color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        """Draw an ellipse with subtle shading."""
        if shadow_color is None:
            shadow_color = tuple(max(0, c - 30) for c in color)  # type: ignore

        # Main ellipse
        pygame.draw.ellipse(surface, color, rect)

        # Highlight
        highlight_rect = pygame.Rect(
            rect.x + rect.width // 4,
            rect.y + rect.height // 4,
            rect.width // 2,
            rect.height // 2,
        )
        highlight_color = tuple(min(255, c + 40) for c in color)
        pygame.draw.ellipse(surface, highlight_color, highlight_rect)

    def generate_head(self) -> pygame.Surface:
        """Generate the character's head."""
        surface = self.create_surface()
        center = (self.width // 2, self.height // 2 - 40)
        radius = self.proportions["head_radius"]

        # Head (wood-like)
        self.draw_circle_with_shading(
            surface, center, radius, self.colors["wood"], self.colors["wood_dark"]
        )

        # Face features
        self.generate_face(surface, center)

        return surface

    def generate_face(
        self, surface: pygame.Surface, head_center: Tuple[int, int]
    ) -> None:
        """Generate facial features."""
        x, y = head_center

        # Eyes
        eye_y = y - 10
        left_eye = (x - 15, eye_y)
        right_eye = (x + 15, eye_y)
        pygame.draw.circle(surface, self.colors["eyes"], left_eye, 6)
        pygame.draw.circle(surface, self.colors["eyes"], right_eye, 6)

        # Eye highlights
        pygame.draw.circle(surface, (255, 255, 255), (x - 12, eye_y - 2), 2)
        pygame.draw.circle(surface, (255, 255, 255), (x + 18, eye_y - 2), 2)

        # Nose
        nose_rect = pygame.Rect(x - 3, y - 5, 6, 8)
        pygame.draw.ellipse(surface, self.colors["nose"], nose_rect)

        # Mouth
        mouth_rect = pygame.Rect(x - 8, y + 5, 16, 6)
        pygame.draw.ellipse(surface, self.colors["mouth"], mouth_rect)

        # Wood grain lines on face
        for i in range(3):
            line_y = y - 20 + i * 15
            pygame.draw.line(
                surface, self.colors["wood_dark"], (x - 25, line_y), (x + 25, line_y), 1
            )

    def generate_torso(self) -> pygame.Surface:
        """Generate the character's torso."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 + 20

        # Torso (wood-like)
        torso_rect = pygame.Rect(center_x - 30, center_y - 40, 60, 80)
        self.draw_ellipse_with_shading(
            surface, torso_rect, self.colors["wood"], self.colors["wood_dark"]
        )

        # Shirt
        shirt_rect = pygame.Rect(center_x - 25, center_y - 35, 50, 60)
        pygame.draw.ellipse(surface, self.colors["shirt"], shirt_rect)

        # Wood grain lines
        for i in range(4):
            line_y = center_y - 30 + i * 15
            pygame.draw.line(
                surface,
                self.colors["wood_dark"],
                (center_x - 25, line_y),
                (center_x + 25, line_y),
                1,
            )

        return surface

    def generate_left_arm(self) -> pygame.Surface:
        """Generate the left arm."""
        surface = self.create_surface()
        center_x = self.width // 2 - 40
        center_y = self.height // 2

        # Upper arm
        upper_arm_rect = pygame.Rect(center_x - 10, center_y - 30, 20, 40)
        self.draw_ellipse_with_shading(
            surface, upper_arm_rect, self.colors["wood"], self.colors["wood_dark"]
        )

        # Lower arm
        lower_arm_rect = pygame.Rect(center_x - 8, center_y + 10, 16, 30)
        self.draw_ellipse_with_shading(
            surface, lower_arm_rect, self.colors["wood_light"], self.colors["wood_dark"]
        )

        # Hand
        hand_center = (center_x, center_y + 35)
        pygame.draw.circle(surface, self.colors["wood"], hand_center, 8)

        return surface

    def generate_right_arm(self) -> pygame.Surface:
        """Generate the right arm."""
        surface = self.create_surface()
        center_x = self.width // 2 + 40
        center_y = self.height // 2

        # Upper arm
        upper_arm_rect = pygame.Rect(center_x - 10, center_y - 30, 20, 40)
        self.draw_ellipse_with_shading(
            surface, upper_arm_rect, self.colors["wood"], self.colors["wood_dark"]
        )

        # Lower arm
        lower_arm_rect = pygame.Rect(center_x - 8, center_y + 10, 16, 30)
        self.draw_ellipse_with_shading(
            surface, lower_arm_rect, self.colors["wood_light"], self.colors["wood_dark"]
        )

        # Hand
        hand_center = (center_x, center_y + 35)
        pygame.draw.circle(surface, self.colors["wood"], hand_center, 8)

        return surface

    def generate_left_leg(self) -> pygame.Surface:
        """Generate the left leg."""
        surface = self.create_surface()
        center_x = self.width // 2 - 15
        center_y = self.height // 2 + 60

        # Upper leg
        upper_leg_rect = pygame.Rect(center_x - 12, center_y - 40, 24, 50)
        self.draw_ellipse_with_shading(
            surface, upper_leg_rect, self.colors["pants"], self.colors["wood_dark"]
        )

        # Lower leg
        lower_leg_rect = pygame.Rect(center_x - 10, center_y + 10, 20, 40)
        self.draw_ellipse_with_shading(
            surface, lower_leg_rect, self.colors["pants"], self.colors["wood_dark"]
        )

        # Foot
        foot_rect = pygame.Rect(center_x - 12, center_y + 45, 24, 12)
        pygame.draw.ellipse(surface, self.colors["shoes"], foot_rect)

        return surface

    def generate_right_leg(self) -> pygame.Surface:
        """Generate the right leg."""
        surface = self.create_surface()
        center_x = self.width // 2 + 15
        center_y = self.height // 2 + 60

        # Upper leg
        upper_leg_rect = pygame.Rect(center_x - 12, center_y - 40, 24, 50)
        self.draw_ellipse_with_shading(
            surface, upper_leg_rect, self.colors["pants"], self.colors["wood_dark"]
        )

        # Lower leg
        lower_leg_rect = pygame.Rect(center_x - 10, center_y + 10, 20, 40)
        self.draw_ellipse_with_shading(
            surface, lower_leg_rect, self.colors["pants"], self.colors["wood_dark"]
        )

        # Foot
        foot_rect = pygame.Rect(center_x - 12, center_y + 45, 24, 12)
        pygame.draw.ellipse(surface, self.colors["shoes"], foot_rect)

        return surface

    def generate_hat(self) -> pygame.Surface:
        """Generate Pinocchio's hat."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 - 60

        # Hat base
        hat_rect = pygame.Rect(center_x - 25, center_y - 10, 50, 20)
        pygame.draw.ellipse(surface, self.colors["hat"], hat_rect)

        # Hat crown
        crown_rect = pygame.Rect(center_x - 20, center_y - 25, 40, 20)
        pygame.draw.ellipse(surface, self.colors["hat"], crown_rect)

        # Gold band
        band_rect = pygame.Rect(center_x - 22, center_y - 5, 44, 8)
        pygame.draw.ellipse(surface, self.colors["hat_band"], band_rect)

        return surface

    def generate_eyes_open(self) -> pygame.Surface:
        """Generate open eyes expression."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 - 50

        # Eyes
        left_eye = (center_x - 15, center_y)
        right_eye = (center_x + 15, center_y)
        pygame.draw.circle(surface, self.colors["eyes"], left_eye, 6)
        pygame.draw.circle(surface, self.colors["eyes"], right_eye, 6)

        # Eye highlights
        pygame.draw.circle(surface, (255, 255, 255), (center_x - 12, center_y - 2), 2)
        pygame.draw.circle(surface, (255, 255, 255), (center_x + 18, center_y - 2), 2)

        return surface

    def generate_eyes_closed(self) -> pygame.Surface:
        """Generate closed eyes expression."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 - 50

        # Closed eyes (curved lines)
        pygame.draw.arc(
            surface,
            self.colors["eyes"],
            pygame.Rect(center_x - 21, center_y - 6, 12, 12),
            0,
            math.pi,
            2,
        )
        pygame.draw.arc(
            surface,
            self.colors["eyes"],
            pygame.Rect(center_x + 9, center_y - 6, 12, 12),
            0,
            math.pi,
            2,
        )

        return surface

    def generate_mouth_neutral(self) -> pygame.Surface:
        """Generate neutral mouth expression."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 - 35

        # Neutral mouth (small line)
        pygame.draw.line(
            surface,
            self.colors["mouth"],
            (center_x - 8, center_y),
            (center_x + 8, center_y),
            3,
        )

        return surface

    def generate_mouth_open(self) -> pygame.Surface:
        """Generate open mouth expression."""
        surface = self.create_surface()
        center_x = self.width // 2
        center_y = self.height // 2 - 35

        # Open mouth (oval)
        mouth_rect = pygame.Rect(center_x - 8, center_y - 4, 16, 8)
        pygame.draw.ellipse(surface, self.colors["mouth"], mouth_rect)

        return surface

    def generate_all_assets(self, output_dir: Path) -> Dict[str, str]:
        """Generate all character assets and save them."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        body_dir = output_dir / "body"
        face_dir = output_dir / "face" / "eyes"
        mouth_dir = output_dir / "face" / "mouths"
        gear_dir = output_dir / "gear"

        for dir_path in [body_dir, face_dir, mouth_dir, gear_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Generate and save assets
        asset_paths = {}

        # Body parts
        asset_paths["head"] = self._save_asset(
            self.generate_head(), body_dir / "head.png"
        )
        asset_paths["torso"] = self._save_asset(
            self.generate_torso(), body_dir / "torso.png"
        )
        asset_paths["left_arm"] = self._save_asset(
            self.generate_left_arm(), body_dir / "left_arm.png"
        )
        asset_paths["right_arm"] = self._save_asset(
            self.generate_right_arm(), body_dir / "right_arm.png"
        )
        asset_paths["left_leg"] = self._save_asset(
            self.generate_left_leg(), body_dir / "left_leg.png"
        )
        asset_paths["right_leg"] = self._save_asset(
            self.generate_right_leg(), body_dir / "right_leg.png"
        )

        # Facial features
        asset_paths["eyes_open"] = self._save_asset(
            self.generate_eyes_open(), face_dir / "eyes_open.png"
        )
        asset_paths["eyes_closed"] = self._save_asset(
            self.generate_eyes_closed(), face_dir / "eyes_closed.png"
        )
        asset_paths["mouth_neutral"] = self._save_asset(
            self.generate_mouth_neutral(), mouth_dir / "mouth_neutral.png"
        )
        asset_paths["mouth_open"] = self._save_asset(
            self.generate_mouth_open(), mouth_dir / "mouth_open.png"
        )

        # Gear
        asset_paths["hat"] = self._save_asset(self.generate_hat(), gear_dir / "hat.png")

        return asset_paths

    def _save_asset(self, surface: pygame.Surface, file_path: Path) -> str:
        """Save a surface as a PNG file."""
        pygame.image.save(surface, str(file_path))
        return str(file_path)


# Global cache for character assets to ensure consistency
_character_assets_cache: Optional[Dict[str, str]] = None
_character_assets_output_dir: Optional[Path] = None


def generate_character_assets(
    output_dir: Path = Path("generated_assets"),
) -> Dict[str, str]:
    """Generate all Pinocchio-inspired character assets."""
    global _character_assets_cache, _character_assets_output_dir

    # Return cached assets if they exist and output directory is the same
    if (
        _character_assets_cache is not None
        and _character_assets_output_dir is not None
        and _character_assets_output_dir == output_dir
    ):
        return _character_assets_cache

    # Generate new assets
    generator = PinocchioAssetGenerator()
    asset_paths = generator.generate_all_assets(output_dir)

    # Cache the results
    _character_assets_cache = asset_paths
    _character_assets_output_dir = output_dir

    return asset_paths


def reset_character_assets_cache():
    """Reset the global character assets cache."""
    global _character_assets_cache, _character_assets_output_dir
    _character_assets_cache = None
    _character_assets_output_dir = None


if __name__ == "__main__":
    # Generate assets when run directly
    assets = generate_character_assets()
    print("Generated character assets:")
    for name, path in assets.items():
        print(f"  {name}: {path}")
