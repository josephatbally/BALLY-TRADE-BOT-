"""
BALLY FLOW API - Orders and Execution Router (Phase 2 & 3 Protected)
Authenticated execution is bound to the tenant's active DB-3 trading account.
MT5 remains the source of truth for live execution/account state.
"""
from __future__ import annotations

from backend.notifications.telegram_alerts import notify_order_executed, notify_position_closed

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.trading_engine.execution.execution_pipeline import execute_pipeline
from backend.trading_engine.execution.live_executor import close_position
from backend.trading_engine.execution.trade_persistence import (
    create_execution_record, create_order_record, create_trade_plan_record,
    create_trade_record,
)
from backend.trading_engine.engine import analyze_live_market
from backend.trading_engine.hybrid.hybrid_engine import analyze_hybrid_market
from backend.main import app as application
from backend.security.jwt_auth import get_current_user
from backend.trading_engine.tenant_router import tenant_router
from backend.trading_engine.trading_account_runtime import resolve_authenticated_trading_account
from backend.trading_engine.market_data.mt5_connection import get_positions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


class ExecuteOrderRequest(BaseModel):
    symbol: str = Field(..., description="Tradable symbol, e.g. EURUSD")
    action: str = Field(..., description="Requested BUY or SELL direction")
    lot_size: float = Field(0.01, ge=0.01, le=10.0, description="Legacy request field; backend risk sizing remains authoritative")
    comment: str | None = Field("BALLY FLOW Execution", description="Order comment")


def _risk_trade_plan(execution: Dict[str, Any]) -> Dict[str, Any]:
    risk = execution.get("risk")
    if not isinstance(risk, dict):
        return {}
    nested = risk.get("trade_plan")
    return nested if isinstance(nested, dict) else {}


def _persist_execution_lifecycle(*, user_id: int, requested_lot_size: float, requested_comment: str | None, trade_plan: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    risk_plan = _risk_trade_plan(execution)
    approved_order = execution.get("order") if isinstance(execution.get("order"), dict) else {}
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
    # The authoritative live result is returned by execute_pipeline()
    # under live_execution. Keep the executor fallback for compatibility.
    live_stage = execution.get("live_execution")
    if isinstance(live_stage, dict) and isinstance(live_stage.get("live_executor_result"), dict):
        live_result = live_stage["live_executor_result"]
        real_trade = bool(live_stage.get("real_trade") or live_result.get("real_trade"))
    else:
        executor = execution.get("executor")
        if isinstance(executor, dict) and isinstance(executor.get("executor_result"), dict):
            live_result = executor["executor_result"]
            real_trade = bool(live_result.get("real_trade"))
    send_result = live_result.get("mt5_order_send") if isinstance(live_result.get("mt5_order_send"), dict) else {}
    order_ticket = send_result.get("order") or live_result.get("order_ticket")
    deal_ticket = send_result.get("deal") or live_result.get("deal_ticket")
    position_ticket = send_result.get("position") or live_result.get("position_ticket")
    broker_retcode = send_result.get("retcode") or live_result.get("retcode")
    execution_price = send_result.get("price") or live_result.get("price") or entry
    execution_volume = send_result.get("volume") or live_result.get("volume") or volume

    if real_trade:
        order_status = execution_status = plan_status = "EXECUTED"
    elif live_result.get("reason") == "DRY_RUN is enabled":
        order_status = execution_status = "DRY_RUN"
        plan_status = "READY"
    else:
        order_status = execution_status = "BLOCKED"
        plan_status = "EXECUTION_BLOCKED"

    conn = get_db_connection()
    try:
        plan_row = create_trade_plan_record(
            user_id=user_id, symbol=symbol, decision=decision,
            timeframe=str(trade_plan.get("timeframe", "M15")), entry=entry,
            stop_loss=stop_loss, take_profit=take_profit, volume=volume,
            risk_percent=risk_percent, risk_reward=risk_reward,
            opportunity_score=trade_plan.get("opportunity_score"),
            market_context=trade_plan.get("market_context"),
            structural_context=trade_plan.get("structural_context"),
            metadata={"source": "api.orders.execute", "requested_action": decision,
                      "requested_lot_size": requested_lot_size,
                      "pipeline_status": execution.get("status")},
            status=plan_status, conn=conn,
        )
        plan_id = plan_row.get("id")
        if not approved_order:
            conn.commit()
            return {"trade_plan_id": plan_id, "order_id": None, "execution_id": None, "trade_record_id": None, "persistence_status": "TRADE_PLAN_ONLY"}
        if execution_volume is None:
            raise RuntimeError("Authoritative execution volume is missing.")

        order_row = create_order_record(
            user_id=user_id, trade_plan_id=plan_id, symbol=symbol, action=decision,
            volume=float(execution_volume), magic_number=approved_order.get("magic_number"),
            mt5_order_ticket=order_ticket, price=execution_price,
            stop_loss=approved_order.get("stop_loss", stop_loss),
            take_profit=approved_order.get("take_profit", take_profit),
            comment=approved_order.get("comment", requested_comment), status=order_status,
            broker_retcode=broker_retcode, request_json=live_result.get("request") or approved_order,
            response_json=live_result or execution, conn=conn,
        )
        order_id = order_row.get("id")
        execution_row = create_execution_record(
            order_id=order_id, user_id=user_id, symbol=symbol, action=decision,
            deal_ticket=deal_ticket, order_ticket=order_ticket, position_ticket=position_ticket,
            volume=execution_volume, price=execution_price, broker_retcode=broker_retcode,
            status=execution_status, response_json=live_result or execution, conn=conn,
        )
        trade_row = None
        if real_trade:
            trade_row = create_trade_record(
                user_id=user_id, trade_plan_id=plan_id, order_id=order_id, symbol=symbol,
                direction=decision, position_ticket=position_ticket, volume=execution_volume,
                entry_price=execution_price, stop_loss=approved_order.get("stop_loss", stop_loss),
                take_profit=approved_order.get("take_profit", take_profit), status="OPEN",
                metadata={"source": "api.orders.execute"}, conn=conn,
            )

            # DB-2 persistence records the execution history, while DB-3's
            # user_orders table is the ownership index used by authenticated
            # position filtering and close authorization. Keep the two in sync
            # for a successfully opened MT5 position.
            ownership_ticket = position_ticket or order_ticket
            if ownership_ticket:
                ownership_ok = tenant_router.record_user_order(
                    user_id=user_id,
                    ticket=int(ownership_ticket),
                    symbol=symbol,
                    action=decision,
                    lot_size=float(execution_volume),
                    status="SUBMITTED",
                    magic_number=int(approved_order.get("magic_number") or 20260817),
                )
                if not ownership_ok:
                    logger.error(
                        "MT5 trade executed but tenant ownership could not be recorded: user_id=%s ticket=%s",
                        user_id,
                        ownership_ticket,
                    )
                    raise RuntimeError("Executed trade ownership could not be recorded.")

        conn.commit()
        return {"trade_plan_id": plan_id, "order_id": order_id, "execution_id": execution_row.get("id"),
                "trade_record_id": trade_row.get("id") if trade_row else None,
                "persistence_status": "EXECUTED" if real_trade else order_status}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _authoritative_analysis(symbol: str) -> Dict[str, Any]:
    if application.is_technical():
        result = analyze_live_market(symbol)
        if not isinstance(result, dict):
            raise RuntimeError("Technical Engine returned an invalid result.")
        return result
    if application.is_hybrid():
        technical_result = analyze_live_market(symbol)
        if not isinstance(technical_result, dict):
            raise RuntimeError("Technical Engine returned an invalid result.")
        result = analyze_hybrid_market(symbol=symbol, technical_result=technical_result)
        if not isinstance(result, dict):
            raise RuntimeError("Hybrid Engine returned an invalid result.")
        result["technical_analysis"] = technical_result.get("technical_analysis", technical_result)
        result.setdefault("enhanced_quality_score", technical_result.get("enhanced_quality_score"))
        result.setdefault("core_confluence_score", technical_result.get("core_confluence_score"))
        return result
    raise RuntimeError("Unsupported BALLY FLOW trading mode.")


@router.post("/execute")
def execute_order(request: ExecuteOrderRequest, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    symbol = request.symbol.strip().upper()
    action = request.action.strip().upper()
    if action not in ("BUY", "SELL"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported action: {action}. Must be BUY or SELL.")
    try:
        user_id = int(current_user["id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user has no valid numeric user id.")

    resolved = resolve_authenticated_trading_account(user_id)
    if resolved["status"] == "NO_ACCOUNT":
        raise HTTPException(status_code=409, detail="No active trading account is configured for this user.")
    if resolved["status"] != "READY":
        raise HTTPException(status_code=409, detail=f"Trading account is not ready: {resolved['status']}.")

    if not application.running:
        application.start()
    # Manual BUY/SELL is an operator instruction. It must not be rejected
    # merely because the strategy engine currently has the opposite signal.
    # The requested direction still passes through the complete risk,
    # position, final-gate, broker-check and MT5 execution pipeline.
    analysis = _authoritative_analysis(symbol)
    trade_plan = application._build_upstream_trade_plan(
        market=symbol,
        decision=action,
        analysis=analysis,
    )
    trade_plan["metadata"] = {
        **(trade_plan.get("metadata") if isinstance(trade_plan.get("metadata"), dict) else {}),
        "source": "manual_app",
        "requested_action": action,
    }

    pipeline_result = execute_pipeline(
        trade_plan=trade_plan,
        risk_context=application._get_risk_context(),
        execute_live=True,
    )
    persistence = _persist_execution_lifecycle(
        user_id=user_id,
        requested_lot_size=float(request.lot_size),
        requested_comment=request.comment,
        trade_plan=trade_plan,
        execution=pipeline_result,
    )

    live_stage = pipeline_result.get("live_execution")
    live_result = (
        live_stage.get("live_executor_result", {})
        if isinstance(live_stage, dict)
        else {}
    )
    send_result = (
        live_result.get("mt5_order_send", {})
        if isinstance(live_result, dict)
        else {}
    )
    order_sent = bool(
        live_stage.get("real_trade")
        if isinstance(live_stage, dict)
        else live_result.get("real_trade")
    )
    ticket = (
        send_result.get("position")
        or send_result.get("order")
        or send_result.get("deal")
        or live_result.get("position_ticket")
        or live_result.get("order_ticket")
        or live_result.get("deal_ticket")
        or 0
    )
    return {
        "status": "EXECUTED" if order_sent else "BLOCKED",
        "order_sent": order_sent,
        "ticket": ticket,
        "retcode": send_result.get("retcode") or live_result.get("retcode"),
        "reason": (
            live_stage.get("reason")
            if isinstance(live_stage, dict)
            else None
        ) or pipeline_result.get("reason"),
        "details": pipeline_result,
        "tenant_id": user_id,
        "trading_account_id": resolved["configured_account"]["id"],
        "persistence": persistence,
    }


@router.post("/close/{ticket}")
def close_order(ticket: int, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = int(current_user["id"])
    resolved = resolve_authenticated_trading_account(user_id)
    if resolved["status"] != "READY":
        raise HTTPException(status_code=409, detail=f"Trading account is not ready: {resolved['status']}.")
    if ticket not in set(tenant_router.get_user_order_tickets(user_id)):
        raise HTTPException(status_code=404, detail="Position does not belong to the authenticated user.")
    res = close_position(ticket=ticket)
    if not res.get("closed"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Failed to close position"))
    try:
        notify_position_closed(ticket=ticket, symbol="", action="", profit=float(res.get("profit", 0.0) or 0.0), close_price=float(res.get("price", 0.0) or 0.0))
    except Exception:
        pass
    return res


@router.post("/close-all")
def close_all_orders(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = int(current_user["id"])
    resolved = resolve_authenticated_trading_account(user_id)
    if resolved["status"] != "READY":
        raise HTTPException(status_code=409, detail=f"Trading account is not ready: {resolved['status']}.")
    tickets = set(tenant_router.get_user_order_tickets(user_id))
    raw_positions = get_positions() or []
    live_positions = []
    for position in raw_positions:
        try:
            live_positions.append({"ticket": int(getattr(position, "ticket"))})
        except (TypeError, ValueError, AttributeError):
            continue
    owned = [p["ticket"] for p in live_positions if p["ticket"] in tickets]
    results = [close_position(ticket=ticket) for ticket in owned]
    return {"closed": all(r.get("closed") for r in results) if results else True, "count": len(results), "results": results}
