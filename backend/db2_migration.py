"""BALLY FLOW - DB-2 trading persistence migration.

DB-2 adds durable trade lifecycle tables while preserving every DB-1 table.
MT5 remains the source of truth for live state.
"""
from __future__ import annotations

from backend.database import get_db_connection

DB2_SCHEMA_VERSION = 2


def migrate_db2() -> None:
    """Apply the DB-2 migration idempotently and non-destructively."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trade_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            decision TEXT NOT NULL,
            timeframe TEXT NOT NULL DEFAULT 'M15',
            entry REAL,
            stop_loss REAL,
            take_profit REAL,
            volume REAL,
            risk_percent REAL,
            risk_amount REAL,
            risk_reward REAL,
            opportunity_score REAL,
            market_context_json TEXT,
            structural_context_json TEXT,
            metadata_json TEXT,
            status TEXT NOT NULL DEFAULT 'READY',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trade_plan_id INTEGER,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            volume REAL NOT NULL,
            magic_number INTEGER,
            mt5_order_ticket INTEGER,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            comment TEXT,
            status TEXT NOT NULL DEFAULT 'SUBMITTED',
            broker_retcode INTEGER,
            request_json TEXT,
            response_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (trade_plan_id) REFERENCES trade_plans(id) ON DELETE SET NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            deal_ticket INTEGER,
            order_ticket INTEGER,
            position_ticket INTEGER,
            volume REAL,
            price REAL,
            commission REAL,
            swap REAL,
            profit REAL,
            broker_retcode INTEGER,
            status TEXT NOT NULL DEFAULT 'EXECUTED',
            response_json TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trade_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trade_plan_id INTEGER,
            order_id INTEGER,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            position_ticket INTEGER,
            volume REAL,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            opened_at TIMESTAMP,
            close_price REAL,
            closed_at TIMESTAMP,
            gross_profit REAL,
            commission REAL,
            swap REAL,
            net_profit REAL,
            outcome TEXT,
            status TEXT NOT NULL DEFAULT 'OPEN',
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (trade_plan_id) REFERENCES trade_plans(id) ON DELETE SET NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
        )""")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trade_plans_user_created ON trade_plans(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trade_plans_symbol_created ON trade_plans(symbol, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trade_plans_status ON trade_plans(status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_created_v2 ON orders(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_plan ON orders(trade_plan_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_mt5_ticket ON orders(mt5_order_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_executions_user_time ON executions(user_id, executed_at)",
            "CREATE INDEX IF NOT EXISTS idx_executions_order ON executions(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_executions_deal_ticket ON executions(deal_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_executions_position_ticket ON executions(position_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_trade_records_user_created ON trade_records(user_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trade_records_position ON trade_records(position_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_trade_records_status ON trade_records(status)",
            "CREATE INDEX IF NOT EXISTS idx_trade_records_symbol ON trade_records(symbol, created_at)",
        ]
        for statement in indexes:
            cur.execute(statement)

        cur.execute("""
        INSERT INTO schema_metadata(key, value)
        VALUES ('db_schema_version', ?)
        ON CONFLICT(key) DO UPDATE SET
            value=excluded.value,
            updated_at=CURRENT_TIMESTAMP
        """, (str(DB2_SCHEMA_VERSION),))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_db2()
    print("DB-2 migration complete")
