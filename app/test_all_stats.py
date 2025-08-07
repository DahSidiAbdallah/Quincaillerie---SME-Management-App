#!/usr/bin/env python3
# Complete database stats test

from data.database import DatabaseManager

def main():
    print('=== COMPLETE DATABASE STATS TEST ===')
    db = DatabaseManager()

    print('1. Inventory Stats:')
    inv_stats = db.get_inventory_stats()
    print(f'   Products: {inv_stats.get("total", 0)}')
    print(f'   Low Stock: {inv_stats.get("low_stock", 0)}')
    print(f'   Total Items: {inv_stats.get("total_items", 0)}')
    print(f'   Inventory Value: {inv_stats.get("inventory_value", 0)}')

    print()
    print('2. Financial Stats:')
    print(f'   Total Revenue: {db.get_total_revenue()}')
    print(f'   Cash Balance: {db.get_cash_balance()}')
    debts = db.get_pending_debts()
    print(f'   Pending Debts: {debts.get("total", 0)} ({debts.get("count", 0)} customers)')

    print()
    print('3. Sales Stats:')
    today = db.get_today_sales()
    print(f'   Today Sales: {today.get("total", 0)} ({today.get("count", 0)} transactions)')

    print()
    print('4. Top Products:')
    top = db.get_top_selling_products(days=90)  # Expand to 90 days
    if top:
        for product in top:
            print(f'   {product.get("name", "Unknown")}: {product.get("quantity_sold", 0)} units, {product.get("total_sales", 0)} MRU')
    else:
        print('   No top selling products found')

    print()
    print('5. Low Stock Items:')
    low_stock = db.get_low_stock_items()
    if low_stock:
        for item in low_stock:
            print(f'   {item.get("name", "Unknown")}: {item.get("current_stock", 0)} (reorder at {item.get("reorder_level", 0)})')
    else:
        print('   No low stock items')

if __name__ == '__main__':
    main()
