# Legacy Architect

Gemini 3-powered autonomous agent for safe legacy code refactoring

**Hackathon Entry: Gemini 3 Global Hackathon**

This project demonstrates an agentic workflow that:

- Scans legacy code and builds an impact map
- Generates characterization tests to lock current behavior
- Refactors code behind a feature flag (BILLING_V2=1)
- Runs tests in both modes and iterates on failures
- Produces a judge-ready evidence pack

## Quick Start

```powershell
# Install dependencies
python -m pip install -e ".[dev]"

# Set environment variables
$env:GEMINI_API_KEY = "your-api-key"
$env:GEMINI_MODEL = "gemini-3-flash-preview"

# Run the agent
python -m legacy_architect run
```

## Author

GitHub: https://github.com/konduyx18

## License

MIT
