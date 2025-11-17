@echo off
REM AGBot Quick Start - Batch Wrapper
REM Run this from anywhere to start the AGBot controller

cd /d "%~dp0"
echo 📁 Starting AGBot from: %cd%
echo.

python start_agbot.py
pause
