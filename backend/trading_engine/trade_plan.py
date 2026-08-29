"""
BALLY TRADES BOT - Trade Plan

AUTHORITATIVE TRADE-PLAN DATA CONTRACT
======================================

This module packages an already-authorized trading decision into a
standardized trade plan for the Risk Manager.

RESPONSIBILITIES
----------------
- Preserve the upstream BUY / SELL / NO_TRADE decision
- Preserve symbol and market information
- Carry entry information when available
- Carry structural context required by risk management
- Carry opportunity-quality information
- Provide a standardized trade-plan structure

THIS MODULE DOES NOT
--------------------
- generate BUY / SELL decisions
- perform technical analysis
- perform fundamental analysis
- calculate SMC
- calculate final risk
- calculate final lot size
- calculate margin
- send orders
- override the Decision Engine
"""

from __future__ import annotations

from typing import Any, Dict, Optional


NAME = "BALLY FLOW Trade Plan"
VERSION = "1.0.0"

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

SUPPORTED_TIMEFRAMES = (
    "H4",
    "H1",
    "M15",
)


def _normalize_signal(signal: Any) -> str:
    """Normalize a trading signal."""

    return str(signal or "").strip().upper()


def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def trade_plan_info() -> Dict[str, Any]:
    """Return module architecture information."""

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),
        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),

        "responsibilities": [
            "preserve_authoritative_decision",
            "standardize_trade_plan",
            "carry_symbol",
            "carry_entry",
            "carry_market_context",
            "carry_structural_context",
            "carry_opportunity_quality",
            "provide_risk_manager_input",
        ],

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_calculation": False,
        "position_sizing": False,
        "margin_check": False,

        "execution": False,
        "order_builder": False,
        "mt5_order_check": False,
        "mt5_order_send": False,

        "decision_authority": "upstream_decision_engine",
        "risk_authority": "downstream_risk_manager",
        "execution_authority": "downstream_execution_pipeline",
    }


def create_trade_plan(
    decision: str,
    symbol: str,
    entry: Any = None,
    market_context: Optional[Dict[str, Any]] = None,
    structural_context: Optional[Dict[str, Any]] = None,
    opportunity_score: Any = None,
    timeframe: str = "M15",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized upstream trade plan.

    The decision is preserved exactly as BUY, SELL, or NO_TRADE.

    Risk values such as final SL, TP, volume and authorized risk
    are intentionally left to the Risk Manager.
    """

    signal = _normalize_signal(decision)

    if signal not in SUPPORTED_SIGNALS:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "invalid trading decision",
            "decision": signal,
        }

    if not isinstance(symbol, str) or not symbol.strip():
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "symbol is required",
            "decision": signal,
        }

    timeframe = str(timeframe or "M15").strip().upper()

    if timeframe not in SUPPORTED_TIMEFRAMES:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "unsupported timeframe",
            "decision": signal,
            "timeframe": timeframe,
        }

    normalized_entry = _safe_float(entry)

    if signal in ("BUY", "SELL") and normalized_entry is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "entry is required for BUY/SELL",
            "decision": signal,
            "symbol": symbol.strip(),
        }

    if not isinstance(market_context, dict):
        market_context = {}

    if not isinstance(structural_context, dict):
        structural_context = {}

    if not isinstance(metadata, dict):
        metadata = {}

    normalized_opportunity_score = _safe_float(opportunity_score)

    return {
        "status": "READY",
        "valid": True,

        # ----------------------------------------------------------
        # AUTHORITATIVE DECISION
        # ----------------------------------------------------------

        "decision": signal,
        "signal": signal,

        # ----------------------------------------------------------
        # MARKET
        # ----------------------------------------------------------

        "symbol": symbol.strip(),
        "timeframe": timeframe,
        "entry": normalized_entry,

        # ----------------------------------------------------------
        # CONTEXT FOR RISK MANAGEMENT
        # ----------------------------------------------------------

        "market_context": market_context,
        "structural_context": structural_context,
        "opportunity_score": normalized_opportunity_score,

        # ----------------------------------------------------------
        # RISK VALUES ARE NOT CREATED HERE
        # ----------------------------------------------------------

        "stop_loss": None,
        "take_profit": None,
        "volume": None,

        "risk_percent": None,
        "risk_amount": None,
        "risk_reward": None,

        "risk_authorized": False,
        "risk_managed": False,

        # ----------------------------------------------------------
        # EXECUTION IS NOT AUTHORIZED HERE
        # ----------------------------------------------------------

        "execution_allowed": False,

        # ----------------------------------------------------------
        # METADATA
        # ----------------------------------------------------------

        "metadata": metadata,

        "source": "upstream_decision_engine",
    }


def build_trade_plan(
    decision: str,
    symbol: str,
    entry: Any = None,
    market_context: Optional[Dict[str, Any]] = None,
    structural_context: Optional[Dict[str, Any]] = None,
    opportunity_score: Any = None,
    timeframe: str = "M15",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compatibility alias for create_trade_plan."""

    return create_trade_plan(
        decision=decision,
        symbol=symbol,
        entry=entry,
        market_context=market_context,
        structural_context=structural_context,
        opportunity_score=opportunity_score,
        timeframe=timeframe,
        metadata=metadata,
    )


def create_no_trade_plan(
    symbol: str,
    reason: str = "upstream decision is NO_TRADE",
    timeframe: str = "M15",
) -> Dict[str, Any]:
    """Create an explicit NO_TRADE plan."""

    plan = create_trade_plan(
        decision="NO_TRADE",
        symbol=symbol,
        entry=None,
        timeframe=timeframe,
    )

    plan["reason"] = reason

    return plan


def is_trade_plan_valid(plan: Any) -> bool:
    """Check whether an object is a valid basic trade plan."""

    if not isinstance(plan, dict):
        return False

    if plan.get("status") != "READY":
        return False

    if plan.get("valid") is not True:
        return False

    decision = _normalize_signal(
        plan.get("decision") or plan.get("signal")
    )

    if decision not in SUPPORTED_SIGNALS:
        return False

    symbol = plan.get("symbol")

    if not isinstance(symbol, str) or not symbol.strip():
        return False

    return True


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW TRADE PLAN")
    print("==============================================")

    print(trade_plan_info())

    result = create_trade_plan(
        decision="BUY",
        symbol="XAUUSD",
        entry=4700.0,
        market_context={
            "market_condition_score": 85.0,
        },
        structural_context={
            "liquidity_sweep_low": 4678.0,
            "order_block": {
                "low": 4685.0,
                "high": 4695.0,
            },
        },
        opportunity_score=85.0,
        timeframe="M15",
    )

    print("TRADE PLAN:")
    print(result)