@echo off
echo ============================================
echo  HYDRO RAIN GUARD - Backend Setup & Launch
echo ============================================
echo.

REM Check for Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version

echo.
echo Installing Python packages...
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Package installation failed. Try running as Administrator.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Starting HYDRO RAIN GUARD Backend API...
echo ============================================
echo.
echo API will be available at: http://localhost:8000
echo Swagger UI (API docs):   http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.
python -m uvicorn main:app --reload --port 8000
pause
