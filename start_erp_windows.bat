@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  GARAKLAND ERP RELEASE v6.0 - STAGING
 echo  Customer site: http://localhost:8769/market.html
 echo  ERP control:   http://localhost:8769/ops.html
 echo  Word forms:    http://localhost:8769/documents.html
 echo ============================================
echo  Local development mode only. No real payments / messages.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8769/ops.html'"
where py >nul 2>nul
if %errorlevel%==0 (py -3 server.py) else (python server.py)
pause
