# The Dark Closet

A small Pygame project managed with Poetry. You play a boy who discovers a portal in his closet and, rather than seeking wonder, chooses conquest.

## Requirements

- Python 3.10–3.x (tested with the system's Python)
- Poetry 2.x (installed locally by the setup steps below)

## Quick start

```bash
# If Poetry is not on your PATH after install, use the full path
/home/ubuntu/.local/bin/poetry --version

# Install dependencies and create a virtualenv
/home/ubuntu/.local/bin/poetry install

# Run the game
/home/ubuntu/.local/bin/poetry run the-dark-closet

# Headless smoke test (runs 3 frames then exits)
TDC_MAX_FRAMES=3 /home/ubuntu/.local/bin/poetry run the-dark-closet
```

If you are on a headless machine without a display, the game will fall back to SDL's "dummy" video driver and run without opening a visible window.

## Project layout

```
src/
  the_dark_closet/
    __init__.py
    __main__.py   # entrypoint for `the-dark-closet`
    game.py       # core loop and scenes
assets/           # put images, sounds here (optional)
```

## Scripts

- `the-dark-closet`: launches the game. Use `poetry run the-dark-closet`.

## Development

```bash
# Lint (ruff) and format (black)
/home/ubuntu/.local/bin/poetry run ruff check .
/home/ubuntu/.local/bin/poetry run black .
```

## Packaging

```bash
/home/ubuntu/.local/bin/poetry build
```
