@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/2] Server and coupon tests
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m unittest discover -s tests -p test_beta.py -v) else (python -m unittest discover -s tests -p test_beta.py -v)
if errorlevel 1 (echo SERVER TEST FAILED & pause & exit /b 1)
echo [2/2] Google Maps URL tests
where node >nul 2>nul
if %errorlevel%==0 (node tests\test_navigation.mjs) else (echo Node.js not found. Skipping navigation JS test.)
pause
