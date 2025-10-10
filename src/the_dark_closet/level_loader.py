"""
Level JSON loader and object placement system.

This module handles loading level definitions from JSON files and managing
object placement across different rendering layers.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pygame


class LevelObject:
    """Represents a single object in a level layer."""
    
    def __init__(self, obj_data: Dict[str, Any]):
        self.id: str = obj_data["id"]
        self.type: str = obj_data["type"]
        self.x: int = obj_data["x"]
        self.y: int = obj_data["y"]
        self.width: int = obj_data["width"]
        self.height: int = obj_data["height"]
        self.color: Optional[Tuple[int, int, int]] = None
        self.properties: Dict[str, Any] = {}
        
        # Extract color if present
        if "color" in obj_data:
            self.color = tuple(obj_data["color"])
        
        # Extract additional properties
        for key, value in obj_data.items():
            if key not in ["id", "type", "x", "y", "width", "height", "color"]:
                self.properties[key] = value
    
    def get_rect(self) -> pygame.Rect:
        """Get the pygame Rect for this object."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def get_rect_with_camera(self, camera_x: float, camera_y: float, parallax_factor: float = 1.0) -> pygame.Rect:
        """Get the pygame Rect with camera and parallax offset applied."""
        offset_x = int(camera_x * parallax_factor)
        offset_y = int(camera_y * parallax_factor)
        return pygame.Rect(
            self.x - offset_x,
            self.y - offset_y,
            self.width,
            self.height
        )


class LevelLayer:
    """Represents a single rendering layer in a level."""
    
    def __init__(self, layer_data: Dict[str, Any]):
        self.parallax_factor: float = layer_data.get("parallax_factor", 1.0)
        self.objects: List[LevelObject] = []
        
        for obj_data in layer_data.get("objects", []):
            self.objects.append(LevelObject(obj_data))
    
    def get_objects_in_view(self, camera_x: float, camera_y: float, screen_width: int, screen_height: int) -> List[LevelObject]:
        """Get objects that are visible in the current camera view."""
        visible_objects = []
        
        for obj in self.objects:
            rect = obj.get_rect_with_camera(camera_x, camera_y, self.parallax_factor)
            
            # Check if object is in view
            if (rect.right > 0 and rect.left < screen_width and 
                rect.bottom > 0 and rect.top < screen_height):
                visible_objects.append(obj)
        
        return visible_objects


class LevelData:
    """Represents a complete level loaded from JSON."""
    
    def __init__(self, level_path: Path):
        self.path = level_path
        self.metadata: Dict[str, Any] = {}
        self.layers: Dict[str, LevelLayer] = {}
        self.player_spawn: Tuple[int, int] = (0, 0)
        
        self._load_level()
    
    def _load_level(self) -> None:
        """Load level data from JSON file."""
        with open(self.path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Load metadata
        self.metadata = data.get("metadata", {})
        
        # Load layers
        layers_data = data.get("layers", {})
        for layer_name, layer_data in layers_data.items():
            self.layers[layer_name] = LevelLayer(layer_data)
        
        # Load player spawn
        player_data = data.get("player", {})
        self.player_spawn = (
            player_data.get("spawn_x", 0),
            player_data.get("spawn_y", 0)
        )
    
    def get_layer(self, layer_name: str) -> Optional[LevelLayer]:
        """Get a specific layer by name."""
        return self.layers.get(layer_name)
    
    def get_all_objects(self) -> List[LevelObject]:
        """Get all objects from all layers."""
        all_objects = []
        for layer in self.layers.values():
            all_objects.extend(layer.objects)
        return all_objects
    
    def get_objects_by_type(self, object_type: str) -> List[LevelObject]:
        """Get all objects of a specific type across all layers."""
        objects = []
        for layer in self.layers.values():
            for obj in layer.objects:
                if obj.type == object_type:
                    objects.append(obj)
        return objects
    
    def get_objects_in_view(self, camera_x: float, camera_y: float, screen_width: int, screen_height: int) -> Dict[str, List[LevelObject]]:
        """Get all visible objects organized by layer."""
        visible_objects = {}
        for layer_name, layer in self.layers.items():
            visible_objects[layer_name] = layer.get_objects_in_view(camera_x, camera_y, screen_width, screen_height)
        return visible_objects


class LevelRenderer:
    """Handles rendering of level objects based on JSON definitions."""
    
    def __init__(self, level_data: LevelData):
        self.level_data = level_data
    
    def render_layer(self, surface: pygame.Surface, layer_name: str, camera_x: float, camera_y: float) -> None:
        """Render a specific layer of the level."""
        layer = self.level_data.get_layer(layer_name)
        if not layer:
            return
        
        visible_objects = layer.get_objects_in_view(
            camera_x, camera_y, surface.get_width(), surface.get_height()
        )
        
        for obj in visible_objects:
            self._render_object(surface, obj, camera_x, camera_y, layer.parallax_factor)
    
    def _render_object(self, surface: pygame.Surface, obj: LevelObject, camera_x: float, camera_y: float, parallax_factor: float) -> None:
        """Render a single level object."""
        rect = obj.get_rect_with_camera(camera_x, camera_y, parallax_factor)
        
        if obj.type == "brick":
            self._render_brick(surface, rect)
        elif obj.type == "platform":
            self._render_platform(surface, rect)
        elif obj.type == "ladder":
            self._render_ladder(surface, rect)
        elif obj.type == "mountain":
            self._render_mountain(surface, rect, obj.color)
        elif obj.type == "hill":
            self._render_hill(surface, rect, obj.color)
        elif obj.type == "foreground_accent":
            self._render_foreground_accent(surface, rect, obj.color)
        else:
            # Default rendering for unknown object types
            color = obj.color or (128, 128, 128)
            pygame.draw.rect(surface, color, rect)
    
    def _render_brick(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a brick tile using the same logic as the game."""
        # Brick tile with mortar lines (exact copy from game code)
        pygame.draw.rect(surface, (135, 90, 60), rect)
        
        # Mortar lines
        for i in range(0, rect.width, 64):
            mortar_rect = pygame.Rect(rect.x + i, rect.y, 2, rect.height)
            pygame.draw.rect(surface, (200, 200, 200), mortar_rect)
        for j in range(0, rect.height, 32):
            mortar_rect = pygame.Rect(rect.x, rect.y + j, rect.width, 2)
            pygame.draw.rect(surface, (200, 200, 200), mortar_rect)
        
        # Brick texture
        for i in range(0, rect.width, 32):
            for j in range(0, rect.height, 16):
                if (i // 32 + j // 16) % 2 == 0:
                    brick_rect = pygame.Rect(rect.x + i + 2, rect.y + j + 2, 28, 12)
                    pygame.draw.rect(surface, (155, 110, 80), brick_rect)
    
    def _render_mountain(self, surface: pygame.Surface, rect: pygame.Rect, color: Optional[Tuple[int, int, int]]) -> None:
        """Render a mountain silhouette."""
        mountain_color = color or (30, 34, 46)
        pygame.draw.rect(surface, mountain_color, rect)
    
    def _render_hill(self, surface: pygame.Surface, rect: pygame.Rect, color: Optional[Tuple[int, int, int]]) -> None:
        """Render a hill."""
        hill_color = color or (40, 46, 60)
        pygame.draw.rect(surface, hill_color, rect)
    
    def _render_platform(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a platform tile using the same logic as the game."""
        # Platform with wood grain (exact copy from game code)
        platform_rect = pygame.Rect(
            rect.x, rect.y + rect.height - 24, rect.width, 24
        )
        pygame.draw.rect(surface, (190, 190, 200), platform_rect)
        # Wood grain lines
        for i in range(0, rect.width, 16):
            grain_rect = pygame.Rect(rect.x + i, rect.y + rect.height - 20, 1, 16)
            pygame.draw.rect(surface, (170, 170, 180), grain_rect)
    
    def _render_ladder(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        """Render a ladder tile using the same logic as the game."""
        # Ladder with rungs (exact copy from game code)
        pygame.draw.rect(surface, (200, 170, 70), rect)
        # Vertical rails
        left_rail = pygame.Rect(rect.x + 8, rect.y, 8, rect.height)
        right_rail = pygame.Rect(rect.x + rect.width - 16, rect.y, 8, rect.height)
        pygame.draw.rect(surface, (180, 150, 50), left_rail)
        pygame.draw.rect(surface, (180, 150, 50), right_rail)
        # Rungs
        for j in range(16, rect.height, 32):
            rung_rect = pygame.Rect(rect.x + 8, rect.y + j, rect.width - 16, 8)
            pygame.draw.rect(surface, (180, 150, 50), rung_rect)
    
    def _render_foreground_accent(self, surface: pygame.Surface, rect: pygame.Rect, color: Optional[Tuple[int, int, int]]) -> None:
        """Render a foreground accent object."""
        accent_color = color or (12, 14, 18)
        pygame.draw.rect(surface, accent_color, rect)


def load_level(level_path: Path) -> LevelData:
    """Load a level from a JSON file."""
    return LevelData(level_path)
