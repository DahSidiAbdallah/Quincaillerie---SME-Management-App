#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, './app')
from data.database import DatabaseManager
from datetime import datetime, timedelta

def add_recent_sales():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Add some sales for the last few days
        recent_sales = [
            {
                'date': datetime.now() - timedelta(days=1),
                'customer': 'Mohamed Ali',
                'phone': '+222 45 12 34 67',
                'amount': 1500.0,
                'paid': 1500.0
            },
            {
                'date': datetime.now() - timedelta(days=2),
                'customer': 'Fatima Mint Ahmed',
                'phone': '+222 45 98 76 54',
                'amount': 850.0,
                'paid': 850.0
            },
            {
                'date': datetime.now() - timedelta(days=3),
                'customer': 'Abdellahi Ould Salem',
                'phone': '+222 45 11 22 33',
                'amount': 2200.0,
                'paid': 1500.0
            },
            {
                'date': datetime.now() - timedelta(days=4),
                'customer': 'Mariem Bint Sidi',
                'phone': '+222 45 44 55 66',
                'amount': 750.0,
                'paid': 750.0
            }
        ]
        
        for sale in recent_sales:
            cursor.execute('''
                INSERT INTO sales (
                    sale_date, customer_name, customer_phone, 
                    total_amount, paid_amount, payment_method,
                    is_credit, status, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sale['date'].strftime('%Y-%m-%d %H:%M:%S'),
                sale['customer'],
                sale['phone'],
                sale['amount'],
                sale['paid'],
                'cash' if sale['paid'] == sale['amount'] else 'credit',
                1 if sale['paid'] < sale['amount'] else 0,
                'completed',
                sale['date'].strftime('%Y-%m-%d %H:%M:%S'),
                1  # admin user ID
            ))
        
        conn.commit()
        print(f"Added {len(recent_sales)} recent sales")
        
        # Check total sales now
        cursor.execute("SELECT COUNT(*) FROM sales WHERE is_deleted = 0")
        total_sales = cursor.fetchone()[0]
        print(f"Total sales in database: {total_sales}")
        
    except Exception as e:
        print(f"Error adding sales: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_recent_sales()
