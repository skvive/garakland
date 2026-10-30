@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 (echo TEST FAILURE: Not ready. & pause & exit /b 1)
echo All Python tests passed.
pause
