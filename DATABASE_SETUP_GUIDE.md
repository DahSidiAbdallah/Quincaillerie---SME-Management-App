# Database Setup Guide for Quincaillerie Management App

This guide explains how to properly set up the database for the Quincaillerie Management App, resolving path issues and ensuring consistent configuration.

## Database Path Issues

The application has multiple database path references that can cause confusion:

1. **Multiple Locations**:
   - `app/data/quincaillerie.db` (primary location)
   - `app/db/quincaillerie.db` (secondary location)

2. **Environment Variables**:
   - `DATABASE_PATH`: Used by most modules
   - `DATABASE_URL`: Alternative format that supports SQLAlchemy URL format

## Automated Setup

We've created three setup scripts to address these issues:

### 1. Complete Setup (Recommended)

This script runs all necessary setup steps:

```bash
python setup_app.py
```

### 2. Database-Only Setup

This script focuses only on database initialization and path consistency:

```bash
python setup_database.py
```

### 3. Directory Structure Setup

This script creates all necessary directories and placeholder files:

```bash
python setup_directories.py
```

## What the Setup Scripts Do

### Database Setup (`setup_database.py`)

1. **Path Consolidation**: 
   - Identifies existing database files
   - Ensures a single canonical database at `app/data/quincaillerie.db`
   - Creates a copy at `app/db/quincaillerie.db` for compatibility

2. **Redirector Module**:
   - Creates or updates `app/db/database.py` to redirect imports
   - Ensures consistent database access regardless of import path

3. **Database Initialization**:
   - Creates tables if they don't exist
   - Sets up basic schema for users, products, sales, etc.

4. **Admin User Creation**:
   - Creates a default admin user if none exists
   - Default credentials: Username: `admin` / PIN: `1234`

### Directory Setup (`setup_directories.py`)

1. **Creates Required Directories**:
   - `app/logs` - For application logs
   - `app/data` - For database and data files
   - `app/backups` - For database backups
   - `app/static/splash` - For splash screen images
   - `app/static/uploads` - For user uploads
   - `app/static/icons` - For app icons

2. **Generates Placeholder Images**:
   - Creates missing splash screen images
   - Creates required app icons in various sizes

## Manual Database Setup (If Needed)

If you need to manually set up the database:

1. Ensure SQLite is installed
2. Set the correct environment variable:
   ```bash
   # On Windows PowerShell
   $env:DATABASE_PATH = "C:\path\to\app\data\quincaillerie.db"
   
   # On Linux/Mac
   export DATABASE_PATH="/path/to/app/data/quincaillerie.db"
   ```
3. Run database initialization:
   ```bash
   python create_admin.py
   ```

## Troubleshooting Database Issues

If you encounter database-related errors:

1. **Path Issues**:
   - Run `python setup_database.py` to consolidate paths
   - Check if DATABASE_PATH environment variable is set correctly

2. **Permission Issues**:
   - Ensure the application has write access to the database directories
   - On Windows, run the application as administrator if needed

3. **Database Corruption**:
   - Check if the database file exists and is not corrupted
   - Use the backup files in `backups/` if needed

4. **Missing Tables**:
   - Run `python setup_database.py` to initialize missing tables

## Verifying Database Setup

To verify that the database is properly set up:

```bash
python check_database.py
```

This will check if the database exists and contains the necessary tables.
