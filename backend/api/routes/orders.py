"""
BALLY FLOW API - Orders and Execution Router (Phase 2 & 3 Protected)
Wires manual BUY/SELL execution to the authoritative decision/risk pipeline,
and persists the DB-2 trading lifecycle for the authenticated tenant.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.trading_engine.execution.execution_pipeline import execute_pipeline
from backend.trading_engine.execution.live_executor import (
    close_all_positions,
    close_position,
)
from backend.trading_engine.execution.trade_persistence import (
    create_execution_record,
    create_order_record,
    create_trade_plan_record,
    create_trade_record,
)
from backend.trading_engine.hybrid_engine import analyze_hybrid_market
from backend.trading_engine.technical_engine import analyze_live_market
from backend import main as application
from backend.security.jwt_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
)


class ExecuteOrderRequest(BaseModel):
    symbol: str = Field(..., description="Tradable symbol, e.g. EURUSD")
    action: str = Field(..., description="Requested BUY or SELL direction")
    lot_size: float = Field(
        0.01,
        ge=0.01,
        le=10.0,
        description="Legacy request field; authoritative risk sizing remains backend-controlled",
    )
    comment: str | None = Field("BALLY FLOW Execution", description="Order comment")


def _risk_trade_plan(execution: Dict[str, Any]) -> Dict[str, Any]:
    risk = execution.get("risk")
    if not isinstance(risk, dict):
        return {}
    nested = risk.get("trade_plan")
    return nested if isinstance(nested, dict) else {}


def _persist_execution_lifecycle(
    *,
    user_id: int,
    requested_comment: str | None,
    trade_plan: Dict[str, Any],
    execution: Dict[str, Any],
) -> Dict[str, Any]:
    """Persist one execution attempt using one DB transaction."""
    risk_plan = _risk_trade_plan(execution)
    approved_order = execution.get("order")
    if not isinstance(approved_order, dict):
        approved_order = {}

    symbol = str(trade_plan.get("symbol", "")).strip().upper()
    decision = str(trade_plan.get("decision", "")).strip().upper()

    stop_loss = risk_plan.get("stop_loss")
    take_profit = risk_plan.get("take_profit")
    volume = risk_plan.get("volume")
    risk_percent = risk_plan.get("risk_percent")
    risk_reward = risk_plan.get("risk_reward")
    entry = risk_plan.get("entry", trade_plan.get("entry"))

    real_trade = False
    live_result: Dict[str, Any] = {}
    executor = execution.get("executor")
    if isinstance(executor, dict):
        candidate = executor.get("executor_result")
        if isinstance(candidate, dict):
            live_result = candidate
            real_trade = bool(candidate.get("real_trade"))

    send_result = live_result.get("mt5_order_send")
    if not isinstance(send_result, dict):
        send_result = {}

    order_ticket = send_result.get("order") or live_result.get("order_ticket")
    deal_ticket = send_result.get("deal") or live_result.get("deal_ticket")
    position_ticket = send_result.get("position") or live_result.get("position_ticket")
    broker_retcode = send_result.get("retcode") or live_result.get("retcode")
    execution_price = send_result.get("price") or live_result.get("price") or entry
    execution_volume = send_result.get("volume") or live_result.get("volume") or volume

    if real_trade:
        order_status = "EXECUTED"
        execution_status = "EXECUTED"
        plan_status = "EXECUTED"
    elif live_result.get("reason") == "DRY_RUN is enabled":
        order_status = "DRY_RUN"
        execution_status = "DRY_RUN"
        plan_status = "READY"
    else:
        order_status = "BLOCKED"
        execution_status = "BLOCKED"
        plan_status = "EXECUTION_BLOCKED"

    conn = get_db_connection()
    try:
        plan_row = create_trade_plan_record(
            user_id=user_id,
            symbol=symbol,
            decision=decision,
            timeframe=str(trade_plan.get("timeframe", "M15")),
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volume=volume,
            risk_percent=risk_percent,
            risk_reward=risk_reward,
            opportunity_score=trade_plan.get("opportunity_score"),
            market_context=trade_plan.get("market_context"),
            structural_context=trade_plan.get("structural_context"),
            metadata={
                "source": "api.orders.execute",
                "requested_action": decision,
                "requested_lot_size": None,
                "pipeline_status": execution.get("status"),
            },
            status=plan_status,
            conn=conn,
        )

        plan_id = plan_row.get("id")

        if not approved_order:
            conn.commit()
            return {
                "trade_plan_id": plan_id,
                "order_id": None,
                "execution_id": None,
                "trade_record_id": None,
                "persistence_status": "TRADE_PLAN_ONLY",
            }

        order_row = create_order_record(
            user_id=user_id,
            trade_plan_id=plan_id,
            symbol=symbol,
            action=decision,
            volume=float(execution_volume),
            magic_number=approved_order.get("magic_number"),
            mt5_order_ticket=order_ticket,
            price=execution_price,
            stop_loss=approved_order.get("stop_loss", stop_loss),
            take_profit=approved_order.get("take_profit", take_profit),
            comment=approved_order.get("comment", requested_comment),
            status=order_status,
            broker_retcode=broker_retcode,
            request_json=live_result.get("request") or approved_order,
            response_json=live_result or execution,
            conn=conn,
        )

        order_id = order_row.get("id")
        execution_row = create_execution_record(
            order_id=order_id,
            user_id=user_id,
            symbol=symbol,
            action=decision,
            deal_ticket=deal_ticket,
            order_ticket=order_ticket,
            position_ticket=position_ticket,
            volume=execution_volume,
            price=execution_price,
            broker_retcode=broker_retcode,
            status=execution_status,
            response_json=live_result or execution,
            conn=conn,
        )

        trade_row = None
        if real_trade:
            trade_row = create_trade_record(
                user_id=user_id,
                trade_plan_id=plan_id,
                order_id=order_id,
                symbol=symbol,
                direction=decision,
                position_ticket=position_ticket,
                volume=execution_volume,
                entry_price=execution_price,
                stop_loss=approved_order.get("stop_loss", stop_loss),
                take_profit=approved_order.get("take_profit", take_profit),
                status="OPEN",
                metadata={"source": "api.orders.execute"},
                conn=conn,
            )

        conn.commit()
        return {
            "trade_plan_id": plan_id,
            "order_id": order_id,
            "execution_id": execution_row.get("id"),
            "trade_record_id": trade_row.get("id") if trade_row else None,
            "persistence_status": "EXECUTED" if real_trade else order_status,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _authoritative_analysis(symbol: str) -> Dict[str, Any]:
    """Run the existing Technical/Hybrid decision engines without bypassing them."""
    if application.is_technical():
        result = analyze_live_market(symbol)
        if not isinstance(result, dict):
            raise RuntimeError("Technical Engine returned an invalid result.")
        return result

    if application.is_hybrid():
        technical_result = analyze_live_market(symbol)
        if not isinstance(technical_result, dict):
            raise RuntimeError("Technical Engine returned an invalid result.")
        result = analyze_hybrid_market(
            symbol=symbol,
            technical_result=technical_result,
        )
        if not isinstance(result, dict):
            raise RuntimeError("Hybrid Engine returned an invalid result.")
        result["technical_analysis"] = technical_result.get(
            "technical_analysis",
            technical_result,
        )
        result.setdefault(
            "enhanced_quality_score",
            technical_result.get("enhanced_quality_score"),
        )
        result.setdefault(
            "core_confluence_score",
            technical_result.get("core_confluence_score"),
        )
        return result

    raise RuntimeError("Unsupported BALLY FLOW trading mode.")


@router.post("/execute")
def execute_order(
    request: ExecuteOrderRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    symbol = request.symbol.strip().upper()
    action = request.action.strip().upper()

    if action not in ("BUY", "SELL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported action: {action}. Must be BUY or SELL.",
        )

    try:
        user_id = int(current_user["id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user has no valid numeric user id.",
        )

    if not application.running:
        application.start()

    analysis = _authoritative_analysis(symbol)
    decision = str(
        analysis.get(
            "hybrid_signal",
            analysis.get("decision", analysis.get("signal", "NO_TRADE")),
        )
        or "NO_TRADE"
    ).strip().upper()

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": analysis.get(
                "reason",
                analysis.get("rejection_reason", "Decision Engine returned NO_TRADE."),
            ),
            "decision": decision,
            "tenant_id": user_id,
        }

    if decision != action:
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": (
                f"Requested {action} does not match the authoritative "
                f"Decision Engine signal {decision}."
            ),
            "decision": decision,
            "requested_action": action,
            "tenant_id": user_id,
        }

    trade_plan = application._build_upstream_trade_plan(
        market=symbol,
        decision=decision,
        analysis=analysis,
    )
    risk_context = application._get_risk_context()

    pipeline_result = execute_pipeline(
        trade_plan=trade_plan,
        risk_context=risk_context,
        execute_live=False,
    )

    execution = pipeline_result
    persistence = _persist_execution_lifecycle(
        user_id=user_id,
        requested_comment=request.comment,
        trade_plan=trade_plan,
        execution=execution,
    )

    executor = execution.get("executor")
    live_result = executor.get("executor_result", {}) if isinstance(executor, dict) else {}
    order_sent = bool(live_result.get("real_trade"))
    ticket = (
        live_result.get("ticket")
        or live_result.get("order_ticket")
        or live_result.get("deal_ticket")
        or 0
    )

    return {
        "status": "EXECUTED" if order_sent else "BLOCKED",
        "order_sent": order_sent,
        "ticket": ticket,
        "retcode": live_result.get("retcode"),
        "reason": live_result.get("reason") or execution.get("reason"),
        "details": execution,
        "tenant_id": user_id,
        "persistence": persistence,
    }


@router.post("/close/{ticket}")
def close_order(ticket: int) -> Dict[str, Any]:
    res = close_position(ticket=ticket)
    if not res.get("closed"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Failed to close position"))
    return res


@router.post("/close-all")
def close_all_orders() -> Dict[str, Any]:
    return close_all_positions()
