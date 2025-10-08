from __future__ import annotations

import os
import os
from dataclasses import dataclass
from typing import Optional, List, Tuple, Callable, Any

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
                self.app.switch_scene(SideScrollerScene(self.app))
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


TILE_SIZE: int = 32
TILE_EMPTY = " "
TILE_METAL = "#"
TILE_BRICK = "B"
TILE_PLATFORM = "-"  # one-way (from above only)
TILE_LADDER = "H"
TILE_BOUNDARY = "X"  # impassable, unbreakable level boundary


class SideScrollerScene(Scene):
    def __init__(self, app: "GameApp", world_tiles: Optional[List[str]] = None, player_spawn_px: Optional[Tuple[int, int]] = None) -> None:
        super().__init__(app)
        self.world_tiles: List[str] = world_tiles if world_tiles is not None else self._build_world()
        self.world_cols = max(len(row) for row in self.world_tiles)
        self.world_rows = len(self.world_tiles)
        self.world_width_px = self.world_cols * TILE_SIZE
        self.world_height_px = self.world_rows * TILE_SIZE

        # Player properties
        if player_spawn_px is None:
            spawn_x = 3 * TILE_SIZE
            spawn_y = self.world_height_px - 5 * TILE_SIZE
        else:
            spawn_x, spawn_y = player_spawn_px
        self.player_rect = pygame.Rect(spawn_x, spawn_y, 26, 30)
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

    def on_enter(self) -> None:
        self.hud_font = pygame.font.Font(None, 24)

    # --- World helpers ---
    def _build_world(self) -> List[str]:
        # Simple handcrafted map: top sky, platforms, bricks, metals ground
        rows: List[str] = []
        empty = TILE_EMPTY
        width = 120
        # Sky
        for _ in range(12):
            rows.append(empty * width)
        # Floating structures
        row = list(empty * width)
        for i in range(10, 25):
            row[i] = TILE_PLATFORM
        for i in range(40, 48):
            row[i] = TILE_PLATFORM
        for i in range(70, 90, 2):
            row[i] = TILE_LADDER if i % 4 == 0 else empty
        rows.append("".join(row))

        row = list(empty * width)
        for i in range(15, 17):
            row[i] = TILE_BRICK
        for i in range(30, 36):
            row[i] = TILE_BRICK
        for i in range(60, 62):
            row[i] = TILE_BRICK
        rows.append("".join(row))

        # Mid-level platforms and ladders
        for _ in range(4):
            rows.append(empty * width)

        row = list(empty * width)
        for i in range(20, 50):
            if i % 6 in (0, 1, 2):
                row[i] = TILE_PLATFORM
        for i in range(80, 90):
            row[i] = TILE_PLATFORM
        rows.append("".join(row))

        # More sky
        for _ in range(8):
            rows.append(empty * width)

        # Ground top bricks/metal mix
        ground_row_top = list(empty * width)
        for i in range(width):
            if i % 13 == 0:
                ground_row_top[i] = TILE_BRICK
        rows.append("".join(ground_row_top))

        # Solid metal ground (2 layers)
        metal_row = TILE_METAL * width
        rows.append(metal_row)
        rows.append(metal_row)

        # Stamp a couple of vertical ladders connecting layers
        def put_ladder(col: int, start_row: int, end_row: int) -> None:
            lo = max(0, min(start_row, end_row))
            hi = min(len(rows) - 1, max(start_row, end_row))
            for r in range(lo, hi + 1):
                line = list(rows[r])
                if 0 <= col < len(line):
                    line[col] = TILE_LADDER
                    rows[r] = "".join(line)

        # Example ladders
        put_ladder(22, 6, len(rows) - 4)
        put_ladder(84, 8, len(rows) - 6)

        return rows

    def _tile_at(self, col: int, row: int) -> str:
        if row < 0 or row >= self.world_rows:
            return TILE_METAL  # outside treated as solid
        line = self.world_tiles[row]
        if col < 0 or col >= len(line):
            return TILE_METAL  # outside treated as solid
        return line[col]

    def _set_tile(self, col: int, row: int, value: str) -> None:
        if 0 <= row < self.world_rows:
            line = list(self.world_tiles[row])
            if 0 <= col < len(line):
                line[col] = value
                self.world_tiles[row] = "".join(line)

    def _tiles_overlapping_rect(self, rect: pygame.Rect) -> List[Tuple[int, int, str, pygame.Rect]]:
        tiles: List[Tuple[int, int, str, pygame.Rect]] = []
        left = rect.left // TILE_SIZE
        right = (rect.right - 1) // TILE_SIZE
        top = rect.top // TILE_SIZE
        bottom = (rect.bottom - 1) // TILE_SIZE
        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                t = self._tile_at(tx, ty)
                if t != TILE_EMPTY:
                    tile_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    tiles.append((tx, ty, t, tile_rect))
        return tiles

    # --- Input & Update ---
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.request_quit()

    def update(self, delta_seconds: float) -> None:
        keys = pygame.key.get_pressed()

        # Horizontal input
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.player_velocity_x = 0.0
        if move_left:
            self.player_velocity_x -= self.player_speed_px_per_sec
        if move_right:
            self.player_velocity_x += self.player_speed_px_per_sec

        # Ladder check: inside any ladder tile at player center
        player_center_col = (self.player_rect.centerx) // TILE_SIZE
        player_center_row = (self.player_rect.centery) // TILE_SIZE
        inside_ladder = self._tile_at(player_center_col, player_center_row) == TILE_LADDER

        # Jump / climb
        want_jump = keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]
        want_down = keys[pygame.K_s] or keys[pygame.K_DOWN]

        self.on_ladder = inside_ladder and (want_jump or want_down or keys[pygame.K_UP])
        if self.on_ladder:
            # Climb: cancel gravity, allow up/down movement
            climb_speed = self.player_speed_px_per_sec * 0.8
            self.player_velocity_y = 0.0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.player_velocity_y = -climb_speed
            elif want_down:
                self.player_velocity_y = climb_speed
        else:
            # Gravity
            self.player_velocity_y += self.gravity_px_per_sec2 * delta_seconds
            if want_jump and self.on_ground:
                self.player_velocity_y = -self.player_jump_speed_px_per_sec
                self.on_ground = False

        prev_rect = self.player_rect.copy()

        # Horizontal movement and collisions (solid tiles only)
        self.player_rect.x += int(self.player_velocity_x * delta_seconds)
        for tx, ty, t, tile_rect in self._tiles_overlapping_rect(self.player_rect):
            if t in (TILE_METAL, TILE_BRICK, TILE_BOUNDARY):
                if self.player_velocity_x > 0 and self.player_rect.right > tile_rect.left:
                    self.player_rect.right = tile_rect.left
                elif self.player_velocity_x < 0 and self.player_rect.left < tile_rect.right:
                    self.player_rect.left = tile_rect.right

        # Vertical movement and collisions
        prev_bottom = self.player_rect.bottom
        prev_top = self.player_rect.top
        self.player_rect.y += int(self.player_velocity_y * delta_seconds)
        self.on_ground = False

        collisions = self._tiles_overlapping_rect(self.player_rect)
        for tx, ty, t, tile_rect in collisions:
            if t == TILE_BRICK and self.player_velocity_y < 0:
                # Break brick when hitting from below: previously below its bottom, now intersecting upward
                if prev_top >= tile_rect.bottom and self.player_rect.top <= tile_rect.bottom:
                    self._set_tile(tx, ty, TILE_EMPTY)
                    continue

            if t in (TILE_METAL, TILE_BRICK, TILE_BOUNDARY):
                if self.player_velocity_y > 0 and self.player_rect.bottom > tile_rect.top:
                    self.player_rect.bottom = tile_rect.top
                    self.player_velocity_y = 0
                    self.on_ground = True
                elif self.player_velocity_y < 0 and self.player_rect.top < tile_rect.bottom:
                    self.player_rect.top = tile_rect.bottom
                    self.player_velocity_y = 0

            elif t == TILE_PLATFORM:
                # One-way: only collide if falling and was above the platform
                if self.player_velocity_y > 0 and prev_bottom <= tile_rect.top and self.player_rect.bottom >= tile_rect.top:
                    # Optional: drop-through by holding down
                    if not want_down:
                        self.player_rect.bottom = tile_rect.top
                        self.player_velocity_y = 0
                        self.on_ground = True

        # Constrain to world bounds
        self.player_rect.clamp_ip(pygame.Rect(0, 0, self.world_width_px, self.world_height_px))

        # Camera follow
        target_camera_x = self.player_rect.centerx - self.app.width // 2
        self.camera_x = max(0, min(self.world_width_px - self.app.width, target_camera_x))
        self.camera_y = 0

    # --- Rendering ---
    def draw(self, surface: pygame.Surface) -> None:
        # Sky
        surface.fill((18, 22, 30))

        # Parallax backgrounds
        self._draw_parallax(surface)

        # World tiles in view
        self._draw_tiles(surface)

        # Player
        pr = self.player_rect.move(-int(self.camera_x), -int(self.camera_y))
        pygame.draw.rect(surface, (220, 80, 80), pr)

        # Foreground accents (slightly faster than camera for depth)
        self._draw_foreground(surface)

        # HUD
        if self.hud_font:
            msg = "Arrows/WASD to move, Space/Up to jump, Esc to quit"
            text = self.hud_font.render(msg, True, (210, 210, 220))
            surface.blit(text, (12, 12))

    def _draw_parallax(self, surface: pygame.Surface) -> None:
        width = surface.get_width()
        height = surface.get_height()

        # Far background (mountain silhouettes)
        factor_far = 0.3
        offset_far = -int(self.camera_x * factor_far) % (4 * TILE_SIZE)
        for x in range(-offset_far, width + 4 * TILE_SIZE, 4 * TILE_SIZE):
            rect = pygame.Rect(x, height - 8 * TILE_SIZE, 3 * TILE_SIZE, 8 * TILE_SIZE)
            pygame.draw.rect(surface, (30, 34, 46), rect)

        # Near background (hills)
        factor_near = 0.6
        offset_near = -int(self.camera_x * factor_near) % (3 * TILE_SIZE)
        for x in range(-offset_near, width + 3 * TILE_SIZE, 3 * TILE_SIZE):
            rect = pygame.Rect(x, height - 5 * TILE_SIZE, 2 * TILE_SIZE, 5 * TILE_SIZE)
            pygame.draw.rect(surface, (40, 46, 60), rect)

    def _draw_tiles(self, surface: pygame.Surface) -> None:
        view_left_col = max(0, int(self.camera_x) // TILE_SIZE)
        view_right_col = min(self.world_cols - 1, (int(self.camera_x) + self.app.width) // TILE_SIZE + 1)
        view_top_row = 0
        view_bottom_row = self.world_rows - 1

        for ty in range(view_top_row, view_bottom_row + 1):
            line = self.world_tiles[ty]
            for tx in range(view_left_col, view_right_col + 1):
                t = line[tx] if tx < len(line) else TILE_EMPTY
                if t == TILE_EMPTY:
                    continue
                rect = pygame.Rect(tx * TILE_SIZE - int(self.camera_x), ty * TILE_SIZE - int(self.camera_y), TILE_SIZE, TILE_SIZE)
                if t == TILE_METAL:
                    pygame.draw.rect(surface, (100, 105, 115), rect)
                elif t == TILE_BRICK:
                    pygame.draw.rect(surface, (145, 100, 70), rect)
                elif t == TILE_PLATFORM:
                    platform_rect = pygame.Rect(rect.x, rect.y + TILE_SIZE - 6, TILE_SIZE, 6)
                    pygame.draw.rect(surface, (190, 190, 200), platform_rect)
                elif t == TILE_LADDER:
                    pygame.draw.rect(surface, (210, 180, 80), rect)
                elif t == TILE_BOUNDARY:
                    pygame.draw.rect(surface, (80, 120, 160), rect)

    def _draw_foreground(self, surface: pygame.Surface) -> None:
        factor_fore = 1.2
        width = surface.get_width()
        height = surface.get_height()
        offset_fore = -int(self.camera_x * factor_fore) % (5 * TILE_SIZE)
        for x in range(-offset_fore, width + 5 * TILE_SIZE, 5 * TILE_SIZE):
            rect = pygame.Rect(x, height - 2 * TILE_SIZE, TILE_SIZE, 2 * TILE_SIZE)
            pygame.draw.rect(surface, (12, 14, 18), rect)

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

    def run_scripted(
        self,
        total_frames: int,
        keys_for_frame: Optional[Callable[[int], set[int]]] = None,
        capture_callback: Optional[Callable[[int, pygame.Surface], None]] = None,
    ) -> int:
        """
        Deterministic, headless-friendly loop for test scenarios.
        - keys_for_frame(frame_index) -> Set[int] of pygame.K_* to hold pressed
        - capture_callback(frame_index, surface) -> None to save screenshots
        """
        # Use fixed timestep for determinism
        delta_seconds = 1.0 / float(self.config.target_fps)
        pressed_prev: set[int] = set()

        # Provide a proxy that emulates pygame.key.get_pressed() based on a dynamic set
        class _PressedProxy:
            def __init__(self, pressed_keys: set[int]) -> None:
                self._pressed_keys = pressed_keys

            def __getitem__(self, key_code: int) -> int:
                return 1 if key_code in self._pressed_keys else 0

        original_get_pressed = pygame.key.get_pressed

        for frame in range(total_frames):
            desired_pressed: set[int] = set()
            if keys_for_frame is not None:
                try:
                    desired = keys_for_frame(frame)
                    if desired:
                        desired_pressed = set(desired)
                except Exception:
                    desired_pressed = set()

            # Inject synthetic KEYDOWN/KEYUP events to mirror desired key state
            # Issue KEYUP for keys no longer pressed
            for key in (pressed_prev - desired_pressed):
                pygame.event.post(pygame.event.Event(pygame.KEYUP, {"key": key}))
            # Issue KEYDOWN for newly pressed keys
            for key in (desired_pressed - pressed_prev):
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": key}))
            pressed_prev = desired_pressed

            # Monkey-patch get_pressed to reflect our desired state for this frame
            pygame.key.get_pressed = lambda: _PressedProxy(desired_pressed)  # type: ignore[assignment,return-value]

            # Process event queue
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.key.get_pressed = original_get_pressed  # restore
                    return 0
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.key.get_pressed = original_get_pressed  # restore
                    return 0
                elif self._current_scene is not None:
                    self._current_scene.handle_event(event)

            # Update and draw
            if self._current_scene is not None:
                self._current_scene.update(delta_seconds)
                self._current_scene.draw(self._screen)

            pygame.display.flip()

            if capture_callback is not None:
                capture_callback(frame, self._screen)

        # Restore original get_pressed after loop
        pygame.key.get_pressed = original_get_pressed
        return 0
