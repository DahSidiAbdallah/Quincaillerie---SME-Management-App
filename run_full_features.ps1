# Run SME Management App with Full Features
# This script starts the application with all modules and offline capabilities enabled

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please ensure Python is installed and in your PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install required packages if not already installed
Write-Host "Installing required packages..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

# Set environment variables
$env:FLASK_APP = "app.app"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = 1

# Ensure database path is consistent
Write-Host "Setting up database..." -ForegroundColor Cyan
python fix_database_paths.py

# Create admin user if none exists
Write-Host "Checking admin setup..." -ForegroundColor Cyan
python setup_admin.py

# Start the application
Write-Host "Starting application with all features enabled..." -ForegroundColor Green
Write-Host "Access the application at http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test offline capabilities, visit http://localhost:5000/offline-test" -ForegroundColor Yellow
Write-Host ""
python -m flask run --host=0.0.0.0 --port=5000

# Keep the window open if there was an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Application exited with error code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to continue"
}
