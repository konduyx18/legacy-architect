"""Main orchestration loop for Legacy Architect agent."""

import os
from typing import Optional

from legacy_architect.impact import scan_for_symbol, build_impact_map
from legacy_architect.artifacts import write_json, write_text, ensure_artifacts_dir
from legacy_architect.git_tools import ensure_clean_working_tree, create_branch, get_current_branch


# Agent workflow steps
STEPS = [
    "Check prerequisites",
    "Scan for symbol usage",
    "Build impact map",
    "Generate characterization tests",
    "Run tests (default mode)",
    "Generate refactoring plan",
    "Apply refactored code",
    "Run tests (both modes)",
    "Generate evidence pack",
]


def print_step(step_num: int, total: int, message: str):
    """Print a formatted step indicator."""
    print(f"\n[{step_num}/{total}] {message}")
    print("-" * 50)


def run_agent(
    target_file: str,
    symbol: str,
    max_iterations: int = 5,
    dry_run: bool = False
) -> bool:
    """
    Run the refactoring agent.
    
    Args:
        target_file: Path to the file containing the symbol to refactor
        symbol: Name of the function/class to refactor
        max_iterations: Maximum number of fix iterations
        dry_run: If True, show what would be done without making changes
    
    Returns:
        True if refactoring was successful, False otherwise
    """
    total_steps = len(STEPS)
    
    try:
        # ============================================================
        # STEP 1: Check prerequisites
        # ============================================================
        print_step(1, total_steps, "Checking prerequisites...")
        
        # Check target file exists
        if not os.path.exists(target_file):
            print(f"❌ Target file not found: {target_file}")
            return False
        print(f"✅ Target file exists: {target_file}")
        
        # Check for API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY environment variable not set")
            return False
        print("✅ GEMINI_API_KEY is set")
        
        # Check model
        model = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
        print(f"✅ Using model: {model}")
        
        # Check git working tree
        if not dry_run:
            is_clean, message = ensure_clean_working_tree()
            if not is_clean:
                print(f"⚠️  Git working tree: {message}")
                print("   (Continuing anyway for demo purposes)")
            else:
                print("✅ Git working tree is clean")
        
        # Ensure artifacts directory exists
        ensure_artifacts_dir()
        print("✅ Artifacts directory ready")
        
        # ============================================================
        # STEP 2: Scan for symbol usage
        # ============================================================
        print_step(2, total_steps, f"Scanning for '{symbol}' usage...")
        
        usage_map = scan_for_symbol(symbol)
        
        if not usage_map:
            print(f"⚠️  No usage of '{symbol}' found outside target file")
        else:
            print(f"✅ Found {len(usage_map)} file(s) using '{symbol}':")
            for file, lines in usage_map.items():
                print(f"   - {file}: lines {lines}")
        
        # ============================================================
        # STEP 3: Build impact map
        # ============================================================
        print_step(3, total_steps, "Building impact map...")
        
        impact_map = build_impact_map(target_file, symbol, usage_map)
        write_json("impact.json", impact_map)
        print(f"✅ Impact map saved to artifacts/impact.json")
        
        if dry_run:
            print("\n🔍 DRY RUN MODE - Stopping here")
            print("   Would continue with:")
            print("   - Generate characterization tests")
            print("   - Run tests in default mode")
            print("   - Generate refactoring plan with Gemini")
            print("   - Apply refactored code")
            print("   - Run tests in both modes")
            print("   - Generate evidence pack")
            return True
        
        # ============================================================
        # STEP 4: Generate characterization tests
        # ============================================================
        print_step(4, total_steps, "Generating characterization tests...")
        
        # Placeholder - will be implemented in Phase 3
        print("📝 TODO: Implement characterization test generation")
        print("   (Will be added in Phase 3)")
        
        # ============================================================
        # STEP 5: Run tests (default mode)
        # ============================================================
        print_step(5, total_steps, "Running tests (default mode)...")
        
        # Placeholder - will be implemented in Phase 3
        print("📝 TODO: Implement test runner")
        print("   (Will be added in Phase 3)")
        
        # ============================================================
        # STEP 6: Generate refactoring plan
        # ============================================================
        print_step(6, total_steps, "Generating refactoring plan...")
        
        # Placeholder - will be implemented in Phase 4
        print("📝 TODO: Implement Gemini integration for planning")
        print("   (Will be added in Phase 4)")
        
        # ============================================================
        # STEP 7: Apply refactored code
        # ============================================================
        print_step(7, total_steps, "Applying refactored code...")
        
        # Placeholder - will be implemented in Phase 4
        print("📝 TODO: Implement code patching")
        print("   (Will be added in Phase 4)")
        
        # ============================================================
        # STEP 8: Run tests (both modes)
        # ============================================================
        print_step(8, total_steps, "Running tests (both modes)...")
        
        # Placeholder - will be implemented in Phase 4
        print("📝 TODO: Implement dual-mode testing")
        print("   (Will be added in Phase 4)")
        
        # ============================================================
        # STEP 9: Generate evidence pack
        # ============================================================
        print_step(9, total_steps, "Generating evidence pack...")
        
        # Placeholder - will be implemented in Phase 4
        print("📝 TODO: Implement evidence generation")
        print("   (Will be added in Phase 4)")
        
        # ============================================================
        # DONE
        # ============================================================
        print("\n" + "=" * 60)
        print("🎉 Agent run complete!")
        print("=" * 60)
        print("\nNote: Steps 4-9 are placeholders.")
        print("They will be implemented in Phase 3 and Phase 4.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Agent failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
