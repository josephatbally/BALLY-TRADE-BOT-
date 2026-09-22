"""
BALLY FLOW - Multi-Tenant MT5 Routing Engine (Phase 3)

Manages multi-user isolation, routes authenticated users to their durable
trading-account identity, and preserves broker_profiles as a compatibility
fallback for older records.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.database import get_db_connection


class TenantRouter:
    """
    Multi-tenant trade router.

    DB-3 makes trading_accounts the primary tenant routing record. The legacy
    broker_profiles table remains a read-only compatibility fallback so older
    users/data continue to work during the transition.
    """

    def get_user_trading_account(
        self, user_id: int | str
    ) -> Optional[Dict[str, Any]]:
        """Return the authenticated user's active DB-3 trading account only."""
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT *
                FROM trading_accounts
                WHERE user_id = ? AND is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user_id),),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_broker_profile(
        self, user_id: int | str
    ) -> Optional[Dict[str, Any]]:
        """Return tenant routing metadata with DB-3 as the primary source.

        The return shape intentionally preserves the legacy broker-profile
        fields used by existing callers. If no DB-3 trading account exists,
        the active DB-1 broker profile is returned as a compatibility fallback.
        """
        trading_account = self.get_user_trading_account(user_id)
        if trading_account:
            return {
                "id": trading_account.get("broker_profile_id") or trading_account.get("id"),
                "trading_account_id": trading_account.get("id"),
                "user_id": trading_account.get("user_id"),
                "broker_server": trading_account.get("broker_server"),
                "broker_name": trading_account.get("broker_name"),
                "account_number": trading_account.get("account_number"),
                "currency": trading_account.get("currency"),
                "leverage": trading_account.get("leverage"),
                "is_demo": trading_account.get("is_demo"),
                "is_active": trading_account.get("is_active"),
                "platform": trading_account.get("platform"),
                "connection_status": trading_account.get("connection_status"),
                "last_connected_at": trading_account.get("last_connected_at"),
            }

        # DB-1 compatibility path for users whose legacy broker profile has
        # not yet been represented in trading_accounts.
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT id, user_id, broker_server, broker_name, account_number,
                       currency, leverage, is_demo, is_active
                FROM broker_profiles
                WHERE user_id = ? AND is_active = 1
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(user_id),),
            ).fetchone()
            if not row:
                return None
            result = dict(row)
            result["trading_account_id"] = None
            result["platform"] = "MT5"
            result["connection_status"] = "DISCONNECTED"
            result["last_connected_at"] = None
            return result
        finally:
            conn.close()

    def record_user_order(
        self,
        user_id: int | str,
        ticket: int,
        symbol: str,
        action: str,
        lot_size: float,
        status: str = "SUBMITTED",
        magic_number: int = 100001,
    ) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO user_orders (user_id, ticket, symbol, action, lot_size, status, magic_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    int(ticket),
                    symbol.upper(),
                    action.upper(),
                    float(lot_size),
                    status,
                    magic_number,
                ),
            )
            conn.commit()
            return True
        except Exception as exc:
            print(f"[TENANT ROUTER] Failed to record user order: {exc}")
            return False
        finally:
            conn.close()

    def get_user_order_tickets(self, user_id: int | str) -> List[int]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT ticket FROM user_orders WHERE user_id = ?", (int(user_id),)
            )
            rows = cursor.fetchall()
            return [int(r["ticket"]) for r in rows]
        finally:
            conn.close()

    def filter_user_positions(
        self,
        user_id: Optional[int | str],
        live_positions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Filter live positions for a tenant.

        ``None`` remains the explicit administrative/unscoped path. An
        authenticated tenant with no recorded tickets receives no positions;
        returning every live position would violate tenant isolation.
        """
        if not user_id:
            return live_positions

        user_tickets = set(self.get_user_order_tickets(user_id))
        if not user_tickets:
            return []

        filtered = []
        for pos in live_positions:
            ticket = (
                pos.get("ticket")
                if isinstance(pos, dict)
                else getattr(pos, "ticket", None)
            )
            if ticket in user_tickets or str(ticket) in user_tickets:
                filtered.append(pos)

        return filtered


tenant_router = TenantRouter()
