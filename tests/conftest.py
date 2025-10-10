"""
Shared pytest fixtures and configuration.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator, Tuple, List
import tempfile
import shutil

import pytest
import pygame

# Add src to path for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from the_dark_closet.game import GameApp, GameConfig, SideScrollerScene, ControlledTimeProvider
from the_dark_closet.assets import generate_character_assets


@pytest.fixture(scope="session", autouse=True)
def setup_display():
    """Set up dummy display for headless testing."""
    if os.environ.get("DISPLAY") is None and os.environ.get("SDL_VIDEODRIVER") is None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"


@pytest.fixture
def game_config() -> GameConfig:
    """Standard game configuration for testing."""
    return GameConfig(
        window_width=512,
        window_height=384,
        window_title="Test Game",
        target_fps=60,
    )


@pytest.fixture
def controlled_time_provider() -> ControlledTimeProvider:
    """Controlled time provider for deterministic testing."""
    return ControlledTimeProvider(1.0 / 60.0)


@pytest.fixture
def test_game_app(game_config, controlled_time_provider) -> GameApp:
    """Create a test game app with controlled time."""
    return GameApp(game_config, controlled_time_provider)


@pytest.fixture
def simple_room() -> List[str]:
    """Simple test room layout."""
    return [
        "BBBBBBBBBBBB",  # Top boundary
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "BBBBBBBBBBBB",  # Bottom boundary
    ]


@pytest.fixture
def platform_room() -> List[str]:
    """Room with platforms for testing."""
    return [
        "BBBBBBBBBBBB",  # Top boundary
        "B          B",  # Empty
        "B    PP    B",  # Platform
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "BBBBBBBBBBBB",  # Bottom boundary
    ]


@pytest.fixture
def brick_room() -> List[str]:
    """Room with breakable bricks."""
    return [
        "BBBBBBBBBBBB",  # Top boundary
        "B          B",  # Empty
        "B          B",  # Empty
        "B   BBBB   B",  # Breakable bricks
        "B          B",  # Empty
        "B          B",  # Empty
        "B          B",  # Empty
        "BBBBBBBBBBBB",  # Bottom boundary
    ]


@pytest.fixture
def ladder_room() -> List[str]:
    """Room with ladders."""
    return [
        "BBBBBBBBBBBB",  # Top boundary
        "B          B",  # Empty
        "B    HH    B",  # Ladder
        "B    HH    B",  # Ladder
        "B    HH    B",  # Ladder
        "B          B",  # Empty
        "B          B",  # Empty
        "BBBBBBBBBBBB",  # Bottom boundary
    ]


@pytest.fixture
def test_scene(test_game_app, simple_room) -> SideScrollerScene:
    """Create a test scene with simple room."""
    spawn_px = (6 * 128, 4 * 128)  # Center
    scene = SideScrollerScene(test_game_app, simple_room, spawn_px)
    test_game_app.switch_scene(scene)
    return scene


@pytest.fixture
def temp_assets_dir() -> Generator[Path, None, None]:
    """Temporary directory for generated assets."""
    build_dir = Path("build/generated_assets")
    build_dir.mkdir(parents=True, exist_ok=True)
    yield build_dir


@pytest.fixture
def generated_assets(temp_assets_dir) -> dict:
    """Generate procedural assets for testing."""
    return generate_character_assets(temp_assets_dir)


@pytest.fixture
def output_dir() -> Generator[Path, None, None]:
    """Temporary directory for test outputs."""
    build_dir = Path("build/test_outputs")
    build_dir.mkdir(parents=True, exist_ok=True)
    yield build_dir


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files after each test."""
    yield
    # Clean up any temporary files created during tests
    temp_patterns = [
        "debug_*.png",
        "temp_assets_*",
        "test_assets",
    ]
    for pattern in temp_patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)


# Pytest markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "visual: Visual regression tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "asset: Asset generation tests")
    config.addinivalue_line("markers", "rendering: Rendering tests")


# Helper functions for tests
def find_center_mass_position(surface: pygame.Surface) -> Tuple[int, int] | None:
    """Find the center mass dot position in a surface."""
    width, height = surface.get_size()
    for y in range(height):
        for x in range(width):
            color = surface.get_at((x, y))
            if color[:3] == (255, 0, 255):  # Magenta center mass dot
                return (x, y)
    return None


def assert_center_mass_at(surface: pygame.Surface, expected_x: int, expected_y: int, tolerance: int = 2) -> bool:
    """Assert that the center mass dot is at the expected position."""
    pos = find_center_mass_position(surface)
    if pos is None:
        return False
    actual_x, actual_y = pos
    return (abs(actual_x - expected_x) <= tolerance and
            abs(actual_y - expected_y) <= tolerance)


def save_surface(surface: pygame.Surface, out_path: Path) -> None:
    """Save a pygame surface to a file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(out_path))
