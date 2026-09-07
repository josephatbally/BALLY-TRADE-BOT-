"""
BALLY FLOW - Risk Execution Bridge

RISK -> EXECUTION AUTHORIZATION BOUNDARY
========================================

Pipeline:

    Decision Engine
          |
    Trade Plan
          |
    Risk Manager
          |
    Risk Execution Bridge
          |
    Position Check
          |
    Final Gate
          |
    Order Builder
          |
    Executor
          |
    Live Executor
          |
         MT5

RESPONSIBILITY
--------------

This module is the controlled boundary between the Risk Layer and
the Execution Layer.

It DOES:

    - consume the output of risk_manager.py
    - verify risk authorization
    - verify signal integrity
    - verify SL/TP integrity
    - verify maximum RR
    - verify final risk-managed volume
    - preserve broker-aware volume
    - preserve account-aware risk decisions
    - preserve preferred-lot soft-preference behavior
    - produce an execution authorization payload

It DOES NOT:

    - generate BUY / SELL decisions
    - modify BUY / SELL decisions
    - calculate technical analysis
    - calculate fundamental analysis
    - calculate hybrid analysis
    - independently calculate position size
    - independently calculate SL
    - independently calculate TP
    - perform MT5 order_check()
    - perform MT5 order_send()
    - place orders
    - bypass risk_manager.py
    - bypass drawdown protection
    - bypass margin protection
    - bypass the maximum RR rule

IMPORTANT
---------

Risk authorization must come from risk_manager.py.

This module is a SECURITY/CONTROL BOUNDARY, not a second risk engine.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Risk Execution Bridge"
VERSION = "1.0.0"

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

MINIMUM_RR = 1.0
BENCHMARK_RR = 3.0


# ======================================================================
# SAFE HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_signal(value: Any) -> str:
    """Normalize a trading signal."""

    return str(value or "").upper().strip()


def _get_first(
    source: Dict[str, Any],
    *keys: str,
) -> Any:
    """Return the first available value from a dictionary."""

    for key in keys:
        if key in source and source[key] is not None:
            return source[key]

    return None


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def risk_execution_bridge_info() -> Dict[str, Any]:
    """
    Return architecture and responsibility information.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),

        "pipeline_position": [
            "decision_engine",
            "trade_plan",
            "risk_manager",
            "risk_execution_bridge",
            "position_check",
            "final_gate",
            "order_builder",
            "executor",
            "live_executor",
            "mt5",
        ],

        "responsibilities": [
            "consume_risk_manager_output",
            "require_risk_authorization",
            "preserve_decision_integrity",
            "validate_risk_managed_trade_plan",
            "validate_stop_loss",
            "validate_take_profit",
            "validate_risk_reward",
            "validate_final_volume",
            "preserve_broker_constraints",
            "preserve_account_constraints",
            "produce_execution_authorization",
        ],

        "minimum_rr": MINIMUM_RR,
        "benchmark_rr": BENCHMARK_RR,

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_calculation": False,
        "position_sizing": False,
        "stop_loss_calculation": False,
        "take_profit_calculation": False,
        "drawdown_calculation": False,
        "margin_calculation": False,

        "position_check": False,
        "final_gate": False,
        "order_builder": False,
        "execution": False,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "preferred_lot_hard": False,
        "minimum_rr_enforced": True,

        "risk_authority": "risk_manager.py",
        "bridge_authority": "this_module",
        "execution_authority": "downstream_execution_pipeline",
    }


# ======================================================================
# SIGNAL VALIDATION
# ======================================================================

def validate_signal(signal: Any) -> Dict[str, Any]:
    """
    Validate the signal without generating or changing it.
    """

    normalized = _normalize_signal(signal)

    if normalized not in SUPPORTED_SIGNALS:

        return {
            "status": "BLOCKED",
            "valid": False,
            "signal": normalized,
            "reason": "invalid trading signal",
        }

    if normalized == "NO_TRADE":

        return {
            "status": "BLOCKED",
            "valid": False,
            "signal": normalized,
            "reason": "NO_TRADE cannot enter execution pipeline",
        }

    return {
        "status": "READY",
        "valid": True,
        "signal": normalized,
        "reason": "signal accepted unchanged",
    }


# ======================================================================
# RISK AUTHORIZATION VALIDATION
# ======================================================================

def validate_risk_authorization(
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verify that risk_manager.py explicitly authorized the trade.

    This function does not create authorization.
    """

    if not isinstance(risk_result, dict):

        return {
            "status": "BLOCKED",
            "authorized": False,
            "reason": "risk result must be a dictionary",
        }

    risk_authorized = risk_result.get("risk_authorized")

    if risk_authorized is not True:

        return {
            "status": "BLOCKED",
            "authorized": False,
            "reason": (
                "risk_manager.py did not authorize the trade"
            ),
            "risk_authorized": risk_authorized,
        }

    status = str(
        risk_result.get("status", "")
    ).upper().strip()

    if status and status not in {"READY", "AUTHORIZED", "PASS"}:

        return {
            "status": "BLOCKED",
            "authorized": False,
            "reason": "risk manager status is not authorized",
            "risk_status": status,
        }

    return {
        "status": "READY",
        "authorized": True,
        "reason": "risk manager authorization confirmed",
    }


# ======================================================================
# RR VALIDATION
# ======================================================================

def validate_risk_reward(
    signal: Any,
    entry: Any,
    stop_loss: Any,
    take_profit: Any,
) -> Dict[str, Any]:
    """
    Validate the risk/reward relationship.

    Minimum RR is 1:1.

    3R is a benchmark only and is not a maximum ceiling.
    Structural targets above 3R are permitted.

    This is a boundary validation only. The risk manager remains
    responsible for calculating the official TP.
    """

    normalized_signal = _normalize_signal(signal)

    entry_value = _safe_float(entry)
    stop_value = _safe_float(stop_loss)
    target_value = _safe_float(take_profit)

    if normalized_signal not in {"BUY", "SELL"}:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid execution signal",
        }

    if (
        entry_value is None
        or stop_value is None
        or target_value is None
    ):

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "entry, stop_loss and take_profit are required",
        }

    if normalized_signal == "BUY":

        risk_distance = entry_value - stop_value
        reward_distance = target_value - entry_value

    else:

        risk_distance = stop_value - entry_value
        reward_distance = entry_value - target_value

    if risk_distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid stop loss relationship",
            "risk_distance": risk_distance,
        }

    if reward_distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid take profit relationship",
            "reward_distance": reward_distance,
        }

    rr = reward_distance / risk_distance

    if rr < MINIMUM_RR:

        return {
            "status": "BLOCKED",
            "valid": False,
            "rr": rr,
            "benchmark_rr": BENCHMARK_RR,
            "minimum_rr": MINIMUM_RR,
            "reason": "risk reward is below minimum allowed",
        }

    return {
        "status": "READY",
        "valid": True,
        "risk_distance": risk_distance,
        "reward_distance": reward_distance,
        "rr": rr,
        "risk_reward": f"1:{rr:.2f}",
        "benchmark_rr": BENCHMARK_RR,
        "above_benchmark": rr > BENCHMARK_RR,
        "reason": "risk reward meets minimum requirement",
    }


# ======================================================================
# TRADE PLAN VALIDATION
# ======================================================================

def validate_risk_managed_trade_plan(
    signal: Any,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate the risk-managed trade plan received from risk_manager.py.
    """

    if not isinstance(risk_result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk result must be a dictionary",
        }

    normalized_signal = _normalize_signal(signal)

    risk_signal = _normalize_signal(
        _get_first(
            risk_result,
            "signal",
            "decision",
        )
    )

    # --------------------------------------------------------------
    # Signal integrity
    # --------------------------------------------------------------

    if risk_signal and risk_signal != normalized_signal:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk manager signal differs from upstream signal",
            "upstream_signal": normalized_signal,
            "risk_signal": risk_signal,
        }

    # --------------------------------------------------------------
    # Trade plan extraction
    # --------------------------------------------------------------

    trade_plan = risk_result.get("trade_plan")

    if isinstance(trade_plan, dict):

        source = trade_plan

    else:

        source = risk_result

    symbol = _get_first(
        source,
        "symbol",
    )

    entry = _get_first(
        source,
        "entry",
        "entry_price",
    )

    stop_loss = _get_first(
        source,
        "stop_loss",
        "sl",
    )

    take_profit = _get_first(
        source,
        "take_profit",
        "tp",
    )

    volume = _get_first(
        source,
        "volume",
        "lot",
        "lot_size",
        "final_volume",
    )

    # --------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------

    if not isinstance(symbol, str) or not symbol.strip():

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk-managed trade plan has no symbol",
        }

    entry_value = _safe_float(entry)
    stop_value = _safe_float(stop_loss)
    target_value = _safe_float(take_profit)
    volume_value = _safe_float(volume)

    if entry_value is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk-managed trade plan has no valid entry",
        }

    if stop_value is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk-managed trade plan has no valid stop_loss",
        }

    if target_value is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk-managed trade plan has no valid take_profit",
        }

    if volume_value is None or volume_value <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk-managed trade plan has no valid final volume",
        }

    # --------------------------------------------------------------
    # RR boundary
    # --------------------------------------------------------------

    rr_result = validate_risk_reward(
        signal=normalized_signal,
        entry=entry_value,
        stop_loss=stop_value,
        take_profit=target_value,
    )

    if not rr_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk/reward validation failed",
            "risk_reward_validation": rr_result,
        }

    return {
        "status": "READY",
        "valid": True,

        "signal": normalized_signal,
        "symbol": symbol.strip(),

        "entry": entry_value,
        "stop_loss": stop_value,
        "take_profit": target_value,

        "volume": volume_value,

        "risk_reward": rr_result,

        "risk_authorized": True,

        "preferred_lot_is_hard": False,

        "reason": "risk-managed trade plan validated",
    }


# ======================================================================
# EXECUTION PAYLOAD
# ======================================================================

def build_execution_payload(
    signal: Any,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the payload consumed by the execution layer.

    No MT5 calls are made here.
    """

    signal_result = validate_signal(signal)

    if not signal_result["valid"]:

        return {
            "status": "BLOCKED",
            "execution_allowed": False,
            "reason": signal_result["reason"],
            "signal_validation": signal_result,
        }

    authorization = validate_risk_authorization(
        risk_result
    )

    if not authorization["authorized"]:

        return {
            "status": "BLOCKED",
            "execution_allowed": False,
            "signal": signal_result["signal"],
            "risk_authorization": authorization,
            "reason": authorization["reason"],
        }

    plan = validate_risk_managed_trade_plan(
        signal=signal_result["signal"],
        risk_result=risk_result,
    )

    if not plan["valid"]:

        return {
            "status": "BLOCKED",
            "execution_allowed": False,
            "signal": signal_result["signal"],
            "risk_authorization": authorization,
            "trade_plan_validation": plan,
            "reason": plan["reason"],
        }

    # --------------------------------------------------------------
    # Preserve risk-managed values exactly.
    #
    # Do NOT recalculate volume here.
    # Do NOT change SL.
    # Do NOT change TP.
    # --------------------------------------------------------------

    execution_order = {
        "symbol": plan["symbol"],
        "decision": plan["signal"],
        "order_type": plan["signal"],

        "volume": plan["volume"],

        "entry": plan["entry"],
        "stop_loss": plan["stop_loss"],
        "take_profit": plan["take_profit"],

        "risk_reward": plan["risk_reward"]["rr"],

        "risk_authorized": True,

        # Explicitly mark these as coming from risk management.
        "risk_managed": True,
        "broker_aware_volume": True,
        "account_aware_risk": True,
        "preferred_lot_is_hard": False,
    }

    return {
        "status": "READY",
        "execution_allowed": True,

        "signal": plan["signal"],
        "symbol": plan["symbol"],

        "risk_authorized": True,

        "risk_authorization": authorization,

        "trade_plan": {
            "entry": plan["entry"],
            "stop_loss": plan["stop_loss"],
            "take_profit": plan["take_profit"],
            "volume": plan["volume"],
            "rr": plan["risk_reward"]["rr"],
        },

        "execution_order": execution_order,

        "position_check_allowed": True,
        "final_gate_allowed": True,
        "order_builder_allowed": True,
        "executor_allowed": True,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "reason": (
            "risk authorization passed; "
            "execution may proceed to position check"
        ),
    }


# ======================================================================
# MAIN BRIDGE FUNCTION
# ======================================================================

def authorize_for_execution(
    signal: Any,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main Risk -> Execution bridge entry point.

    The result can be passed downstream to:

        position_check.py
            â†“
        final_gate.py
            â†“
        order_builder.py
            â†“
        executor.py
            â†“
        live_executor.py

    This function never sends an MT5 order.
    """

    return build_execution_payload(
        signal=signal,
        risk_result=risk_result,
    )


# ======================================================================
# COMPATIBILITY ALIASES
# ======================================================================

def bridge_risk_to_execution(
    signal: Any,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Compatibility alias."""

    return authorize_for_execution(
        signal=signal,
        risk_result=risk_result,
    )


def prepare_execution(
    signal: Any,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Compatibility alias."""

    return authorize_for_execution(
        signal=signal,
        risk_result=risk_result,
    )


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW RISK EXECUTION BRIDGE")
    print("==============================================")

    print("\nINFO:")
    print(risk_execution_bridge_info())

    # --------------------------------------------------------------
    # Example authorized risk result
    # --------------------------------------------------------------

    example_risk_result = {
        "status": "READY",
        "risk_authorized": True,
        "signal": "BUY",

        "trade_plan": {
            "symbol": "XAUUSD",
            "entry": 4700.0,
            "stop_loss": 4680.0,
            "take_profit": 4760.0,
            "volume": 0.01,
        },

        "preferred_lot_is_hard": False,
        "broker_aware": True,
        "account_balance_aware": True,
        "account_equity_aware": True,
    }

    result = authorize_for_execution(
        signal="BUY",
        risk_result=example_risk_result,
    )

    print("\nRESULT:")
    print(result)
    
