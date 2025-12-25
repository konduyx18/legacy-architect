"""Test runner - execute pytest in dual modes and capture logs."""

import os
import subprocess
import sys
from typing import Tuple, Optional
from datetime import datetime

from legacy_architect.artifacts import write_text, append_text, get_artifact_path


def run_pytest(
    test_path: str = "tests/",
    env_vars: Optional[dict] = None,
    capture_output: bool = True,
    verbose: bool = True
) -> Tuple[bool, str, str]:
    """
    Run pytest with optional environment variables.
    
    Args:
        test_path: Path to test file or directory
        env_vars: Additional environment variables to set
        capture_output: Whether to capture stdout/stderr
        verbose: Whether to run pytest in verbose mode
    
    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")
    cmd.append("--tb=short")  # Short traceback format
    
    # Set up environment
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            env=env,
            cwd=os.getcwd()
        )
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        success = result.returncode == 0
        
        return success, stdout, stderr
        
    except Exception as e:
        return False, "", str(e)


def run_tests_default_mode(
    test_path: str = "tests/test_characterization_billing.py"
) -> Tuple[bool, str]:
    """
    Run tests in DEFAULT mode (no BILLING_V2 flag).
    
    Args:
        test_path: Path to test file
    
    Returns:
        Tuple of (success: bool, log_content: str)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Ensure BILLING_V2 is NOT set
    env_vars = {}
    if "BILLING_V2" in os.environ:
        # We need to explicitly unset it in the subprocess
        pass  # subprocess will use our env without BILLING_V2
    
    # Create a clean environment without BILLING_V2
    clean_env = {k: v for k, v in os.environ.items() if k != "BILLING_V2"}
    
    # Run pytest
    cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=clean_env,
            cwd=os.getcwd()
        )
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        success = result.returncode == 0
        
        # Build log content
        log_content = f"""# Test Run: DEFAULT MODE

Timestamp: {timestamp}
Test Path: {test_path}
BILLING_V2: NOT SET (default behavior)
Exit Code: {result.returncode}
Success: {success}

{'=' * 60}
STDOUT:
{'=' * 60}

{stdout}

{'=' * 60}
STDERR:
{'=' * 60}

{stderr}
"""
        
        # Save to artifacts
        write_text("test_default.log", log_content)
        
        return success, log_content
        
    except Exception as e:
        error_log = f"""# Test Run: DEFAULT MODE

Timestamp: {timestamp}
Test Path: {test_path}
ERROR: {str(e)}
"""
        write_text("test_default.log", error_log)
        return False, error_log


def run_tests_v2_mode(
    test_path: str = "tests/test_characterization_billing.py"
) -> Tuple[bool, str]:
    """
    Run tests in BILLING_V2 mode (feature flag enabled).
    
    Args:
        test_path: Path to test file
    
    Returns:
        Tuple of (success: bool, log_content: str)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Set BILLING_V2 flag
    env = os.environ.copy()
    env["BILLING_V2"] = "1"
    
    # Run pytest
    cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=os.getcwd()
        )
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        success = result.returncode == 0
        
        # Build log content
        log_content = f"""# Test Run: BILLING_V2 MODE

Timestamp: {timestamp}
Test Path: {test_path}
BILLING_V2: SET TO "1" (refactored behavior)
Exit Code: {result.returncode}
Success: {success}

{'=' * 60}
STDOUT:
{'=' * 60}

{stdout}

{'=' * 60}
STDERR:
{'=' * 60}

{stderr}
"""
        
        # Save to artifacts
        write_text("test_flag.log", log_content)
        
        return success, log_content
        
    except Exception as e:
        error_log = f"""# Test Run: BILLING_V2 MODE

Timestamp: {timestamp}
Test Path: {test_path}
ERROR: {str(e)}
"""
        write_text("test_flag.log", error_log)
        return False, error_log


def run_dual_mode_tests(
    test_path: str = "tests/test_characterization_billing.py"
) -> Tuple[bool, bool, str]:
    """
    Run tests in BOTH modes and compare results.
    
    Args:
        test_path: Path to test file
    
    Returns:
        Tuple of (default_success: bool, v2_success: bool, summary: str)
    """
    print("\n🧪 Running tests in DEFAULT mode...")
    default_success, default_log = run_tests_default_mode(test_path)
    default_status = "✅ PASSED" if default_success else "❌ FAILED"
    print(f"   {default_status}")
    
    print("\n🧪 Running tests in BILLING_V2 mode...")
    v2_success, v2_log = run_tests_v2_mode(test_path)
    v2_status = "✅ PASSED" if v2_success else "❌ FAILED"
    print(f"   {v2_status}")
    
    # Build summary
    summary = f"""
{'=' * 60}
DUAL MODE TEST SUMMARY
{'=' * 60}

DEFAULT Mode: {default_status}
BILLING_V2 Mode: {v2_status}

Log files:
  artifacts/test_default.log
  artifacts/test_flag.log

"""
    
    if default_success and v2_success:
        summary += "🎉 BOTH MODES PASSED - Safe to deploy refactored code!\n"
    elif default_success and not v2_success:
        summary += "⚠️  BILLING_V2 mode FAILED - Refactored code has bugs!\n"
    elif not default_success and v2_success:
        summary += "⚠️  DEFAULT mode FAILED - Original code has issues!\n"
    else:
        summary += "❌ BOTH MODES FAILED - Tests or code have problems!\n"
    
    return default_success, v2_success, summary


def count_test_results(log_content: str) -> dict:
    """
    Parse pytest output to count passed/failed tests.
    
    Args:
        log_content: Pytest output log
    
    Returns:
        Dict with passed, failed, error counts
    """
    import re
    
    # Look for summary line like "24 passed in 0.21s"
    passed_match = re.search(r'(\d+) passed', log_content)
    failed_match = re.search(r'(\d+) failed', log_content)
    error_match = re.search(r'(\d+) error', log_content)
    
    return {
        "passed": int(passed_match.group(1)) if passed_match else 0,
        "failed": int(failed_match.group(1)) if failed_match else 0,
        "errors": int(error_match.group(1)) if error_match else 0,
    }


def run_smoke_tests() -> Tuple[bool, str]:
    """
    Run the basic smoke tests.
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    success, stdout, stderr = run_pytest("tests/test_smoke.py")
    return success, stdout + stderr


if __name__ == "__main__":
    print("=" * 60)
    print("Testing test_runner module")
    print("=" * 60)
    
    # Run dual mode tests
    default_ok, v2_ok, summary = run_dual_mode_tests()
    print(summary)
    
    # Show test counts
    if os.path.exists(get_artifact_path("test_default.log")):
        with open(get_artifact_path("test_default.log"), "r") as f:
            default_log = f.read()
        counts = count_test_results(default_log)
        print(f"DEFAULT mode: {counts['passed']} passed, {counts['failed']} failed")
    
    if os.path.exists(get_artifact_path("test_flag.log")):
        with open(get_artifact_path("test_flag.log"), "r") as f:
            v2_log = f.read()
        counts = count_test_results(v2_log)
        print(f"V2 mode: {counts['passed']} passed, {counts['failed']} failed")
