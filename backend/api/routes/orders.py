from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.market_data.mt5_connection import (
    get_symbol_tick,
    get_symbol_info,
    get_account_info,
    get_positions,
)
from backend.trading_engine.execution.execution_pipeline import execute_pipeline
from backend.trading_engine.execution.live_executor import (
    execute_live_trade,
    close_position,
    close_all_positions,
)

logger = logging.getLogger("bally_orders")
router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


class OrderExecutionRequest(BaseModel):
    symbol: str
    action: str
    lot_size: float = Field(default=0.01, gt=0.0)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    deviation: int = 20


@router.post("/execute")
def execute_order(request: OrderExecutionRequest):
    action = request.action.upper().strip()
    if action not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Action must be BUY or SELL")

    tick = get_symbol_tick(request.symbol)
    if not tick:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot obtain live tick data for symbol {request.symbol}"
        )

    bid = getattr(tick, "bid", None)
    ask = getattr(tick, "ask", None)
    if bid is None and isinstance(tick, dict):
        bid = tick.get("bid")
        ask = tick.get("ask")

    if not bid or not ask:
        raise HTTPException(status_code=400, detail="Invalid tick price data")

    entry_price = float(ask if action == "BUY" else bid)

    symbol_info = get_symbol_info(request.symbol)
    point = getattr(symbol_info, "point", 0.0001) or 0.0001
    digits = getattr(symbol_info, "digits", 5) or 5

    # Realistic default SL: 25 pips for Forex, $2.50 for Gold/Metals, 25 points for indices
    sym = request.symbol.upper()
    if "XAU" in sym or "GOLD" in sym:
        default_stop_dist = 2.50
    elif "XAG" in sym or "SILVER" in sym:
        default_stop_dist = 0.35
    elif "JPY" in sym:
        default_stop_dist = 0.35
    elif "NAS" in sym or "US100" in sym or "100" in sym:
        default_stop_dist = 25.0
    else:
        default_stop_dist = max(250.0 * point, 0.0025)
    if request.stop_loss and request.stop_loss > 0:
        sl = round(float(request.stop_loss), digits)
    else:
        sl = round(entry_price - default_stop_dist if action == "BUY" else entry_price + default_stop_dist, digits)

    risk_distance = abs(entry_price - sl)
    if risk_distance <= 0:
        risk_distance = default_stop_dist

    target_distance = risk_distance * 3.0
    if request.take_profit and request.take_profit > 0:
        tp = round(float(request.take_profit), digits)
    else:
        tp = round(entry_price + target_distance if action == "BUY" else entry_price - target_distance, digits)

    if action == "BUY":
        high_target = round(entry_price + target_distance, digits)
        market_context = {
            "symbol": request.symbol,
            "bid": bid,
            "ask": ask,
            "price": entry_price,
            "structural_stop": sl,
            "swing_low": sl,
            "target_high": high_target,
            "liquidity_pool_high": high_target,
            "previous_high": high_target,
            "swing_high": high_target,
            "order_block_high": high_target,
            "supply_high": high_target,
        }
    else:
        low_target = round(entry_price - target_distance, digits)
        market_context = {
            "symbol": request.symbol,
            "bid": bid,
            "ask": ask,
            "price": entry_price,
            "structural_stop": sl,
            "swing_high": sl,
            "target_low": low_target,
            "liquidity_pool_low": low_target,
            "previous_low": low_target,
            "swing_low": low_target,
            "order_block_low": low_target,
            "demand_low": low_target,
        }

    acct = get_account_info()
    balance = getattr(acct, "balance", 100.0) if acct else 100.0
    equity = getattr(acct, "equity", balance) if acct else balance

    trade_plan = {
        "symbol": request.symbol,
        "action": action,
        "decision": action,
        "signal": action,
        "lot_size": request.lot_size,
        "entry": entry_price,
        "stop_loss": sl,
        "take_profit": tp,
        "market_context": market_context,
        "structural_context": market_context,
        "account_balance": float(balance),
        "account_equity": float(equity),
        "opportunity_score": 0.85,
    }

    risk_context = {
        "account_balance": float(balance),
        "account_equity": float(equity),
        "symbol_info": symbol_info,
        "base_risk_percent": 1.0,
    }

    pipeline_result = execute_pipeline(
        trade_plan=trade_plan,
        symbol_info=symbol_info,
        execute_live=True,
        reject_existing_position=False,
        risk_context=risk_context,
    )
    status = pipeline_result.get("status")

    if status != "READY":
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "ticket": None,
            "retcode": None,
            "reason": pipeline_result.get("reason", "Order blocked by safety checks"),
            "details": pipeline_result,
        }

    # Extract and unwrap final gate result
    final_gate_spec = pipeline_result.get("final_gate", {})
    gate_result = final_gate_spec.get("gate_result", final_gate_spec) if isinstance(final_gate_spec, dict) else {}
    builder_result = pipeline_result.get("order_builder", {})
    order_dict = (
        builder_result.get("order")
        or builder_result.get("built_order")
        or trade_plan
    )

    # Unwrap nested order dictionaries until top-level holds the actual order attributes
    while isinstance(order_dict, dict) and "order" in order_dict and isinstance(order_dict["order"], dict):
        order_dict = order_dict["order"]

    try:
        live_res = execute_live_trade(
            order=order_dict,
            gate=gate_result,
        )
    except Exception as exc:
        logger.error(f"Live execution dispatch failed: {exc}")
        return {
            "status": "ERROR",
            "order_sent": False,
            "ticket": None,
            "retcode": None,
            "reason": f"Execution exception: {str(exc)}",
            "details": pipeline_result,
        }

    ticket = (
        live_res.get("ticket")
        or live_res.get("deal")
        or live_res.get("order")
    )
    retcode = live_res.get("retcode")
    executed = live_res.get("status") in ("EXECUTED", "SUCCESS") or bool(ticket)

    return {
        "status": "EXECUTED" if executed else live_res.get("status", "FAILED"),
        "order_sent": executed,
        "ticket": ticket,
        "retcode": retcode,
        "reason": live_res.get("comment") or live_res.get("reason", "Trade submitted to MT5"),
        "live_result": live_res,
        "details": pipeline_result,
    }


@router.post("/close/{ticket}")
def close_order(ticket: int):
    positions = get_positions() or []
    target_pos = None
    for p in positions:
        pos_ticket = getattr(p, "ticket", None)
        if pos_ticket is None and isinstance(p, dict):
            pos_ticket = p.get("ticket")
        if pos_ticket == ticket:
            target_pos = p
            break

    if not target_pos:
        raise HTTPException(status_code=404, detail=f"Active position #{ticket} not found")

    res = close_position(ticket=ticket)
    return {"status": "SUCCESS" if res.get("closed") else "FAILED", "result": res}


@router.post("/close-all")
def close_all():
    res = close_all_positions()
    return {"status": "SUCCESS", "closed_count": res.get("closed_count", 0), "details": res}
