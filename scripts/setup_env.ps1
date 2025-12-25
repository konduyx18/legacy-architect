# Setup script for Legacy Architect
# Run this at the start of each session: .\scripts\setup_env.ps1

$env:GEMINI_API_KEY = "YOUR_KEY_HERE"
$env:GEMINI_MODEL = "gemini-3-flash-preview"

Write-Host "Environment variables set!" -ForegroundColor Green
Write-Host "Model: $env:GEMINI_MODEL"
