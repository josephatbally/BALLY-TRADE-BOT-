"""
Appends close_position() and close_all_positions() to live_executor.py.
These are the ONLY places besides order_send that touch MT5 deals,
consistent with the architecture: live_executor owns all MT5 calls.
"""

path = "backend/trading_engine/execution/live_executor.py"

with open(path, "r", encoding="utf-8") as f:
    code = f.read()

if "def close_position" in code:
    print("[SKIP] close_position already exists.")
else:
    addition = '''

# ======================================================================
# POSITION CLOSING (owned by live_executor)
# ======================================================================

def close_position(ticket: int) -> Dict[str, Any]:
    """
    Close a single open position by ticket.
    Uses mt5.order_send with TRADE_ACTION_DEAL and position ticket.
    """
    if not MT5_AVAILABLE or mt5 is None:
        return {"status": "FAILED", "reason": "MT5 unavailable"}

    try:
        positions = mt5.positions_get(ticket=ticket)
    except Exception as exc:
        return {"status": "FAILED", "reason": f"positions_get exception: {exc}"}

    if not positions:
        return {"status": "FAILED", "reason": f"Position {ticket} not found"}

    pos = positions[0]

    close_type = (
        mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY
        else mt5.ORDER_TYPE_BUY
    )

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": close_type,
        "price": mt5.symbol_info_tick(pos.symbol).bid
        if close_type == mt5.ORDER_TYPE_SELL
        else mt5.symbol_info_tick(pos.symbol).ask,
        "deviation": 20,
        "magic": pos.magic,
        "comment": f"BALLY close #{ticket}",
        "type_time": mt5.ORDER_TIME_GTC,
    }

    try:
        result = mt5.order_send(request)
    except Exception as exc:
        return {"status": "FAILED", "reason": f"order_send exception: {exc}"}

    if result is None:
        return {"status": "FAILED", "reason": "order_send returned None"}

    retcode = getattr(result, "retcode", None)
    if retcode in (mt5.TRADE_RETCODE_DONE, 10009):
        return {
            "status": "OK",
            "ticket": ticket,
            "message": f"Position {ticket} closed",
        }

    return {
        "status": "FAILED",
        "retcode": retcode,
        "comment": getattr(result, "comment", "close rejected"),
    }


def close_all_positions() -> Dict[str, Any]:
    """
    Close every open position (emergency flush).
    """
    if not MT5_AVAILABLE or mt5 is None:
        return {"status": "FAILED", "reason": "MT5 unavailable"}

    try:
        positions = mt5.positions_get()
    except Exception as exc:
        return {"status": "FAILED", "reason": f"positions_get exception: {exc}"}

    if not positions:
        return {"status": "OK", "closed_count": 0, "message": "No positions to close"}

    closed = 0
    for pos in positions:
        res = close_position(pos.ticket)
        if res.get("status") == "OK":
            closed += 1

    return {
        "status": "OK",
        "closed_count": closed,
        "message": f"Closed {closed} of {len(positions)} positions",
    }
'''

    with open(path, "a", encoding="utf-8") as f:
        f.write(addition)
    print("[OK] close_position and close_all_positions appended to live_executor.py")
