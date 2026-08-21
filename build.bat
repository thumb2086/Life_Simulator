@echo off
chcp 65001 >nul
echo ============================================
echo   Life Simulator - Auto Build Script
echo ============================================
echo.

:: Step 1: Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements-desktop.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo.

:: Step 2: Clean previous build
echo [2/3] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist\新股票銀行遊戲" rmdir /s /q "dist\新股票銀行遊戲"
echo.

:: Step 3: Compile with PyInstaller
echo [3/3] Compiling exe...
pyinstaller "新股票銀行遊戲.spec" --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Compilation failed.
    pause
    exit /b 1
)
echo.

echo ============================================
echo   Build Complete!
echo   Output: dist\新股票銀行遊戲\新股票銀行遊戲.exe
echo ============================================
pause
