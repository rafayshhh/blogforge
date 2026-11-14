@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo BlogForge - Setup & Environment Initializer
echo ==============================================================================
echo.

echo [1/5] Checking Python installation...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH.
    echo BlogForge requires Python 3.11 or newer.
    echo Please install Python from https://www.python.org/
    echo Ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo.
    echo [ERROR] Unsupported Python version detected.
    echo BlogForge requires Python 3.11 or newer.
    echo.
    pause
    exit /b 1
)

echo [2/5] Creating Python virtual environment (.venv)...
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Created virtual environment in .venv.
) else (
    echo Virtual environment (.venv) already exists.
)

echo [3/5] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies from requirements.txt.
    pause
    exit /b 1
)

echo [4/5] Initializing application data directories...
if not exist data\projects mkdir data\projects
if not exist data\articles mkdir data\articles
if not exist data\generation mkdir data\generation
if not exist data\research mkdir data\research
if not exist logs mkdir logs

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo Created .env file from .env.example.
    ) else (
        echo GEMINI_API_KEY= > .env
        echo Created default .env file.
    )
)

echo.
echo [5/5] Setup completed successfully!
echo ==============================================================================
echo You can now configure your GEMINI_API_KEY in .env, or inside Settings in the app.
echo Launch the application anytime by executing:
echo   run.bat
echo ==============================================================================
pause
