@echo off
REM Playwright Test Setup Script for NEWSEAMS Project
REM This script checks prerequisites and helps set up the test environment

echo ========================================
echo NEWSEAMS Playwright Test Setup
echo ========================================
echo.

REM Check if Node.js is installed
echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js is installed
node --version
echo.

REM Check if npm is installed
echo Checking npm installation...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not installed
    pause
    exit /b 1
)
echo [OK] npm is installed
npm --version
echo.

REM Check if Playwright is installed
echo Checking Playwright installation...
if not exist "node_modules\playwright" (
    echo [INFO] Playwright not found in node_modules
    echo Installing Playwright...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Playwright is installed
echo.

REM Check if Playwright browsers are installed
echo Checking Playwright browsers...
npx playwright --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Playwright CLI not working
    pause
    exit /b 1
)
npx playwright --version
echo.

REM Create necessary directories
echo Creating test directories...
if not exist "test-screenshots" mkdir "test-screenshots"
if not exist "test-responses" mkdir "test-responses"
echo [OK] Test directories created
echo.

REM Check if services are running
echo Checking if frontend service is running...
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Frontend service (http://localhost:5173) is not responding
    echo Please start the frontend service: cd frontend ^&^& npm run dev
) else (
    echo [OK] Frontend service is running
)
echo.

echo Checking if backend API service is running...
curl -s http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend API service (http://localhost:8000) is not responding
    echo Please start the backend service: cd backend ^&^& python manage.py runserver
) else (
    echo [OK] Backend API service is running
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the comprehensive test:
echo   npx playwright test test_all_objects.spec.ts
echo.
echo To run tests with UI:
echo   npx playwright test test_all_objects.spec.ts --ui
echo.
echo To run tests in headed mode:
echo   npx playwright test test_all_objects.spec.ts --headed
echo.
echo To run specific test:
echo   npx playwright test test_all_objects.spec.ts -g "should login successfully"
echo.
pause
