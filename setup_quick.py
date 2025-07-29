#!/usr/bin/env python3
"""
Quick Setup for Quincailleriedef create_database():
    """Create a basic SQLite database"""
    print("\n🗄️  Creating basic database...")
    
    try:
        import sqlite3
        
        # Create database directory
        Path("app/data").mkdir(parents=True, exist_ok=True)
        
        # Get database path from environment or use default
        env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
        if env_path and env_path.startswith('sqlite:///'):
            env_path = env_path.replace('sqlite:///', '', 1)
        db_path = env_path or "app/data/quincaillerie.db"
        
        # Create basic database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()ment App
Simplified version for Python 3.13 compatibility
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def install_basic_dependencies():
    """Install only essential dependencies"""
    print("\n📦 Installing Basic Dependencies...")
    
    # Essential packages only
    basic_packages = [
        "Flask>=2.3.0",
        "python-dotenv>=1.0.0",
        "waitress>=2.1.0"
    ]
    
    for package in basic_packages:
        if run_command(f"pip install {package}", f"Installing {package.split('>=')[0]}"):
            continue
        else:
            print(f"⚠️  Failed to install {package}")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "app/static/uploads",
        "app/logs",
        "app/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_basic_database():
    """Create a basic SQLite database"""
    print("\n🗄️  Creating basic database...")
    
    try:
        import sqlite3
        
        # Create database directory
        Path("app/data").mkdir(parents=True, exist_ok=True)
        
        # Create basic database
        conn = sqlite3.connect("app/data/quincaillerie.db")
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                role TEXT DEFAULT 'employee',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create basic admin user (PIN: 1234)
        # Simple hash for demo - in production use proper hashing
        admin_pin_hash = "81dc9bdb52d04dc20036dbd8313ed055"  # Simple MD5 of "1234" for demo
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, pin_hash, role)
            VALUES (?, ?, ?)
        ''', ("admin", admin_pin_hash, "admin"))
        
        conn.commit()
        conn.close()
        
        print("✅ Basic database created successfully")
        print("📝 Default admin user created:")
        print("   Username: admin")
        print("   PIN: 1234")
        
        return True
        
    except Exception as e:
        print(f"❌ Database creation failed: {e}")
        return False

def create_minimal_app():
    """Create a minimal version of app.py that works without all dependencies"""
    print("\n🔧 Creating minimal app version...")
    
    minimal_app_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quincaillerie & SME Management App - Minimal Version
This version works without complex dependencies
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'quincaillerie-demo-key-change-in-production'

def get_db():
    """Get database connection"""
    # Get database path from environment or use default
    env_path = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PATH')
    if env_path and env_path.startswith('sqlite:///'):
        env_path = env_path.replace('sqlite:///', '', 1)
    db_path = env_path or "app/data/quincaillerie.db"
    return sqlite3.connect(db_path)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html') if os.path.exists('templates/login.html') else '''
    <html>
    <head><title>Quincaillerie Management</title></head>
    <body style="font-family: Arial; padding: 50px; text-align: center;">
        <h1>🔧 Quincaillerie Management</h1>
        <h2>Connexion</h2>
        <form method="POST" action="/login">
            <p><input type="text" name="username" placeholder="Nom d'utilisateur" required></p>
            <p><input type="password" name="pin" placeholder="PIN" required></p>
            <p><button type="submit">Se connecter</button></p>
        </form>
        <p><small>Admin: username=admin, PIN=1234</small></p>
    </body>
    </html>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        pin = request.form.get('pin')
        
        if username and pin:
            # Simple authentication - in production use proper hashing
            pin_hash = hashlib.md5(pin.encode()).hexdigest()
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, role FROM users WHERE username = ? AND pin_hash = ?', 
                         (username, pin_hash))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['user_role'] = user[2]
                return redirect(url_for('dashboard'))
        
        flash('Nom d\\'utilisateur ou PIN incorrect', 'error')
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard"""
    username = session.get('username', 'Utilisateur')
    return f'''
    <html>
    <head><title>Tableau de Bord</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h1>🔧 Quincaillerie Management</h1>
        <h2>Tableau de Bord</h2>
        <p>Bonjour, <strong>{username}</strong>!</p>
        <p>Rôle: {session.get('user_role', 'employee')}</p>
        <hr>
        <h3>🚧 Application en cours de développement</h3>
        <p>Cette version minimale fonctionne avec les fonctionnalités de base.</p>
        <p>Pour la version complète, installez toutes les dépendances.</p>
        <hr>
        <a href="/logout">Déconnexion</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("🚀 Démarrage de l'application Quincaillerie Management...")
    print("📍 URL: http://localhost:5000")
    print("👤 Login: admin / PIN: 1234")
    app.run(debug=True, host='0.0.0.0', port=5000)
'''
    
    try:
        with open("app/app_minimal.py", "w", encoding='utf-8') as f:
            f.write(minimal_app_content)
        print("✅ Minimal app created: app/app_minimal.py")
        return True
    except Exception as e:
        print(f"❌ Failed to create minimal app: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Quincaillerie & SME Management App - Quick Setup")
    print("=" * 55)
    print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Install basic dependencies
    if not install_basic_dependencies():
        print("⚠️  Failed to install dependencies. You can still run the minimal version.")
    
    # Create directories
    create_directories()
    
    # Create basic database
    if not create_basic_database():
        print("❌ Setup failed at database creation")
        return
    
    # Create minimal app
    create_minimal_app()
    
    print("\n🎉 Quick setup completed!")
    print("\n🚀 To start the application:")
    print("   cd app")
    print("   python app_minimal.py")
    print("\n🌐 Then open your browser to: http://localhost:5000")
    print("\n👤 Login with:")
    print("   Username: admin")
    print("   PIN: 1234")
    print("\n💡 This is a minimal version. For full features, install all dependencies later.")

if __name__ == "__main__":
    main()
