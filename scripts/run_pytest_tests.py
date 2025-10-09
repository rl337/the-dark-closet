#!/usr/bin/env python3
"""
Pytest test runner script.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def run_pytest_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run a pytest command and return success status and output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy", "PYTHONPATH": "src"}
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False, e.stderr


def main():
    """Run pytest test suites."""
    print("🧪 Running Pytest Test Suite")
    print("=" * 60)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Test results
    results = []
    
    # 1. Generate procedural assets first
    print("Generating procedural assets...")
    from the_dark_closet.assets import generate_character_assets
    generate_character_assets(Path("generated_assets"))
    print("✓ Assets generated")
    
    # 2. Run unit tests
    success, output = run_pytest_command(
        ["poetry", "run", "pytest", "tests/unit/", "-v", "--tb=short"],
        "Unit Tests"
    )
    results.append(("Unit Tests", success))
    
    # 3. Run integration tests
    success, output = run_pytest_command(
        ["poetry", "run", "pytest", "tests/integration/", "-v", "--tb=short"],
        "Integration Tests"
    )
    results.append(("Integration Tests", success))
    
    # 4. Run visual regression tests
    success, output = run_pytest_command(
        ["poetry", "run", "pytest", "tests/visual/", "-v", "--tb=short"],
        "Visual Regression Tests"
    )
    results.append(("Visual Regression Tests", success))
    
    # 5. Run performance tests
    success, output = run_pytest_command(
        ["poetry", "run", "pytest", "tests/performance/", "-v", "--tb=short"],
        "Performance Tests"
    )
    results.append(("Performance Tests", success))
    
    # 6. Run all tests with coverage
    success, output = run_pytest_command(
        ["poetry", "run", "pytest", "tests/", "-v", "--tb=short", "--cov=src", "--cov-report=html:reports/coverage"],
        "All Tests with Coverage"
    )
    results.append(("All Tests with Coverage", success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("💥 SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
