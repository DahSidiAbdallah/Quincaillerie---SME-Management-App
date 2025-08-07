#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, './app')
from data.database import DatabaseManager

def create_low_stock_alerts():
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Check current stock levels
        cursor.execute("SELECT id, name, current_stock, reorder_level FROM products LIMIT 5")
        products = cursor.fetchall()
        print("Current products:")
        for product in products:
            print(f"  {product['name']}: stock={product['current_stock']}, reorder={product['reorder_level']}")
        
        # Set some products to low stock
        low_stock_updates = [
            (1, 2),  # Marteau: set to 2 (below reorder level of 5)
            (2, 1),  # Tournevis: set to 1
            (3, 3),  # Ciment: set to 3
        ]
        
        for product_id, new_stock in low_stock_updates:
            cursor.execute('''
                UPDATE products 
                SET current_stock = ?
                WHERE id = ?
            ''', (new_stock, product_id))
        
        conn.commit()
        print(f"\nUpdated {len(low_stock_updates)} products to low stock levels")
        
        # Test low stock items
        low_stock = db.get_low_stock_items()
        print(f"Low stock items found: {len(low_stock)}")
        for item in low_stock:
            print(f"  {item['name']}: {item['current_stock']} (threshold: {item['reorder_level']})")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_low_stock_alerts()
