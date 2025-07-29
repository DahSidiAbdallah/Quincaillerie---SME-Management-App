#!/usr/bin/env python3
"""
Setup script for Quincaillerie & SME Management App
Automatically installs dependencies and initializes the application
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install required Python packages with Python 3.13 compatibility"""
    print("\n📦 Installing Dependencies...")
    
    # First, upgrade pip and setuptools to latest versions
    if not run_command("python -m pip install --upgrade pip setuptools wheel", "Upgrading pip and setuptools"):
        print("⚠️  Failed to upgrade pip, but continuing...")
    
    # Try to install essential packages first
    essential_packages = [
        "Flask>=3.0.0",
        "python-dotenv>=1.0.0",
        "waitress>=2.1.0",
        "bcrypt>=4.1.0",
        "requests>=2.31.0"
    ]
    
    print("🔄 Installing essential packages first...")
    for package in essential_packages:
        if not run_command(f"pip install \"{package}\"", f"Installing {package.split('>=')[0]}"):
            print(f"⚠️  Failed to install {package}, trying without version constraint...")
            package_name = package.split('>=')[0]
            run_command(f"pip install {package_name}", f"Installing {package_name} (latest)")
    
    # Try minimal requirements file
    if os.path.exists("requirements-minimal.txt"):
        print("🔄 Installing from requirements-minimal.txt...")
        if run_command("pip install -r requirements-minimal.txt", "Installing minimal dependencies"):
            return True
        else:
            print("⚠️  Some packages from minimal requirements failed, trying individual installation...")
    
    # Try data science packages with better error handling
    data_science_packages = [
        ("numpy>=1.26.0", "numpy"),
        ("pandas>=2.2.0", "pandas"),  
        ("scikit-learn>=1.4.0", "scikit-learn"),
        ("matplotlib>=3.8.0", "matplotlib"),
        ("openpyxl>=3.1.0", "openpyxl")
    ]
    
    print("🔄 Installing data science packages...")
    for package_spec, package_name in data_science_packages:
        if not run_command(f"pip install \"{package_spec}\"", f"Installing {package_name}"):
            print(f"⚠️  Failed to install {package_spec}, trying latest version...")
            if not run_command(f"pip install {package_name}", f"Installing {package_name} (latest)"):
                print(f"❌ Could not install {package_name} - you may need to install manually later")
    
    # Try additional features
    additional_packages = [
        ("reportlab>=4.0.0", "reportlab"),
        ("qrcode>=7.4.0", "qrcode"),
        ("python-barcode>=0.15.0", "python-barcode"),
        ("Pillow>=10.0.0", "Pillow"),
        ("Flask-CORS>=4.0.0", "Flask-CORS"),
        ("Flask-Mail>=0.9.1", "Flask-Mail")
    ]
    
    print("🔄 Installing additional features...")
    for package_spec, package_name in additional_packages:
        if not run_command(f"pip install \"{package_spec}\"", f"Installing {package_name}"):
            print(f"⚠️  {package_name} installation failed - feature may not work")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "app/static/uploads",
        "app/static/icons",
        "app/static/screenshots",
        "app/logs",
        "app/backups",
        "app/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def initialize_database():
    """Initialize the SQLite database"""
    print("\n🗄️  Initializing database...")
    
    try:
        # Add app directory to Python path
        current_dir = os.getcwd()
        app_dir = os.path.join(current_dir, "app")
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        
        # Import and initialize database
        from db.database import DatabaseManager
        
        # Create database manager with proper path
        db_path = os.path.join(app_dir, 'data', 'quincaillerie.db')
        db_manager = DatabaseManager(db_path)
        db_manager.init_database()
        
        print("✅ Database initialized successfully")
        print("📝 Default admin user available:")
        print("   Username: admin")
        print("   PIN: 1234")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print(f"Error details: {str(e)}")
        return False

def create_env_file():
    """Create environment configuration file"""
    print("\n⚙️  Creating environment configuration...")
    
    env_content = """# Quincaillerie & SME Management App Configuration
# Production settings
SECRET_KEY=quincaillerie-app-2025-secure-key-change-in-production
DEBUG=True
DATABASE_URL=sqlite:///data/quincaillerie.db

# Upload settings
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216

# AI Settings
ENABLE_AI_FEATURES=True

# Email settings (optional)
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=

# Backup settings
BACKUP_FREQUENCY=daily
BACKUP_RETENTION_DAYS=30

# Sync settings
ENABLE_CLOUD_SYNC=False
SYNC_INTERVAL_MINUTES=30
"""
    
    with open("app/.env", "w") as f:
        f.write(env_content)
    
    print("✅ Environment file created at app/.env")

def run_tests():
    """Run basic tests to verify installation"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Add app directory to Python path
        current_dir = os.getcwd()
        app_dir = os.path.join(current_dir, "app")
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        
        # Test database connection
        from db.database import DatabaseManager
        db_path = os.path.join(app_dir, 'data', 'quincaillerie.db')
        db = DatabaseManager(db_path)
        
        # Test basic database functionality
        total_products = db.get_total_products()
        print(f"✅ Database connection test passed - {total_products} products found")
        
        # Test AI modules
        try:
            from models.ml_forecasting import StockPredictor
            predictor = StockPredictor()
            print("✅ AI modules test passed")
        except Exception as e:
            print(f"⚠️  AI modules test failed (optional feature): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Quincaillerie & SME Management App Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("⚠️  Some dependencies failed to install, but continuing...")
    
    # Create directories
    create_directories()
    
    # Create environment file
    create_env_file()
    
    # Initialize database
    if not initialize_database():
        print("❌ Setup failed at database initialization")
        sys.exit(1)
    
    # Run tests
    if run_tests():
        print("\n🎉 Setup completed successfully!")
        print("\n🚀 To start the application:")
        print("   cd app")
        print("   python app.py")
        print("\n🌐 Then open your browser to: http://localhost:5000")
        print("\n👤 Login with:")
        print("   Username: admin")
        print("   PIN: 1234")
        print("\n📱 Features available:")
        print("   ✅ Inventory Management")
        print("   ✅ Sales & Customer Management") 
        print("   ✅ Financial Reporting")
        print("   ✅ Employee Management")
        print("   ✅ Offline PWA Support")
        print("   ✅ AI Forecasting (with fallbacks)")
    else:
        print("\n⚠️  Setup completed with warnings. You can still start the app:")
        print("   cd app")
        print("   python app.py")
        print("\n🌐 Open browser to: http://localhost:5000")
        print("👤 Login: admin / 1234")

if __name__ == "__main__":
    main()
