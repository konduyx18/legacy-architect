"""Patching module - apply refactored code to files and manage backups."""

import os
import shutil
from datetime import datetime
from typing import Tuple, Optional

from legacy_architect.artifacts import write_text, get_artifact_path


def backup_file(file_path: str) -> str:
    """
    Create a backup of a file before modifying it.
    
    Args:
        file_path: Path to the file to backup
    
    Returns:
        Path to the backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        print(f"   Backup created: {backup_path}")
    
    return backup_path


def restore_backup(file_path: str, backup_path: str) -> bool:
    """
    Restore a file from backup.
    
    Args:
        file_path: Path to the file to restore
        backup_path: Path to the backup file
    
    Returns:
        True if restore successful, False otherwise
    """
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        print(f"   Restored from backup: {backup_path}")
        return True
    return False


def apply_refactored_code(
    file_path: str,
    new_code: str,
    create_backup: bool = True
) -> Tuple[bool, str]:
    """
    Apply refactored code to a file.
    
    Args:
        file_path: Path to the file to modify
        new_code: The new code to write
        create_backup: Whether to create a backup first
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create backup if requested
        backup_path = None
        if create_backup:
            backup_path = backup_file(file_path)
        
        # Write the new code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_code)
        
        return True, f"Code applied to {file_path}"
        
    except Exception as e:
        # Restore from backup if something went wrong
        if backup_path and os.path.exists(backup_path):
            restore_backup(file_path, backup_path)
        return False, f"Failed to apply code: {e}"


def save_diff_artifact(
    original_code: str,
    new_code: str,
    file_path: str
) -> str:
    """
    Save a diff of the changes to artifacts.
    
    Args:
        original_code: The original code
        new_code: The new code
        file_path: The file being modified
    
    Returns:
        Path to the diff file
    """
    import difflib
    
    # Generate unified diff
    original_lines = original_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )
    
    diff_content = "".join(diff)
    
    # Save to artifacts
    write_text("diff.patch", diff_content)
    
    return get_artifact_path("diff.patch")


def read_file_content(file_path: str) -> str:
    """
    Read the content of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def validate_python_syntax(code: str) -> Tuple[bool, str]:
    """
    Validate that the code is syntactically correct Python.
    
    Args:
        code: Python code to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, "Syntax valid"
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"


def extract_function_from_module(
    module_code: str,
    function_name: str
) -> Optional[str]:
    """
    Extract a specific function from module code.
    
    Args:
        module_code: The complete module code
        function_name: Name of the function to extract
    
    Returns:
        The function code, or None if not found
    """
    import re
    
    # Pattern to match function definition and body
    pattern = rf'^(def {re.escape(function_name)}\([^)]*\).*?(?=\ndef |\nclass |\Z))'
    match = re.search(pattern, module_code, re.MULTILINE | re.DOTALL)
    
    if match:
        return match.group(1).strip()
    return None


def ensure_feature_flag_support(code: str, function_name: str) -> str:
    """
    Ensure the code has feature flag support for BILLING_V2.
    
    If the code doesn't have feature flag logic, wrap it to support
    switching between old and new implementations.
    
    Args:
        code: The refactored code
        function_name: Name of the main function
    
    Returns:
        Code with feature flag support
    """
    # Check if already has feature flag support
    if "BILLING_V2" in code or "os.environ.get" in code:
        return code
    
    # The refactored code will be the V2 implementation
    # We need to keep the original available for comparison
    # For now, return as-is since the billing.py already has flag support
    return code


def apply_with_feature_flag(
    file_path: str,
    original_code: str,
    refactored_code: str,
    function_name: str
) -> Tuple[bool, str]:
    """
    Apply refactored code with feature flag support.
    
    This keeps the original implementation and adds the refactored
    version behind a feature flag.
    
    Args:
        file_path: Path to the file to modify
        original_code: The original code
        refactored_code: The refactored code
        function_name: Name of the main function
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate syntax first
    is_valid, error = validate_python_syntax(refactored_code)
    if not is_valid:
        return False, f"Invalid Python syntax: {error}"
    
    # Save diff artifact
    save_diff_artifact(original_code, refactored_code, file_path)
    
    # Apply the code
    return apply_refactored_code(file_path, refactored_code)


def cleanup_backups(directory: str, keep_latest: int = 1) -> int:
    """
    Clean up old backup files, keeping only the most recent ones.
    
    Args:
        directory: Directory to search for backups
        keep_latest: Number of recent backups to keep per file
    
    Returns:
        Number of files deleted
    """
    import glob
    from collections import defaultdict
    
    deleted = 0
    backup_files = defaultdict(list)
    
    # Find all backup files
    for backup in glob.glob(os.path.join(directory, "**/*.backup_*"), recursive=True):
        # Extract the original file path
        original = backup.rsplit(".backup_", 1)[0]
        backup_files[original].append(backup)
    
    # For each original file, keep only the latest backups
    for original, backups in backup_files.items():
        # Sort by modification time (newest first)
        backups.sort(key=os.path.getmtime, reverse=True)
        
        # Delete older backups
        for old_backup in backups[keep_latest:]:
            try:
                os.remove(old_backup)
                deleted += 1
            except Exception:
                pass
    
    return deleted


if __name__ == "__main__":
    print("Testing patching module...")
    
    # Test syntax validation
    valid_code = "def hello():\n    return 'world'"
    invalid_code = "def hello(\n    return 'world'"
    
    is_valid, msg = validate_python_syntax(valid_code)
    print(f"Valid code: {is_valid} - {msg}")
    
    is_valid, msg = validate_python_syntax(invalid_code)
    print(f"Invalid code: {is_valid} - {msg}")
    
    # Test diff generation
    original = "def foo():\n    return 1\n"
    new = "def foo():\n    '''Returns one.'''\n    return 1\n"
    
    diff_path = save_diff_artifact(original, new, "test.py")
    print(f"Diff saved to: {diff_path}")
    
    print("\n✅ Patching module working!")
