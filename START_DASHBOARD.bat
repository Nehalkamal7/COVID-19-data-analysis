@echo off
title COVID-19 Dashboard
color 0A

echo.
echo  ==========================================
echo    COVID-19 Analytics Dashboard
echo  ==========================================
echo.

:: Try to find python
where python >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON=python
) else (
    where py >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON=py
    ) else (
        echo  ERROR: Python not found!
        echo  Please install Python from https://python.org
        pause
        exit
    )
)

:: Install requirements silently
echo  Installing/checking dependencies...
%PYTHON% -m pip install -r requirements.txt --quiet

echo.
echo  Starting Flask server...
echo.

:: Start Flask server in a new window (background)
start "COVID-19 Flask Server" cmd /k "%PYTHON% app.py"

:: Wait 4 seconds for the server to fully start
echo  Waiting for server to start...
timeout /t 4 /nobreak >nul

:: Open browser automatically
echo  Opening dashboard in browser...
start "" http://127.0.0.1:5000

echo.
echo  ==========================================
echo   Dashboard is running at:
echo   http://127.0.0.1:5000
echo  ==========================================
echo.
echo  Close the "COVID-19 Flask Server" window to stop the server.
echo.
pause
