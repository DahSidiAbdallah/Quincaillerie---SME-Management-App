#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, './app')
from data.database import DatabaseManager

def check_activity_table():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check user_activity_log table structure
    cursor.execute("PRAGMA table_info(user_activity_log)")
    activity_info = cursor.fetchall()
    print("user_activity_log table structure:")
    for col in activity_info:
        print(f"  {col[1]} - {col[2]}")
    
    # Check if we have activity data
    cursor.execute("SELECT COUNT(*) FROM user_activity_log")
    activity_count = cursor.fetchone()[0]
    print(f"\nActivity records: {activity_count}")
    
    if activity_count > 0:
        cursor.execute("SELECT * FROM user_activity_log LIMIT 3")
        activities = cursor.fetchall()
        print("Sample activities:")
        for activity in activities:
            print(f"  {activity}")
    
    conn.close()

if __name__ == "__main__":
    check_activity_table()
