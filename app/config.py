#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment configuration for Quincaillerie & SME Management App
Loads environment variables from .env file
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_environment_variables():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if not env_file.exists():
        logger.warning(".env file not found, using default environment")
        return
    
    logger.info("Loading environment variables from .env file")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
            
    logger.info(f"Database path set to: {os.environ.get('DATABASE_PATH', 'default')}")
