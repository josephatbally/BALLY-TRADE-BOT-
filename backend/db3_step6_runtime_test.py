"""DB-3 Step 6 tests for authenticated MT5 account resolution."""
from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from backend.trading_engine.trading_account_runtime import resolve_authenticated_trading_account


class FakeAccount:
    def __init__(self, login=123456, server="Broker-Demo", balance=100.0):
        self.login = login
        self.server = server
        self.company = "Broker"
        self.name = "Trader"
        self.leverage = 100
        self.currency = "USD"
        self.balance = balance
        self.equity = balance
        self.profit = 0.0
        self.margin = 0.0
        self.margin_free = balance


class DB3Step6RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.db_uri = f"file:db3_step6_{id(self)}?mode=memory&cache=shared"
        self.anchor = sqlite3.connect(self.db_uri, uri=True)
        self.anchor.row_factory = sqlite3.Row
        self.anchor.execute(
            """
            CREATE TABLE trading_accounts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                broker_server TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                currency TEXT NOT NULL,
                leverage INTEGER,
                is_demo INTEGER NOT NULL,
                platform TEXT NOT NULL,
                connection_status TEXT NOT NULL,
                is_active INTEGER NOT NULL
            )
            """
        )
        self.anchor.execute(
            """INSERT INTO trading_accounts
               (id,user_id,broker_server,broker_name,account_number,currency,
                leverage,is_demo,platform,connection_status,is_active)
               VALUES (1,1,'Broker-Demo','Broker','123456','USD',100,1,'MT5','DISCONNECTED',1)"""
        )
        self.anchor.commit()

    def tearDown(self):
        self.anchor.close()

    def _connection(self):
        conn = sqlite3.connect(self.db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def test_matching_mt5_identity_is_ready(self):
        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ), patch(
            "backend.trading_engine.trading_account_runtime.is_mt5_connected",
            return_value=True,
        ), patch(
            "backend.trading_engine.trading_account_runtime.get_account_info",
            return_value=FakeAccount(),
        ):
            resolved = resolve_authenticated_trading_account(1)

        self.assertEqual(resolved["status"], "READY")
        self.assertTrue(resolved["identity_match"])
        self.assertEqual(resolved["configured_account"]["id"], 1)

    def test_mismatched_mt5_identity_fails_closed(self):
        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ), patch(
            "backend.trading_engine.trading_account_runtime.is_mt5_connected",
            return_value=True,
        ), patch(
            "backend.trading_engine.trading_account_runtime.get_account_info",
            return_value=FakeAccount(login=999999),
        ):
            resolved = resolve_authenticated_trading_account(1)

        self.assertEqual(resolved["status"], "ACCOUNT_MISMATCH")
        self.assertFalse(resolved["identity_match"])

    def test_offline_mt5_does_not_use_sqlite_as_live_state(self):
        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ), patch(
            "backend.trading_engine.trading_account_runtime.is_mt5_connected",
            return_value=False,
        ):
            resolved = resolve_authenticated_trading_account(1)

        self.assertEqual(resolved["status"], "OFFLINE")
        self.assertIsNone(resolved["live_account"])

    def test_missing_tenant_account_is_not_routed_to_mt5(self):
        with patch(
            "backend.trading_engine.tenant_router.get_db_connection",
            side_effect=self._connection,
        ), patch(
            "backend.trading_engine.trading_account_runtime.is_mt5_connected",
        ) as connected:
            resolved = resolve_authenticated_trading_account(2)

        self.assertEqual(resolved["status"], "NO_ACCOUNT")
        self.assertFalse(resolved["identity_match"])
        connected.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
