import sqlite3

# Path to your database
DB_PATH = '../app/data/quincaillerie.db'

def get_session_user_id():
    # Simulate getting the session user_id (replace with actual session logic if needed)
    # For demo, print a placeholder or fetch from a config if available
    print('Session user_id (replace with actual session logic):', 1)
    return 1

def print_user_profiles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print('\nuser_profiles table:')
    for row in cursor.execute('SELECT id, user_id, first_name, last_name, email, photo_path FROM user_profiles'):
        print(row)
    conn.close()

def main():
    session_user_id = get_session_user_id()
    print_user_profiles()
    print('\nCompare the session user_id to the user_id column above.')

if __name__ == '__main__':
    main()
