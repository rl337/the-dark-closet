import os
import sys

# Hide pygame's support prompt to keep CLI output clean
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

# Fall back to a headless video driver when no display is available
if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

from .game import GameApp, GameConfig


def main() -> int:
    config = GameConfig(
        window_width=1280,
        window_height=720,
        window_title="The Dark Closet",
        target_fps=60,
    )
    app = GameApp(config)
    # Allow CI/headless smoke test via env var: run limited frames then exit
    try:
        max_frames_env = os.environ.get("TDC_MAX_FRAMES")
        max_frames = int(max_frames_env) if max_frames_env is not None else None
    except ValueError:
        max_frames = None
    # Allow autostart of side scroller from env
    if os.environ.get("TDC_AUTOSTART") == "sidescroller":
        try:
            from .game import SideScrollerScene
        except Exception:
            SideScrollerScene = None  # type: ignore
        if SideScrollerScene is not None:
            app.switch_scene(SideScrollerScene(app))
    return app.run(max_frames=max_frames)


if __name__ == "__main__":
    raise SystemExit(main())
