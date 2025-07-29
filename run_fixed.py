#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple starter script with import path fixes
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Add the current directory to the Python path for absolute imports
    project_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_dir)
    
    # Add the app directory to the Python path for relative imports
    app_dir = os.path.join(project_dir, 'app')
    sys.path.append(app_dir)
    
    # Add the db directory to the Python path
    db_dir = os.path.join(project_dir, 'app', 'db')
    sys.path.append(db_dir)
    
    # Set environment variables before importing the app
    os.environ['DATABASE_PATH'] = os.path.join(app_dir, 'data', 'quincaillerie.db')
    logger.info(f"Using database: {os.environ['DATABASE_PATH']}")
    
    # Now import and run the application
    try:
        # We need to import the app module itself
        import app.app
        
        # Run the Flask application
        logger.info("Starting Quincaillerie & SME Management App...")
        logger.info("Server running at http://localhost:5000")
        app.app.app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
