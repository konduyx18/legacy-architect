"""Prompts for Gemini-powered refactoring agent."""

# System prompt for the refactoring planner
PLANNER_SYSTEM_PROMPT = """You are an expert software engineer specializing in legacy code refactoring.

Your task is to analyze legacy Python code and create a detailed refactoring plan that:
- Improves code readability and maintainability
- Follows Python best practices and PEP 8 style
- Preserves ALL existing behavior exactly
- Uses small, focused helper functions
- Adds clear docstrings and type hints

CRITICAL: The refactored code MUST produce IDENTICAL outputs for all inputs.
This is a behavior-preserving refactor, not a feature change.

When analyzing code, identify:
- Magic numbers that should be constants
- Repeated logic that should be extracted
- Complex conditionals that should be simplified
- Missing type hints and docstrings
- Poor variable names"""


# System prompt for the code patcher
PATCHER_SYSTEM_PROMPT = """You are an expert Python developer who writes clean, refactored code.

Your task is to implement a refactoring plan for a SPECIFIC function while preserving the file structure.

CRITICAL RULES - READ CAREFULLY:
1. The file has THREE functions:
   - _compute_invoice_total_legacy() - DO NOT MODIFY THIS
   - _compute_invoice_total_v2() - REFACTOR THIS ONE ONLY
   - compute_invoice_total() - DO NOT MODIFY THIS (it's a router)

2. You MUST preserve this exact structure:
   - Imports at the top
   - Constants after imports (you can add new ones)
   - Helper functions after constants (you can add new ones)
   - _compute_invoice_total_legacy() - KEEP EXACTLY AS IS
   - _compute_invoice_total_v2() - REPLACE WITH YOUR REFACTORED VERSION
   - compute_invoice_total() - KEEP EXACTLY AS IS
   - __all__ at the end - KEEP AS IS

3. Your refactored _compute_invoice_total_v2 MUST:
   - Use the new constants and helpers you define
   - Produce IDENTICAL outputs to _compute_invoice_total_legacy
   - Have the same function signature: def _compute_invoice_total_v2(order: dict) -> dict

OUTPUT: Return the COMPLETE Python file with all functions. No markdown, no explanations."""


# System prompt for the fix iteration
FIXER_SYSTEM_PROMPT = """You are an expert Python debugger fixing test failures.

A refactored function is failing tests. Your task is to fix the code so tests pass.

RULES:
- Analyze the test failure carefully
- Identify what behavior changed
- Fix the code to match the original behavior
- Output ONLY the complete fixed Python code - no explanations
- Do NOT change the test - fix the implementation

Remember: This is a behavior-preserving refactor. The original code's behavior
is correct by definition."""


def get_planner_prompt(
    legacy_code: str,
    function_name: str,
    call_sites: list = None
) -> str:
    """
    Generate the user prompt for the refactoring planner.
    
    Args:
        legacy_code: The legacy code to refactor
        function_name: Name of the function to refactor
        call_sites: List of files that call this function
    
    Returns:
        Formatted user prompt
    """
    call_sites_text = ""
    if call_sites:
        call_sites_text = f"""

## Call Sites

This function is called from the following locations:
{chr(10).join(f'- {site}' for site in call_sites)}

Ensure the refactored code maintains compatibility with all call sites."""
    
    return f"""# Refactoring Task

## Target Function
`{function_name}`

## Current Implementation

```python
{legacy_code}
```
{call_sites_text}

## Your Task

Create a detailed refactoring plan in JSON format with:
- `summary`: Brief description of the refactoring approach
- `issues`: List of code quality issues found
- `improvements`: List of specific improvements to make
- `constants`: Any magic numbers to extract as named constants
- `helper_functions`: Any helper functions to create
- `risks`: Potential risks or edge cases to watch for

Respond with ONLY valid JSON."""


def get_patcher_prompt(
    legacy_code: str,
    function_name: str,
    plan: dict
) -> str:
    """
    Generate the user prompt for the code patcher.
    
    Args:
        legacy_code: The original legacy code
        function_name: Name of the function to refactor
        plan: The refactoring plan from the planner
    
    Returns:
        Formatted user prompt
    """
    import json
    plan_text = json.dumps(plan, indent=2)
    
    return f"""# Code Refactoring Task

## Original Code

```python
{legacy_code}
```

## Refactoring Plan

```json
{plan_text}
```

## Your Task

Implement the refactoring plan by producing the complete refactored Python module.

CRITICAL FILE STRUCTURE:
The file contains a feature flag router. You must preserve this structure:
1. Keep _compute_invoice_total_legacy() EXACTLY as written (do not modify)
2. Keep compute_invoice_total() router EXACTLY as written (do not modify)
3. Keep __all__ = ["compute_invoice_total"] at the end
4. Add your constants at the top (after imports)
5. Add your helper functions after constants
6. ONLY replace the body of _compute_invoice_total_v2() with your refactored code
7. Your _compute_invoice_total_v2 must call your new helper functions and use your constants

REQUIREMENTS:
- Include ALL imports at the top
- Define constants at module level
- Include helper functions before the main function
- Add docstrings to all functions
- Add type hints to function signatures
- The main function `{function_name}` must have the EXACT same signature
- The function must return the EXACT same output for any input

Output ONLY the complete Python code. No markdown, no explanations."""


def get_fixer_prompt(
    current_code: str,
    function_name: str,
    test_output: str,
    attempt: int
) -> str:
    """
    Generate the user prompt for fixing failed tests.
    
    Args:
        current_code: The current (failing) code
        function_name: Name of the function being fixed
        test_output: The test failure output
        attempt: Which fix attempt this is (1, 2, 3...)
    
    Returns:
        Formatted user prompt
    """
    return f"""# Fix Test Failures - Attempt {attempt}

## Current Code (FAILING TESTS)

```python
{current_code}
```

## Test Failure Output

```
{test_output}
```

## Your Task

Fix the code so all tests pass. The tests verify that the refactored code
produces IDENTICAL output to the original implementation.

Common issues to check:
- Floating point precision (use round() appropriately)
- Order of operations in calculations
- Edge cases (empty lists, zero values, missing keys)
- Type mismatches (int vs float)

Output ONLY the complete fixed Python code. No markdown, no explanations."""


def get_evidence_prompt(
    original_code: str,
    refactored_code: str,
    plan: dict,
    test_results: dict
) -> str:
    """
    Generate prompt for creating evidence documentation.
    
    Args:
        original_code: The original legacy code
        refactored_code: The refactored code
        plan: The refactoring plan
        test_results: Test results from both modes
    
    Returns:
        Formatted user prompt
    """
    import json
    
    return f"""# Generate Refactoring Evidence Report

## Original Code

```python
{original_code}
```

## Refactored Code

```python
{refactored_code}
```

## Refactoring Plan

```json
{json.dumps(plan, indent=2)}
```

## Test Results

- **Default Mode**: {"PASSED" if test_results.get("default_passed") else "FAILED"}
- **BILLING_V2 Mode**: {"PASSED" if test_results.get("v2_passed") else "FAILED"}
- **Total Tests**: {test_results.get("total_tests", "N/A")}

## Your Task

Create a detailed evidence report in Markdown format that includes:
1. Executive summary of the refactoring
2. List of improvements made
3. Before/after code comparison highlights
4. Test verification results
5. Risk assessment

This report will be reviewed by senior engineers to approve the refactoring."""


if __name__ == "__main__":
    # Test the prompts
    print("Testing prompts module...")
    
    sample_code = '''def compute_total(items):
    total = 0
    for item in items:
        total += item["price"] * item["qty"]
    return total'''
    
    print("\n=== Planner Prompt ===")
    prompt = get_planner_prompt(sample_code, "compute_total", ["app/api.py"])
    print(prompt[:500] + "...")
    
    print("\n=== Patcher Prompt ===")
    plan = {"summary": "Extract constants", "improvements": ["Add types"]}
    prompt = get_patcher_prompt(sample_code, "compute_total", plan)
    print(prompt[:500] + "...")
    
    print("\n✅ Prompts module working!")
