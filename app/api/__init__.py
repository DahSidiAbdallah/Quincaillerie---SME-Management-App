# API package initialization
"""
This package contains all API endpoints for the Quincaillerie & SME Management App.
Each module defines a Blueprint for a specific functionality area.
"""

# Import all blueprints for proper initialization
from . import auth, dashboard, inventory, sales, finance, reports, ai_insights
from . import settings
from . import admin
from . import notifications
