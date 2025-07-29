@echo off
echo Starting Quincaillerie ^& SME Management App...
echo.

REM Set the database path
set DATABASE_PATH=%~dp0app\data\quincaillerie.db
echo Using database: %DATABASE_PATH%

REM First fix import issues
echo Fixing import issues...
python app_fixed_imports.py >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Failed to fix imports. Trying to continue...
)

REM Fix database paths
echo Fixing database paths...
python fix_database_paths.py

REM Populate the database with Mauritanian data if needed
echo Checking and populating database...
python populate_main_db.py

echo.
echo Starting application server...
python run_fixed.py

pause
