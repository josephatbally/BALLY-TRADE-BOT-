"""BALLY FLOW - DB-3 trading-account persistence helpers.

DB-3 separates a user's durable MT5 trading-account identity from the
legacy DB-1 broker_profiles metadata. These helpers always scope reads and
writes by user_id so an authenticated tenant cannot address another user's
account by numeric ID alone.

Credential data is intentionally not accepted or stored here.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.database import get_db_connection


_ALLOWED_STATUS = {
    "DISCONNECTED",
    "CONNECTING",
    "CONNECTED",
    "ERROR",
}


def _row_dict(row: Any) -> Optional[Dict[str, Any]]:
    return dict(row) if row is not None else None


def create_trading_account(
    *,
    user_id: int,
    account_number: str,
    broker_server: str,
    broker_name: str,
    broker_profile_id: Optional[int] = None,
    platform: str = "MT5",
    account_name: Optional[str] = None,
    currency: str = "USD",
    leverage: Optional[int] = None,
    is_demo: bool = True,
    connection_status: str = "DISCONNECTED",
    conn: Any = None,
) -> Dict[str, Any]:
    """Create one active trading account for a user.

    The database partial unique index enforces the one-active-account rule.
    This helper never accepts a password or other credential value.
    """
    user_id = int(user_id)
    if connection_status not in _ALLOWED_STATUS:
        raise ValueError(f"Unsupported connection_status: {connection_status}")

    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO trading_accounts (
                user_id, broker_profile_id, platform, account_number,
                account_name, broker_server, broker_name, currency, leverage,
                is_demo, connection_status, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                user_id,
                broker_profile_id,
                platform.strip().upper(),
                account_number.strip(),
                account_name.strip() if account_name else None,
                broker_server.strip(),
                broker_name.strip(),
                currency.strip().upper() or "USD",
                leverage,
                1 if is_demo else 0,
                connection_status,
            ),
        )
        if own_connection:
            conn.commit()
        row = conn.execute(
            "SELECT * FROM trading_accounts WHERE id = ? AND user_id = ?",
            (cur.lastrowid, user_id),
        ).fetchone()
        return _row_dict(row) or {}
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def get_active_trading_account(
    user_id: int, *, conn: Any = None
) -> Optional[Dict[str, Any]]:
    """Return only the authenticated user's active trading account."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM trading_accounts
            WHERE user_id = ? AND is_active = 1
            ORDER BY id DESC LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        return _row_dict(row)
    finally:
        if own_connection:
            conn.close()


def list_trading_accounts(
    user_id: int, *, include_inactive: bool = True, conn: Any = None
) -> List[Dict[str, Any]]:
    """List only accounts owned by the authenticated user."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        if include_inactive:
            rows = conn.execute(
                """
                SELECT * FROM trading_accounts
                WHERE user_id = ?
                ORDER BY is_active DESC, id DESC
                """,
                (int(user_id),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM trading_accounts
                WHERE user_id = ? AND is_active = 1
                ORDER BY id DESC
                """,
                (int(user_id),),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        if own_connection:
            conn.close()


def get_trading_account(
    user_id: int, account_id: int, *, conn: Any = None
) -> Optional[Dict[str, Any]]:
    """Fetch an account only when both account_id and user_id match."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        row = conn.execute(
            """
            SELECT * FROM trading_accounts
            WHERE id = ? AND user_id = ?
            LIMIT 1
            """,
            (int(account_id), int(user_id)),
        ).fetchone()
        return _row_dict(row)
    finally:
        if own_connection:
            conn.close()


def update_trading_account_status(
    user_id: int,
    account_id: int,
    status: str,
    *,
    last_connected_at: Optional[str] = None,
    conn: Any = None,
) -> Optional[Dict[str, Any]]:
    """Update connection state only for the authenticated user's account."""
    if status not in _ALLOWED_STATUS:
        raise ValueError(f"Unsupported connection_status: {status}")

    if status == "CONNECTED" and last_connected_at is None:
        last_connected_at = datetime.now(timezone.utc).isoformat()

    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        conn.execute(
            """
            UPDATE trading_accounts
            SET connection_status = ?,
                last_connected_at = CASE
                    WHEN ? = 'CONNECTED' THEN ?
                    ELSE last_connected_at
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (
                status,
                status,
                last_connected_at,
                int(account_id),
                int(user_id),
            ),
        )
        if own_connection:
            conn.commit()
        return get_trading_account(user_id, account_id, conn=conn)
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def deactivate_trading_account(
    user_id: int, account_id: int, *, conn: Any = None
) -> bool:
    """Deactivate only the authenticated user's specified account."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            UPDATE trading_accounts
            SET is_active = 0,
                connection_status = 'DISCONNECTED',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ? AND is_active = 1
            """,
            (int(account_id), int(user_id)),
        )
        if own_connection:
            conn.commit()
        return cur.rowcount == 1
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


__all__ = [
    "create_trading_account",
    "get_active_trading_account",
    "list_trading_accounts",
    "get_trading_account",
    "update_trading_account_status",
    "deactivate_trading_account",
]
