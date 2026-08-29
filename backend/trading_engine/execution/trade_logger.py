
"""
BALLY TRADES BOT
TRADE LOGGER

Purpose
-------
Centralized execution/trading event logging.

Responsibilities
----------------
- Record execution events.
- Record validation events.
- Record MT5 order-check results.
- Record MT5 order-send results.
- Record blocked/rejected/failed execution events.
- Provide a simple in-memory event history.
- Never generate trading decisions.
- Never modify trading orders.
- Never authorize execution.
- Never call MT5 order_send().
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import threading


# ======================================================================
# LOGGER STATE
# ======================================================================

_MAX_EVENTS = 1000

_events: List[Dict[str, Any]] = []

_lock = threading.Lock()


# ======================================================================
# INTERNAL HELPERS
# ======================================================================

def _timestamp() -> str:
    """Return a UTC ISO-8601 timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def _safe_copy(value: Any) -> Any:
    """
    Convert common mutable values into safe logging representations.

    The logger must never mutate the caller's object.
    """

    if isinstance(value, dict):
        return {
            str(key): _safe_copy(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _safe_copy(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _safe_copy(item)
            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
            type(None),
        ),
    ):
        return value

    return str(value)


# ======================================================================
# EVENT RECORDING
# ======================================================================

def record_event(
    event: str,
    *,
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    order: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """
    Record one execution event.

    This function is logging-only.

    It does not:
        - make decisions
        - authorize execution
        - modify orders
        - call MT5
        - send trades
    """

    if not isinstance(event, str):
        event = str(event)

    record: Dict[str, Any] = {
        "timestamp": _timestamp(),
        "event": event,
        "status": status,
        "symbol": symbol,
        "decision": decision,
        "reason": reason,
    }

    if order is not None:
        record["order"] = _safe_copy(order)

    if result is not None:
        record["result"] = _safe_copy(result)

    if metadata:
        record["metadata"] = _safe_copy(metadata)

    with _lock:

        _events.append(record)

        if len(_events) > _MAX_EVENTS:
            del _events[
                :len(_events) - _MAX_EVENTS
            ]

    return _safe_copy(record)


# ======================================================================
# EXECUTION EVENT HELPERS
# ======================================================================

def record_validation(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    valid: bool = False,
    reason: Optional[str] = None,
    order: Optional[Dict[str, Any]] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record order-validation result."""

    return record_event(
        "ORDER_VALIDATION",
        status="READY" if valid else "BLOCKED",
        symbol=symbol,
        decision=decision,
        order=order,
        reason=reason,
        valid=bool(valid),
        **metadata,
    )


def record_authorization(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    authorized: bool = False,
    reason: Optional[str] = None,
    order: Optional[Dict[str, Any]] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record execution authorization result."""

    return record_event(
        "EXECUTION_AUTHORIZATION",
        status="AUTHORIZED"
        if authorized
        else "BLOCKED",
        symbol=symbol,
        decision=decision,
        order=order,
        reason=reason,
        authorized=bool(authorized),
        **metadata,
    )


def record_order_check(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    passed: bool = False,
    result: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record MT5 order_check result."""

    return record_event(
        "MT5_ORDER_CHECK",
        status="PASSED"
        if passed
        else "FAILED",
        symbol=symbol,
        decision=decision,
        result=result,
        reason=reason,
        passed=bool(passed),
        **metadata,
    )


def record_order_send(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    executed: bool = False,
    result: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record MT5 order_send result."""

    return record_event(
        "MT5_ORDER_SEND",
        status="EXECUTED"
        if executed
        else "REJECTED",
        symbol=symbol,
        decision=decision,
        result=result,
        reason=reason,
        executed=bool(executed),
        **metadata,
    )


def record_blocked(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    reason: Optional[str] = None,
    order: Optional[Dict[str, Any]] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record a blocked execution."""

    return record_event(
        "EXECUTION_BLOCKED",
        status="BLOCKED",
        symbol=symbol,
        decision=decision,
        order=order,
        reason=reason,
        **metadata,
    )


def record_rejected(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    reason: Optional[str] = None,
    order: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record a rejected execution."""

    return record_event(
        "EXECUTION_REJECTED",
        status="REJECTED",
        symbol=symbol,
        decision=decision,
        order=order,
        result=result,
        reason=reason,
        **metadata,
    )


def record_failure(
    *,
    symbol: Optional[str] = None,
    decision: Optional[str] = None,
    reason: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    **metadata: Any,
) -> Dict[str, Any]:
    """Record an execution failure."""

    return record_event(
        "EXECUTION_FAILED",
        status="FAILED",
        symbol=symbol,
        decision=decision,
        result=result,
        reason=reason,
        **metadata,
    )


# ======================================================================
# EVENT RETRIEVAL
# ======================================================================

def get_events(
    *,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Return recorded events.

    The returned data is copied so callers cannot mutate
    the logger's internal history.
    """

    with _lock:
        events = _safe_copy(_events)

    if limit is None:
        return events

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return events

    if limit <= 0:
        return []

    return events[-limit:]


def get_last_event() -> Optional[Dict[str, Any]]:
    """Return the most recent event."""

    with _lock:

        if not _events:
            return None

        return _safe_copy(
            _events[-1]
        )


def clear_events() -> None:
    """Clear the in-memory event history."""

    with _lock:
        _events.clear()


def event_count() -> int:
    """Return the number of stored events."""

    with _lock:
        return len(_events)


# ======================================================================
# LOGGER INFORMATION
# ======================================================================

def trade_logger_info() -> Dict[str, Any]:
    """Return logger capability information."""

    return {
        "name": "BALLY TRADES BOT Trade Logger",
        "version": "1.0.0",
        "status": "READY",
        "max_events": _MAX_EVENTS,
        "event_count": event_count(),
        "mt5_order_send": False,
        "decision_generation": False,
        "decision_override": False,
        "execution_authorization": False,
        "risk_management": False,
        "position_sizing": False,
        "technical_analysis": False,
        "fundamental_analysis": False,
        "logging_only": True,
    }


# ======================================================================
# COMPATIBILITY ALIASES
# ======================================================================

log_event = record_event
get_trade_events = get_events
clear_trade_events = clear_events


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    "record_event",
    "record_validation",
    "record_authorization",
    "record_order_check",
    "record_order_send",
    "record_blocked",
    "record_rejected",
    "record_failure",
    "get_events",
    "get_last_event",
    "clear_events",
    "event_count",
    "trade_logger_info",
    "log_event",
    "get_trade_events",
    "clear_trade_events",
]


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY TRADES BOT TRADE LOGGER")
    print("==============================================")

    print("INFO:")
    print(trade_logger_info())

    test_event = record_event(
        "LOGGER_SELF_TEST",
        status="READY",
        symbol="XAUUSD",
        decision="BUY",
        reason="logger self-test",
    )

    print("\nEVENT:")
    print(test_event)

    print("\nCOUNT:")
    print(event_count())

    print("\nLAST EVENT:")
    print(get_last_event())

    clear_events()

    print("\nAFTER CLEAR:")
    print(event_count())

    print("==============================================")
