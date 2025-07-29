#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility script to check for proper imports and setup.
"""

import os
import sys
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_module_available(module_name):
    """Check if a module can be imported"""
    spec = importlib.util.find_spec(module_name)
    return spec is not None

def check_module_path(module_name):
    """Try to import a module and return its file path"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec:
            return spec.origin
        return "Not found"
    except ImportError:
        return "Import error"

def main():
    """Check modules and paths"""
    print("Checking Python import paths and module availability...\n")
    
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"sys.path[0]: {sys.path[0]}")
    print()
    
    # Check key modules
    modules_to_check = [
        "app", 
        "app.app", 
        "app.db.database", 
        "app.api.inventory",
        "db.database",  # This is the problematic import
        "api.inventory"
    ]
    
    for module in modules_to_check:
        available = check_module_available(module)
        path = check_module_path(module) if available else "N/A"
        print(f"Module '{module}': {'Available' if available else 'Not available'}")
        print(f"  Path: {path}")
    
    print("\nTrying direct import of DatabaseManager...")
    try:
        # Try both import styles
        try:
            from db.database import DatabaseManager
            print("✓ Successfully imported from app.db.database")
            db = DatabaseManager()
            print(f"  Database path: {db.db_path}")
        except ImportError as e:
            print(f"✗ Failed to import from app.db.database: {e}")
            
            try:
                from db.database import DatabaseManager
                print("✓ Successfully imported from db.database")
                db = DatabaseManager()
                print(f"  Database path: {db.db_path}")
            except ImportError as e:
                print(f"✗ Failed to import from db.database: {e}")
                
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
