"""
JSON-based scene implementation.

This scene uses level JSON files to define object placement and rendering.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import pygame

from .game import Scene, GameApp, TILE_SIZE
from .level_loader import LevelData, LevelRenderer


class JSONScene(Scene):
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
        self.player_rect = pygame.Rect(spawn_x, spawn_y, 104, 120)  # 4x 26x30
        self.player_velocity_x: float = 0.0
        self.player_velocity_y: float = 0.0
        self.player_speed_px_per_sec: float = 220.0
        self.player_jump_speed_px_per_sec: float = 420.0
        self.gravity_px_per_sec2: float = 1200.0
        self.on_ground: bool = False
        self.on_ladder: bool = False
        
        # Camera
        self.camera_x: float = 0.0
        self.camera_y: float = 0.0
        
        # Fonts
        self.hud_font: Optional[pygame.font.Font] = None
        
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
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
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
            
            # Check if player is standing on brick
            if (self.player_rect.colliderect(brick_rect) and 
                player_bottom <= brick_rect.top + 10 and 
                self.player_velocity_y >= 0):
                self.player_rect.bottom = brick_rect.top
                self.player_velocity_y = 0
                self.on_ground = True
                break
        
        # Keep player within level bounds
        self.player_rect.x = max(0, min(self.player_rect.x, self.level_width - self.player_rect.width))
        self.player_rect.y = max(0, min(self.player_rect.y, self.level_height - self.player_rect.height))
    
    def _update_camera(self) -> None:
        """Update camera position to follow player."""
        # Center camera on player
        target_camera_x = self.player_rect.centerx - self.app.width // 2
        target_camera_y = self.player_rect.centery - self.app.height // 2
        
        # Keep camera within level bounds
        self.camera_x = max(0, min(target_camera_x, self.level_width - self.app.width))
        self.camera_y = max(0, min(target_camera_y, self.level_height - self.app.height))
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the scene."""
        # Sky
        surface.fill((18, 22, 30))
        
        # Render layers in order
        layer_order = ["background", "midground", "tiles", "foreground"]
        for layer_name in layer_order:
            self.level_renderer.render_layer(surface, layer_name, self.camera_x, self.camera_y)
        
        # Player
        pr = self.player_rect.move(-int(self.camera_x), -int(self.camera_y))
        self._draw_procedural_player(surface, pr)
        
        # HUD
        if self.hud_font:
            msg = "Arrows/WASD to move, Space/Up to jump, Esc to quit"
            text = self.hud_font.render(msg, True, (210, 210, 220))
            surface.blit(text, (48, 48))  # 4x 12, 12 for higher resolution
        
        # Draw center mass dot after all other rendering (so it's not overwritten)
        pr = self.player_rect.move(-int(self.camera_x), -int(self.camera_y))
        center_x = pr.x + pr.width // 2
        center_y = pr.y + pr.height // 2
        center_dot_rect = pygame.Rect(center_x - 4, center_y - 4, 8, 8)
        pygame.draw.rect(surface, (255, 0, 255), center_dot_rect)  # Bright magenta
    
    def _draw_procedural_player(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
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
            from pathlib import Path
            
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
