#!/usr/bin/env python3
"""
Comprehensive test runner for all test suites.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
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
    """Run all test suites."""
    print("🚀 Running Comprehensive Test Suite")
    print("=" * 60)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    # Test results
    results = []
    
    # 1. Generate procedural assets
    success, output = run_command(
        ["poetry", "run", "python", "scripts/build_assets.py"],
        "Generate Procedural Assets"
    )
    results.append(("Asset Generation", success))
    
    # 2. Basic functionality tests
    success, output = run_command(
        ["poetry", "run", "python", "scripts/test_utils.py"],
        "Basic Functionality Tests"
    )
    results.append(("Basic Functionality", success))
    
    # 3. Procedural asset tests
    success, output = run_command(
        ["poetry", "run", "python", "scripts/test_procedural_assets.py"],
        "Procedural Asset Tests"
    )
    results.append(("Procedural Assets", success))
    
    # 4. Comprehensive scenario tests
    success, output = run_command(
        ["poetry", "run", "python", "scripts/test_comprehensive_scenarios.py"],
        "Comprehensive Scenario Tests"
    )
    results.append(("Comprehensive Scenarios", success))
    
    # 5. Visual regression tests
    success, output = run_command(
        ["poetry", "run", "python", "scripts/test_visual_regression.py"],
        "Visual Regression Tests"
    )
    results.append(("Visual Regression", success))
    
    # 6. Performance tests
    success, output = run_command(
        ["poetry", "run", "python", "scripts/test_performance.py"],
        "Performance Tests"
    )
    results.append(("Performance", success))
    
    # 7. Screenshot generation
    success, output = run_command(
        ["poetry", "run", "python", "scripts/run_action_tests.py"],
        "Screenshot Generation"
    )
    results.append(("Screenshot Generation", success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25} {status}")
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
