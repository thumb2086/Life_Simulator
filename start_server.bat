@echo off
cd /d "%~dp0server"
echo 啟動 Life Simulator 伺服器...
echo 伺服器將運行在 http://127.0.0.1:8000
echo 按 Ctrl+C 停止伺服器
echo.

python main.py

pause
