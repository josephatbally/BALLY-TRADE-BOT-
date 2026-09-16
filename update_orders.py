from pathlib import Path

orders_code = '''from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    get_market_tick,
    prepare_symbol,
    close_position,
    close_all_positions,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.market_data.mt5_connection import (
    is_mt5_connected,
    get_account_info,
    get_symbol_info,
)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

class OrderExecutionRequest(BaseModel):
    symbol: str = Field(..., description="Market symbol, e.g. EURUSD, XAUUSD")
    action: str = Field(..., description="BUY or SELL")
    lot_size: Optional[float] = Field(default=0.01, description="Trade volume")
    sl: Optional[float] = Field(default=None, description="Optional Stop Loss")
    tp: Optional[float] = Field(default=None, description="Optional Take Profit")

@router.post("/execute")
def execute_manual_order(req: OrderExecutionRequest) -> Dict[str, Any]:
    symbol = req.symbol.upper().strip()
    action = req.action.upper().strip()

    if action not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Action must be BUY or SELL")

    if not is_mt5_connected():
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": "MT5 is not connected or initialized",
        }

    prepare_symbol(symbol)
    tick = get_market_tick(symbol)
    if not tick.get("ready") and not tick.get("success"):
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": f"Unable to fetch live tick for {symbol}",
        }

    entry_price = float(tick.get("ask") if action == "BUY" else tick.get("bid"))
    lot_size = float(req.lot_size if req.lot_size and req.lot_size > 0 else 0.01)

    sym_info = get_symbol_info(symbol)
    point = getattr(sym_info, "point", 0.0001) or 0.0001
    digits = getattr(sym_info, "digits", 5) or 5

    sl = req.sl
    tp = req.tp
    default_pips = 300 * point if ("JPY" in symbol or "XAU" in symbol) else 30 * point

    if sl is None or sl <= 0:
        sl = round(entry_price - default_pips if action == "BUY" else entry_price + default_pips, digits)

    if tp is None or tp <= 0:
        tp = round(entry_price + (default_pips * 2.0) if action == "BUY" else entry_price - (default_pips * 2.0), digits)

    structural_levels = {
        "swing_high": tp if action == "BUY" else entry_price + default_pips,
        "swing_low": sl if action == "BUY" else entry_price - default_pips,
        "previous_high": tp if action == "BUY" else None,
        "previous_low": tp if action == "SELL" else None,
        "target_high": tp if action == "BUY" else None,
        "target_low": tp if action == "SELL" else None,
    }

    trade_plan = {
        "symbol": symbol,
        "market": symbol,
        "decision": action,
        "signal": action,
        "action": action,
        "lot_size": lot_size,
        "volume": lot_size,
        "entry_price": entry_price,
        "sl": sl,
        "tp": tp,
        "stop_loss": sl,
        "take_profit": tp,
        "structural_stop": sl,
        "risk_ratio": 2.0,
        "confidence": 100.0,
        "source": "manual_app_execution",
        "market_context": dict(structural_levels),
        "structural_context": dict(structural_levels),
    }

    acc = get_account_info()
    balance = getattr(acc, "balance", None) or 100.0
    equity = getattr(acc, "equity", None) or balance

    risk_context = {
        "account_balance": float(balance),
        "account_equity": float(equity),
        "balance": float(balance),
        "equity": float(equity),
        "base_risk_percent": 1.0,
        "preferred_lot": lot_size,
    }

    result = execute_trade_pipeline(
        trade_plan=trade_plan,
        risk_context=risk_context,
        execute_live=True,
    )

    order_sent = bool(result.get("order_sent") or result.get("success") or result.get("status") == "EXECUTED")
    reason = result.get("reason") or result.get("message") or ("Order executed successfully" if order_sent else "Order blocked by safety checks")

    return {
        "status": "EXECUTED" if order_sent else result.get("status", "BLOCKED"),
        "order_sent": order_sent,
        "reason": reason,
        "details": result,
    }

@router.post("/close/{ticket}")
def close_order(ticket: int):
    return close_position(ticket)

@router.post("/close-all")
def close_all():
    return close_all_positions()
'''

target = Path("backend/api/routes/orders.py")
target.write_text(orders_code, encoding="utf-8")
print("[OK] backend/api/routes/orders.py updated with structural targets in market_context.")
