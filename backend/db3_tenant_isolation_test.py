"""DB-3 tenant routing isolation test using an isolated in-memory database.

This test never opens backend/bally_flow.db and never creates persistent users,
accounts, or orders in the application database.
"""
from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from backend.trading_engine.tenant_router import TenantRouter


class DB3TenantIsolationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE trading_accounts (
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
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE broker_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                broker_server TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                currency TEXT DEFAULT 'USD',
                leverage INTEGER DEFAULT 100,
                is_demo INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1
            );

            CREATE TABLE user_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticket INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                lot_size REAL NOT NULL,
                status TEXT NOT NULL,
                magic_number INTEGER
            );
            """
        )
        self.router = TenantRouter()

    def tearDown(self) -> None:
        self.conn.close()

    def _connection(self):
        return self.conn

    def test_active_trading_account_is_primary_and_user_scoped(self) -> None:
        self.conn.execute(
            """
            INSERT INTO trading_accounts
                (user_id, broker_profile_id, account_number, broker_server, broker_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (101, 11, "1010001", "BrokerA-MT5", "Broker A"),
        )
        self.conn.execute(
            """
            INSERT INTO trading_accounts
                (user_id, broker_profile_id, account_number, broker_server, broker_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (202, 22, "2020002", "BrokerB-MT5", "Broker B"),
        )
        self.conn.commit()

        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ):
            account_a = self.router.get_user_trading_account(101)
            route_a = self.router.get_user_broker_profile(101)
            account_b = self.router.get_user_trading_account(202)

        self.assertEqual(account_a["user_id"], 101)
        self.assertEqual(account_a["account_number"], "1010001")
        self.assertEqual(route_a["trading_account_id"], account_a["id"])
        self.assertEqual(route_a["broker_server"], "BrokerA-MT5")
        self.assertEqual(account_b["user_id"], 202)
        self.assertEqual(account_b["account_number"], "2020002")
        self.assertNotEqual(account_a["account_number"], account_b["account_number"])

    def test_legacy_broker_profile_remains_fallback(self) -> None:
        self.conn.execute(
            """
            INSERT INTO broker_profiles
                (user_id, broker_server, broker_name, account_number)
            VALUES (?, ?, ?, ?)
            """,
            (303, "Legacy-MT5", "Legacy Broker", "3030003"),
        )
        self.conn.commit()

        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ):
            route = self.router.get_user_broker_profile(303)

        self.assertEqual(route["user_id"], 303)
        self.assertEqual(route["account_number"], "3030003")
        self.assertIsNone(route["trading_account_id"])
        self.assertEqual(route["platform"], "MT5")

    def test_positions_fail_closed_when_tenant_has_no_orders(self) -> None:
        live_positions = [
            {"ticket": 9001, "symbol": "XAUUSD"},
            {"ticket": 9002, "symbol": "EURUSD"},
        ]
        self.conn.execute(
            """
            INSERT INTO user_orders
                (user_id, ticket, symbol, action, lot_size, status, magic_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (101, 9001, "XAUUSD", "BUY", 0.01, "SUBMITTED", 100001),
        )
        self.conn.commit()

        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ):
            user_a = self.router.filter_user_positions(101, live_positions)
            user_b = self.router.filter_user_positions(202, live_positions)
            admin = self.router.filter_user_positions(None, live_positions)

        self.assertEqual([p["ticket"] for p in user_a], [9001])
        self.assertEqual(user_b, [])
        self.assertEqual([p["ticket"] for p in admin], [9001, 9002])


if __name__ == "__main__":
    unittest.main(verbosity=2)
