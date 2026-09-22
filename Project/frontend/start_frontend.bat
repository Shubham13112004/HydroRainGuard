@echo off
echo ============================================
echo  HYDRO RAIN GUARD - Frontend Setup & Launch
echo ============================================
echo.

REM Check for Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js not found!
    echo.
    echo Please install Node.js 18+ LTS from:
    echo   https://nodejs.org/en/download/
    echo.
    echo Choose the "Windows Installer (.msi)" option.
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js found:
node --version
echo [OK] npm version:
npm --version

echo.
echo Installing Node.js packages (this may take 1-2 minutes)...
npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Starting HYDRO RAIN GUARD Frontend...
echo ============================================
echo.
echo App will be available at: http://localhost:3000
echo.
echo Make sure the backend is running at http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.
npm run dev
pause
