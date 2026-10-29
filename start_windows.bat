@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =============================================
echo  GARAKLAND ERP RELEASE v6.0 STAGING
echo  http://localhost:8769/market.html
 echo  ERP: http://localhost:8769/ops.html
echo  Existing AR: http://localhost:8769/
echo  No real gifts, payments or mass messaging in this beta
 echo =============================================
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8769/market.html'"
where py >nul 2>nul
if %errorlevel%==0 (py -3 server.py) else (python server.py)
pause
