#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import fix script for Quincaillerie & SME Management App
This script adjusts import statements and fixes various path issues
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_python_path_file():
    """Create a .pth file in site-packages to add app directory to Python path"""
    try:
        # Get the app directory path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create a .pth file content
        content = f"{app_dir}\n"
        
        # Create the .pth file in the current environment's site-packages
        import site
        site_packages = site.getsitepackages()[0]
        pth_file = os.path.join(site_packages, "quincaillerie_app.pth")
        
        with open(pth_file, "w") as f:
            f.write(content)
        
        logger.info(f"Created Python path file at {pth_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to create Python path file: {e}")
        return False

def fix_import_statements():
    """Fix import statements in all Python files"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    replacements = [
        ("from db.database import", "from db.database import"),
        ("from db.database import", "from db.database import"),
        ("import db.database", "import db.database"),
        ("import db.database", "import db.database"),
    ]
    
    files_changed = 0
    occurrences_fixed = 0
    
    # Walk through all Python files in the app directory
    for root, _, files in os.walk(app_dir):
        for filename in [f for f in files if f.endswith('.py')]:
            filepath = os.path.join(root, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                new_content = content
                local_changes = 0
                
                # Apply all replacements
                for old_str, new_str in replacements:
                    count = new_content.count(old_str)
                    if count > 0:
                        new_content = new_content.replace(old_str, new_str)
                        local_changes += count
                
                # Only write to file if changes were made
                if local_changes > 0:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    
                    files_changed += 1
                    occurrences_fixed += local_changes
                    logger.info(f"Fixed {local_changes} occurrences in {filepath}")
                    
            except UnicodeDecodeError:
                logger.warning(f"Skipping {filepath} due to encoding issues")
                continue
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")
                continue
    
    logger.info(f"Completed! Fixed {occurrences_fixed} occurrences in {files_changed} files.")
    return True

def create_init_files():
    """Create __init__.py files in all directories if they don't exist"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    count = 0
    
    # Walk through all directories in the app directory
    for root, dirs, _ in os.walk(app_dir):
        for dir_name in dirs:
            # Skip __pycache__ directories
            if dir_name == "__pycache__":
                continue
                
            dir_path = os.path.join(root, dir_name)
            init_file = os.path.join(dir_path, "__init__.py")
            
            # Create __init__.py if it doesn't exist
            if not os.path.exists(init_file):
                try:
                    with open(init_file, 'w') as f:
                        f.write("# Auto-generated __init__.py\n")
                    count += 1
                    logger.info(f"Created {init_file}")
                except Exception as e:
                    logger.error(f"Error creating {init_file}: {e}")
    
    logger.info(f"Created {count} __init__.py files")
    return True

if __name__ == "__main__":
    logger.info("Starting import fix script...")
    
    # Fix import statements
    logger.info("Fixing import statements...")
    fix_import_statements()
    
    # Create __init__.py files
    logger.info("Creating __init__.py files...")
    create_init_files()
    
    # Create Python path file
    logger.info("Setting up Python path...")
    create_python_path_file()
    
    logger.info("Import fix script completed successfully!")
    print("\nYou can now run the application using:")
    print("  start_app.bat")
