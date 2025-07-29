@echo off
echo Starting Quincaillerie ^& SME Management App...
echo.

REM First fix import issues
echo Fixing import issues...
python app_fixed_imports.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Failed to fix imports. Trying to continue...
)

REM Run setup_admin.py first to ensure admin user exists
echo Checking for admin user...
python setup_admin.py

echo.
echo Starting application server...
python run_fixed.py

pause
