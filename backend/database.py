"""BALLY FLOW - SQLite Database Layer.

DB-1 owns durable application state: identity, authentication state, sessions,
user preferences, risk/trading configuration, broker profiles, audit records,
and the existing AI learning tables.

Live MT5 state remains the source of truth for account, positions, market data,
and trading intelligence. The mobile app never connects directly to SQLite.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "bally_flow.db"
DB_SCHEMA_VERSION = 1


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _add_column_if_missing(
    cursor: sqlite3.Cursor,
    table: str,
    column: str,
    definition: str,
) -> None:
    columns = {
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create lookup indexes without changing existing application data."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)",
        "CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)",
        "CREATE INDEX IF NOT EXISTS idx_verification_user ON verification_codes(user_id, is_used)",
        "CREATE INDEX IF NOT EXISTS idx_verification_destination ON verification_codes(destination, is_used)",
        "CREATE INDEX IF NOT EXISTS idx_verification_created ON verification_codes(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_settings_updated ON user_settings(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_risk_user_active ON risk_configurations(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_preferences_updated ON trading_preferences(updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user_created ON audit_logs(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_audit_event_created ON audit_logs(event_type, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_broker_user_active ON broker_profiles(user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS idx_orders_user_created ON user_orders(user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_ticket ON user_orders(ticket)",
        "CREATE INDEX IF NOT EXISTS idx_ai_pattern_symbol_tf ON ai_pattern_knowledge(symbol, timeframe)",
    ]
    for statement in indexes:
        cursor.execute(statement)


def init_db() -> None:
    """Initialize the DB-1 foundation and apply newer migrations safely.

    DB-1 remains the base schema. Higher schema versions are never overwritten
    by this initializer. If the database is below DB-2 or DB-3, the matching
    migration is invoked after the DB-1 connection is closed, avoiding circular
    imports and keeping normal application startup migration-safe.
    """
    needs_db2_migration = False
    needs_db3_migration = False
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

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
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            identifier TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT 'email',
            code TEXT,
            code_hash TEXT,
            destination TEXT,
            provider TEXT DEFAULT 'twilio_verify',
            provider_verification_id TEXT,
            expires_at TIMESTAMP NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            is_used INTEGER NOT NULL DEFAULT 0,
            verified_at TIMESTAMP,
            delivery_status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        # Safe migrations for databases created before DB-1.
        for table, column, definition in [
            ("verification_codes", "code_hash", "TEXT"),
            ("verification_codes", "destination", "TEXT"),
            ("verification_codes", "provider", "TEXT DEFAULT 'twilio_verify'"),
            ("verification_codes", "provider_verification_id", "TEXT"),
            ("verification_codes", "verified_at", "TIMESTAMP"),
            ("verification_codes", "delivery_status", "TEXT NOT NULL DEFAULT 'pending'"),
            ("users", "email_verified", "INTEGER NOT NULL DEFAULT 0"),
            ("users", "phone_verified", "INTEGER NOT NULL DEFAULT 0"),
        ]:
            _add_column_if_missing(cursor, table, column, definition)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_jti TEXT UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            min_confidence REAL DEFAULT 70.0,
            risk_per_trade_pct REAL DEFAULT 1.0,
            max_positions INTEGER DEFAULT 1,
            scan_interval_seconds INTEGER DEFAULT 60,
            trading_mode TEXT DEFAULT 'Technical',
            theme TEXT DEFAULT 'SYSTEM',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            risk_per_trade_pct REAL NOT NULL DEFAULT 1.0,
            max_risk_pct REAL NOT NULL DEFAULT 2.0,
            min_risk_pct REAL NOT NULL DEFAULT 0.10,
            max_positions INTEGER NOT NULL DEFAULT 1,
            min_rr REAL NOT NULL DEFAULT 1.0,
            max_rr REAL NOT NULL DEFAULT 3.0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_preferences (
            user_id INTEGER PRIMARY KEY,
            trading_mode TEXT NOT NULL DEFAULT 'Technical',
            approval_required INTEGER NOT NULL DEFAULT 1,
            enabled INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_type TEXT NOT NULL,
            channel TEXT,
            ip_address TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )""")

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
        )""")
        _add_column_if_missing(cursor, "broker_profiles", "password_encrypted", "TEXT")
        _add_column_if_missing(cursor, "broker_profiles", "is_active", "INTEGER DEFAULT 1")

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
        )""")

        # Existing AI persistence is intentionally preserved.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_pattern_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            regime TEXT NOT NULL,
            signature_hash TEXT NOT NULL,
            setup_type TEXT NOT NULL,
            direction TEXT NOT NULL,
            win_count INTEGER DEFAULT 0,
            loss_count INTEGER DEFAULT 0,
            total_pnl REAL DEFAULT 0.0,
            avg_confidence REAL DEFAULT 0.0,
            last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_symbol_learning (
            symbol TEXT PRIMARY KEY,
            total_scans INTEGER DEFAULT 0,
            total_trades INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            market_regime TEXT DEFAULT 'UNKNOWN',
            volatility_score REAL DEFAULT 0.0,
            trend_strength REAL DEFAULT 0.0,
            adaptive_multiplier REAL DEFAULT 1.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        _create_indexes(cursor)

        # DB-1 must never downgrade an already-migrated database.
        cursor.execute("""
        INSERT INTO schema_metadata(key, value)
        VALUES ('db_schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET
            value=CASE
                WHEN CAST(schema_metadata.value AS INTEGER) < CAST(excluded.value AS INTEGER)
                THEN excluded.value
                ELSE schema_metadata.value
            END,
            updated_at=CURRENT_TIMESTAMP
        """, (str(DB_SCHEMA_VERSION),))

        current_version_row = cursor.execute(
            "SELECT value FROM schema_metadata WHERE key='db_schema_version'"
        ).fetchone()
        current_version = int(current_version_row[0]) if current_version_row else DB_SCHEMA_VERSION
        needs_db2_migration = current_version < 2
        needs_db3_migration = current_version < 3

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    if needs_db2_migration:
        from backend.db2_migration import migrate_db2

        migrate_db2()

    if needs_db3_migration:
        from backend.db3_migration import migrate_db3

        migrate_db3()


init_db()
