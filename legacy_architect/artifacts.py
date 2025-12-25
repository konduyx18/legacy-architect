"""Artifacts management - write JSON/text files to artifacts/ directory."""

import os
import json
from datetime import datetime
from typing import Any, Dict, Optional


# Artifacts directory path
ARTIFACTS_DIR = "artifacts"


def ensure_artifacts_dir() -> str:
    """
    Ensure the artifacts directory exists.
    
    Returns:
        Path to the artifacts directory
    """
    if not os.path.exists(ARTIFACTS_DIR):
        os.makedirs(ARTIFACTS_DIR)
    return ARTIFACTS_DIR


def get_artifact_path(filename: str) -> str:
    """
    Get full path for an artifact file.
    
    Args:
        filename: Name of the artifact file
    
    Returns:
        Full path to the artifact file
    """
    ensure_artifacts_dir()
    return os.path.join(ARTIFACTS_DIR, filename)


def write_json(filename: str, data: Dict[str, Any], indent: int = 2) -> str:
    """
    Write data to a JSON file in the artifacts directory.
    
    Args:
        filename: Name of the JSON file (e.g., "impact.json")
        data: Dictionary to serialize to JSON
        indent: JSON indentation level (default: 2)
    
    Returns:
        Path to the written file
    """
    filepath = get_artifact_path(filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    return filepath


def write_text(filename: str, content: str) -> str:
    """
    Write text content to a file in the artifacts directory.
    
    Args:
        filename: Name of the file (e.g., "test_default.log")
        content: Text content to write
    
    Returns:
        Path to the written file
    """
    filepath = get_artifact_path(filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath


def append_text(filename: str, content: str) -> str:
    """
    Append text content to a file in the artifacts directory.
    
    Args:
        filename: Name of the file
        content: Text content to append
    
    Returns:
        Path to the written file
    """
    filepath = get_artifact_path(filename)
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content)
    
    return filepath


def read_json(filename: str) -> Optional[Dict[str, Any]]:
    """
    Read JSON data from an artifact file.
    
    Args:
        filename: Name of the JSON file
    
    Returns:
        Parsed JSON data, or None if file doesn't exist
    """
    filepath = get_artifact_path(filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return None


def read_text(filename: str) -> Optional[str]:
    """
    Read text content from an artifact file.
    
    Args:
        filename: Name of the file
    
    Returns:
        File content, or None if file doesn't exist
    """
    filepath = get_artifact_path(filename)
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return None


def list_artifacts() -> list:
    """
    List all files in the artifacts directory.
    
    Returns:
        List of artifact filenames
    """
    ensure_artifacts_dir()
    return os.listdir(ARTIFACTS_DIR)


def clear_artifacts() -> int:
    """
    Clear all files in the artifacts directory (except .gitkeep).
    
    Returns:
        Number of files deleted
    """
    ensure_artifacts_dir()
    deleted = 0
    
    for filename in os.listdir(ARTIFACTS_DIR):
        if filename == ".gitkeep":
            continue
        
        filepath = os.path.join(ARTIFACTS_DIR, filename)
        try:
            os.remove(filepath)
            deleted += 1
        except Exception as e:
            print(f"Warning: Could not delete {filepath}: {e}")
    
    return deleted


def write_evidence_header() -> str:
    """
    Write the header for the EVIDENCE.md file.
    
    Returns:
        Path to the EVIDENCE.md file
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"""# Legacy Architect - Evidence Pack

Generated: {timestamp}
Agent: Legacy Architect (Gemini 3 Powered)

## Summary

This document contains evidence of the refactoring process performed by the Legacy Architect agent.

"""
    
    return write_text("EVIDENCE.md", header)


def append_evidence_section(title: str, content: str) -> str:
    """
    Append a section to the EVIDENCE.md file.
    
    Args:
        title: Section title
        content: Section content
    
    Returns:
        Path to the EVIDENCE.md file
    """
    section = f"""
## {title}

{content}

"""
    
    return append_text("EVIDENCE.md", section)


if __name__ == "__main__":
    # Test the artifacts module
    print("Testing artifacts module...")
    
    ensure_artifacts_dir()
    print(f"✅ Artifacts directory: {ARTIFACTS_DIR}")
    
    # Test JSON write/read
    test_data = {"test": "data", "number": 42}
    write_json("test.json", test_data)
    read_back = read_json("test.json")
    assert read_back == test_data, "JSON read/write failed"
    print("✅ JSON write/read works")
    
    # Test text write/read
    write_text("test.txt", "Hello, World!")
    read_back = read_text("test.txt")
    assert read_back == "Hello, World!", "Text read/write failed"
    print("✅ Text write/read works")
    
    # Clean up test files
    os.remove(get_artifact_path("test.json"))
    os.remove(get_artifact_path("test.txt"))
    print("✅ Cleanup complete")
    
    print("\nAll tests passed!")
