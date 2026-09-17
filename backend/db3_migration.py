"""BALLY FLOW - DB-3 broker/trading-account persistence migration.

DB-3 adds durable trading-account records for authenticated users while
preserving the existing DB-1 broker_profiles table and all DB-2 lifecycle data.

Design boundary:
- broker_profiles remains backward-compatible application/broker metadata.
- trading_accounts represents the user's actual MT5 trading-account identity.
- Secrets are not copied into trading_accounts. Credential storage/handling
  remains outside this schema boundary.
- MT5 remains the source of truth for live balance, equity, margin, positions,
  and connection state.
"""
from __future__ import annotations

from backend.database import get_db_connection

DB3_SCHEMA_VERSION = 3


def migrate_db3() -> None:
    """Apply DB-3 idempotently and non-destructively."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trading_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            broker_profile_id INTEGER,
            platform TEXT NOT NULL DEFAULT 'MT5',
            account_number TEXT NOT NULL,
            account_name TEXT,
            broker_server TEXT NOT NULL,
            broker_name TEXT NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            leverage INTEGER,
            is_demo INTEGER NOT NULL DEFAULT 1,
            connection_status TEXT NOT NULL DEFAULT 'DISCONNECTED',
            last_connected_at TIMESTAMP,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (broker_profile_id) REFERENCES broker_profiles(id) ON DELETE SET NULL
        )""")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_active ON trading_accounts(user_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_created ON trading_accounts(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trading_accounts_broker_profile ON trading_accounts(broker_profile_id)",
            "CREATE INDEX IF NOT EXISTS idx_trading_accounts_server_account ON trading_accounts(broker_server, account_number)",
            "CREATE INDEX IF NOT EXISTS idx_trading_accounts_status ON trading_accounts(connection_status)",
        ]
        for statement in indexes:
            cur.execute(statement)

        # One active trading account per user is the initial application rule.
        # This is enforced by a partial unique index so historical/inactive
        # accounts remain available for audit and future multi-account support.
        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_trading_accounts_user_active
        ON trading_accounts(user_id)
        WHERE is_active = 1
        """)

        # Non-destructive backfill from the existing DB-1 broker profile. Do not
        # copy password_encrypted: DB-3 deliberately has no credential column.
        cur.execute("""
        INSERT INTO trading_accounts
            (user_id, broker_profile_id, platform, account_number, broker_server,
             broker_name, currency, leverage, is_demo, connection_status, is_active)
        SELECT
            bp.user_id,
            bp.id,
            'MT5',
            bp.account_number,
            bp.broker_server,
            bp.broker_name,
            COALESCE(NULLIF(bp.currency, ''), 'USD'),
            bp.leverage,
            COALESCE(bp.is_demo, 1),
            'DISCONNECTED',
            1
        FROM broker_profiles bp
        WHERE bp.is_active = 1
          AND NOT EXISTS (
              SELECT 1
              FROM trading_accounts ta
              WHERE ta.broker_profile_id = bp.id
          )
          AND NOT EXISTS (
              SELECT 1
              FROM trading_accounts ta
              WHERE ta.user_id = bp.user_id
                AND ta.is_active = 1
          )
        """)

        cur.execute("""
        INSERT INTO schema_metadata(key, value)
        VALUES ('db_schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET
            value=CASE
                WHEN CAST(schema_metadata.value AS INTEGER) < CAST(excluded.value AS INTEGER)
                THEN excluded.value
                ELSE schema_metadata.value
            END,
            updated_at=CURRENT_TIMESTAMP
        """, (str(DB3_SCHEMA_VERSION),))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_db3()
    print("DB-3 migration complete")
