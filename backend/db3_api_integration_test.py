"""DB-3 authenticated trading-account API integration tests.

These tests use an isolated shared in-memory SQLite database and override the
FastAPI authentication dependency. The real backend/bally_flow.db is never
opened for test writes.
"""
from __future__ import annotations

import sqlite3
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.api.app import app
from backend.security.jwt_auth import get_current_user


class DB3AuthenticatedAPIIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        # Use a unique shared-memory database per test. The anchor connection
        # keeps that database alive while production-style connections are
        # opened and closed by the patched get_db_connection functions.
        self.db_uri = f"file:db3_api_integration_test_{id(self)}?mode=memory&cache=shared"
        self.anchor = sqlite3.connect(self.db_uri, uri=True)
        self.anchor.row_factory = sqlite3.Row
        self._create_schema()
        self._seed_users()
        self.current_user = {"id": 1, "email": "user-a@ballyflow.test", "role": "trader", "status": "active"}

        def connection() -> sqlite3.Connection:
            conn = sqlite3.connect(self.db_uri, uri=True)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        self.connection = connection
        app.dependency_overrides[get_current_user] = lambda: self.current_user
        # trading_accounts routes use the persistence module's database
        # helper; auth routes use their own imported helper.
        self.patches = [
            patch("backend.trading_engine.trading_account_persistence.get_db_connection", side_effect=connection),
            patch("backend.api.routes.auth.get_db_connection", side_effect=connection),
        ]
        for item in self.patches:
            item.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.pop(get_current_user, None)
        for item in reversed(self.patches):
            item.stop()
        self.anchor.close()

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

            CREATE TABLE broker_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                broker_server TEXT NOT NULL,
                broker_name TEXT NOT NULL,
                account_number TEXT NOT NULL,
                password_encrypted TEXT,
                currency TEXT NOT NULL DEFAULT 'USD',
                leverage INTEGER,
                is_demo INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
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
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(broker_profile_id) REFERENCES broker_profiles(id) ON DELETE SET NULL
            );

            CREATE UNIQUE INDEX uq_trading_accounts_user_active
            ON trading_accounts(user_id) WHERE is_active = 1;
            """
        )
        self.anchor.commit()

    def _seed_users(self) -> None:
        self.anchor.execute(
            "INSERT INTO users (full_name,email,role,status) VALUES (?,?,?,?)",
            ("User A", "user-a@ballyflow.test", "trader", "active"),
        )
        self.anchor.execute(
            "INSERT INTO users (full_name,email,role,status) VALUES (?,?,?,?)",
            ("User B", "user-b@ballyflow.test", "trader", "active"),
        )
        self.anchor.commit()

    def _create_account_as(self, user_id: int) -> dict:
        self.current_user = {
            "id": user_id,
            "email": f"user-{chr(96 + user_id)}@ballyflow.test",
            "role": "trader",
            "status": "active",
        }
        response = self.client.post(
            "/api/v1/trading-accounts",
            json={
                "broker_server": "Demo-Server",
                "broker_name": "Demo Broker",
                "account_number": str(100000 + user_id),
                "platform": "MT5",
                "account_name": f"Account {user_id}",
                "currency": "USD",
                "leverage": 100,
                "is_demo": True,
                "password": "must-never-be-persisted",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["trading_account"]

    def test_authenticated_create_and_read_are_tenant_scoped(self) -> None:
        account_a = self._create_account_as(1)
        account_id = account_a["id"]

        own = self.client.get(f"/api/v1/trading-accounts/{account_id}")
        self.assertEqual(own.status_code, 200, own.text)
        self.assertEqual(own.json()["trading_account"]["user_id"], 1)

        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        cross = self.client.get(f"/api/v1/trading-accounts/{account_id}")
        self.assertEqual(cross.status_code, 404, cross.text)

        active_b = self.client.get("/api/v1/trading-accounts/active")
        self.assertEqual(active_b.status_code, 404, active_b.text)

        accounts_b = self.client.get("/api/v1/trading-accounts")
        self.assertEqual(accounts_b.status_code, 200, accounts_b.text)
        self.assertEqual(accounts_b.json()["count"], 0)

    def test_status_change_and_deactivation_are_tenant_scoped(self) -> None:
        account_a = self._create_account_as(1)
        account_id = account_a["id"]

        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        denied_status = self.client.patch(
            f"/api/v1/trading-accounts/{account_id}/status",
            json={"status": "CONNECTED"},
        )
        self.assertEqual(denied_status.status_code, 404, denied_status.text)

        denied_delete = self.client.delete(f"/api/v1/trading-accounts/{account_id}")
        self.assertEqual(denied_delete.status_code, 404, denied_delete.text)

        self.current_user = {"id": 1, "email": "user-a@ballyflow.test", "role": "trader", "status": "active"}
        changed = self.client.patch(
            f"/api/v1/trading-accounts/{account_id}/status",
            json={"status": "CONNECTED"},
        )
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["trading_account"]["connection_status"], "CONNECTED")

        active = self.client.get("/api/v1/trading-accounts/active")
        self.assertEqual(active.status_code, 200, active.text)
        self.assertEqual(active.json()["trading_account"]["id"], account_id)

        deleted = self.client.delete(f"/api/v1/trading-accounts/{account_id}")
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(self.client.get("/api/v1/trading-accounts/active").status_code, 404)

        row = self.anchor.execute(
            "SELECT is_active, connection_status FROM trading_accounts WHERE id=?",
            (account_id,),
        ).fetchone()
        self.assertEqual(tuple(row), (0, "DISCONNECTED"))

    def test_credentials_are_not_stored_in_trading_accounts(self) -> None:
        account = self._create_account_as(1)
        self.assertNotIn("password", account)
        self.assertNotIn("password_encrypted", account)

        columns = [row[1] for row in self.anchor.execute("PRAGMA table_info(trading_accounts)")]
        self.assertNotIn("password", columns)
        self.assertNotIn("password_encrypted", columns)

    def test_legacy_broker_profile_fallback_remains_available(self) -> None:
        self.anchor.execute(
            """
            INSERT INTO broker_profiles
            (user_id, broker_server, broker_name, account_number, password_encrypted,
             currency, leverage, is_demo, is_active)
            VALUES (?,?,?,?,?,?,?,?,1)
            """,
            (2, "Legacy-Server", "Legacy Broker", "222222", "legacy-secret", "USD", 200, 1),
        )
        self.anchor.commit()

        self.current_user = {"id": 2, "email": "user-b@ballyflow.test", "role": "trader", "status": "active"}
        response = self.client.get("/api/v1/auth/me")
        self.assertEqual(response.status_code, 200, response.text)
        broker = response.json()["broker"]
        self.assertEqual(broker["broker_server"], "Legacy-Server")
        self.assertEqual(broker["account_number"], "222222")
        self.assertNotIn("password_encrypted", broker)


if __name__ == "__main__":
    unittest.main(verbosity=2)
