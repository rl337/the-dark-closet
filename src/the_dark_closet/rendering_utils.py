"""
Shared rendering utilities to eliminate code duplication.

This module contains common rendering functions used across different
scene implementations to maintain consistency and reduce duplication.
"""

from typing import Optional
import pygame


def render_brick_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Render a brick tile with mortar lines and texture."""
    # Brick tile with mortar lines
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


def render_platform_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Render a platform tile with wood grain."""
    # Platform with wood grain
    platform_rect = pygame.Rect(rect.x, rect.y + rect.height - 24, rect.width, 24)
    pygame.draw.rect(surface, (190, 190, 200), platform_rect)
    # Wood grain lines
    for i in range(0, rect.width, 16):
        grain_rect = pygame.Rect(rect.x + i, rect.y + rect.height - 20, 1, 16)
        pygame.draw.rect(surface, (170, 170, 180), grain_rect)


def render_ladder_tile(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """Render a ladder tile with rungs."""
    # Ladder with rungs
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


def render_hud(surface: pygame.Surface, hud_font: Optional[pygame.font.Font]) -> None:
    """Render the HUD with controls information."""
    if hud_font:
        msg = "Arrows/WASD to move, Space/Up to jump, Esc to quit"
        text = hud_font.render(msg, True, (210, 210, 220))
        surface.blit(text, (48, 48))  # 4x 12, 12 for higher resolution


def render_center_mass_dot(
    surface: pygame.Surface, player_rect: pygame.Rect, camera_x: float, camera_y: float
) -> None:
    """Render the center mass dot for debugging."""
    pr = player_rect.move(-int(camera_x), -int(camera_y))
    center_x = pr.x + pr.width // 2
    center_y = pr.y + pr.height // 2
    center_dot_rect = pygame.Rect(center_x - 4, center_y - 4, 8, 8)
    pygame.draw.rect(surface, (255, 0, 255), center_dot_rect)  # Bright magenta


class PlayerState:
    """Shared player state configuration to eliminate duplication."""

    def __init__(self, spawn_x: int, spawn_y: int):
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


def initialize_player_from_state(scene_instance, player_state: PlayerState) -> None:
    """Initialize player attributes from PlayerState to eliminate duplication."""
    scene_instance.player_rect = player_state.player_rect
    scene_instance.player_velocity_x = player_state.player_velocity_x
    scene_instance.player_velocity_y = player_state.player_velocity_y
    scene_instance.player_speed_px_per_sec = player_state.player_speed_px_per_sec
    scene_instance.player_jump_speed_px_per_sec = (
        player_state.player_jump_speed_px_per_sec
    )
    scene_instance.gravity_px_per_sec2 = player_state.gravity_px_per_sec2
    scene_instance.on_ground = player_state.on_ground
    scene_instance.on_ladder = player_state.on_ladder
    scene_instance.camera_x = player_state.camera_x
    scene_instance.camera_y = player_state.camera_y
    scene_instance.hud_font = player_state.hud_font


class PlayerMixin:
    """Mixin class to provide common player functionality and eliminate duplication."""

    def _init_player_state(self, spawn_x: int, spawn_y: int) -> None:
        """Initialize player state using shared configuration."""
        self.player_state = PlayerState(spawn_x, spawn_y)
        self.player_rect = self.player_state.player_rect
        self.player_velocity_x = self.player_state.player_velocity_x
        self.player_velocity_y = self.player_state.player_velocity_y
        self.player_speed_px_per_sec = self.player_state.player_speed_px_per_sec
        self.player_jump_speed_px_per_sec = (
            self.player_state.player_jump_speed_px_per_sec
        )
        self.gravity_px_per_sec2 = self.player_state.gravity_px_per_sec2
        self.on_ground = self.player_state.on_ground
        self.on_ladder = self.player_state.on_ladder
        self.camera_x = self.player_state.camera_x
        self.camera_y = self.player_state.camera_y
        self.hud_font = self.player_state.hud_font
