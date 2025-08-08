#!/usr/bin/env python3
"""
Test runner script for the diary application.
This script provides an easy way to run tests with different configurations.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(command: list[str]) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run tests for the diary application")
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "test_file",
        nargs="?",
        help="Specific test file to run"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add verbose flag if requested
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Add specific markers
    if args.integration:
        cmd.extend(["-m", "integration"])
    elif args.unit:
        cmd.extend(["-m", "unit"])
    
    # Add specific test file if provided
    if args.test_file:
        test_path = Path(args.test_file)
        if not test_path.exists():
            test_path = Path("tests") / args.test_file
        cmd.append(str(test_path))
    
    # Run the tests
    exit_code = run_command(cmd)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main()) 