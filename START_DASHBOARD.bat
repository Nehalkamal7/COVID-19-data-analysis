@echo off
title COVID-19 Dashboard
color 0A

echo.
echo  ==========================================
echo    COVID-19 Analytics Dashboard
echo  ==========================================
echo.
echo  Starting server, please wait...
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
echo  Installing dependencies...
%PYTHON% -m pip install -r requirements.txt --quiet

echo.
echo  Launching dashboard in your browser...
echo.

:: Open browser after 3 seconds
start "" timeout /t 3 >nul & start http://127.0.0.1:5000

:: Start the Flask app
%PYTHON% app.py

echo.
echo  Server stopped.
pause
