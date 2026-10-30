@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==============================================
echo GARAKHANSANG Hub v2 - LOCAL DEMO
 echo http://localhost:8769/hub.html
 echo IMPORTANT: Copy LOCAL ADMIN TOKEN from below
 echo ==============================================
where python >nul 2>&1
if errorlevel 1 (echo Python 3.10+ installation required. & pause & exit /b 1)
python server.py
pause
