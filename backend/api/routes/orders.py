from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    get_market_tick,
    prepare_symbol,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.market_data.mt5_connection import is_mt5_connected

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

    # Ensure symbol is selected in Market Watch and fetch current tick
    prepare_symbol(symbol)
    tick = get_market_tick(symbol)
    if not tick.get("success"):
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": f"Unable to fetch live tick for {symbol}",
        }

    entry_price = tick.get("ask") if action == "BUY" else tick.get("bid")
    lot_size = req.lot_size if req.lot_size and req.lot_size > 0 else 0.01

    # Standardized Trade Plan for execution pipeline
    trade_plan = {
        "symbol": symbol,
        "market": symbol,
        "decision": action,
        "signal": action,
        "action": action,
        "lot_size": lot_size,
        "volume": lot_size,
        "entry_price": entry_price,
        "sl": req.sl,
        "tp": req.tp,
        "risk_ratio": 1.0,
        "confidence": 100.0,
        "source": "manual_app_execution",
    }

    # Run through risk manager, position check, final gate, and live executor
    result = execute_trade_pipeline(
        trade_plan=trade_plan,
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
