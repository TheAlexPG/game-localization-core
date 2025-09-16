#!/usr/bin/env python3
"""Main test runner for all tests"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_provider_tests():
    """Run all provider tests"""
    print("=" * 50)
    print("RUNNING PROVIDER TESTS")
    print("=" * 50)

    provider_tests = [
        ("OpenAI Provider", "tests.providers.test_openai"),
        ("Local Provider", "tests.providers.test_local"),
        ("Structured Output", "tests.providers.test_structured_output"),
    ]

    for test_name, module_name in provider_tests:
        print(f"\n{test_name}...")
        try:
            module = __import__(module_name, fromlist=['main'])
            if hasattr(module, 'main'):
                module.main()
                print(f"OK: {test_name} completed")
            else:
                print(f"SKIP: {test_name} - no main function")
        except Exception as e:
            print(f"ERROR: {test_name} failed: {e}")


def run_validation_tests():
    """Run all validation tests"""
    print("\n" + "=" * 50)
    print("RUNNING VALIDATION TESTS")
    print("=" * 50)

    # Import validation test modules
    validation_tests = [
        ("Core Validation", "tests.validation.test_core_validation"),
        ("Game Data Validation", "tests.validation.test_game_validation"),
        ("Custom Patterns", "tests.validation.test_custom_simple"),
    ]

    for test_name, module_name in validation_tests:
        print(f"\n{test_name}...")
        try:
            module = __import__(module_name, fromlist=['main'])
            if hasattr(module, 'main'):
                module.main()
                print(f"OK: {test_name} completed")
            else:
                print(f"SKIP: {test_name} - no main function")
        except Exception as e:
            print(f"ERROR: {test_name} failed: {e}")


def run_basic_tests():
    """Run basic system tests"""
    print("\n" + "=" * 50)
    print("RUNNING BASIC TESTS")
    print("=" * 50)

    basic_tests = [
        ("Basic Functionality", "tests.test_basic"),
        ("Translation Pipeline", "tests.test_translation"),
    ]

    for test_name, module_name in basic_tests:
        print(f"\n{test_name}...")
        try:
            module = __import__(module_name, fromlist=['main'])
            if hasattr(module, 'main'):
                module.main()
                print(f"OK: {test_name} completed")
            else:
                print(f"SKIP: {test_name} - no main function")
        except Exception as e:
            print(f"ERROR: {test_name} failed: {e}")


def main():
    """Run all tests"""
    print("GAME TRANSLATOR TEST SUITE")
    print("=" * 50)
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[0]}")

    try:
        # Run test categories
        run_basic_tests()
        run_provider_tests()
        run_validation_tests()

        print("\n" + "=" * 50)
        print("ALL TESTS COMPLETED")
        print("=" * 50)
        print("Check individual test outputs for detailed results.")
        print("Some tests may be skipped if dependencies are missing.")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()