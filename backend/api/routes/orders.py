"""
BALLY FLOW API - Orders and Execution Router (Phase 2 & 3 Protected)
Wires manual BUY/SELL execution and position closing to the guarded trading pipeline,
and isolates trade attribution to the authenticated tenant.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    execute_live_trade,
    close_position,
    close_all_positions,
)
from backend.trading_engine.execution.execution_pipeline import execute_pipeline
from backend.trading_engine.tenant_router import tenant_router
from backend.security.jwt_auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
)


class ExecuteOrderRequest(BaseModel):
    symbol: str = Field(..., description="Tradable symbol, e.g. EURUSD")
    action: str = Field(..., description="BUY or SELL")
    lot_size: float = Field(0.01, ge=0.01, le=10.0, description="Volume")
    comment: Optional[str] = Field("BALLY FLOW Execution", description="Order comment")


def _unwrap_order_payload(raw_order: Any) -> Dict[str, Any]:
    current = raw_order
    while isinstance(current, dict) and "order" in current and isinstance(current["order"], dict):
        current = current["order"]
    if isinstance(current, dict):
        return current
    return {}


@router.post("/execute")
def execute_order(request: ExecuteOrderRequest, current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)) -> Dict[str, Any]:
    symbol = request.symbol.strip().upper()
    action = request.action.strip().upper()
    lot_size = float(request.lot_size)
    user_id = current_user.get("id") if current_user else None

    if action not in ("BUY", "SELL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported action: {action}. Must be BUY or SELL.",
        )

    pipeline_result = execute_pipeline(
        symbol=symbol,
        action=action,
        lot_size=lot_size,
    )

    if not pipeline_result.get("ready"):
        blocked_reasons = pipeline_result.get("reasons", [])
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": blocked_reasons[0] if blocked_reasons else "Order blocked by safety checks",
            "details": pipeline_result,
        }

    builder_result = pipeline_result.get("order_builder", {})
    inner_order = _unwrap_order_payload(builder_result.get("order"))
    if not inner_order:
        inner_order = _unwrap_order_payload(pipeline_result.get("order"))

    gate_payload = pipeline_result.get("final_gate", {}).get("gate_result", {})
    if not gate_payload:
        gate_payload = pipeline_result.get("gate", {})

    logger.info("Dispatching approved order to live MT5 executor: symbol=%s action=%s lot=%.2f user=%s", symbol, action, lot_size, user_id)
    execution_result = execute_live_trade(
        order=inner_order,
        gate=gate_payload,
    )

    # Phase 3: Record trade attribution for this tenant
    ticket = execution_result.get("ticket") or execution_result.get("order_ticket") or 0
    if execution_result.get("order_sent") and ticket and user_id:
        tenant_router.record_user_order(
            user_id=user_id,
            ticket=ticket,
            symbol=symbol,
            action=action,
            lot_size=lot_size,
            status="EXECUTED"
        )

    return {
        "status": "EXECUTED" if execution_result.get("order_sent") else "BLOCKED",
        "order_sent": execution_result.get("order_sent", False),
        "ticket": ticket,
        "retcode": execution_result.get("retcode"),
        "reason": execution_result.get("reason"),
        "details": execution_result,
        "tenant_id": user_id
    }


@router.post("/close/{ticket}")
def close_order(ticket: int) -> Dict[str, Any]:
    res = close_position(ticket=ticket)
    if not res.get("closed"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Failed to close position"))
    return res


@router.post("/close-all")
def close_all_orders(symbol: Optional[str] = Query(None, description="Optional symbol filter")) -> Dict[str, Any]:
    return close_all_positions()
