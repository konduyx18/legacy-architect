"""Git tools - branch creation, status checks, and git operations."""

import subprocess
import os
from typing import Tuple, Optional


def run_git_command(args: list, capture_output: bool = True) -> Tuple[bool, str]:
    """
    Run a git command and return the result.
    
    Args:
        args: List of git command arguments (without 'git' prefix)
        capture_output: Whether to capture and return output
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=capture_output,
            text=True,
            cwd=os.getcwd()
        )
        
        output = result.stdout.strip() if result.stdout else ""
        if result.returncode != 0:
            error = result.stderr.strip() if result.stderr else "Unknown error"
            return False, error
        
        return True, output
        
    except FileNotFoundError:
        return False, "Git is not installed or not in PATH"
    except Exception as e:
        return False, str(e)


def ensure_clean_working_tree() -> Tuple[bool, str]:
    """
    Check if the git working tree is clean (no uncommitted changes).
    
    Returns:
        Tuple of (is_clean: bool, message: str)
    """
    # Check if we're in a git repository
    success, output = run_git_command(["rev-parse", "--git-dir"])
    if not success:
        return False, "Not a git repository"
    
    # Check for uncommitted changes
    success, output = run_git_command(["status", "--porcelain"])
    if not success:
        return False, f"Failed to check git status: {output}"
    
    if output:
        # There are uncommitted changes
        changed_files = output.split("\n")
        return False, f"Uncommitted changes in {len(changed_files)} file(s)"
    
    return True, "Working tree is clean"


def get_current_branch() -> Optional[str]:
    """
    Get the name of the current git branch.
    
    Returns:
        Branch name, or None if not in a git repository
    """
    success, output = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if success:
        return output
    return None


def create_branch(branch_name: str, checkout: bool = True) -> Tuple[bool, str]:
    """
    Create a new git branch.
    
    Args:
        branch_name: Name of the branch to create
        checkout: Whether to checkout the new branch (default: True)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Check if branch already exists
    success, output = run_git_command(["branch", "--list", branch_name])
    if success and output:
        return False, f"Branch '{branch_name}' already exists"
    
    if checkout:
        # Create and checkout in one command
        success, output = run_git_command(["checkout", "-b", branch_name])
        if success:
            return True, f"Created and checked out branch '{branch_name}'"
        return False, f"Failed to create branch: {output}"
    else:
        # Just create the branch
        success, output = run_git_command(["branch", branch_name])
        if success:
            return True, f"Created branch '{branch_name}'"
        return False, f"Failed to create branch: {output}"


def checkout_branch(branch_name: str) -> Tuple[bool, str]:
    """
    Checkout an existing git branch.
    
    Args:
        branch_name: Name of the branch to checkout
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    success, output = run_git_command(["checkout", branch_name])
    if success:
        return True, f"Checked out branch '{branch_name}'"
    return False, f"Failed to checkout branch: {output}"


def commit_changes(message: str, add_all: bool = True) -> Tuple[bool, str]:
    """
    Commit changes to the current branch.
    
    Args:
        message: Commit message
        add_all: Whether to add all changes before committing (default: True)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if add_all:
        success, output = run_git_command(["add", "-A"])
        if not success:
            return False, f"Failed to stage changes: {output}"
    
    success, output = run_git_command(["commit", "-m", message])
    if success:
        return True, f"Committed: {message}"
    
    # Check if there's nothing to commit
    if "nothing to commit" in output.lower():
        return True, "Nothing to commit (working tree clean)"
    
    return False, f"Failed to commit: {output}"


def get_diff(staged: bool = False) -> str:
    """
    Get the current git diff.
    
    Args:
        staged: If True, show staged changes. If False, show unstaged changes.
    
    Returns:
        Diff output as string
    """
    args = ["diff"]
    if staged:
        args.append("--staged")
    
    success, output = run_git_command(args)
    return output if success else ""


def get_file_diff(file_path: str) -> str:
    """
    Get the git diff for a specific file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Diff output as string
    """
    success, output = run_git_command(["diff", file_path])
    return output if success else ""


def stash_changes() -> Tuple[bool, str]:
    """
    Stash current changes.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    success, output = run_git_command(["stash", "push", "-m", "legacy-architect-backup"])
    if success:
        return True, "Changes stashed"
    return False, f"Failed to stash: {output}"


def pop_stash() -> Tuple[bool, str]:
    """
    Pop the most recent stash.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    success, output = run_git_command(["stash", "pop"])
    if success:
        return True, "Stash popped"
    return False, f"Failed to pop stash: {output}"


if __name__ == "__main__":
    # Test the git tools
    print("Testing git tools...")
    
    # Test current branch
    branch = get_current_branch()
    print(f"✅ Current branch: {branch}")
    
    # Test working tree status
    is_clean, message = ensure_clean_working_tree()
    status = "✅" if is_clean else "⚠️"
    print(f"{status} Working tree: {message}")
    
    # Test diff
    diff = get_diff()
    if diff:
        print(f"📝 Unstaged changes:\n{diff[:200]}...")
    else:
        print("📝 No unstaged changes")
    
    print("\nGit tools test complete!")
