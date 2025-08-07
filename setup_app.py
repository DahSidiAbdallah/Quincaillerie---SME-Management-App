#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Combined Setup Script for Quincaillerie & SME Management App
This script sets up both the database and required directories
"""

import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a Python script and handle errors"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script {script_path} not found")
        return False
    
    logger.info(f"Running {script_name}...")
    
    try:
        # Use the current Python executable to run the script
        python_executable = sys.executable
        result = subprocess.run([python_executable, script_path], check=True)
        
        if result.returncode == 0:
            logger.info(f"{script_name} completed successfully")
            return True
        else:
            logger.error(f"{script_name} failed with return code {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {script_name}: {e}")
        return False

def main():
    """Run all setup scripts in sequence"""
    # Step 1: Set up directories and placeholder files
    if not run_script('setup_directories.py'):
        logger.warning("Directory setup had issues, but continuing...")
    
    # Step 2: Set up database
    if not run_script('setup_database.py'):
        logger.error("Database setup failed")
        return False
    
    logger.info("Setup completed successfully!")
    logger.info("\nYou can now run the application using:")
    logger.info("python run_fixed.py")
    logger.info("\nDefault login credentials:")
    logger.info("Username: admin")
    logger.info("PIN: 1234")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
