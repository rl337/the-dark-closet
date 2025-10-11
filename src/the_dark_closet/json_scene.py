# pylint: disable=attribute-defined-outside-init
"""
JSON-based scene implementation.

This scene uses level JSON files to define object placement and rendering.
"""

from pathlib import Path
from typing import Optional, Dict
import pygame

from .game import Scene, GameApp, TILE_SIZE
from .level_loader import LevelData, LevelRenderer
from .rendering_utils import render_hud, render_center_mass_dot, PlayerMixin


class JSONScene(Scene, PlayerMixin):
    """A scene that loads object placement from JSON level files."""

    def __init__(
        self,
        app: "GameApp",
        level_path: Path,
        player_spawn_override: Optional[tuple] = None,
    ) -> None:
        super().__init__(app)

        # Load level data
        self.level_data = LevelData(level_path)
        self.level_renderer = LevelRenderer(self.level_data)

        # Player properties
        if player_spawn_override is not None:
            spawn_x, spawn_y = player_spawn_override
        else:
            spawn_x, spawn_y = self.level_data.player_spawn

        # Character assets (lazy loaded)
        self._character_assets: Optional[Dict[str, pygame.Surface]] = None

        # Initialize player state using shared configuration
        self._init_player_state(spawn_x, spawn_y)

        # Level dimensions
        self.level_width = self.level_data.metadata.get("width", 12) * TILE_SIZE
        self.level_height = self.level_data.metadata.get("height", 8) * TILE_SIZE

    def on_enter(self) -> None:
        self.hud_font = pygame.font.Font(None, 96)  # 4x 24 for higher resolution

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.request_quit()

    def update(self, delta_seconds: float) -> None:
        """Update game logic."""
        keys = pygame.key.get_pressed()

        # Movement
        movement_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )

        # Apply movement
        self.player_velocity_x = movement_x * self.player_speed_px_per_sec

        # Jumping
        if (
            keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        ) and self.on_ground:
            self.player_velocity_y = -self.player_jump_speed_px_per_sec
            self.on_ground = False

        # Apply gravity
        if not self.on_ground:
            self.player_velocity_y += self.gravity_px_per_sec2 * delta_seconds

        # Update position
        self.player_rect.x += int(self.player_velocity_x * delta_seconds)
        self.player_rect.y += int(self.player_velocity_y * delta_seconds)

        # Collision detection with level objects
        self._check_collisions()

        # Update camera to follow player
        self._update_camera()

    def _check_collisions(self) -> None:
        """Check collisions with level objects."""
        # Get all brick objects for collision
        brick_objects = self.level_data.get_objects_by_type("brick")

        # Check ground collision
        self.on_ground = False
        player_bottom = self.player_rect.bottom

        for brick in brick_objects:
            brick_rect = brick.get_rect()

            # Check if player is standing on brick (only for ground-level bricks)
            if (
                self.player_rect.colliderect(brick_rect)
                and player_bottom <= brick_rect.top + 10
                and self.player_velocity_y >= 0
                and brick_rect.y >= self.level_height - 256
            ):  # Only ground-level bricks
                self.player_rect.bottom = brick_rect.top
                self.player_velocity_y = 0
                self.on_ground = True
                break

        # Gravity is now handled in update method

        # Keep player within level bounds (but allow movement)
        self.player_rect.x = max(
            0, min(self.player_rect.x, self.level_width - self.player_rect.width)
        )
        # Don't constrain Y position to allow jumping

    def _update_camera(self) -> None:
        """Update camera position to follow player."""
        # Center camera on player
        target_camera_x = self.player_rect.centerx - self.app.width // 2
        target_camera_y = self.player_rect.centery - self.app.height // 2

        # Keep camera within level bounds
        self.camera_x = max(0, min(target_camera_x, self.level_width - self.app.width))
        self.camera_y = max(
            0, min(target_camera_y, self.level_height - self.app.height)
        )

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the scene."""
        # Sky
        surface.fill((18, 22, 30))

        # Render layers in order
        layer_order = ["background", "midground", "tiles", "foreground"]
        for layer_name in layer_order:
            self.level_renderer.render_layer(
                surface, layer_name, self.camera_x, self.camera_y
            )

        # Player
        pr = self.player_rect.move(-int(self.camera_x), -int(self.camera_y))
        self._draw_procedural_player(surface, pr)

        # HUD
        render_hud(surface, self.hud_font)

        # Draw center mass dot after all other rendering (so it's not overwritten)
        render_center_mass_dot(surface, self.player_rect, self.camera_x, self.camera_y)

    def _draw_procedural_player(
        self, surface: pygame.Surface, rect: pygame.Rect
    ) -> None:
        """Draw player using procedurally generated assets."""
        # Load assets if not already loaded
        if self._character_assets is None:
            self._character_assets = self._load_character_assets()

        assets = self._character_assets
        if not assets:
            # Fallback: draw a simple rectangle
            pygame.draw.rect(surface, (220, 80, 80), rect)
            return

        # Draw character parts
        head_rect = pygame.Rect(rect.x + 20, rect.y + 10, 88, 88)
        surface.blit(assets["head"], head_rect)

        torso_rect = pygame.Rect(rect.x + 20, rect.y + 80, 88, 88)
        surface.blit(assets["torso"], torso_rect)

        # Arms
        left_arm_rect = pygame.Rect(rect.x + 5, rect.y + 85, 44, 44)
        surface.blit(assets["left_arm"], left_arm_rect)

        right_arm_rect = pygame.Rect(rect.x + 79, rect.y + 85, 44, 44)
        surface.blit(assets["right_arm"], right_arm_rect)

        # Legs
        left_leg_rect = pygame.Rect(rect.x + 20, rect.y + 150, 44, 44)
        surface.blit(assets["left_leg"], left_leg_rect)

        right_leg_rect = pygame.Rect(rect.x + 64, rect.y + 150, 44, 44)
        surface.blit(assets["right_leg"], right_leg_rect)

    def _load_character_assets(self) -> Dict[str, pygame.Surface]:
        """Load character assets from the generated assets directory."""
        try:
            from .assets import generate_character_assets

            # Generate assets to a temporary directory
            temp_assets_dir = Path("build/generated_assets")
            temp_assets_dir.mkdir(parents=True, exist_ok=True)

            asset_paths = generate_character_assets(temp_assets_dir)

            # Load the generated assets
            assets = {}
            for asset_name, asset_path in asset_paths.items():
                if Path(asset_path).exists():
                    assets[asset_name] = pygame.image.load(asset_path)

            return assets
        except Exception as e:
            print(f"Failed to load character assets: {e}")
            return {}

    def get_all_objects(self) -> list:
        """Get all objects in the level for testing purposes."""
        return self.level_data.get_all_objects()

    def get_objects_by_type(self, object_type: str) -> list:
        """Get objects of a specific type for testing purposes."""
        return self.level_data.get_objects_by_type(object_type)
