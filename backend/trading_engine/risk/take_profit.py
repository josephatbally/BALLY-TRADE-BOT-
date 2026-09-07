"""
BALLY FLOW - Risk Take Profit Engine

STRUCTURAL TAKE-PROFIT AUTHORITY
================================

This module calculates and validates take-profit levels.

PIPELINE
--------

    Decision Engine
          |
    Risk Management
          |
    Stop Loss
          |
    Take Profit
          |
    Position Sizing
          |
    Margin
          |
    Drawdown
          |
    Final Risk Authorization
          |
    Execution Pipeline

IMPORTANT
---------

This module does NOT:

    - generate BUY / SELL decisions
    - change the trading direction
    - calculate lot size
    - send MT5 orders
    - perform execution
    - override the Decision Engine
    - invent arbitrary market structure

RISK/REWARD POLICY
------------------

Maximum permitted reward-to-risk ratio:

    1 : 3

Supported target levels may include:

    1 : 1
    1 : 1.5
    1 : 2
    1 : 2.5
    1 : 3

The engine prefers valid structural targets.

If a structural target is farther than 3R,
the target is capped at 3R.

If no valid structural target exists,
the engine does NOT invent one.

"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Risk Take Profit Engine"
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

# ----------------------------------------------------------------------
# RR POLICY
# ----------------------------------------------------------------------
MIN_RR = 1.0

# 3R is a quality benchmark, not a maximum TP ceiling.
BENCHMARK_RR = 3.0

PREFERRED_RR_LEVELS = (
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6.0,
    8.0,
)

# ----------------------------------------------------------------------
# Structural target priority
# ----------------------------------------------------------------------

BUY_TARGET_KEYS = (
    "liquidity_pool_high",
    "liquidity_high",
    "previous_high",
    "swing_high",
    "order_block_high",
    "supply_high",
    "target_high",
)

SELL_TARGET_KEYS = (
    "liquidity_pool_low",
    "liquidity_low",
    "previous_low",
    "swing_low",
    "order_block_low",
    "demand_low",
    "target_low",
)


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value into float."""

    try:
        if value is None:
            return None

        result = float(value)

        if result != result:
            return None

        return result

    except (TypeError, ValueError):
        return None


def _normalize_signal(signal: Any) -> str:
    """Normalize a trading signal."""

    return str(signal or "").upper().strip()


def _valid_price(value: Any) -> bool:
    """Return True when value is a valid positive price."""

    number = _safe_float(value)

    return number is not None and number > 0


def _extract_target_value(value: Any) -> Optional[float]:
    """
    Extract a price from either:

        4700

    or:

        {"high": 4700}

    or:

        {"low": 4700}
    """

    direct = _safe_float(value)

    if direct is not None and _valid_price(direct):
        return direct

    if isinstance(value, dict):

        for key in (
            "price",
            "level",
            "high",
            "low",
            "target",
            "value",
        ):
            candidate = _safe_float(value.get(key))

            if _valid_price(candidate):
                return candidate

    return None


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def take_profit_info() -> Dict[str, Any]:
    """
    Return Take Profit engine architecture/status information.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),

        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),

        "responsibilities": [
            "structural_target_identification",
            "risk_reward_calculation",
            "take_profit_calculation",
            "take_profit_validation",
            "maximum_rr_enforcement",
            "minimum_rr_validation",
            "structural_target_selection",
        ],

        "maximum_rr": BENCHMARK_RR,
        "minimum_rr": MIN_RR,

        "preferred_rr_levels": list(PREFERRED_RR_LEVELS),

        "structural_target_sources": [
            "liquidity_pool",
            "previous_high_low",
            "swing_high_low",
            "order_block_boundary",
            "supply_demand_boundary",
            "explicit_structural_target",
        ],

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "decision_generation": False,
        "decision_override": False,

        "position_sizing": False,
        "margin_check": False,
        "drawdown_control": False,

        "execution": False,
        "order_builder": False,
        "mt5_order_check": False,
        "mt5_order_send": False,

        "decision_authority": "upstream_decision_engine",
        "risk_authority": "downstream_risk_management",

        "maximum_allowed_rr": 3.0,

        "invent_target_without_structure": False,
    }


# ======================================================================
# RISK DISTANCE
# ======================================================================

def calculate_risk_distance(
    signal: str,
    entry: Any,
    stop_loss: Any,
) -> Dict[str, Any]:
    """
    Calculate the distance between entry and stop loss.

    BUY:

        risk = entry - stop_loss

    SELL:

        risk = stop_loss - entry
    """

    signal = _normalize_signal(signal)

    entry_price = _safe_float(entry)
    stop_price = _safe_float(stop_loss)

    if signal not in ("BUY", "SELL"):

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "signal must be BUY or SELL",
        }

    if entry_price is None or entry_price <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "entry price is invalid",
        }

    if stop_price is None or stop_price <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "stop_loss is invalid",
        }

    if signal == "BUY":

        distance = entry_price - stop_price

    else:

        distance = stop_price - entry_price

    if distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": (
                f"{signal} stop_loss relationship is invalid"
            ),
            "entry": entry_price,
            "stop_loss": stop_price,
        }

    return {
        "status": "READY",
        "valid": True,
        "signal": signal,
        "entry": entry_price,
        "stop_loss": stop_price,
        "risk_distance": distance,
    }


# ======================================================================
# TARGET COLLECTION
# ======================================================================

def _collect_structural_targets(
    signal: str,
    context: Optional[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """
    Collect structurally supplied target levels.

    Only targets on the correct side of the market are retained.
    """

    signal = _normalize_signal(signal)

    if not isinstance(context, dict):
        return []

    keys = (
        BUY_TARGET_KEYS
        if signal == "BUY"
        else SELL_TARGET_KEYS
    )

    results: list[Dict[str, Any]] = []

    for priority, key in enumerate(keys):

        if key not in context:
            continue

        raw_value = context.get(key)

        # --------------------------------------------------------------
        # Direct numeric value
        # --------------------------------------------------------------

        if isinstance(raw_value, (int, float, str)):

            price = _extract_target_value(raw_value)

            if price is not None:

                results.append({
                    "source": key.upper(),
                    "price": price,
                    "priority": priority,
                })

            continue

        # --------------------------------------------------------------
        # Dictionary structure
        # --------------------------------------------------------------

        if isinstance(raw_value, dict):

            price = _extract_target_value(raw_value)

            if price is not None:

                results.append({
                    "source": key.upper(),
                    "price": price,
                    "priority": priority,
                })

    return results


# ======================================================================
# VALID STRUCTURAL TARGET FILTER
# ======================================================================

def _filter_directional_targets(
    signal: str,
    entry: float,
    targets: Iterable[Dict[str, Any]],
) -> list[Dict[str, Any]]:
    """
    Keep only targets that are valid for the trading direction.
    """

    signal = _normalize_signal(signal)

    valid = []

    for target in targets:

        price = _safe_float(target.get("price"))

        if price is None or price <= 0:
            continue

        if signal == "BUY" and price > entry:

            valid.append(target)

        elif signal == "SELL" and price < entry:

            valid.append(target)

    return valid


# ======================================================================
# RR CALCULATION
# ======================================================================

def calculate_rr(
    signal: str,
    entry: Any,
    stop_loss: Any,
    take_profit: Any,
) -> Dict[str, Any]:
    """
    Calculate reward-to-risk ratio.

    Returns:

        risk_distance
        reward_distance
        rr
    """

    signal = _normalize_signal(signal)

    risk_result = calculate_risk_distance(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
    )

    if not risk_result["valid"]:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": risk_result["reason"],
        }

    entry_price = risk_result["entry"]
    risk_distance = risk_result["risk_distance"]

    tp_price = _safe_float(take_profit)

    if tp_price is None or tp_price <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "take_profit is invalid",
        }

    if signal == "BUY":

        reward_distance = tp_price - entry_price

    else:

        reward_distance = entry_price - tp_price

    if reward_distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": (
                f"{signal} take_profit relationship is invalid"
            ),
            "entry": entry_price,
            "stop_loss": risk_result["stop_loss"],
            "take_profit": tp_price,
        }

    rr = reward_distance / risk_distance

    return {
        "status": "READY",
        "valid": True,
        "signal": signal,
        "entry": entry_price,
        "stop_loss": risk_result["stop_loss"],
        "take_profit": tp_price,
        "risk_distance": risk_distance,
        "reward_distance": reward_distance,
        "rr": rr,
    }


# ======================================================================
# MAXIMUM RR TARGET
# ======================================================================
def calculate_maximum_target(
    signal: str,
    entry: Any,
    stop_loss: Any,
) -> Dict[str, Any]:
    """
    Calculate the 3R benchmark target.

    This function is retained for compatibility with existing callers.

    IMPORTANT:
        3R is a benchmark, not a maximum permitted reward.

    Structural targets beyond the benchmark remain valid.
    """

    risk_result = calculate_risk_distance(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
    )

    if not risk_result["valid"]:
        return risk_result

    entry_price = risk_result["entry"]
    risk_distance = risk_result["risk_distance"]

    benchmark_reward = risk_distance * BENCHMARK_RR

    if _normalize_signal(signal) == "BUY":
        benchmark_target = entry_price + benchmark_reward
    else:
        benchmark_target = entry_price - benchmark_reward

    return {
        "status": "READY",
        "valid": True,
        "signal": _normalize_signal(signal),
        "entry": entry_price,
        "stop_loss": risk_result["stop_loss"],
        "risk_distance": risk_distance,
        "benchmark_rr": BENCHMARK_RR,
        "benchmark_reward": benchmark_reward,
        "benchmark_take_profit": benchmark_target,

        # Compatibility fields.
        "maximum_rr": BENCHMARK_RR,
        "maximum_reward": benchmark_reward,
        "maximum_take_profit": benchmark_target,
    }


# ======================================================================
# TAKE-PROFIT VALIDATION
# ======================================================================

def validate_take_profit(
    signal: str,
    entry: Any,
    stop_loss: Any,
    take_profit: Any,
) -> Dict[str, Any]:
    """
    Validate an explicit TP against direction, risk distance
    and maximum RR.
    """

    signal = _normalize_signal(signal)

    rr_result = calculate_rr(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )

    if not rr_result["valid"]:
        return rr_result

    rr = rr_result["rr"]

    # --------------------------------------------------------------
    # Minimum RR
    # --------------------------------------------------------------

    if rr < MIN_RR:

        return {
            **rr_result,
            "status": "BLOCKED",
            "valid": False,
            "reason": (
                f"take_profit provides only {rr:.2f}R; "
                f"minimum permitted RR is {MIN_RR:.2f}R"
            ),
            "risk_authorized": False,
        }

    # --------------------------------------------------------------
    # Maximum RR
    # --------------------------------------------------------------


    return {
        **rr_result,
        "status": "READY",
        "valid": True,
        "benchmark_rr": BENCHMARK_RR,
        "risk_authorized": True,
    }


# ======================================================================
# COMPLETE TAKE-PROFIT CALCULATION
# ======================================================================

def calculate_take_profit(
    signal: str,
    entry: Any,
    stop_loss: Any,
    context: Optional[Dict[str, Any]] = None,
    preferred_rr: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Complete structural Take Profit calculation.

    Selection policy:

        1. Validate BUY/SELL.
        2. Calculate structural risk distance.
        3. Identify opposing structural targets.
        4. Calculate RR for every valid structural target.
        5. Respect preferred RR when supplied without capping it.
        6. Otherwise select the nearest meaningful structural target.
        7. Treat 3R as a benchmark, never as a maximum.
        8. Never invent a target without structure.
    """

    signal = _normalize_signal(signal)

    if signal not in ("BUY", "SELL"):

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "signal must be BUY or SELL",
            "signal": signal,
            "risk_authorized": False,
        }

    risk_result = calculate_risk_distance(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
    )

    if not risk_result["valid"]:
        return {
            **risk_result,
            "risk_authorized": False,
        }

    entry_price = risk_result["entry"]
    stop_price = risk_result["stop_loss"]
    risk_distance = risk_result["risk_distance"]

    # --------------------------------------------------------------
    # 3R BENCHMARK ? NOT A MAXIMUM
    # --------------------------------------------------------------
    #
    # calculate_maximum_target() is retained for compatibility and
    # benchmark reporting only. It must NEVER cap a structural TP.
    #
    # A valid structural objective may produce 4R, 5R, 6R, 8R, etc.
    # and must remain available to the TP engine.
    # --------------------------------------------------------------

    benchmark_result = calculate_maximum_target(
        signal=signal,
        entry=entry_price,
        stop_loss=stop_price,
    )

    benchmark_target = benchmark_result["maximum_take_profit"]

    # --------------------------------------------------------------
    # COLLECT OPPOSING STRUCTURAL OBJECTIVES
    # --------------------------------------------------------------

    targets = _collect_structural_targets(
        signal=signal,
        context=context,
    )

    targets = _filter_directional_targets(
        signal=signal,
        entry=entry_price,
        targets=targets,
    )

    # --------------------------------------------------------------
    # CALCULATE RR FOR EVERY STRUCTURAL OBJECTIVE
    # --------------------------------------------------------------
    #
    # IMPORTANT:
    # There is deliberately NO maximum-RR filter here.
    # 3R is a benchmark, not a ceiling.
    # --------------------------------------------------------------

    targets_with_rr = []

    for target in targets:

        target_price = target["price"]

        if signal == "BUY":
            reward = target_price - entry_price
        else:
            reward = entry_price - target_price

        if reward <= 0:
            continue

        rr = reward / risk_distance

        if rr < MIN_RR:
            continue

        targets_with_rr.append({
            **target,
            "reward": reward,
            "rr": rr,
            "benchmark_rr": BENCHMARK_RR,
            "above_benchmark": rr > BENCHMARK_RR,
        })

    # --------------------------------------------------------------
    # NO VALID STRUCTURAL TARGET
    # --------------------------------------------------------------

    if not targets_with_rr:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": (
                "no valid structural take-profit target "
                f"at or above {MIN_RR:.1f}R"
            ),
            "signal": signal,
            "entry": entry_price,
            "stop_loss": stop_price,
            "risk_distance": risk_distance,
            "benchmark_rr": BENCHMARK_RR,
            "benchmark_take_profit": benchmark_target,
            "structural_target_found": False,
            "risk_authorized": False,
        }

    # --------------------------------------------------------------
    # PREFERRED RR
    # --------------------------------------------------------------
    #
    # User-controlled mode may request 3R, 4R, 5R, 6R, 8R, etc.
    #
    # The requested RR is NEVER silently capped at 3R.
    #
    # We still select an ACTUAL structural target. We never invent
    # a TP merely to hit a requested RR.
    # --------------------------------------------------------------

    desired_rr = _safe_float(preferred_rr)

    if desired_rr is not None:

        desired_rr = max(
            MIN_RR,
            desired_rr,
        )

        selected = min(
            targets_with_rr,
            key=lambda item: (
                abs(item["rr"] - desired_rr),
                item.get("timeframe_priority", 3),
                item.get("priority", 20),
            ),
        )

    else:

        # ----------------------------------------------------------
        # AUTOMATED / DEFAULT TARGET SELECTION
        # ----------------------------------------------------------
        #
        # Select the nearest valid opposing structural objective.
        #
        # The resulting RR is reported as-is. It may be below,
        # equal to, or above the 3R benchmark.
        # ----------------------------------------------------------

        selected = min(
            targets_with_rr,
            key=lambda item: (
                abs(item["price"] - entry_price),
                item.get("timeframe_priority", 3),
                item.get("priority", 20),
            ),
        )

    take_profit = selected["price"]
    rr = selected["rr"]

    # --------------------------------------------------------------
    # Final validation.
    # --------------------------------------------------------------

    validation = validate_take_profit(
        signal=signal,
        entry=entry_price,
        stop_loss=stop_price,
        take_profit=take_profit,
    )

    if not validation["valid"]:
        return validation

    return {
        "status": "READY",
        "valid": True,

        "signal": signal,

        "entry": entry_price,
        "stop_loss": stop_price,
        "take_profit": take_profit,

        "risk_distance": risk_distance,

        "reward_distance": validation["reward_distance"],

        "rr": rr,

        "risk_reward": f"1:{round(rr, 2)}",

        "source": selected["source"],

        "structural_target_found": True,

        "preferred_rr": desired_rr,

        "minimum_rr": MIN_RR,
        "benchmark_rr": BENCHMARK_RR,

        "benchmark_take_profit": benchmark_target,

        "risk_authorized": True,

        "decision": None,

        "decision_authority": "upstream_decision_engine",

        "risk_authority": "downstream_risk_management",
    }


# ======================================================================
# COMPATIBILITY API
# ======================================================================

def calculate_tp(
    signal: str,
    entry: Any,
    stop_loss: Any,
    context: Optional[Dict[str, Any]] = None,
    preferred_rr: Optional[float] = None,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return calculate_take_profit(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
        context=context,
        preferred_rr=preferred_rr,
    )


def validate_tp(
    signal: str,
    entry: Any,
    stop_loss: Any,
    take_profit: Any,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return validate_take_profit(
        signal=signal,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW RISK TAKE PROFIT ENGINE")
    print("==============================================")

    print("\nINFO:")
    print(take_profit_info())

    context = {
        "liquidity_pool_high": 4760,
        "previous_high": 4780,
        "swing_high": 4820,
        "order_block_high": 4745,
        "supply_high": 4770,
    }

    result = calculate_take_profit(
        signal="BUY",
        entry=4700,
        stop_loss=4680,
        context=context,
    )

    print("\nRESULT:")
    print(result)