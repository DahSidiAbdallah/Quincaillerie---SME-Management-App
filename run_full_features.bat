# Run SME Management App with Full Features
# This script starts the application with all modules and offline capabilities enabled

# Check if Python is installed and in PATH
python --version 2>nul
if %errorlevel% neq 0 (
    echo Python not found in PATH. Please ensure Python is installed and in your PATH.
    pause
    exit /b 1
)

# Install required packages if not already installed
echo Installing required packages...
python -m pip install -r requirements.txt

# Set environment variables
set FLASK_APP=app.app
set FLASK_ENV=development
set FLASK_DEBUG=1

# Ensure database path is consistent
echo Setting up database...
python fix_database_paths.py

# Create admin user if none exists
echo Checking admin setup...
python setup_admin.py

# Start the application
echo Starting application with all features enabled...
echo Access the application at http://localhost:5000
echo.
echo To test offline capabilities, visit http://localhost:5000/offline-test
echo.
python -m flask run --host=0.0.0.0 --port=5000

# Keep the window open if there was an error
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
