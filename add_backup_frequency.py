#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.data.database import DatabaseManager

db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE settings ADD COLUMN backup_frequency TEXT DEFAULT "daily"')
    conn.commit()
    print('✅ Added backup_frequency column')
except Exception as e:
    if 'duplicate column name' in str(e):
        print('⏭️  backup_frequency column already exists')
    else:
        print(f'❌ Error: {e}')
finally:
    conn.close()
