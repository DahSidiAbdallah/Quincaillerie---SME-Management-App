#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix import statements script
Changes 'from db.database import' to 'from db.database import'
"""

import os
import fnmatch
import re

def fix_imports(directory):
    """
    Walk through directory and fix import statements in Python files
    """
    print(f"Fixing imports in {directory}...")
    
    pattern = "from db.database import"
    replacement = "from db.database import"
    
    # Counter for tracking changes
    files_changed = 0
    occurrences_fixed = 0
    
    # Walk through all Python files in the directory
    for root, _, files in os.walk(directory):
        for filename in fnmatch.filter(files, "*.py"):
            filepath = os.path.join(root, filename)
            
            # Read the file content
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Count occurrences
                count = content.count(pattern)
            except UnicodeDecodeError:
                # Try with another encoding or skip the file
                print(f"  Skipping {filepath} due to encoding issues")
                continue
            
            if count > 0:
                # Replace the import statements
                new_content = content.replace(pattern, replacement)
                
                # Write the modified content back to the file
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                files_changed += 1
                occurrences_fixed += count
                print(f"  Fixed {count} occurrences in {filepath}")
    
    print(f"Completed! Fixed {occurrences_fixed} occurrences in {files_changed} files.")

if __name__ == "__main__":
    # Fix imports in the app directory
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
    fix_imports(app_dir)
    
    # Also fix imports in the root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    fix_imports(root_dir)
