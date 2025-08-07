import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.data.database import DatabaseManager

def main():
    """
    Initializes the database and populates it with Mauritania-specific sample data.
    """
    print("Initializing and populating the database with Mauritania data...")
    
    # Use the correct path for the database
    db_path = os.path.join(project_root, 'app', 'db', 'quincaillerie.db')
    
    db_manager = DatabaseManager(db_path=db_path)
    
    # Initialize the database schema
    print("Step 1: Initializing database schema...")
    db_manager.init_database()
    print("Database schema initialized.")
    
    # Populate with Mauritania data
    print("Step 2: Populating with Mauritania sample data...")
    try:
        db_manager.populate_mauritania_data()
        print("Successfully populated the database with Mauritania sample data.")
    except Exception as e:
        print(f"An error occurred during data population: {e}")

if __name__ == '__main__':
    main()