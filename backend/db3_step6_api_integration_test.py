"""DB-3 Step 6 authenticated runtime API integration tests.

These tests exercise the real FastAPI route layer while mocking only the MT5
runtime boundary and the authenticated user. SQLite is isolated in memory and
never touches backend/bally_flow.db.
"""
from __future__ import annotations

import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.security.jwt_auth import get_current_user


class DB3Step6APIIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.db_uri = f"file:db3_step6_api_{id(self)}?mode=memory&cache=shared"
        self.anchor = sqlite3.connect(self.db_uri, uri=True, check_same_thread=False)
        self.anchor.row_factory = sqlite3.Row
        self._create_schema()
        self._seed_users()
        self.current_user = {"id": 1, "email": "user-a@ballyflow.test", "role": "trader", "status": "active"}
        self.client = TestClient(app)
        app.dependency_overrides[get_current_user] = lambda: self.current_user

        self.patches = []
        self._start_patch(
            "backend.trading_engine.trading_account_persistence.get_db_connection",
            self._connection,
        )
        self._start_patch(
            "backend.api.routes.auth.get_db_connection",
            self._connection,
        )
        self._start_patch(
            "backend.api.routes.account.resolve_authenticated_trading_account",
            self._resolve_account,
        )
        self._start_patch(
            "backend.api.routes.account.get_positions",
            self._live_positions,
        )
        self._start_patch(
            "backend.api.routes.positions.get_authenticated_trading_account",
            self._get_account,
        )
        self._start_patch(
            "backend.api.routes.positions.is_mt5_connected",
            lambda: True,
        )
        self._start_patch(
            "backend.api.routes.positions.get_positions",
            self._live_positions,
        )
        self._start_patch(
            "backend.api.routes.positions.tenant_router.filter_user_positions",
            self._filter_positions,
        )
        self._start_patch(
            "backend.api.routes.orders.resolve_authenticated_trading_account",
            self._resolve_account,
        )
        self._start_patch(
            "backend.api.routes.orders.tenant_router.get_user_order_tickets",
            self._owned_tickets,
        )
        self._start_patch(
            "backend.api.routes.orders.close_position",
            self._close_position,
        )
        self.closed_tickets = []

    def tearDown(self) -> None:
        app.dependency_overrides.pop(get_current_user, None)
        for item in reversed(self.patches):
            item.stop()
        self.client.close()
        self.anchor.close()

    def _start_patch(self, target: str, value) -> None:
        patcher = patch(target, side_effect=value if callable(value) else None)
        if not callable(value):
            patcher = patch(target, value=value)
        patcher.start()
        self.patches.append(patcher)

    def _connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_schema(self) -> None:
        self.anchor.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT,
                email TEXT NOT NULL,
                phone TEXT,
                country_code TEXT,
                role TEXT NOT NULL DEFAULT 'trader',
                status TEXT NOT NULL DEFAULT 'active',
                email_verified INTEGER NOT NULL DEFAULT 1,
                phone_verified INTEGER NOT NULL DEFAULT 0
            );

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
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE UNIQUE INDEX uq_trading_accounts_user_active
            ON trading_accounts(user_id) WHERE is_active = 1;
            """
        )
        self.anchor.commit()

    def _seed_users(self) -> None:
        self.anchor.executemany(
            "INSERT INTO users (full_name,email,role,status) VALUES (?,?,?,?)",
            [
                ("User A", "user-a@ballyflow.test", "trader", "active"),
                ("User B", "user-b@ballyflow.test", "trader", "active"),
            ],
        )
        self.anchor.executemany(
            """
            INSERT INTO trading_accounts
            (user_id, account_number, account_name, broker_server, broker_name,
             currency, leverage, is_demo, connection_status, is_active)
            VALUES (?,?,?,?,?,?,?,?,?,1)
            """,
            [
                (1, "111111", "User A MT5", "Broker-A", "Broker A", "USD", 100, 1, "CONNECTED"),
                (2, "222222", "User B MT5", "Broker-B", "Broker B", "USD", 200, 1, "CONNECTED"),
            ],
        )
        self.anchor.commit()

    def _account_row(self, user_id: int) -> dict | None:
        row = self.anchor.execute(
            "SELECT * FROM trading_accounts WHERE user_id=? AND is_active=1",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None

    def _get_account(self, user_id: int) -> dict | None:
        return self._account_row(user_id)

    def _live_account(self, user_id: int) -> SimpleNamespace:
        row = self._account_row(user_id)
        return SimpleNamespace(
            login=int(row["account_number"]),
            server=row["broker_server"],
            company=row["broker_name"],
            name=row["account_name"],
            leverage=row["leverage"],
            currency=row["currency"],
            balance=1000.0 + user_id,
            equity=995.0 + user_id,
            profit=-5.0,
            margin=100.0,
            margin_free=895.0 + user_id,
        )

    def _resolve_account(self, user_id: int) -> dict:
        row = self._account_row(user_id)
        if not row:
            return {
                "status": "NO_ACCOUNT",
                "configured_account": None,
                "live_account": None,
                "identity_match": False,
            }
        return {
            "status": "READY",
            "configured_account": row,
            "live_account": self._live_account(user_id),
            "identity_match": True,
        }

    def _live_positions(self):
        return [
            SimpleNamespace(ticket=101, symbol="EURUSD", type=0, volume=0.10,
                            price_open=1.1000, price_current=1.1010, sl=1.0950,
                            tp=1.1100, profit=10.0, swap=0.0, magic=1,
                            comment="USER_A", time=1750000000),
            SimpleNamespace(ticket=202, symbol="XAUUSD", type=1, volume=0.20,
                            price_open=3400.0, price_current=3398.0, sl=3410.0,
                            tp=3380.0, profit=20.0, swap=0.0, magic=2,
                            comment="USER_B", time=1750000001),
        ]

    def _owned_tickets(self, user_id: int):
        return [101] if user_id == 1 else [202]

    def _filter_positions(self, user_id: int, positions):
        owned = set(self._owned_tickets(user_id))
        return [p for p in positions if int(p.get("ticket", 0)) in owned]

    def _close_position(self, ticket: int):
        self.closed_tickets.append(ticket)
        return {"closed": True, "ticket": ticket}

    def test_account_endpoint_uses_authenticated_tenant_and_matching_mt5_identity(self) -> None:
        response_a = self.client.get("/api/v1/account")
        self.assertEqual(response_a.status_code, 200, response_a.text)
        data_a = response_a.json()
        self.assertEqual(data_a["status"], "READY")
        self.assertEqual(data_a["account"]["trading_account_id"], 1)
        self.assertEqual(data_a["account"]["account_number"], "111111")
        self.assertEqual(data_a["broker"]["server"], "Broker-A")
        self.assertEqual(data_a["balance"], 1001.0)

        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        response_b = self.client.get("/api/v1/account")
        self.assertEqual(response_b.status_code, 200, response_b.text)
        data_b = response_b.json()
        self.assertEqual(data_b["account"]["trading_account_id"], 2)
        self.assertEqual(data_b["account"]["account_number"], "222222")
        self.assertEqual(data_b["broker"]["server"], "Broker-B")
        self.assertEqual(data_b["balance"], 1002.0)

    def test_positions_are_filtered_to_authenticated_tenant(self) -> None:
        response_a = self.client.get("/api/v1/positions")
        self.assertEqual(response_a.status_code, 200, response_a.text)
        data_a = response_a.json()
        self.assertEqual(data_a["count"], 1)
        self.assertEqual(data_a["positions"][0]["ticket"], 101)

        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        response_b = self.client.get("/api/v1/positions")
        self.assertEqual(response_b.status_code, 200, response_b.text)
        data_b = response_b.json()
        self.assertEqual(data_b["count"], 1)
        self.assertEqual(data_b["positions"][0]["ticket"], 202)

    def test_close_position_denies_cross_tenant_ticket_before_mt5_close(self) -> None:
        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        denied = self.client.post("/api/v1/orders/close/101")
        self.assertEqual(denied.status_code, 404, denied.text)
        self.assertEqual(self.closed_tickets, [])

        allowed = self.client.post("/api/v1/orders/close/202")
        self.assertEqual(allowed.status_code, 200, allowed.text)
        self.assertEqual(allowed.json()["ticket"], 202)
        self.assertEqual(self.closed_tickets, [202])

    def test_execute_requires_authenticated_account_ready_before_analysis(self) -> None:
        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        self._start_patch(
            "backend.api.routes.orders._authoritative_analysis",
            lambda symbol: (_ for _ in ()).throw(AssertionError("analysis must not run before runtime account check")),
        )
        self._start_patch(
            "backend.api.routes.orders.resolve_authenticated_trading_account",
            lambda user_id: {
                "status": "ACCOUNT_MISMATCH",
                "configured_account": self._account_row(user_id),
                "live_account": None,
                "identity_match": False,
            },
        )
        response = self.client.post(
            "/api/v1/orders/execute",
            json={"symbol": "EURUSD", "action": "BUY", "lot_size": 0.01},
        )
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("ACCOUNT_MISMATCH", response.text)

    def test_missing_account_fails_closed_for_account_and_execution(self) -> None:
        self.current_user = {"id": 999, "email": "missing@ballyflow.test", "role": "trader", "status": "active"}
        account = self.client.get("/api/v1/account")
        self.assertEqual(account.status_code, 200, account.text)
        self.assertEqual(account.json()["status"], "NO_ACCOUNT")
        self.assertIsNone(account.json()["account"])

        execute = self.client.post(
            "/api/v1/orders/execute",
            json={"symbol": "EURUSD", "action": "BUY", "lot_size": 0.01},
        )
        self.assertEqual(execute.status_code, 409, execute.text)
        self.assertIn("No active trading account", execute.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
