@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 가락한상 브랜드 사이트 v1.0 + 기존 v7 기능을 시작합니다.
echo Python 3.10 이상이 필요합니다.
python server.py
pause
