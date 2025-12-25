"""CLI entry point for Legacy Architect agent."""

import argparse
import sys
from legacy_architect.runner import run_agent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="legacy_architect",
        description="Gemini 3-powered autonomous agent for safe legacy code refactoring"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run the refactoring agent")
    run_parser.add_argument(
        "--target",
        type=str,
        default="app/legacy/billing.py",
        help="Target file to refactor (default: app/legacy/billing.py)"
    )
    run_parser.add_argument(
        "--symbol",
        type=str,
        default="compute_invoice_total",
        help="Function/symbol to refactor (default: compute_invoice_total)"
    )
    run_parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum fix iterations (default: 5)"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    # Scan command (for testing impact analysis)
    scan_parser = subparsers.add_parser("scan", help="Scan for symbol usage (impact analysis)")
    scan_parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Symbol to search for"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        print("=" * 60)
        print("🏗️  LEGACY ARCHITECT - Gemini 3 Refactoring Agent")
        print("=" * 60)
        print(f"Target: {args.target}")
        print(f"Symbol: {args.symbol}")
        print(f"Max iterations: {args.max_iterations}")
        print(f"Dry run: {args.dry_run}")
        print("=" * 60)
        print()
        
        success = run_agent(
            target_file=args.target,
            symbol=args.symbol,
            max_iterations=args.max_iterations,
            dry_run=args.dry_run
        )
        
        sys.exit(0 if success else 1)
    
    elif args.command == "scan":
        from legacy_architect.impact import scan_for_symbol
        print(f"Scanning for symbol: {args.symbol}")
        results = scan_for_symbol(args.symbol)
        for file, lines in results.items():
            print(f"  {file}: lines {lines}")


if __name__ == "__main__":
    main()
