"""Update backend/api/routes/orders.py to dispatch approved trades to live_executor."""
from pathlib import Path

target = Path("backend/api/routes/orders.py")
if not target.exists():
    print(f"[ERR] File not found: {target}")
    exit(1)

code = '''from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    get_market_tick,
    prepare_symbol,
    execute_live_trade,
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

    # Standard structural fallback (30 pips) if trader did not supply explicit SL/TP
    sl = req.sl
    tp = req.tp
    default_pips = 300 * point if ("JPY" in symbol or "XAU" in symbol) else 30 * point

    if sl is None or sl <= 0:
        sl = round(entry_price - default_pips if action == "BUY" else entry_price + default_pips, digits)

    if tp is None or tp <= 0:
        tp = round(entry_price + (default_pips * 2.0) if action == "BUY" else entry_price - (default_pips * 2.0), digits)

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
        "target_high": tp if action == "BUY" else None,
        "target_low": tp if action == "SELL" else None,
        "swing_high": tp if action == "BUY" else entry_price + default_pips,
        "swing_low": sl if action == "BUY" else entry_price - default_pips,
        "risk_ratio": 2.0,
        "confidence": 100.0,
        "source": "manual_app_execution",
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

    # Run complete safety and authorization pipeline
    pipeline_result = execute_trade_pipeline(
        trade_plan=trade_plan,
        risk_context=risk_context,
        execute_live=True,
    )

    execution_allowed = bool(pipeline_result.get("execution_allowed"))
    approved_order = pipeline_result.get("order")
    final_gate = pipeline_result.get("final_gate", {}).get("gate_result", pipeline_result.get("final_gate"))

    if not execution_allowed or not approved_order:
        reason = pipeline_result.get("reason") or "Order blocked by safety checks"
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": reason,
            "details": pipeline_result,
        }

    # Unwrap if nested under 'order' key
    if isinstance(approved_order, dict) and "order" in approved_order and isinstance(approved_order["order"], dict):
        raw_order = approved_order["order"]
    else:
        raw_order = approved_order

    # Hand authorized order to Live Executor for MT5 order_check and order_send
    live_result = execute_live_trade(order=raw_order, gate=final_gate)
    order_sent = bool(live_result.get("success") or live_result.get("order_sent") or live_result.get("status") == "EXECUTED")
    reason = live_result.get("reason") or live_result.get("message") or ("Order executed successfully on MT5" if order_sent else "Order send failed")

    return {
        "status": "EXECUTED" if order_sent else live_result.get("status", "BLOCKED"),
        "order_sent": order_sent,
        "ticket": live_result.get("ticket"),
        "retcode": live_result.get("retcode"),
        "reason": reason,
        "live_result": live_result,
        "pipeline_safety": pipeline_result,
    }

@router.post("/close/{ticket}")
def close_order(ticket: int):
    return close_position(ticket)

@router.post("/close-all")
def close_all():
    return close_all_positions()
'''

target.write_text(code, encoding="utf-8")
print("[OK] backend/api/routes/orders.py updated to call execute_live_trade on authorized orders.")
