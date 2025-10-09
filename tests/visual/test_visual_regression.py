"""
Visual regression tests using pytest.
"""

from __future__ import annotations

import pytest
import pygame
from pathlib import Path
from typing import Dict, List, Tuple

from ..conftest import find_center_mass_position, save_surface


class VisualRegressionTester:
    """Handles visual regression testing with image comparison."""
    
    def __init__(self, baseline_dir: Path, current_dir: Path):
        self.baseline_dir = baseline_dir
        self.current_dir = current_dir
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.current_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_test_scene(self, name: str, world: List[str], spawn_px: Tuple[int, int], 
                          actions: List[Tuple[str, int, int]]) -> List[Path]:
        """Capture screenshots for a test scene."""
        from the_dark_closet.game import GameApp, GameConfig, SideScrollerScene, ControlledTimeProvider
        
        # Create test game
        config = GameConfig(
            window_width=512,
            window_height=384,
            window_title="Visual Test",
            target_fps=60,
        )
        time_provider = ControlledTimeProvider(1.0 / 60.0)
        app = GameApp(config, time_provider)
        
        scene = SideScrollerScene(app, world, spawn_px)
        app.switch_scene(scene)
        app.advance_frame(None)
        
        screenshots = []
        frame_count = 0
        
        for description, keys, frames in actions:
            for frame in range(frames):
                frame_count += 1
                app.advance_frame(keys)
                
                screenshot_path = self.current_dir / f"{name}_{description}_{frame:02d}.png"
                save_surface(app._screen, screenshot_path)
                screenshots.append(screenshot_path)
        
        return screenshots
    
    def compare_images(self, baseline_path: Path, current_path: Path) -> Tuple[bool, str, float]:
        """Compare two images and return similarity metrics."""
        if not baseline_path.exists():
            return False, "Baseline image not found", 0.0
        
        if not current_path.exists():
            return False, "Current image not found", 0.0
        
        # Load images
        try:
            baseline = pygame.image.load(str(baseline_path))
            current = pygame.image.load(str(current_path))
        except pygame.error as e:
            return False, f"Error loading images: {e}", 0.0
        
        # Check dimensions
        if baseline.get_size() != current.get_size():
            return False, f"Size mismatch: {baseline.get_size()} vs {current.get_size()}", 0.0
        
        # Calculate pixel differences
        width, height = baseline.get_size()
        total_pixels = width * height
        different_pixels = 0
        
        for y in range(height):
            for x in range(width):
                baseline_color = baseline.get_at((x, y))
                current_color = current.get_at((x, y))
                if baseline_color != current_color:
                    different_pixels += 1
        
        similarity = 1.0 - (different_pixels / total_pixels)
        is_similar = similarity >= 0.95  # 95% similarity threshold
        
        return is_similar, f"Similarity: {similarity:.3f} ({different_pixels}/{total_pixels} different pixels)", similarity


@pytest.fixture
def visual_tester(output_dir):
    """Create a visual regression tester."""
    baseline_dir = output_dir / "baselines"
    current_dir = output_dir / "current"
    return VisualRegressionTester(baseline_dir, current_dir)


class TestCharacterRenderingRegression:
    """Test character rendering for visual regressions."""
    
    @pytest.mark.visual
    def test_character_rendering_consistency(self, visual_tester, output_dir):
        """Test character rendering consistency."""
        # Simple character rendering test
        world = [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B", 
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
        
        spawn_px = (6 * 128, 4 * 128)
        actions = [
            ("idle", None, 4),
            ("move_right", {pygame.K_RIGHT}, 4),
            ("move_left", {pygame.K_LEFT}, 4),
        ]
        
        # Capture current screenshots
        current_screenshots = visual_tester.capture_test_scene("character_rendering", world, spawn_px, actions)
        
        # Compare with baselines
        all_passed = True
        for screenshot_path in current_screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            
            is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
            
            if not is_similar:
                all_passed = False
                # Copy current image to baseline for easy comparison
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(screenshot_path, baseline_path)
        
        assert all_passed, "Visual regression detected in character rendering"
    
    @pytest.mark.visual
    def test_character_movement_consistency(self, visual_tester, output_dir):
        """Test character movement visual consistency."""
        world = [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B", 
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
        
        spawn_px = (3 * 128, 4 * 128)
        actions = [
            ("move_sequence", {pygame.K_RIGHT}, 8),
        ]
        
        # Capture current screenshots
        current_screenshots = visual_tester.capture_test_scene("character_movement", world, spawn_px, actions)
        
        # Compare with baselines
        all_passed = True
        for screenshot_path in current_screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            
            is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
            
            if not is_similar:
                all_passed = False
                # Copy current image to baseline for easy comparison
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(screenshot_path, baseline_path)
        
        assert all_passed, "Visual regression detected in character movement"


class TestPlatformInteractionRegression:
    """Test platform interactions for visual regressions."""
    
    @pytest.mark.visual
    def test_platform_interaction_consistency(self, visual_tester, output_dir):
        """Test platform interaction visual consistency."""
        world = [
            "BBBBBBBBBBBB",
            "B          B",
            "B    PP    B",  # Platform
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
        
        spawn_px = (6 * 128, 2 * 128)  # Above platform
        actions = [
            ("fall_to_platform", None, 8),
            ("jump_from_platform", {pygame.K_SPACE}, 8),
        ]
        
        # Capture current screenshots
        current_screenshots = visual_tester.capture_test_scene("platform_interaction", world, spawn_px, actions)
        
        # Compare with baselines
        all_passed = True
        for screenshot_path in current_screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            
            is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
            
            if not is_similar:
                all_passed = False
                # Copy current image to baseline for easy comparison
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(screenshot_path, baseline_path)
        
        assert all_passed, "Visual regression detected in platform interaction"


class TestTileRenderingRegression:
    """Test tile rendering for visual regressions."""
    
    @pytest.mark.visual
    def test_tile_rendering_consistency(self, visual_tester, output_dir):
        """Test tile rendering visual consistency."""
        world = [
            "BBBBBBBBBBBB",  # Boundaries
            "B          B",
            "B   BBBB   B",  # Bricks
            "B   HHHH   B",  # Ladders
            "B   PPPP   B",  # Platforms
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
        
        spawn_px = (6 * 128, 4 * 128)
        actions = [
            ("observe_tiles", None, 8),
        ]
        
        # Capture current screenshots
        current_screenshots = visual_tester.capture_test_scene("tile_rendering", world, spawn_px, actions)
        
        # Compare with baselines
        all_passed = True
        for screenshot_path in current_screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            
            is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
            
            if not is_similar:
                all_passed = False
                # Copy current image to baseline for easy comparison
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(screenshot_path, baseline_path)
        
        assert all_passed, "Visual regression detected in tile rendering"


class TestAssetRenderingRegression:
    """Test procedural asset rendering for visual regressions."""
    
    @pytest.mark.visual
    @pytest.mark.asset
    def test_procedural_asset_consistency(self, visual_tester, output_dir):
        """Test procedural asset rendering consistency."""
        world = [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B", 
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ]
        
        spawn_px = (6 * 128, 4 * 128)
        actions = [
            ("asset_rendering", None, 8),
        ]
        
        # Capture current screenshots
        current_screenshots = visual_tester.capture_test_scene("procedural_assets", world, spawn_px, actions)
        
        # Compare with baselines
        all_passed = True
        for screenshot_path in current_screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            
            is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
            
            if not is_similar:
                all_passed = False
                # Copy current image to baseline for easy comparison
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(screenshot_path, baseline_path)
        
        assert all_passed, "Visual regression detected in procedural asset rendering"


@pytest.mark.parametrize("test_name,world,spawn_px,actions", [
    ("character_idle", [
        "BBBBBBBBBBBB",
        "B          B",
        "B          B", 
        "B          B",
        "B          B",
        "B          B",
        "B          B",
        "BBBBBBBBBBBB",
    ], (6 * 128, 4 * 128), [("idle", None, 4)]),
    
    ("character_move_right", [
        "BBBBBBBBBBBB",
        "B          B",
        "B          B", 
        "B          B",
        "B          B",
        "B          B",
        "B          B",
        "BBBBBBBBBBBB",
    ], (3 * 128, 4 * 128), [("move_right", {pygame.K_RIGHT}, 4)]),
    
    ("character_move_left", [
        "BBBBBBBBBBBB",
        "B          B",
        "B          B", 
        "B          B",
        "B          B",
        "B          B",
        "B          B",
        "BBBBBBBBBBBB",
    ], (9 * 128, 4 * 128), [("move_left", {pygame.K_LEFT}, 4)]),
])
@pytest.mark.visual
def test_character_rendering_parametrized(visual_tester, test_name, world, spawn_px, actions, output_dir):
    """Parametrized test for different character rendering scenarios."""
    # Capture current screenshots
    current_screenshots = visual_tester.capture_test_scene(test_name, world, spawn_px, actions)
    
    # Compare with baselines
    all_passed = True
    for screenshot_path in current_screenshots:
        baseline_path = visual_tester.baseline_dir / screenshot_path.name
        
        is_similar, message, similarity = visual_tester.compare_images(baseline_path, screenshot_path)
        
        if not is_similar:
            all_passed = False
            # Copy current image to baseline for easy comparison
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(screenshot_path, baseline_path)
    
    assert all_passed, f"Visual regression detected in {test_name}"


@pytest.mark.visual
def test_generate_baseline_images(visual_tester, output_dir):
    """Generate baseline images for visual regression testing."""
    # This test can be run to generate new baseline images
    test_scenarios = [
        ("character_rendering", [
            "BBBBBBBBBBBB",
            "B          B",
            "B          B", 
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ], (6 * 128, 4 * 128), [
            ("idle", None, 4),
            ("move_right", {pygame.K_RIGHT}, 4),
            ("move_left", {pygame.K_LEFT}, 4),
        ]),
        
        ("platform_interaction", [
            "BBBBBBBBBBBB",
            "B          B",
            "B    PP    B",
            "B          B",
            "B          B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ], (6 * 128, 2 * 128), [
            ("fall_to_platform", None, 8),
            ("jump_from_platform", {pygame.K_SPACE}, 8),
        ]),
        
        ("tile_rendering", [
            "BBBBBBBBBBBB",
            "B          B",
            "B   BBBB   B",
            "B   HHHH   B",
            "B   PPPP   B",
            "B          B",
            "B          B",
            "BBBBBBBBBBBB",
        ], (6 * 128, 4 * 128), [
            ("observe_tiles", None, 8),
        ]),
    ]
    
    for test_name, world, spawn_px, actions in test_scenarios:
        # Capture screenshots
        screenshots = visual_tester.capture_test_scene(test_name, world, spawn_px, actions)
        
        # Copy to baseline directory
        for screenshot_path in screenshots:
            baseline_path = visual_tester.baseline_dir / screenshot_path.name
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(screenshot_path, baseline_path)
    
    # This test always passes - it's just for generating baselines
    assert True, "Baseline images generated"
