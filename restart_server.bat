@echo off
echo ======================================================================
echo  Moon Dev's Trading Agent - Server Restart
echo ======================================================================
echo.
echo [1/3] Killing all Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo       SUCCESS: Python processes terminated
) else (
    echo       INFO: No Python processes were running
)
echo.
echo [2/3] Waiting for cleanup...
timeout /t 2 /nobreak >nul
echo       Done
echo.
echo [3/3] Starting fresh server...
echo.
python src/web/app.py
