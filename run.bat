@echo off
setlocal

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python -m app.main %*

if errorlevel 1 (
    echo.
    echo BlogForge encountered an error during startup.
    echo Review the error above or check logs/blogforge.log for details.
    pause
)
