# AGBot Quick Start - PowerShell Wrapper
# Run this from anywhere to start the AGBot controller

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

Write-Host "📁 Starting AGBot from: $projectDir" -ForegroundColor Cyan
Write-Host ""

python start_agbot.py
