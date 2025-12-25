"""Main orchestration loop for Legacy Architect agent."""

import os
from typing import Optional

from legacy_architect.impact import scan_for_symbol, build_impact_map
from legacy_architect.artifacts import write_json, write_text, ensure_artifacts_dir
from legacy_architect.git_tools import ensure_clean_working_tree, create_branch, get_current_branch
from legacy_architect.char_tests import generate_characterization_tests, get_test_case_count
from legacy_architect.test_runner import run_tests_default_mode, run_tests_v2_mode, run_dual_mode_tests, count_test_results
from legacy_architect.gemini_client import generate_json, generate_code, generate_text
from legacy_architect.prompts import (
    PLANNER_SYSTEM_PROMPT, PATCHER_SYSTEM_PROMPT, FIXER_SYSTEM_PROMPT,
    get_planner_prompt, get_patcher_prompt, get_fixer_prompt
)
from legacy_architect.patching import (
    read_file_content, apply_refactored_code, save_diff_artifact,
    validate_python_syntax, backup_file
)
from legacy_architect.evidence import generate_evidence_report


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
        
        test_file = generate_characterization_tests(
            target_module="app.legacy.billing",
            target_function=symbol,
            output_file="tests/test_characterization_billing.py"
        )
        test_count = get_test_case_count()
        print(f"✅ Generated {test_count} characterization tests")
        print(f"   Output: {test_file}")
        
        # ============================================================
        # STEP 5: Run tests (default mode)
        # ============================================================
        print_step(5, total_steps, "Running tests (default mode)...")
        
        default_success, default_log = run_tests_default_mode()
        counts = count_test_results(default_log)
        
        if default_success:
            print(f"✅ All tests passed: {counts['passed']} passed, {counts['failed']} failed")
        else:
            print(f"❌ Tests failed: {counts['passed']} passed, {counts['failed']} failed")
            print("   Check artifacts/test_default.log for details")
            return False
        
        # ============================================================
        # STEP 6: Generate refactoring plan with Gemini
        # ============================================================
        print_step(6, total_steps, "Generating refactoring plan with Gemini...")
        
        # Read the original code
        original_code = read_file_content(target_file)
        
        # Get call sites for context
        call_sites = [site["file"] for site in impact_map.get("call_sites", [])]
        call_sites += [site["file"] for site in impact_map.get("other_files", []) if "app/" in site["file"]]
        
        # Generate the plan
        planner_prompt = get_planner_prompt(original_code, symbol, call_sites)
        
        try:
            plan = generate_json(
                prompt=planner_prompt,
                system_instruction=PLANNER_SYSTEM_PROMPT,
                temperature=0.3
            )
            write_json("plan.json", plan)
            print(f"✅ Refactoring plan generated")
            print(f"   Summary: {plan.get('summary', 'N/A')[:80]}...")
            print(f"   Issues found: {len(plan.get('issues', []))}")
            print(f"   Improvements planned: {len(plan.get('improvements', []))}")
        except Exception as e:
            print(f"❌ Failed to generate plan: {e}")
            return False
        
        # ============================================================
        # STEP 7: Apply refactored code
        # ============================================================
        print_step(7, total_steps, "Generating and applying refactored code...")
        
        # Create backup
        backup_path = backup_file(target_file)
        
        # Generate refactored code
        patcher_prompt = get_patcher_prompt(original_code, symbol, plan)
        
        try:
            refactored_code = generate_code(
                prompt=patcher_prompt,
                system_instruction=PATCHER_SYSTEM_PROMPT,
                temperature=0.2
            )
            
            # Validate syntax
            is_valid, error = validate_python_syntax(refactored_code)
            if not is_valid:
                print(f"⚠️  Generated code has syntax error: {error}")
                print("   Requesting fix from Gemini...")
                # Try to fix syntax
                fix_prompt = f"Fix this Python syntax error: {error}\n\nCode:\n```python\n{refactored_code}\n```"
                refactored_code = generate_code(prompt=fix_prompt, temperature=0.1)
                is_valid, error = validate_python_syntax(refactored_code)
                if not is_valid:
                    print(f"❌ Could not fix syntax error: {error}")
                    return False
            
            # Save diff
            save_diff_artifact(original_code, refactored_code, target_file)
            
            # Apply the code
            success, message = apply_refactored_code(target_file, refactored_code)
            if success:
                print(f"✅ Refactored code applied to {target_file}")
            else:
                print(f"❌ Failed to apply code: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to generate refactored code: {e}")
            return False
        
        # ============================================================
        # STEP 8: Run tests (both modes) with fix loop
        # ============================================================
        print_step(8, total_steps, "Running tests in both modes...")
        
        iteration = 0
        max_fix_iterations = max_iterations
        
        while iteration < max_fix_iterations:
            iteration += 1
            print(f"\n   --- Iteration {iteration}/{max_fix_iterations} ---")
            
            # Run tests in default mode
            print("   Running DEFAULT mode tests...")
            default_success, default_log = run_tests_default_mode()
            default_counts = count_test_results(default_log)
            
            # Run tests in V2 mode
            print("   Running BILLING_V2 mode tests...")
            v2_success, v2_log = run_tests_v2_mode()
            v2_counts = count_test_results(v2_log)
            
            print(f"   DEFAULT: {default_counts['passed']} passed, {default_counts['failed']} failed")
            print(f"   V2:      {v2_counts['passed']} passed, {v2_counts['failed']} failed")
            
            # Check if both pass
            if default_success and v2_success:
                print(f"\n✅ All tests pass in both modes!")
                break
            
            # If we have more iterations, try to fix
            if iteration < max_fix_iterations:
                print(f"\n⚠️  Tests failed, attempting fix (iteration {iteration + 1})...")
                
                # Get the current code
                current_code = read_file_content(target_file)
                
                # Get failure details
                test_output = default_log if not default_success else v2_log
                
                # Generate fix
                fixer_prompt = get_fixer_prompt(current_code, symbol, test_output, iteration)
                
                try:
                    fixed_code = generate_code(
                        prompt=fixer_prompt,
                        system_instruction=FIXER_SYSTEM_PROMPT,
                        temperature=0.2
                    )
                    
                    # Validate and apply fix
                    is_valid, error = validate_python_syntax(fixed_code)
                    if is_valid:
                        apply_refactored_code(target_file, fixed_code, create_backup=False)
                        save_diff_artifact(original_code, fixed_code, target_file)
                        refactored_code = fixed_code
                        print("   Fix applied, re-running tests...")
                    else:
                        print(f"   Fix has syntax error: {error}")
                except Exception as e:
                    print(f"   Fix generation failed: {e}")
            else:
                print(f"\n❌ Tests still failing after {max_fix_iterations} iterations")
                # Don't return False - still generate evidence
        
        # ============================================================
        # STEP 9: Generate evidence pack
        # ============================================================
        print_step(9, total_steps, "Generating evidence pack...")
        
        # Prepare test results
        test_results = {
            "default_passed": default_success,
            "v2_passed": v2_success,
            "total_tests": default_counts.get("passed", 0) + default_counts.get("failed", 0),
            "default_count": default_counts,
            "v2_count": v2_counts,
        }
        
        # Generate the evidence report
        evidence_path = generate_evidence_report(
            target_file=target_file,
            symbol=symbol,
            original_code=original_code,
            refactored_code=refactored_code,
            plan=plan,
            test_results=test_results,
            iterations=iteration
        )
        
        print(f"✅ Evidence report generated: {evidence_path}")
        
        # List all artifacts
        from legacy_architect.artifacts import list_artifacts
        artifacts = list_artifacts()
        print(f"\n📁 Artifacts generated ({len(artifacts)} files):")
        for artifact in sorted(artifacts):
            print(f"   - {artifact}")
        
        # ============================================================
        # DONE
        # ============================================================
        print("\n" + "=" * 60)
        if default_success and v2_success:
            print("🎉 REFACTORING SUCCESSFUL!")
            print("=" * 60)
            print(f"\n✅ All {test_results['total_tests']} tests pass in both modes")
            print(f"✅ Evidence report: artifacts/EVIDENCE.md")
            print(f"✅ Code diff: artifacts/diff.patch")
        else:
            print("⚠️  REFACTORING COMPLETED WITH ISSUES")
            print("=" * 60)
            print(f"\nSome tests failed. Review artifacts/EVIDENCE.md for details.")
        
        return default_success and v2_success
        
    except Exception as e:
        print(f"\n❌ Agent failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
