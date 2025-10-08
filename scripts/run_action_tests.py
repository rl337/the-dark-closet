from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, List, Tuple

# Ensure we can import from src layout
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pygame

from the_dark_closet.game import (
    GameApp,
    GameConfig,
    SideScrollerScene,
    TILE_BOUNDARY,
    TILE_BRICK,
    TILE_EMPTY,
    TILE_LADDER,
    TILE_METAL,
    TILE_PLATFORM,
    TILE_SIZE,
)


def rect_room(width_tiles: int, height_tiles: int) -> List[str]:
    rows: List[str] = []
    for r in range(height_tiles):
        line = [TILE_EMPTY] * width_tiles
        for c in range(width_tiles):
            is_border = (
                r == 0 or r == height_tiles - 1 or c == 0 or c == width_tiles - 1
            )
            if is_border:
                line[c] = TILE_BOUNDARY
        rows.append("".join(line))
    return rows


def place(rows: List[str], col: int, row: int, tile: str) -> None:
    if 0 <= row < len(rows):
        line = list(rows[row])
        if 0 <= col < len(line):
            line[col] = tile
            rows[row] = "".join(line)


def save_surface(surface: pygame.Surface, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(out_path))


def run_action(
    name: str,
    world: List[str],
    total_frames: int,
    keys_for_frame: Callable[[int], set[int]],
    spawn_px: Tuple[int, int],
    out_dir: Path,
) -> None:
    # Headless-safe defaults
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    config = GameConfig(
        window_width=400, window_height=300, window_title=name, target_fps=30
    )
    app = GameApp(config)
    scene = SideScrollerScene(app, world_tiles=world, player_spawn_px=spawn_px)
    app.switch_scene(scene)

    def capture(frame_idx: int, surface: pygame.Surface) -> None:
        out = out_dir / name
        # Save before and after
        if frame_idx in {0, total_frames - 1}:
            tag = "before" if frame_idx == 0 else "after"
            save_surface(surface, out / f"{name}_{tag}.png")
        # Save 3 evenly spaced timesteps
        for k in range(1, 4):
            t = int(k * (total_frames - 1) / 4)
            if frame_idx == t:
                save_surface(surface, out / f"{name}_t{k}.png")

    out_dir.mkdir(parents=True, exist_ok=True)
    app.run_scripted(
        total_frames=total_frames,
        keys_for_frame=keys_for_frame,
        capture_callback=capture,
    )


def test_move_left_right(out_dir: Path) -> None:
    room = rect_room(12, 8)
    spawn_px = (TILE_SIZE * 6, TILE_SIZE * 6)

    def keys(frame: int):
        if 5 <= frame < 25:
            return {pygame.K_RIGHT}
        if 30 <= frame < 50:
            return {pygame.K_LEFT}
        return set()

    run_action(
        "move_left_right",
        room,
        total_frames=60,
        keys_for_frame=keys,
        spawn_px=spawn_px,
        out_dir=out_dir,
    )


def test_jump(out_dir: Path) -> None:
    room = rect_room(12, 10)
    # add a simple metal floor
    for c in range(1, 11):
        place(room, c, 8, TILE_METAL)
    spawn_px = (TILE_SIZE * 6, TILE_SIZE * 7)

    def keys(frame: int):
        return {pygame.K_SPACE} if frame in {5, 20, 35} else set()

    run_action(
        "jump",
        room,
        total_frames=50,
        keys_for_frame=keys,
        spawn_px=spawn_px,
        out_dir=out_dir,
    )


def test_break_brick(out_dir: Path) -> None:
    room = rect_room(12, 10)
    # place a brick above spawn to hit from below
    place(room, 6, 6, TILE_BRICK)
    # floor to land on
    for c in range(1, 11):
        place(room, c, 8, TILE_METAL)
    spawn_px = (TILE_SIZE * 6, TILE_SIZE * 7)

    def keys(frame: int):
        # a few jumps to ensure collision
        return {pygame.K_SPACE} if frame in {6, 18, 30} else set()

    run_action(
        "break_brick",
        room,
        total_frames=40,
        keys_for_frame=keys,
        spawn_px=spawn_px,
        out_dir=out_dir,
    )


def test_ladders(out_dir: Path) -> None:
    room = rect_room(12, 12)
    # ladder from row 3 to row 9 at column 6
    for r in range(3, 10):
        place(room, 6, r, TILE_LADDER)
    # small platforms near top and bottom
    for c in range(4, 9):
        place(room, c, 10, TILE_PLATFORM)
        place(room, c, 2, TILE_PLATFORM)

    spawn_px = (TILE_SIZE * 6, TILE_SIZE * 10)

    def keys(frame: int):
        if 5 <= frame < 30:
            return {pygame.K_UP}
        if 35 <= frame < 55:
            return {pygame.K_DOWN}
        return set()

    run_action(
        "ladders",
        room,
        total_frames=60,
        keys_for_frame=keys,
        spawn_px=spawn_px,
        out_dir=out_dir,
    )


ALL_TESTS = [
    ("move_left_right", test_move_left_right),
    ("jump", test_jump),
    ("break_brick", test_break_brick),
    ("ladders", test_ladders),
]


def generate_index(out_dir: Path) -> None:
    # Build an index.html that showcases each test's images
    index_path = out_dir / "index.html"
    tests = [name for name, _ in ALL_TESTS]
    html_parts: List[str] = []
    html_parts.append("<!DOCTYPE html>")
    html_parts.append('<html lang="en">')
    html_parts.append("<head>")
    html_parts.append('  <meta charset="utf-8">')
    html_parts.append(
        '  <meta name="viewport" content="width=device-width, initial-scale=1">'
    )
    html_parts.append("  <title>Action Tests</title>")
    html_parts.append(
        "  <style>\nbody{font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; background:#0b0e12; color:#e6e9ef; margin:0; padding:24px;}\n.grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px;}\n.card{background:#11151c; border:1px solid #222835; border-radius:10px; padding:12px;}\n.card h2{font-size:16px; margin:0 0 8px 0;}\n.thumb{display:block; width:100%; height:auto; background:#0b0e12; border-radius:6px; border:1px solid #1f2532; margin-bottom:6px;}\n.row{display:flex; gap:8px; flex-wrap:wrap;}\n.row img{flex:1 1 110px; min-width:110px; max-width:calc(50% - 8px);}\nsmall{color:#98a2b3;}\nfooter{margin-top:24px; color:#98a2b3;}\n  </style>"
    )
    html_parts.append("</head>")
    html_parts.append("<body>")
    html_parts.append("  <h1>Headless Action Tests</h1>")
    html_parts.append(
        "  <p>Automatically generated screenshots demonstrating basic character actions in small enclosed rooms.</p>"
    )
    html_parts.append('  <div class="grid">')

    for name in tests:
        base = f"screens/{name}/{name}"
        images = [
            f"{base}_before.png",
            f"{base}_t1.png",
            f"{base}_t2.png",
            f"{base}_t3.png",
            f"{base}_after.png",
        ]
        html_parts.append('    <div class="card">')
        html_parts.append(f"      <h2>{name}</h2>")
        html_parts.append('      <div class="row">')
        for img in images:
            html_parts.append(f'        <img class="thumb" src="{img}" alt="{name}">')
        html_parts.append("      </div>")
        html_parts.append("      <small>before, t1, t2, t3, after</small>")
        html_parts.append("    </div>")

    html_parts.append("  </div>")
    html_parts.append("  <footer>Generated by scripts/run_action_tests.py</footer>")
    html_parts.append("</body>")
    html_parts.append("</html>")

    index_path.write_text("\n".join(html_parts), encoding="utf-8")


def main() -> int:
    # Output root for the website (consumed by GitHub Pages workflow)
    out_root = Path(os.environ.get("TDC_SITE_DIR", "docs"))
    screens_dir = out_root / "screens"

    for _, fn in ALL_TESTS:
        fn(screens_dir)

    generate_index(out_root)
    print(f"Wrote site to: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
