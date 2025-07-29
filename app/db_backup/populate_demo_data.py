#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to populate the Quincaillerie & SME Management App database with realistic demo data.
"""

import os
import sys
from faker import Faker
import random
from datetime import datetime, timedelta
import sqlite3

# Use environment variables for database path
env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
if env_path and env_path.startswith('sqlite:///'):
    env_path = env_path.replace('sqlite:///', '', 1)
default_path = os.path.join(os.path.dirname(__file__), 'quincaillerie.db')
DB_PATH = os.path.abspath(env_path or default_path)

fake = Faker('fr_FR')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Helper: get admin user id
cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
admin_id = cursor.fetchone()
if admin_id:
    admin_id = admin_id[0]
else:
    admin_id = 1

# Customers
customers = []
for _ in range(20):
    customers.append((
        fake.name(),
        fake.phone_number(),
        fake.email(),
        fake.address()
    ))

cursor.executemany('''
    INSERT INTO customers (name, phone, email, address)
    VALUES (?, ?, ?, ?)
''', customers)

# Products
products = []
for _ in range(30):
    name = fake.unique.word().capitalize() + ' ' + fake.random_element(['Vis', 'Marteau', 'Peinture', 'Tournevis', 'Clé', 'Perceuse', 'Scie', 'Pince'])
    desc = fake.sentence(nb_words=8)
    purchase_price = round(random.uniform(5, 100), 2)
    sale_price = round(purchase_price * random.uniform(1.2, 1.8), 2)
    stock = random.randint(0, 100)
    min_stock = random.randint(3, 10)
    category = fake.random_element(['Outils', 'Quincaillerie', 'Peinture', 'Électricité', 'Plomberie'])
    supplier = fake.company()
    barcode = fake.ean13()
    products.append((name, desc, purchase_price, sale_price, stock, min_stock, category, supplier, barcode, admin_id))

cursor.executemany('''
    INSERT INTO products (name, description, purchase_price, sale_price, current_stock, min_stock_alert, category, supplier, barcode, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', products)

# Sales
sales = []
sale_items = []
for _ in range(50):
    sale_date = fake.date_between(start_date='-60d', end_date='today')
    customer_name = fake.name()
    customer_phone = fake.phone_number()
    invoice_number = f"INV{fake.unique.random_int(min=1000, max=9999)}"
    total_amount = 0
    paid_amount = 0
    payment_method = fake.random_element(['cash', 'credit', 'mobile'])
    is_credit = 1 if payment_method == 'credit' else 0
    if is_credit:
        if isinstance(sale_date, str):
            sale_date_obj = datetime.strptime(sale_date, '%Y-%m-%d')
        else:
            sale_date_obj = sale_date
        credit_due_date = (sale_date_obj + timedelta(days=30)).strftime('%Y-%m-%d')
    else:
        credit_due_date = None
    status = fake.random_element(['completed', 'pending'])
    notes = fake.sentence(nb_words=6)
    # Add sale
    sales.append((sale_date, invoice_number, customer_name, customer_phone, 0, 0, payment_method, is_credit, credit_due_date, status, notes, admin_id))

conn.commit()

# Insert sales and sale_items

for sale in sales:
    cursor.execute('''
        INSERT INTO sales (sale_date, invoice_number, customer_name, customer_phone, total_amount, paid_amount,
                           payment_method, is_credit, credit_due_date, status, notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sale)
    sale_id = cursor.lastrowid
    # Add 1-4 items per sale
    total_amount = 0
    paid_amount = 0
    for _ in range(random.randint(1, 4)):
        product_id = random.randint(1, len(products))
        quantity = random.randint(1, 5)
        cursor.execute('SELECT sale_price, purchase_price FROM products WHERE id=?', (product_id,))
        row = cursor.fetchone()
        if not row:
            continue
        unit_price, purchase_price = row
        total_price = round(unit_price * quantity, 2)
        profit_margin = round((unit_price - purchase_price) * quantity, 2)
        sale_items.append((sale_id, product_id, quantity, unit_price, total_price, profit_margin))
        total_amount += total_price
    paid_amount = total_amount if sale[5] != 'credit' else 0
    # Update sale totals
    cursor.execute('UPDATE sales SET total_amount=?, paid_amount=? WHERE id=?', (total_amount, paid_amount, sale_id))

cursor.executemany('''
    INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, total_price, profit_margin)
    VALUES (?, ?, ?, ?, ?, ?)
''', sale_items)

conn.commit()

# Default application settings
cursor.executemany('INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)', [
    ('company_name', 'Ma Quincaillerie'),
    ('default_language', 'fr'),
    ('currency', 'MRU'),
    ('enable_notifications', '1'),
    ('session_timeout', '60'),
    ('max_login_attempts', '5'),
    ('require_strong_passwords', '0'),
    ('enable_audit_log', '1')
])
conn.commit()
print('Demo data inserted successfully.')
conn.close()
