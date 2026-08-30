@echo off
echo ====================================
echo   Life Simulator - Building EXE
echo ====================================
echo.
cd /d "%~dp0"
echo [1/3] Installing dependencies...
call npm install
echo.
echo [2/3] Building Electron app...
call npx electron-builder build --win
echo.
echo [3/3] Done!
echo.
echo Output: ..\dist-electron\
echo.
pause
