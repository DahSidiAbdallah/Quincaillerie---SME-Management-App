#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Path Diagnostics Tool for Quincaillerie App
Checks for path inconsistencies in the application
"""

import os
import sys
import importlib.util
import inspect

# Add the app directory to the path
app_dir = os.path.abspath(os.path.dirname(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def check_environment_vars():
    """Check environment variables related to the app"""
    print_section("Environment Variables")
    
    # Check DATABASE_PATH
    if 'DATABASE_PATH' in os.environ:
        db_path = os.environ['DATABASE_PATH']
        print(f"DATABASE_PATH: {db_path}")
        if os.path.exists(db_path):
            print("  ✓ Database file exists")
        else:
            print("  ✗ Database file does not exist")
    else:
        print("DATABASE_PATH: Not set")

def check_path_imports():
    """Check Python path and imports"""
    print_section("Python Path and Imports")
    
    print("Python Path:")
    for path in sys.path:
        print(f"  - {path}")
    
    print("\nAttempting to import app modules:")
    
    # Try importing modules
    modules_to_check = [
        ('db.database', 'DatabaseManager'),
        ('app.data.database', 'DatabaseManager'),
        ('app.api.inventory', 'inventory_bp'),
        ('app.api.customers', 'customers_bp'),
        ('app.app', 'app')
    ]
    
    for module_name, attr_name in modules_to_check:
        try:
            # Try to import the module
            spec = importlib.util.find_spec(module_name)
            if spec is not None:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check for the attribute
                if hasattr(module, attr_name):
                    print(f"  ✓ Successfully imported {attr_name} from {module_name}")
                    
                    # If it's DatabaseManager, check its configuration
                    if attr_name == 'DatabaseManager':
                        dm = getattr(module, attr_name)
                        try:
                            # Try to get the source code to find the database path
                            source = inspect.getsource(dm)
                            db_path_line = [line for line in source.split('\n') 
                                           if 'DATABASE_PATH' in line and '=' in line]
                            if db_path_line:
                                print(f"    Database path in code: {db_path_line[0].strip()}")
                            
                            # Check instance creation
                            instance = dm()
                            print(f"    Created instance: {instance}")
                            if hasattr(instance, 'db_path'):
                                print(f"    Instance db_path: {instance.db_path}")
                        except Exception as e:
                            print(f"    Could not inspect DatabaseManager: {e}")
                else:
                    print(f"  ✗ Module {module_name} exists but does not have {attr_name}")
            else:
                print(f"  ✗ Could not find module {module_name}")
        except Exception as e:
            print(f"  ✗ Error importing {module_name}: {e}")

def check_database_files():
    """Check for database files and their structure"""
    print_section("Database Files")
    
    # List of potential database paths
    db_paths = [
        os.path.join(app_dir, 'app', 'data', 'quincaillerie.db'),
        os.path.join(app_dir, 'app', 'db', 'quincaillerie.db'),
        os.path.join(app_dir, 'db', 'quincaillerie.db'),
        os.path.join(app_dir, 'quincaillerie.db')
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            size = os.path.getsize(db_path) / 1024  # Size in KB
            print(f"✓ {db_path} (Size: {size:.2f} KB)")
        else:
            print(f"✗ {db_path} does not exist")

def check_app_files():
    """Check key application files"""
    print_section("Application Files")
    
    # Key files to check
    files_to_check = [
        os.path.join(app_dir, 'app', 'app.py'),
        os.path.join(app_dir, 'app', 'app_fixed.py'),
        os.path.join(app_dir, 'app', 'app_fixed_imports.py'),
        os.path.join(app_dir, 'app', 'api', 'inventory.py'),
        os.path.join(app_dir, 'app', 'api', 'customers.py'),
        os.path.join(app_dir, 'app', 'db', 'database.py'),
        os.path.join(app_dir, 'db', 'database.py'),
        os.path.join(app_dir, 'run_fixed.py'),
        os.path.join(app_dir, 'run_app.py')
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / 1024  # Size in KB
            modified = os.path.getmtime(file_path)
            import time
            modified_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified))
            print(f"✓ {file_path}")
            print(f"  Size: {size:.2f} KB, Last Modified: {modified_str}")
        else:
            print(f"✗ {file_path} does not exist")

def main():
    """Main function"""
    print("Quincaillerie App Path Diagnostics")
    print(f"Working Directory: {os.getcwd()}")
    print(f"App Directory: {app_dir}")
    
    check_environment_vars()
    check_path_imports()
    check_database_files()
    check_app_files()
    
    print("\nDiagnostics complete. Check the results above for any path inconsistencies.")

if __name__ == "__main__":
    main()
