"""
BALLY FLOW - SQLite Database Layer
Persistent user registry, verification codes, multi-tenant broker profiles, and user order isolation.
"""

from __future__ import annotations
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "bally_flow.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        country_code TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'trader',
        status TEXT NOT NULL DEFAULT 'pending_verification',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Verification Codes (OTP) Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        identifier TEXT NOT NULL,
        channel TEXT NOT NULL DEFAULT 'email',
        code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        is_used INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # 3. Multi-Tenant Broker Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broker_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        broker_server TEXT NOT NULL,
        broker_name TEXT NOT NULL,
        account_number TEXT NOT NULL,
        password_encrypted TEXT,
        currency TEXT DEFAULT 'USD',
        leverage INTEGER DEFAULT 100,
        is_demo INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # Check and add columns if upgrading from older schema
    try:
        cursor.execute("ALTER TABLE broker_profiles ADD COLUMN password_encrypted TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE broker_profiles ADD COLUMN is_active INTEGER DEFAULT 1")
    except Exception:
        pass

    # 4. Multi-Tenant User Orders Isolation Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticket INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        action TEXT NOT NULL,
        lot_size REAL NOT NULL,
        magic_number INTEGER DEFAULT 100001,
        status TEXT NOT NULL DEFAULT 'SUBMITTED',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# Auto-initialize on import
init_db()
