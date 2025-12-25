"""Impact analysis - find symbol usage across codebase."""

import os
import re
from typing import Dict, List, Set
from pathlib import Path


# Directories to skip when scanning
SKIP_DIRS = {".venv", ".git", "__pycache__", "node_modules", ".pytest_cache", "artifacts"}

# File extensions to scan
SCAN_EXTENSIONS = {".py"}


def scan_for_symbol(symbol: str, root_dir: str = ".") -> Dict[str, List[int]]:
    """
    Scan codebase for usage of a symbol.
    
    Args:
        symbol: The function/class name to search for
        root_dir: Root directory to start scanning from
    
    Returns:
        Dict mapping file paths to list of line numbers where symbol is used
    """
    usage_map: Dict[str, List[int]] = {}
    
    # Create regex pattern for the symbol
    # Matches: symbol(, symbol,, symbol), from x import symbol, etc.
    pattern = re.compile(
        rf'\b{re.escape(symbol)}\b'
    )
    
    root_path = Path(root_dir).resolve()
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        
        for filename in filenames:
            # Only scan Python files
            if not any(filename.endswith(ext) for ext in SCAN_EXTENSIONS):
                continue
            
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, root_dir)
            
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                matching_lines = []
                for line_num, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        matching_lines.append(line_num)
                
                if matching_lines:
                    usage_map[rel_path] = matching_lines
                    
            except Exception as e:
                print(f"Warning: Could not read {filepath}: {e}")
    
    return usage_map


def build_impact_map(
    target_file: str,
    symbol: str,
    usage_map: Dict[str, List[int]]
) -> Dict:
    """
    Build a comprehensive impact map for a symbol.
    
    Args:
        target_file: The file containing the symbol definition
        symbol: The symbol being refactored
        usage_map: Result from scan_for_symbol()
    
    Returns:
        Dict containing impact analysis
    """
    # Read the target file to extract context
    target_content = ""
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            target_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read target file: {e}")
    
    # Count total usages
    total_usages = sum(len(lines) for lines in usage_map.values())
    
    # Categorize files by type
    call_sites = []
    test_files = []
    other_files = []
    
    for file_path, lines in usage_map.items():
        # Skip the target file itself
        if os.path.normpath(file_path) == os.path.normpath(target_file):
            continue
        
        file_info = {
            "file": file_path,
            "lines": lines,
            "usage_count": len(lines)
        }
        
        if "test" in file_path.lower():
            test_files.append(file_info)
        elif file_path.startswith("app/"):
            call_sites.append(file_info)
        else:
            other_files.append(file_info)
    
    # Build the impact map
    impact_map = {
        "target": {
            "file": target_file,
            "symbol": symbol,
        },
        "summary": {
            "total_files": len(usage_map),
            "total_usages": total_usages,
            "call_sites": len(call_sites),
            "test_files": len(test_files),
            "other_files": len(other_files),
        },
        "call_sites": sorted(call_sites, key=lambda x: x["file"]),
        "test_files": sorted(test_files, key=lambda x: x["file"]),
        "other_files": sorted(other_files, key=lambda x: x["file"]),
        "all_usages": {k: v for k, v in sorted(usage_map.items())},
    }
    
    return impact_map


def get_file_content(file_path: str) -> str:
    """
    Read and return the content of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File content as string, or empty string on error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return ""


def extract_function_code(file_path: str, function_name: str) -> str:
    """
    Extract the code of a specific function from a file.
    
    Args:
        file_path: Path to the Python file
        function_name: Name of the function to extract
    
    Returns:
        The function code as a string, or empty string if not found
    """
    content = get_file_content(file_path)
    if not content:
        return ""
    
    # Simple extraction - find def function_name and capture until next def or end
    pattern = rf'^(def {re.escape(function_name)}\(.*?(?=\ndef |\nclass |\Z))'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    
    if match:
        return match.group(1).strip()
    
    return ""


if __name__ == "__main__":
    # Test the scanner
    print("Testing impact scanner...")
    results = scan_for_symbol("compute_invoice_total")
    print(f"\nFound {len(results)} files using 'compute_invoice_total':")
    for file, lines in results.items():
        print(f"  {file}: lines {lines}")
