"""BALLY FLOW - Durable DB-2 trading persistence.

DB-2 persists the trading lifecycle without replacing live MT5 state.

Lifecycle
---------
Trade Intent -> Trade Plan -> Order -> Execution/Deal -> Position -> Close
-> Final Trade Outcome

SQLite is the durable historical/application store. MT5 remains authoritative
for live account, position, market, and broker state.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from backend.database import get_db_connection


def _json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, default=str, separators=(",", ":"))


def _row_dict(row: Any) -> Optional[Dict[str, Any]]:
    return dict(row) if row is not None else None


def create_trade_plan_record(
    *,
    user_id: Optional[int],
    symbol: str,
    decision: str,
    timeframe: str = "M15",
    entry: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    volume: Optional[float] = None,
    risk_percent: Optional[float] = None,
    risk_amount: Optional[float] = None,
    risk_reward: Optional[float] = None,
    opportunity_score: Optional[float] = None,
    market_context: Optional[Dict[str, Any]] = None,
    structural_context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    status: str = "READY",
    conn: Any = None,
) -> Dict[str, Any]:
    """Persist one authoritative trade plan.

    When ``conn`` is supplied, the caller owns the transaction. The helper
    will not commit or close that connection.
    """
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO trade_plans (
                user_id, symbol, decision, timeframe, entry, stop_loss,
                take_profit, volume, risk_percent, risk_amount, risk_reward,
                opportunity_score, market_context_json, structural_context_json,
                metadata_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, symbol, decision, timeframe, entry, stop_loss,
                take_profit, volume, risk_percent, risk_amount, risk_reward,
                opportunity_score, _json(market_context),
                _json(structural_context), _json(metadata), status,
            ),
        )
        if own_connection:
            conn.commit()
        row = conn.execute(
            "SELECT * FROM trade_plans WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _row_dict(row) or {}
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def create_order_record(
    *,
    user_id: Optional[int],
    trade_plan_id: Optional[int],
    symbol: str,
    action: str,
    volume: float,
    magic_number: Optional[int] = None,
    mt5_order_ticket: Optional[int] = None,
    price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    comment: Optional[str] = None,
    status: str = "SUBMITTED",
    broker_retcode: Optional[int] = None,
    request_json: Optional[Dict[str, Any]] = None,
    response_json: Optional[Dict[str, Any]] = None,
    conn: Any = None,
) -> Dict[str, Any]:
    """Persist an order/request and its broker-facing identifiers."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO orders (
                user_id, trade_plan_id, symbol, action, volume, magic_number,
                mt5_order_ticket, price, stop_loss, take_profit, comment, status,
                broker_retcode, request_json, response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, trade_plan_id, symbol, action, volume, magic_number,
                mt5_order_ticket, price, stop_loss, take_profit, comment, status,
                broker_retcode, _json(request_json), _json(response_json),
            ),
        )
        if own_connection:
            conn.commit()
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_dict(row) or {}
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def create_execution_record(
    *,
    order_id: Optional[int],
    user_id: Optional[int],
    symbol: str,
    action: str,
    deal_ticket: Optional[int] = None,
    order_ticket: Optional[int] = None,
    position_ticket: Optional[int] = None,
    volume: Optional[float] = None,
    price: Optional[float] = None,
    commission: Optional[float] = None,
    swap: Optional[float] = None,
    profit: Optional[float] = None,
    broker_retcode: Optional[int] = None,
    status: str = "EXECUTED",
    response_json: Optional[Dict[str, Any]] = None,
    conn: Any = None,
) -> Dict[str, Any]:
    """Persist one broker execution/deal."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO executions (
                order_id, user_id, symbol, action, deal_ticket, order_ticket,
                position_ticket, volume, price, commission, swap, profit,
                broker_retcode, status, response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id, user_id, symbol, action, deal_ticket, order_ticket,
                position_ticket, volume, price, commission, swap, profit,
                broker_retcode, status, _json(response_json),
            ),
        )
        if own_connection:
            conn.commit()
        row = conn.execute("SELECT * FROM executions WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_dict(row) or {}
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def create_trade_record(
    *,
    user_id: Optional[int],
    trade_plan_id: Optional[int],
    order_id: Optional[int],
    symbol: str,
    direction: str,
    position_ticket: Optional[int] = None,
    volume: Optional[float] = None,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    opened_at: Optional[str] = None,
    close_price: Optional[float] = None,
    closed_at: Optional[str] = None,
    gross_profit: Optional[float] = None,
    commission: Optional[float] = None,
    swap: Optional[float] = None,
    net_profit: Optional[float] = None,
    outcome: Optional[str] = None,
    status: str = "OPEN",
    metadata: Optional[Dict[str, Any]] = None,
    conn: Any = None,
) -> Dict[str, Any]:
    """Persist the durable trade/position outcome record."""
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO trade_records (
                user_id, trade_plan_id, order_id, symbol, direction,
                position_ticket, volume, entry_price, stop_loss, take_profit,
                opened_at, close_price, closed_at, gross_profit, commission,
                swap, net_profit, outcome, status, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, trade_plan_id, order_id, symbol, direction,
                position_ticket, volume, entry_price, stop_loss, take_profit,
                opened_at, close_price, closed_at, gross_profit, commission,
                swap, net_profit, outcome, status, _json(metadata),
            ),
        )
        if own_connection:
            conn.commit()
        row = conn.execute("SELECT * FROM trade_records WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_dict(row) or {}
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def update_order_record(
    order_id: int, *, conn: Any = None, **fields: Any
) -> Optional[Dict[str, Any]]:
    """Update permitted durable order fields."""
    allowed = {
        "mt5_order_ticket", "status", "broker_retcode", "price", "response_json"
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if "response_json" in updates:
        updates["response_json"] = _json(updates["response_json"])
    if not updates:
        return get_order_record(order_id, conn=conn)

    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        assignments = ", ".join(f"{key} = ?" for key in updates)
        conn.execute(
            f"UPDATE orders SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id = ?",
            (*updates.values(), order_id),
        )
        if own_connection:
            conn.commit()
        return get_order_record(order_id, conn=conn)
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def update_trade_record(
    trade_record_id: int, *, conn: Any = None, **fields: Any
) -> Optional[Dict[str, Any]]:
    """Update close/outcome fields on a durable trade record."""
    allowed = {
        "position_ticket", "close_price", "closed_at", "gross_profit",
        "commission", "swap", "net_profit", "outcome", "status", "metadata_json"
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if "metadata_json" in updates and not isinstance(updates["metadata_json"], str):
        updates["metadata_json"] = _json(updates["metadata_json"])
    if not updates:
        return get_trade_record(trade_record_id, conn=conn)

    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        assignments = ", ".join(f"{key} = ?" for key in updates)
        conn.execute(
            f"UPDATE trade_records SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id = ?",
            (*updates.values(), trade_record_id),
        )
        if own_connection:
            conn.commit()
        return get_trade_record(trade_record_id, conn=conn)
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        if own_connection:
            conn.close()


def get_order_record(order_id: int, *, conn: Any = None) -> Optional[Dict[str, Any]]:
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        return _row_dict(conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone())
    finally:
        if own_connection:
            conn.close()


def get_trade_record(trade_record_id: int, *, conn: Any = None) -> Optional[Dict[str, Any]]:
    own_connection = conn is None
    if own_connection:
        conn = get_db_connection()
    try:
        return _row_dict(conn.execute("SELECT * FROM trade_records WHERE id = ?", (trade_record_id,)).fetchone())
    finally:
        if own_connection:
            conn.close()


__all__ = [
    "create_trade_plan_record",
    "create_order_record",
    "create_execution_record",
    "create_trade_record",
    "update_order_record",
    "update_trade_record",
    "get_order_record",
    "get_trade_record",
]
