"""
BALLY FLOW - Risk Management / Stop Loss Engine

AUTHORITATIVE STRUCTURAL STOP-LOSS LAYER
========================================

RESPONSIBILITY
--------------

This module calculates and validates a structurally meaningful
stop-loss for an already-authorized BUY or SELL opportunity.

It does NOT:

    - generate BUY / SELL decisions
    - change BUY to SELL
    - change SELL to BUY
    - perform order placement
    - communicate with MT5
    - calculate final lot size
    - perform margin authorization
    - bypass the Decision Engine
    - bypass downstream Risk Management

The stop-loss is an INVALIDATION level, not an arbitrary distance.

SUPPORTED STRUCTURAL SOURCES
-----------------------------

Preferred sources include:

    - liquidity sweep extreme
    - order block boundary
    - supply/demand boundary
    - swing high / swing low
    - explicit structural stop supplied upstream

If adequate structural information is unavailable, the module
returns BLOCKED rather than inventing a stop.

PIPELINE
--------

Decision Engine
      |
      v
Trade Plan / Market Structure
      |
      v
STOP LOSS ENGINE
      |
      v
Take Profit Engine
      |
      v
Position Sizing
      |
      v
Margin
      |
      v
Drawdown
      |
      v
Risk Manager
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Risk Stop Loss Engine"
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

# Small numerical tolerance used when comparing prices.
PRICE_EPSILON = 1e-9

# Optional ATR safety buffer.
#
# This is intentionally conservative. ATR is used only when the
# upstream structural level is available and a buffer is explicitly
# requested.
DEFAULT_ATR_BUFFER_MULTIPLIER = 0.10

# Minimum percentage of price allowed between entry and SL when the
# caller explicitly requests a minimum distance.
#
# This is NOT a universal trading rule. It is only a validation
# parameter and should normally be supplied by the upstream system.
DEFAULT_MIN_RISK_DISTANCE_PERCENT = 0.0


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        if value is None:
            return None

        result = float(value)

        if result != result:  # NaN
            return None

        return result

    except (TypeError, ValueError):
        return None


def _clean_signal(value: Any) -> str:
    """Normalize a trading decision."""

    return str(value or "").upper().strip()


def _clean_timeframe(value: Any) -> Optional[str]:
    """Normalize timeframe."""

    if value is None:
        return None

    return str(value).upper().strip()


def _first_valid_float(
    values: Iterable[Any],
) -> Optional[float]:
    """Return the first usable positive/negative numeric value."""

    for value in values:
        result = _safe_float(value)

        if result is not None:
            return result

    return None


def _nested_get(
    data: Any,
    *paths: str,
) -> Optional[float]:
    """
    Read the first valid numeric value from nested dictionaries.

    Example:

        _nested_get(
            context,
            "swing_low",
            "structure.swing_low",
            "market_structure.swing_low",
        )
    """

    if not isinstance(data, dict):
        return None

    for path in paths:

        current: Any = data

        valid_path = True

        for part in path.split("."):

            if not isinstance(current, dict):
                valid_path = False
                break

            current = current.get(part)

        if not valid_path:
            continue

        value = _safe_float(current)

        if value is not None:
            return value

    return None


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def stop_loss_info() -> Dict[str, Any]:
    """Return Stop Loss Engine architecture/status."""

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),

        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),

        "responsibilities": [
            "structural_stop_loss_calculation",
            "stop_loss_validation",
            "price_relationship_validation",
            "risk_distance_calculation",
            "structural_source_identification",
        ],

        "preferred_structural_sources": [
            "liquidity_sweep_extreme",
            "order_block_boundary",
            "supply_demand_boundary",
            "swing_high_low",
            "explicit_structural_stop",
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

        "stop_loss_is_invalidation": True,

        "invent_stop_without_structure": False,
    }


# ======================================================================
# STRUCTURAL LEVEL EXTRACTION
# ======================================================================

def extract_structural_levels(
    decision: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract candidate structural levels from upstream analysis.

    No trading decision is generated here.

    The function accepts several compatible representations because
    different SMC modules may expose their structural levels under
    different keys.
    """

    context = context if isinstance(context, dict) else {}

    decision = _clean_signal(decision)

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "only BUY or SELL can receive a structural stop",
            "decision": decision,
        }

    # --------------------------------------------------------------
    # Direct structural stop
    # --------------------------------------------------------------

    explicit_stop = _nested_get(
        context,
        "structural_stop",
        "stop_loss",
        "stop",
        "trade_plan.stop_loss",
        "trade_plan.structural_stop",
        "risk.stop_loss",
    )

    # --------------------------------------------------------------
    # Swing levels
    # --------------------------------------------------------------

    swing_low = _nested_get(
        context,
        "swing_low",
        "structure.swing_low",
        "market_structure.swing_low",
        "swings.low",
        "swing.low",
        "recent_swing_low",
        "recent_low",
    )

    swing_high = _nested_get(
        context,
        "swing_high",
        "structure.swing_high",
        "market_structure.swing_high",
        "swings.high",
        "swing.high",
        "recent_swing_high",
        "recent_high",
    )

    # --------------------------------------------------------------
    # Liquidity sweep extremes
    # --------------------------------------------------------------

    sweep_low = _nested_get(
        context,
        "liquidity_sweep_low",
        "liquidity.sweep_low",
        "liquidity.low",
        "sweep.low",
        "liquidity_sweep.extreme_low",
    )

    sweep_high = _nested_get(
        context,
        "liquidity_sweep_high",
        "liquidity.sweep_high",
        "liquidity.high",
        "sweep.high",
        "liquidity_sweep.extreme_high",
    )

    # --------------------------------------------------------------
    # Order Block boundaries
    # --------------------------------------------------------------

    order_block_low = _nested_get(
        context,
        "order_block_low",
        "order_block.low",
        "order_block.bottom",
        "order_block.lower",
        "order_block.boundary_low",
        "valid_order_block.low",
    )

    order_block_high = _nested_get(
        context,
        "order_block_high",
        "order_block.high",
        "order_block.top",
        "order_block.upper",
        "order_block.boundary_high",
        "valid_order_block.high",
    )

    # --------------------------------------------------------------
    # Supply / Demand boundaries
    # --------------------------------------------------------------

    supply_low = _nested_get(
        context,
        "supply_low",
        "supply.low",
        "supply.bottom",
        "supply_demand.supply_low",
        "supply_demand.low",
    )

    supply_high = _nested_get(
        context,
        "supply_high",
        "supply.high",
        "supply.top",
        "supply_demand.supply_high",
        "supply_demand.high",
    )

    demand_low = _nested_get(
        context,
        "demand_low",
        "demand.low",
        "demand.bottom",
        "supply_demand.demand_low",
        "supply_demand.low",
    )

    demand_high = _nested_get(
        context,
        "demand_high",
        "demand.high",
        "demand.top",
        "supply_demand.demand_high",
        "supply_demand.high",
    )

    return {
        "status": "READY",
        "valid": True,
        "decision": decision,

        "explicit_stop": explicit_stop,

        "swing_low": swing_low,
        "swing_high": swing_high,

        "sweep_low": sweep_low,
        "sweep_high": sweep_high,

        "order_block_low": order_block_low,
        "order_block_high": order_block_high,

        "supply_low": supply_low,
        "supply_high": supply_high,

        "demand_low": demand_low,
        "demand_high": demand_high,
    }


# ======================================================================
# STRUCTURAL STOP SELECTION
# ======================================================================

def select_structural_stop(
    decision: str,
    entry: float,
    levels: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Select a structurally valid stop level.

    BUY:
        stop must be below entry.

    SELL:
        stop must be above entry.

    The closest valid structural invalidation level is preferred.

    Explicit structural stop has highest priority.
    """

    decision = _clean_signal(decision)

    entry = _safe_float(entry)

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid decision",
        }

    if entry is None or entry <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "entry price must be greater than zero",
        }

    if not isinstance(levels, dict):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "structural levels must be a dictionary",
        }

    # --------------------------------------------------------------
    # Priority 1: explicit upstream structural stop
    # --------------------------------------------------------------

    explicit_stop = _safe_float(levels.get("explicit_stop"))

    if explicit_stop is not None:

        if decision == "BUY" and explicit_stop < entry:
            return {
                "status": "READY",
                "valid": True,
                "stop_loss": explicit_stop,
                "source": "EXPLICIT_STRUCTURAL_STOP",
            }

        if decision == "SELL" and explicit_stop > entry:
            return {
                "status": "READY",
                "valid": True,
                "stop_loss": explicit_stop,
                "source": "EXPLICIT_STRUCTURAL_STOP",
            }

    # --------------------------------------------------------------
    # Candidate collection
    # --------------------------------------------------------------

    candidates = []

    def add_candidate(
        value: Any,
        source: str,
    ) -> None:

        price = _safe_float(value)

        if price is None:
            return

        if decision == "BUY":

            if price < entry:
                candidates.append((entry - price, price, source))

        elif decision == "SELL":

            if price > entry:
                candidates.append((price - entry, price, source))

    if decision == "BUY":

        # Liquidity sweep low is strong invalidation evidence.
        add_candidate(
            levels.get("sweep_low"),
            "LIQUIDITY_SWEEP_LOW",
        )

        # Demand / bullish order-block lower boundaries.
        add_candidate(
            levels.get("order_block_low"),
            "ORDER_BLOCK_LOW",
        )

        add_candidate(
            levels.get("demand_low"),
            "DEMAND_LOW",
        )

        add_candidate(
            levels.get("swing_low"),
            "SWING_LOW",
        )

    else:

        add_candidate(
            levels.get("sweep_high"),
            "LIQUIDITY_SWEEP_HIGH",
        )

        add_candidate(
            levels.get("order_block_high"),
            "ORDER_BLOCK_HIGH",
        )

        add_candidate(
            levels.get("supply_high"),
            "SUPPLY_HIGH",
        )

        add_candidate(
            levels.get("swing_high"),
            "SWING_HIGH",
        )

    if not candidates:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "no valid structural stop level available",
            "decision": decision,
            "entry": entry,
        }

    # Closest valid structural invalidation level.
    candidates.sort(key=lambda item: item[0])

    _, selected_stop, source = candidates[0]

    return {
        "status": "READY",
        "valid": True,
        "stop_loss": selected_stop,
        "source": source,
        "candidate_count": len(candidates),
        "candidates": [
            {
                "distance": distance,
                "price": price,
                "source": candidate_source,
            }
            for distance, price, candidate_source in candidates
        ],
    }


# ======================================================================
# ATR BUFFER
# ======================================================================

def apply_atr_buffer(
    decision: str,
    stop_loss: float,
    atr: Optional[float] = None,
    multiplier: float = DEFAULT_ATR_BUFFER_MULTIPLIER,
) -> Dict[str, Any]:
    """
    Optionally move the structural stop slightly beyond the
    structural level using ATR.

    This function does not create a stop from ATR alone.

    ATR is only a buffer around an already-valid structural stop.
    """

    decision = _clean_signal(decision)

    stop_loss = _safe_float(stop_loss)
    atr = _safe_float(atr)
    multiplier = _safe_float(multiplier)

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid decision",
        }

    if stop_loss is None or stop_loss <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid stop_loss",
        }

    if atr is None or atr <= 0:
        return {
            "status": "READY",
            "valid": True,
            "stop_loss": stop_loss,
            "buffer_applied": False,
            "buffer": 0.0,
            "reason": "ATR unavailable; structural stop retained",
        }

    if multiplier is None or multiplier < 0:
        multiplier = DEFAULT_ATR_BUFFER_MULTIPLIER

    buffer = atr * multiplier

    if decision == "BUY":
        adjusted_stop = stop_loss - buffer
    else:
        adjusted_stop = stop_loss + buffer

    if adjusted_stop <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "ATR-adjusted stop became invalid",
        }

    return {
        "status": "READY",
        "valid": True,
        "stop_loss": adjusted_stop,
        "buffer_applied": True,
        "buffer": buffer,
        "atr": atr,
        "atr_multiplier": multiplier,
    }


# ======================================================================
# STOP VALIDATION
# ======================================================================

def validate_stop_loss(
    decision: str,
    entry: float,
    stop_loss: float,
    minimum_distance_percent: float = DEFAULT_MIN_RISK_DISTANCE_PERCENT,
) -> Dict[str, Any]:
    """
    Validate the final stop-loss relationship.

    BUY:
        SL < Entry

    SELL:
        SL > Entry
    """

    decision = _clean_signal(decision)

    entry = _safe_float(entry)
    stop_loss = _safe_float(stop_loss)
    minimum_distance_percent = _safe_float(
        minimum_distance_percent
    )

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid decision",
        }

    if entry is None or entry <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid entry price",
        }

    if stop_loss is None or stop_loss <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid stop_loss",
        }

    if decision == "BUY":

        if stop_loss >= entry:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "BUY stop_loss must be below entry",
            }

        risk_distance = entry - stop_loss

    else:

        if stop_loss <= entry:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "SELL stop_loss must be above entry",
            }

        risk_distance = stop_loss - entry

    if risk_distance <= PRICE_EPSILON:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk distance is zero",
        }

    risk_percent_distance = (
        risk_distance / entry
    ) * 100.0

    if (
        minimum_distance_percent is not None
        and minimum_distance_percent > 0
        and risk_percent_distance < minimum_distance_percent
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "stop distance is below configured minimum",
            "risk_distance": risk_distance,
            "risk_percent_distance": risk_percent_distance,
            "minimum_distance_percent": minimum_distance_percent,
        }

    return {
        "status": "READY",
        "valid": True,
        "decision": decision,
        "entry": entry,
        "stop_loss": stop_loss,
        "risk_distance": risk_distance,
        "risk_percent_distance": risk_percent_distance,
    }


# ======================================================================
# COMPLETE STOP LOSS CALCULATION
# ======================================================================

def calculate_stop_loss(
    decision: str,
    entry: float,
    context: Optional[Dict[str, Any]] = None,
    atr: Optional[float] = None,
    use_atr_buffer: bool = False,
    atr_buffer_multiplier: float = DEFAULT_ATR_BUFFER_MULTIPLIER,
    minimum_distance_percent: float = DEFAULT_MIN_RISK_DISTANCE_PERCENT,
) -> Dict[str, Any]:
    """
    Calculate and validate a structural stop-loss.

    No decision is generated here.
    """

    decision = _clean_signal(decision)

    entry = _safe_float(entry)

    if decision not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "only BUY or SELL can receive a stop-loss",
            "decision": decision,
        }

    if entry is None or entry <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "entry price must be greater than zero",
            "decision": decision,
        }

    # --------------------------------------------------------------
    # Extract structure
    # --------------------------------------------------------------

    levels_result = extract_structural_levels(
        decision=decision,
        context=context,
    )

    if not levels_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": decision,
            "entry": entry,
            "reason": levels_result["reason"],
            "structure": levels_result,
        }

    # --------------------------------------------------------------
    # Select structural stop
    # --------------------------------------------------------------

    selected = select_structural_stop(
        decision=decision,
        entry=entry,
        levels=levels_result,
    )

    if not selected["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": decision,
            "entry": entry,
            "reason": selected["reason"],
            "structure": levels_result,
        }

    stop_loss = selected["stop_loss"]

    # --------------------------------------------------------------
    # Optional ATR buffer
    # --------------------------------------------------------------

    buffer_result = {
        "status": "READY",
        "valid": True,
        "stop_loss": stop_loss,
        "buffer_applied": False,
        "buffer": 0.0,
    }

    if use_atr_buffer:

        buffer_result = apply_atr_buffer(
            decision=decision,
            stop_loss=stop_loss,
            atr=atr,
            multiplier=atr_buffer_multiplier,
        )

        if not buffer_result["valid"]:

            return {
                "status": "BLOCKED",
                "valid": False,
                "decision": decision,
                "entry": entry,
                "reason": buffer_result["reason"],
                "structure": levels_result,
                "selection": selected,
                "atr_buffer": buffer_result,
            }

        stop_loss = buffer_result["stop_loss"]

    # --------------------------------------------------------------
    # Final validation
    # --------------------------------------------------------------

    validation = validate_stop_loss(
        decision=decision,
        entry=entry,
        stop_loss=stop_loss,
        minimum_distance_percent=minimum_distance_percent,
    )

    if not validation["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": decision,
            "entry": entry,
            "reason": validation["reason"],
            "structure": levels_result,
            "selection": selected,
            "atr_buffer": buffer_result,
            "validation": validation,
        }

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    return {
        "status": "READY",
        "valid": True,

        "decision": decision,

        "entry": entry,

        "stop_loss": validation["stop_loss"],

        "risk_distance": validation["risk_distance"],

        "risk_percent_distance": validation[
            "risk_percent_distance"
        ],

        "source": selected["source"],

        "candidate_count": selected.get(
            "candidate_count",
            1,
        ),

        "atr_buffer_applied": buffer_result.get(
            "buffer_applied",
            False,
        ),

        "atr_buffer": buffer_result.get(
            "buffer",
            0.0,
        ),

        "structure": levels_result,

        "decision_authority": "upstream_decision_engine",

        "risk_authorized": False,

        "execution_allowed": False,
    }


# ======================================================================
# VALIDATE EXISTING TRADE PLAN STOP
# ======================================================================

def validate_trade_plan_stop(
    decision: str,
    entry: float,
    stop_loss: float,
) -> Dict[str, Any]:
    """
    Validate an already-created trade-plan stop.

    Useful when the Decision Engine has already calculated the SL
    and Risk Management only needs to verify it.
    """

    result = validate_stop_loss(
        decision=decision,
        entry=entry,
        stop_loss=stop_loss,
    )

    result["decision_authority"] = "upstream_decision_engine"

    return result


# ======================================================================
# COMPATIBILITY ALIASES
# ======================================================================

def calculate_sl(
    decision: str,
    entry: float,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Compatibility alias for calculate_stop_loss."""

    return calculate_stop_loss(
        decision=decision,
        entry=entry,
        context=context,
        **kwargs,
    )


def get_stop_loss(
    decision: str,
    entry: float,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return calculate_stop_loss(
        decision=decision,
        entry=entry,
        context=context,
        **kwargs,
    )


# ======================================================================
# MODULE SELF-TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW RISK STOP LOSS ENGINE")
    print("==============================================")

    print("INFO:")
    print(stop_loss_info())

    test_context = {
        "swing_low": 4680.0,
        "swing_high": 4725.0,

        "liquidity_sweep_low": 4678.0,

        "order_block": {
            "low": 4685.0,
            "high": 4695.0,
        },

        "demand": {
            "low": 4682.0,
            "high": 4690.0,
        },
    }

    result = calculate_stop_loss(
        decision="BUY",
        entry=4700.0,
        context=test_context,
    )

    print("RESULT:")
    print(result)