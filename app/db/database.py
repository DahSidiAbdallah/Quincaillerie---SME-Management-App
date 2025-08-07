#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Module Redirect
This file redirects imports from 'app.db.database' to 'app.data.database'
"""

import os
import sys
import logging

# Get the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the app directory (one level up)
app_dir = os.path.dirname(current_dir)
# Get project root directory (two levels up)
project_dir = os.path.dirname(app_dir)

# Set the database path environment variable
os.environ['DATABASE_PATH'] = os.path.join(app_dir, 'data', 'quincaillerie.db')

# Set up logger
logger = logging.getLogger(__name__)
logger.info(f"App DB redirector setting DATABASE_PATH to: {os.environ['DATABASE_PATH']}")

# Import everything from data.database using sys.path manipulation
data_dir = os.path.join(app_dir, 'data')
if data_dir not in sys.path:
    sys.path.insert(0, data_dir)

# Now import from database
from database import *
