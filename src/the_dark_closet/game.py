from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import pygame


@dataclass(frozen=True)
class GameConfig:
    window_width: int
    window_height: int
    window_title: str
    target_fps: int


class Scene:
    def __init__(self, app: "GameApp") -> None:
        self.app = app

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, delta_seconds: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class MenuScene(Scene):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        self.title_font: Optional[pygame.font.Font] = None
        self.body_font: Optional[pygame.font.Font] = None

    def on_enter(self) -> None:
        self.title_font = pygame.font.Font(None, 72)
        self.body_font = pygame.font.Font(None, 36)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.app.switch_scene(WorldScene(self.app))
            elif event.key == pygame.K_ESCAPE:
                self.app.request_quit()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((8, 8, 12))
        assert self.title_font is not None and self.body_font is not None

        title = self.title_font.render("The Dark Closet", True, (220, 220, 230))
        subtitle = self.body_font.render("Press Enter to step through the portal", True, (200, 200, 210))
        hint = self.body_font.render("Esc to quit", True, (160, 160, 170))

        surface.blit(title, title.get_rect(center=(self.app.width // 2, self.app.height // 2 - 40)))
        surface.blit(subtitle, subtitle.get_rect(center=(self.app.width // 2, self.app.height // 2 + 20)))
        surface.blit(hint, hint.get_rect(center=(self.app.width // 2, self.app.height // 2 + 70)))


class WorldScene(Scene):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        self.font: Optional[pygame.font.Font] = None
        self.player_rect = pygame.Rect(app.width // 2 - 15, app.height // 2 - 15, 30, 30)
        self.player_speed_px_per_sec: int = 240

    def on_enter(self) -> None:
        self.font = pygame.font.Font(None, 28)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.request_quit()

    def update(self, delta_seconds: float) -> None:
        keys = pygame.key.get_pressed()
        movement_x = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        movement_y = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        dx = int(movement_x * self.player_speed_px_per_sec * delta_seconds)
        dy = int(movement_y * self.player_speed_px_per_sec * delta_seconds)
        self.player_rect.move_ip(dx, dy)
        self.player_rect.clamp_ip(pygame.Rect(0, 0, self.app.width, self.app.height))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 12))
        pygame.draw.rect(surface, (220, 80, 80), self.player_rect)
        assert self.font is not None

        text_lines = [
            "Across the portal, ambition hardens into conquest.",
            "Arrows/WASD to move. Esc to quit.",
        ]
        for i, line in enumerate(text_lines):
            rendered = self.font.render(line, True, (210, 210, 220))
            surface.blit(rendered, (16, 16 + i * 24))


class GameApp:
    def __init__(self, config: GameConfig) -> None:
        self.config = config
        self.width = config.window_width
        self.height = config.window_height
        self._running = True
        self._current_scene: Optional[Scene] = None

        # Ensure a minimal SDL audio/video setup in headless mode
        if os.environ.get("SDL_AUDIODRIVER") is None:
            os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

        pygame.init()
        pygame.display.set_caption(config.window_title)
        self._screen = pygame.display.set_mode((self.width, self.height))
        self._clock = pygame.time.Clock()

        self.switch_scene(MenuScene(self))

    def switch_scene(self, scene: Scene) -> None:
        if self._current_scene is not None:
            self._current_scene.on_exit()
        self._current_scene = scene
        self._current_scene.on_enter()

    def request_quit(self) -> None:
        self._running = False

    def run(self, max_frames: Optional[int] = None) -> int:
        frames_rendered = 0
        while self._running:
            delta_seconds = self._clock.tick(self.config.target_fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._running = False
                elif self._current_scene is not None:
                    self._current_scene.handle_event(event)

            if self._current_scene is not None:
                self._current_scene.update(delta_seconds)
                self._current_scene.draw(self._screen)

            pygame.display.flip()

            if max_frames is not None:
                frames_rendered += 1
                if frames_rendered >= max_frames:
                    self._running = False

        pygame.quit()
        return 0
