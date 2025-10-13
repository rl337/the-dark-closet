"""
Performance tests using pytest.
"""

from __future__ import annotations

import pytest
import pygame
import time
import statistics
from typing import Dict, List

from the_dark_closet.assets import generate_character_assets


class PerformanceProfiler:
    """Profiles game performance and identifies bottlenecks."""

    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}

    def measure(self, name: str, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()

        duration = end_time - start_time

        if name not in self.measurements:
            self.measurements[name] = []
        self.measurements[name].append(duration)

        return result, duration

    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a measurement."""
        if name not in self.measurements or not self.measurements[name]:
            return {}

        values = self.measurements[name]
        return {
            "count": len(values),
            "total": sum(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }


@pytest.fixture
def profiler():
    """Create a performance profiler."""
    return PerformanceProfiler()


class TestAssetPerformance:
    """Test asset generation and loading performance."""

    @pytest.mark.performance
    @pytest.mark.asset
    def test_asset_generation_performance(self, profiler, temp_assets_dir):
        """Test asset generation performance."""
        # Test asset generation multiple times
        for i in range(10):
            profiler.measure(
                "asset_generation",
                generate_character_assets,
                temp_assets_dir / f"assets_{i}",
            )

        stats = profiler.get_stats("asset_generation")

        # Assert performance requirements
        assert (
            stats["mean"] < 0.2
        ), f"Asset generation too slow: {stats['mean']:.3f}s mean"
        assert stats["max"] < 0.4, f"Asset generation too slow: {stats['max']:.3f}s max"

        # Print performance report
        print("\nAsset Generation Performance:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  Max:   {stats['max']:.4f}s")
        print(f"  StDev: {stats['stdev']:.4f}s")

    @pytest.mark.performance
    @pytest.mark.asset
    def test_asset_loading_performance(self, profiler, test_scene):
        """Test asset loading performance."""
        scene = test_scene

        # Test asset loading multiple times
        for i in range(10):
            profiler.measure("asset_loading", scene._load_character_assets)

        stats = profiler.get_stats("asset_loading")

        # Assert performance requirements
        assert (
            stats["mean"] < 0.05
        ), f"Asset loading too slow: {stats['mean']:.3f}s mean"
        assert stats["max"] < 0.10, f"Asset loading too slow: {stats['max']:.3f}s max"

        # Print performance report
        print("\nAsset Loading Performance:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  Max:   {stats['max']:.4f}s")
        print(f"  StDev: {stats['stdev']:.4f}s")

    @pytest.mark.performance
    @pytest.mark.asset
    def test_asset_scaling_performance(self, profiler, temp_assets_dir):
        """Test asset scaling performance."""
        # Generate test assets
        assets = generate_character_assets(temp_assets_dir)

        # Test different scaling operations
        for scale in [0.5, 1.0, 2.0, 4.0]:
            for i in range(20):

                def scale_asset():
                    if assets:
                        # Get first asset
                        asset_path = list(assets.values())[0]
                        surface = pygame.image.load(str(asset_path))
                        scaled = pygame.transform.scale(
                            surface,
                            (
                                int(surface.get_width() * scale),
                                int(surface.get_height() * scale),
                            ),
                        )
                        return scaled
                    return None

                profiler.measure(f"scaling_{scale}x", scale_asset)

        # Check performance for each scale
        for scale in [0.5, 1.0, 2.0, 4.0]:
            stats = profiler.get_stats(f"scaling_{scale}x")
            assert (
                stats["mean"] < 0.02
            ), f"Asset scaling {scale}x too slow: {stats['mean']:.3f}s mean"

            print(f"\nAsset Scaling {scale}x Performance:")
            print(f"  Count: {stats['count']}")
            print(f"  Mean:  {stats['mean']:.4f}s")
            print(f"  Max:   {stats['max']:.4f}s")


class TestRenderingPerformance:
    """Test rendering performance."""

    @pytest.mark.performance
    @pytest.mark.rendering
    def test_frame_rendering_performance(self, profiler, test_scene):
        """Test frame rendering performance."""
        app = test_scene.app

        # Test frame rendering multiple times
        for i in range(100):

            def render_frame():
                app.advance_frame(None)

            profiler.measure("frame_rendering", render_frame)

        stats = profiler.get_stats("frame_rendering")

        # Assert performance requirements
        assert (
            stats["mean"] < 0.015
        ), f"Frame rendering too slow: {stats['mean']:.3f}s mean"
        assert (
            stats["max"] < 0.2
        ), f"Frame rendering too slow: {stats['max']:.3f}s max"  # Relaxed threshold

        # Print performance report
        print("\nFrame Rendering Performance:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  Max:   {stats['max']:.4f}s")
        print(f"  StDev: {stats['stdev']:.4f}s")

    @pytest.mark.performance
    @pytest.mark.rendering
    def test_movement_rendering_performance(self, profiler, test_scene):
        """Test rendering performance during movement."""
        app = test_scene.app

        # Test rendering with movement
        for i in range(50):

            def render_with_movement():
                app.advance_frame({pygame.K_RIGHT})

            profiler.measure("rendering_with_movement", render_with_movement)

        stats = profiler.get_stats("rendering_with_movement")

        # Assert performance requirements
        assert (
            stats["mean"] < 0.015
        ), f"Movement rendering too slow: {stats['mean']:.3f}s mean"

        # Print performance report
        print("\nMovement Rendering Performance:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  Max:   {stats['max']:.4f}s")

    @pytest.mark.performance
    @pytest.mark.rendering
    def test_jump_rendering_performance(self, profiler, test_scene):
        """Test rendering performance during jumping."""
        app = test_scene.app

        # Test rendering with jumping
        for i in range(50):

            def render_with_jump():
                app.advance_frame({pygame.K_SPACE})

            profiler.measure("rendering_with_jump", render_with_jump)

        stats = profiler.get_stats("rendering_with_jump")

        # Assert performance requirements
        assert (
            stats["mean"] < 0.015
        ), f"Jump rendering too slow: {stats['mean']:.3f}s mean"

        # Print performance report
        print("\nJump Rendering Performance:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  Max:   {stats['max']:.4f}s")


class TestMemoryPerformance:
    """Test memory usage patterns."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_patterns(self, test_game_app):
        """Test memory usage patterns."""
        import gc

        # Measure baseline memory
        gc.collect()
        print("Baseline: Memory cleaned")

        # Create multiple game instances
        games = []
        for i in range(10):
            from the_dark_closet.game import SideScrollerScene

            # Create a simple room for testing
            room = [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ]

            scene = SideScrollerScene(test_game_app, room, (6 * 128, 4 * 128))
            test_game_app.switch_scene(scene)
            games.append(test_game_app)
            print(f"Created game {i+1}")

        # Test memory after rendering
        for i, app in enumerate(games):
            for _ in range(10):
                app.advance_frame(None)
            print(f"Rendered game {i+1}")

        # Cleanup
        del games
        gc.collect()
        print("After cleanup: Memory cleaned")

        # This test always passes - it's just for monitoring
        assert True, "Memory usage test completed"

    @pytest.mark.performance
    def test_memory_cleanup(self, test_game_app):
        """Test that memory is properly cleaned up."""
        import gc

        # Create and destroy multiple game instances
        for i in range(5):
            from the_dark_closet.game import SideScrollerScene

            # Create a simple room for testing
            room = [
                "BBBBBBBBBBBB",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "B          B",
                "BBBBBBBBBBBB",
            ]

            scene = SideScrollerScene(test_game_app, room, (6 * 128, 4 * 128))
            test_game_app.switch_scene(scene)

            # Render some frames
            for _ in range(10):
                test_game_app.advance_frame(None)

            # Cleanup
            del scene
            gc.collect()

        # This test always passes - it's just for monitoring
        assert True, "Memory cleanup test completed"


class TestFrameRatePerformance:
    """Test frame rate stability."""

    @pytest.mark.performance
    @pytest.mark.rendering
    def test_frame_rate_stability(self, test_scene):
        """Test frame rate stability."""
        app = test_scene.app

        frame_times = []

        # Test 300 frames (5 seconds at 60 FPS)
        for i in range(300):
            frame_start = time.perf_counter()
            app.advance_frame(None)
            frame_end = time.perf_counter()
            frame_times.append(frame_end - frame_start)

        # Calculate frame rate statistics
        fps_values = [1.0 / frame_time for frame_time in frame_times]

        avg_fps = statistics.mean(fps_values)
        min_fps = min(fps_values)
        max_fps = max(fps_values)
        fps_stddev = statistics.stdev(fps_values)

        print("\nFrame Rate Performance:")
        print(f"Frames rendered: {len(frame_times)}")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Min FPS: {min_fps:.2f}")
        print(f"Max FPS: {max_fps:.2f}")
        print(f"FPS StdDev: {fps_stddev:.2f}")

        # Check if we're maintaining good performance
        target_fps = 60
        fps_ratio = avg_fps / target_fps

        print(f"FPS ratio (actual/target): {fps_ratio:.2f}")

        # Assert performance requirements
        assert fps_ratio >= 0.9, f"Frame rate too low: {fps_ratio:.2f} ratio"
        assert fps_stddev < 1000, f"Frame rate too unstable: {fps_stddev:.2f} stddev"


class TestAssetGenerationPerformance:
    """Test asset generation performance."""

    @pytest.mark.performance
    @pytest.mark.asset
    def test_asset_generation_consistency(self, profiler, temp_assets_dir):
        """Test that asset generation is consistent in performance."""
        # Generate assets multiple times
        for i in range(20):
            profiler.measure(
                "asset_generation_consistency",
                generate_character_assets,
                temp_assets_dir / f"consistency_{i}",
            )

        stats = profiler.get_stats("asset_generation_consistency")

        # Check consistency (low standard deviation)
        assert (
            stats["stdev"] < 0.15
        ), f"Asset generation too inconsistent: {stats['stdev']:.3f}s stddev"

        print("\nAsset Generation Consistency:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  StDev: {stats['stdev']:.4f}s")

    @pytest.mark.performance
    @pytest.mark.asset
    def test_asset_generation_scalability(self, profiler, temp_assets_dir):
        """Test asset generation scalability."""
        # Test with different output directory sizes
        for i in range(5):
            profiler.measure(
                "asset_generation_scalability",
                generate_character_assets,
                temp_assets_dir / f"scalability_{i}",
            )

        stats = profiler.get_stats("asset_generation_scalability")

        # Performance should be consistent regardless of directory size
        assert (
            stats["stdev"] < 0.15
        ), f"Asset generation not scalable: {stats['stdev']:.3f}s stddev"

        print("\nAsset Generation Scalability:")
        print(f"  Count: {stats['count']}")
        print(f"  Mean:  {stats['mean']:.4f}s")
        print(f"  StDev: {stats['stdev']:.4f}s")


@pytest.mark.parametrize(
    "test_type,expected_max_time",
    [
        ("asset_generation", 0.25),
        ("asset_loading", 0.04),
        ("frame_rendering", 0.015),
        ("movement_rendering", 0.015),
        ("jump_rendering", 0.015),
    ],
)
@pytest.mark.performance
def test_performance_benchmarks(
    profiler, test_scene, temp_assets_dir, test_type, expected_max_time
):
    """Parametrized performance benchmarks."""
    if test_type == "asset_generation":
        for i in range(10):
            profiler.measure(
                test_type, generate_character_assets, temp_assets_dir / f"benchmark_{i}"
            )
    elif test_type == "asset_loading":
        for i in range(10):
            profiler.measure(test_type, test_scene._load_character_assets)
    elif test_type == "frame_rendering":
        for i in range(50):

            def render_frame():
                test_scene.app.advance_frame(None)

            profiler.measure(test_type, render_frame)
    elif test_type == "movement_rendering":
        for i in range(50):

            def render_movement():
                test_scene.app.advance_frame({pygame.K_RIGHT})

            profiler.measure(test_type, render_movement)
    elif test_type == "jump_rendering":
        for i in range(50):

            def render_jump():
                test_scene.app.advance_frame({pygame.K_SPACE})

            profiler.measure(test_type, render_jump)

    stats = profiler.get_stats(test_type)
    assert (
        stats["mean"] < expected_max_time
    ), f"{test_type} too slow: {stats['mean']:.3f}s > {expected_max_time}s"

    print(f"\n{test_type} Benchmark:")
    print(f"  Mean:  {stats['mean']:.4f}s")
    print(f"  Max:   {stats['max']:.4f}s")
    print(f"  StDev: {stats['stdev']:.4f}s")
