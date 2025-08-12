"""
Cleanup script to remove useless scripts from the project root.
Keeps only essential app, config, and documentation files.
Run this script from the project root.
"""
import os

# List of essential files to keep (add/remove as needed)
KEEP = {
    'README.md',
    'Original README.md',
    'requirements.txt',
    'requirements-minimal.txt',
    'run_app.py',
    'run_full_features.bat',
    'run_full_features.ps1',
    'run_fixed.py',
    'setup.py',
    'app/',
    'static/',
    'backups/',
    'db/',
    'dev_scripts/',
    'legacy/',
    'sqlite-tools/',
    'sqlite.zip',
    '.env',
    '.venv/',
    '.vscode/',
    '.git/',
    '__init__.py',
    '__pycache__/',
    'DATABASE_SETUP_GUIDE.md',
    'QUICKSTART.md',
}

def is_keep(path):
    for keep in KEEP:
        if os.path.normpath(path) == os.path.normpath(keep):
            return True
    return False

def main():
    deleted = []
    for name in os.listdir('.'):
        if not is_keep(name):
            try:
                full = os.path.abspath(name)
                if os.path.isdir(full):
                    continue  # Don't delete unknown directories automatically
                os.remove(full)
                deleted.append(name)
                print(f"Deleted file: {name}")
            except Exception as e:
                print(f"Failed to delete {name}: {e}")
    if not deleted:
        print("No files deleted. All clean!")

if __name__ == "__main__":
    main()
