
"""
BALLY FLOW - Intelligent Risk Manager

CENTRAL RISK MANAGEMENT COORDINATOR

PIPELINE
--------

    Decision Engine
          |
          v
    Risk Manager
          |
          +--> Drawdown Protection
          |
          +--> Stop Loss Engine
          |
          +--> Take Profit Engine
          |
          +--> Position Sizing Engine
          |
          +--> Margin Engine
          |
          v
    FINAL RISK AUTHORIZATION
          |
          v
    Final Gate
          |
          v
    Order Builder
          |
          v
    Executor
          |
          v
    Live Executor
          |
          v
          MT5

IMPORTANT
---------

This module does NOT:

    - generate BUY / SELL decisions
    - change BUY to SELL
    - change SELL to BUY
    - convert NO_TRADE into a trade
    - perform technical analysis
    - perform fundamental analysis
    - perform hybrid analysis
    - place MT5 orders
    - call mt5.order_send()
    - replace the Decision Engine
    - replace the Final Gate
    - bypass execution safety

It coordinates risk-management modules only.

RISK PRINCIPLES
---------------

1. The upstream Decision Engine is authoritative.
2. NO_TRADE can never become a trade.
3. Invalid decisions are blocked.
4. Stop loss must be structurally valid.
5. Take profit must be structurally valid.
6. Take profit may never exceed 1:3 RR.
7. Minimum permitted RR is 1:1.
8. Position size is calculated from actual SL distance.
9. Position sizing remains broker/account/risk constrained.
10. Preferred lot is a SOFT preference only.
11. Drawdown can reduce risk progressively.
12. A blocked drawdown state remains blocked.
13. Margin must pass independently.
14. Critical risk failures fail closed.
15. This module never sends an order.
16. Final Gate remains the final downstream authorization authority.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ======================================================================
# MODULE IMPORTS
# ======================================================================

try:
    from .drawdown import evaluate_drawdown
except ImportError:
    evaluate_drawdown = None

try:
    from .stop_loss import calculate_stop_loss
except ImportError:
    calculate_stop_loss = None

try:
    from .take_profit import calculate_take_profit
except ImportError:
    calculate_take_profit = None

try:
    from .position_sizing import calculate_position_size
except ImportError:
    calculate_position_size = None

try:
    from .margin import check_margin
except ImportError:
    check_margin = None


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Intelligent Risk Manager"
VERSION = "1.1.0"

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


# ======================================================================
# RISK CONFIGURATION
# ======================================================================

DEFAULT_RISK_PERCENT = 1.0
MINIMUM_RISK_PERCENT = 0.1
HARD_MAX_RISK_PERCENT = 2.0

# ======================================================================
# RISK / REWARD POLICY
# ======================================================================

MIN_RR = 1.0
MAXIMUM_RR = 3.0
# Backward-compatible alias.
BENCHMARK_RR = MAXIMUM_RR

RR_TOLERANCE = 1e-9


# ======================================================================
# MARGIN CONFIGURATION
# ======================================================================

DEFAULT_MARGIN_SAFETY_BUFFER_PERCENT = 10.0


# ======================================================================
# PREFERRED LOT POLICY
# ======================================================================

DEFAULT_PREFERRED_LOT = None

# Preferred lot is NEVER authoritative.
PREFERRED_LOT_IS_HARD = False


# ======================================================================
# OPPORTUNITY QUALITY
# ======================================================================

MIN_OPPORTUNITY_SCORE = 0.0
MAX_OPPORTUNITY_SCORE = 100.0


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float.

    Rejects:
        None
        NaN
        invalid numeric values
    """

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
    """
    Normalize a trading decision.
    """

    return str(signal or "").strip().upper()


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """
    Clamp a numeric value to a safe range.
    """

    return max(minimum, min(maximum, value))


def _result_valid(result: Any) -> bool:
    """
    Determine whether a child risk-module result is authorized.

    Supported authorization fields:

        valid=True
        risk_authorized=True
        margin_authorized=True

    Any other result is treated as unauthorized.
    """

    if not isinstance(result, dict):
        return False

    if result.get("valid") is True:
        return True

    if result.get("risk_authorized") is True:
        return True

    if result.get("margin_authorized") is True:
        return True

    return False


def _blocked_result(
    decision: str,
    symbol: str,
    reason: str,
    **details: Any,
) -> Dict[str, Any]:
    """
    Create a consistent blocked risk result.
    """

    result = {
        "status": "BLOCKED",
        "risk_authorized": False,
        "decision": decision,
        "symbol": symbol,
        "execution_allowed": False,
        "order_builder_allowed": False,
        "real_trade": False,
        "reason": reason,
    }

    result.update(details)

    return result


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def risk_manager_info() -> Dict[str, Any]:
    """
    Return architecture and configuration information.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),
        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),

        "responsibilities": [
            "coordinate_drawdown_protection",
            "coordinate_structural_stop_loss",
            "coordinate_structural_take_profit",
            "enforce_minimum_rr",
            "maximum_rr",
            "coordinate_intelligent_position_sizing",
            "coordinate_margin_verification",
            "apply_progressive_risk_reduction",
            "validate_risk_consistency",
            "produce_risk_authorization_result",
        ],

        "default_risk_percent": DEFAULT_RISK_PERCENT,
        "minimum_risk_percent": MINIMUM_RISK_PERCENT,
        "hard_max_risk_percent": HARD_MAX_RISK_PERCENT,

        "minimum_rr": MIN_RR,
        "maximum_rr": MAXIMUM_RR,
        "benchmark_rr": BENCHMARK_RR,

        "default_margin_safety_buffer_percent":
            DEFAULT_MARGIN_SAFETY_BUFFER_PERCENT,

        "default_preferred_lot": DEFAULT_PREFERRED_LOT,
        "preferred_lot_is_hard": PREFERRED_LOT_IS_HARD,

        "preferred_lot_policy": (
            "soft_preference_only; broker/account/risk-calculated "
            "volume remains authoritative"
        ),

        "drawdown_module_available":
            evaluate_drawdown is not None,

        "stop_loss_module_available":
            calculate_stop_loss is not None,

        "take_profit_module_available":
            calculate_take_profit is not None,

        "position_sizing_module_available":
            calculate_position_size is not None,

        "margin_module_available":
            check_margin is not None,

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_management": True,
        "position_sizing": True,

        "execution": False,
        "order_builder": False,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "order_placement": False,

        "decision_authority":
            "upstream_decision_engine",

        "risk_authority":
            "this_module",

        "final_gate_authority":
            "downstream_final_gate",

        "execution_authority":
            "downstream_execution_pipeline",

        "final_output":
            "risk_authorization_and_risk_managed_trade_plan",
    }


# ======================================================================
# RISK PERCENT CALCULATION
# ======================================================================

def calculate_adjusted_risk_percent(
    base_risk_percent: float = DEFAULT_RISK_PERCENT,
    drawdown_result: Optional[Dict[str, Any]] = None,
    opportunity_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate the risk percentage after drawdown and opportunity
    adjustments.

    Important:

        A blocked drawdown result remains blocked.

        A zero drawdown multiplier remains zero.

        The minimum risk floor is NEVER allowed to resurrect
        risk after the drawdown engine has disabled it.
    """

    base = _safe_float(base_risk_percent)

    if base is None:
        base = DEFAULT_RISK_PERCENT

    if base <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "base risk percent must be greater than zero",
        }

    base = _clamp(
        base,
        MINIMUM_RISK_PERCENT,
        HARD_MAX_RISK_PERCENT,
    )


    # ==================================================================
    # DRAWDOWN MULTIPLIER
    # ==================================================================

    drawdown_multiplier = 1.0

    if isinstance(drawdown_result, dict):

        if drawdown_result.get("valid") is False:
            return {
                "status": "BLOCKED",
                "valid": False,
                "risk_authorized": False,
                "reason": (
                    "drawdown engine returned an unauthorized result"
                ),
                "drawdown_result": drawdown_result,
            }

        if drawdown_result.get("risk_authorized") is False:
            return {
                "status": "BLOCKED",
                "valid": False,
                "risk_authorized": False,
                "reason": (
                    "drawdown engine did not authorize risk"
                ),
                "drawdown_result": drawdown_result,
            }

        supplied_multiplier = _safe_float(
            drawdown_result.get("risk_multiplier")
        )

        if supplied_multiplier is not None:

            if supplied_multiplier < 0:
                return {
                    "status": "BLOCKED",
                    "valid": False,
                    "risk_authorized": False,
                    "reason": (
                        "drawdown risk multiplier cannot be negative"
                    ),
                }

            drawdown_multiplier = _clamp(
                supplied_multiplier,
                0.0,
                1.0,
            )


    # ==================================================================
    # OPPORTUNITY QUALITY MULTIPLIER
    # ==================================================================

    opportunity_multiplier = 1.0

    score = _safe_float(opportunity_score)

    if score is not None:

        score = _clamp(
            score,
            MIN_OPPORTUNITY_SCORE,
            MAX_OPPORTUNITY_SCORE,
        )

        if score < 50.0:
            opportunity_multiplier = 0.50

        elif score < 65.0:
            opportunity_multiplier = 0.75

        else:
            opportunity_multiplier = 1.00


    # ==================================================================
    # ADJUSTED RISK
    # ==================================================================

    adjusted = (
        base
        * drawdown_multiplier
        * opportunity_multiplier
    )


    # ==================================================================
    # HARD MAXIMUM
    # ==================================================================

    adjusted = min(
        adjusted,
        HARD_MAX_RISK_PERCENT,
    )


    # ==================================================================
    # IMPORTANT ZERO-RISK PROTECTION
    # ==================================================================

    if drawdown_multiplier <= 0.0:

        adjusted = 0.0

    elif adjusted > 0.0:

        adjusted = max(
            adjusted,
            MINIMUM_RISK_PERCENT,
        )


    # ==================================================================
    # FINAL RESULT
    # ==================================================================

    if adjusted <= 0.0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,

            "base_risk_percent": base,

            "drawdown_multiplier":
                drawdown_multiplier,

            "opportunity_multiplier":
                opportunity_multiplier,

            "adjusted_risk_percent": 0.0,

            "hard_max_risk_percent":
                HARD_MAX_RISK_PERCENT,

            "minimum_risk_percent":
                MINIMUM_RISK_PERCENT,

            "reason":
                "adjusted risk is zero",
        }


    return {
        "status": "READY",
        "valid": True,
        "risk_authorized": True,

        "base_risk_percent": base,

        "drawdown_multiplier":
            drawdown_multiplier,

        "opportunity_multiplier":
            opportunity_multiplier,

        "adjusted_risk_percent":
            round(adjusted, 6),

        "hard_max_risk_percent":
            HARD_MAX_RISK_PERCENT,

        "minimum_risk_percent":
            MINIMUM_RISK_PERCENT,
    }


# ======================================================================
# RISK / REWARD VALIDATION
# ======================================================================

def validate_risk_reward(
    signal: str,
    entry: Any,
    stop_loss: Any,
    take_profit: Any,
) -> Dict[str, Any]:
    """
    Independently validate SL/TP relationships and RR.

    This function does NOT modify TP.

    RR must satisfy:

        RR >= 1R

    RR must satisfy 1R <= RR <= 3R.
    """

    decision = _normalize_signal(signal)

    entry_price = _safe_float(entry)
    stop = _safe_float(stop_loss)
    target = _safe_float(take_profit)


    # ==================================================================
    # SIGNAL
    # ==================================================================

    if decision not in ("BUY", "SELL"):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "only BUY or SELL can be risk validated",
        }


    # ==================================================================
    # PRICES
    # ==================================================================

    if (
        entry_price is None
        or entry_price <= 0
        or stop is None
        or stop <= 0
        or target is None
        or target <= 0
    ):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": (
                "entry, stop_loss and take_profit must "
                "be valid positive prices"
            ),
        }


    # ==================================================================
    # DIRECTIONAL PRICE RELATIONSHIP
    # ==================================================================

    if decision == "BUY":

        risk_distance = entry_price - stop
        reward_distance = target - entry_price

    else:

        risk_distance = stop - entry_price
        reward_distance = entry_price - target


    if risk_distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,

            "signal": decision,
            "entry": entry_price,
            "stop_loss": stop,

            "reason":
                "invalid stop-loss relationship",
        }


    if reward_distance <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,

            "signal": decision,
            "entry": entry_price,
            "stop_loss": stop,
            "take_profit": target,

            "reason":
                "invalid take-profit relationship",
        }


    # ==================================================================
    # RR
    # ==================================================================

    rr = reward_distance / risk_distance


    # ==================================================================
    # MINIMUM RR
    # ==================================================================

    if rr < MIN_RR - RR_TOLERANCE:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,

            "signal": decision,

            "entry": entry_price,
            "stop_loss": stop,
            "take_profit": target,

            "risk_distance": risk_distance,
            "reward_distance": reward_distance,

            "rr": round(rr, 6),

            "minimum_rr": MIN_RR,
            "benchmark_rr": BENCHMARK_RR,

            "reason":
                f"risk reward below minimum {MIN_RR}:1",
        }


    

    # ==================================================================
    # MAXIMUM RR
    # ==================================================================

    if rr > MAXIMUM_RR + RR_TOLERANCE:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "signal": decision,
            "entry": entry_price,
            "stop_loss": stop,
            "take_profit": target,
            "risk_distance": risk_distance,
            "reward_distance": reward_distance,
            "rr": round(rr, 6),
            "minimum_rr": MIN_RR,
            "maximum_rr": MAXIMUM_RR,
            "benchmark_rr": BENCHMARK_RR,
            "reason": f"risk reward exceeds maximum {MAXIMUM_RR}:1",
        }


    # ==================================================================
    # AUTHORIZED
    # ==================================================================

    return {
        "status": "READY",
        "valid": True,
        "risk_authorized": True,

        "signal": decision,

        "entry": entry_price,
        "stop_loss": stop,
        "take_profit": target,

        "risk_distance": risk_distance,
        "reward_distance": reward_distance,

        "rr": round(rr, 6),

        "risk_reward":
            f"1:{round(rr, 2)}",

        "minimum_rr": MIN_RR,
        "maximum_rr": MAXIMUM_RR,
        "benchmark_rr": BENCHMARK_RR,
    }


# ======================================================================
# PREFERRED LOT POLICY
# ======================================================================

def apply_preferred_lot_policy(
    calculated_volume: Any,
    preferred_lot: Any = DEFAULT_PREFERRED_LOT,
) -> Dict[str, Any]:
    """
    Apply preferred lot as a SOFT preference.

    The preferred lot can NEVER replace the calculated broker-valid
    volume.

    Therefore:

        calculated volume = authoritative
        preferred lot      = informational preference
    """

    calculated = _safe_float(calculated_volume)
    preferred = _safe_float(preferred_lot)


    # ==================================================================
    # CALCULATED VOLUME
    # ==================================================================

    if calculated is None or calculated <= 0:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,

            "volume": None,

            "preferred_lot": preferred,

            "preferred_lot_applied": False,

            "preferred_lot_is_hard": False,

            "reason":
                "calculated broker-valid volume is unavailable",
        }


    # ==================================================================
    # NO PREFERENCE
    # ==================================================================

    if preferred is None or preferred <= 0:

        return {
            "status": "READY",
            "valid": True,
            "risk_authorized": True,

            "volume": calculated,

            "calculated_volume": calculated,

            "preferred_lot": None,

            "preferred_lot_applied": False,

            "preferred_lot_is_hard": False,

            "reason":
                "no preferred lot supplied",
        }


    # ==================================================================
    # SOFT PREFERENCE
    # ==================================================================

    return {
        "status": "READY",
        "valid": True,
        "risk_authorized": True,

        "volume": calculated,

        "calculated_volume": calculated,

        "preferred_lot": preferred,

        "preferred_lot_applied": False,

        "preferred_lot_is_hard": False,

        "reason": (
            "preferred lot retained as a soft preference; "
            "broker/risk-calculated volume remains authoritative"
        ),
    }


# ======================================================================
# DRAWDOWN
# ======================================================================

def evaluate_account_drawdown(
    balance: Any,
    equity: Any,
    starting_balance: Any = None,
    max_drawdown_percent: float = 20.0,
    starting_day_balance: Any = None,
    max_daily_loss_percent: float = 5.0,
) -> Dict[str, Any]:
    """
    Run the drawdown engine.

    Fails closed when the module is unavailable or returns an
    unusable result.
    """

    if evaluate_drawdown is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason": "drawdown module unavailable",
        }


    # ==================================================================
    # PRIMARY SIGNATURE
    # ==================================================================

    try:

        result = evaluate_drawdown(
            balance,
            equity,
            starting_balance,
            max_drawdown_percent,
            starting_day_balance,
            max_daily_loss_percent,
        )

    except TypeError:

        # ==============================================================
        # LEGACY 3-ARGUMENT SIGNATURE
        # ==============================================================

        try:

            result = evaluate_drawdown(
                balance,
                equity,
                starting_balance,
            )

        except Exception as exc:

            return {
                "status": "BLOCKED",
                "valid": False,
                "risk_authorized": False,
                "reason":
                    f"drawdown evaluation failed: {exc}",
            }

    except Exception as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"drawdown evaluation failed: {exc}",
        }


    # ==================================================================
    # RESULT VALIDATION
    # ==================================================================

    if not isinstance(result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "drawdown engine returned invalid result",
        }


    return result


# ======================================================================
# STRUCTURAL STOP LOSS
# ======================================================================

def _calculate_structural_stop_loss(
    decision: str,
    entry_price: float,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Call the structural stop-loss engine.

    The function deliberately uses the established positional
    contract and fails closed when the module cannot produce a
    valid result.
    """

    if calculate_stop_loss is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "stop-loss module unavailable",
        }


    try:

        result = calculate_stop_loss(
            decision,
            entry_price,
            context,
        )

    except TypeError as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"stop-loss module signature mismatch: {exc}",
        }

    except Exception as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"stop-loss calculation failed: {exc}",
        }


    if not isinstance(result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "stop-loss engine returned invalid result",
        }


    return result


# ======================================================================
# STRUCTURAL TAKE PROFIT
# ======================================================================

def _calculate_structural_take_profit(
    decision: str,
    entry_price: float,
    stop_loss: float,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Call the structural take-profit engine.

    The Take Profit Engine remains responsible for structural
    target selection.

    The Risk Manager independently validates the resulting RR.
    """

    if calculate_take_profit is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "take-profit module unavailable",
        }


    try:

        result = calculate_take_profit(
            decision,
            entry_price,
            stop_loss,
            context,
        )

    except TypeError as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"take-profit module signature mismatch: {exc}",
        }

    except Exception as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"take-profit calculation failed: {exc}",
        }


    if not isinstance(result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "take-profit engine returned invalid result",
        }


    return result


# ======================================================================
# POSITION SIZING
# ======================================================================

def _calculate_broker_aware_position_size(
    decision: str,
    symbol_name: str,
    entry_price: float,
    stop_loss: float,
    account_balance: Any,
    account_equity: Any,
    adjusted_risk_percent: float,
    preferred_lot: Any,
    opportunity_score: Any,
    symbol_info: Any,
) -> Dict[str, Any]:
    """
    Call the established broker-aware position-sizing engine.

    Position sizing remains authoritative over final volume.
    """

    if calculate_position_size is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "position-sizing module unavailable",
        }


    try:

        result = calculate_position_size(
            decision,
            symbol_name,
            entry_price,
            stop_loss,
            account_balance,
            account_equity,
            adjusted_risk_percent,
            preferred_lot,
            opportunity_score,
            symbol_info,
        )

    except TypeError as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"position-sizing module signature mismatch: {exc}",
        }

    except Exception as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                f"position sizing calculation failed: {exc}",
        }


    if not isinstance(result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "reason":
                "position-sizing engine returned invalid result",
        }


    return result


# ======================================================================
# MARGIN
# ======================================================================

def _check_trade_margin(
    decision: str,
    symbol_name: str,
    volume: float,
    margin_safety_buffer_percent: float,
) -> Dict[str, Any]:
    """
    Call the margin engine.

    The margin engine remains responsible for broker/account
    margin verification.
    """

    if check_margin is None:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "risk_authorized": False,
            "reason":
                "margin module unavailable",
        }


    try:

        result = check_margin(
            decision,
            symbol_name,
            volume,
            margin_safety_buffer_percent,
        )

    except TypeError as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "risk_authorized": False,
            "reason":
                f"margin module signature mismatch: {exc}",
        }

    except Exception as exc:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "risk_authorized": False,
            "reason":
                f"margin verification failed: {exc}",
        }


    if not isinstance(result, dict):

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "risk_authorized": False,
            "reason":
                "margin engine returned invalid result",
        }


    return result


# ======================================================================
# COMPLETE RISK EVALUATION
# ======================================================================

def evaluate_risk(
    signal: str,
    symbol: str,
    entry: Any,
    market_context: Optional[Dict[str, Any]] = None,
    account_balance: Any = None,
    account_equity: Any = None,
    base_risk_percent: float = DEFAULT_RISK_PERCENT,
    preferred_lot: Any = DEFAULT_PREFERRED_LOT,
    opportunity_score: Any = None,
    starting_balance: Any = None,
    starting_day_balance: Any = None,
    max_drawdown_percent: float = 20.0,
    max_daily_loss_percent: float = 5.0,
    margin_safety_buffer_percent:
        float = DEFAULT_MARGIN_SAFETY_BUFFER_PERCENT,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Complete central risk-management pipeline.

    The upstream Decision Engine remains authoritative.

    This function:

        1. validates the decision
        2. evaluates drawdown
        3. calculates adjusted risk
        4. calculates structural SL
        5. calculates structural TP
        6. independently validates RR
        7. calculates broker-aware position size
        8. applies soft preferred-lot policy
        9. verifies margin
        10. performs final risk consistency checks
        11. returns risk authorization

    This function never places an order.
    """

    decision = _normalize_signal(signal)

    context = (
        market_context
        if isinstance(market_context, dict)
        else {}
    )

    symbol_name = str(symbol or "").strip()


    # ==================================================================
    # 1. DECISION VALIDATION
    # ==================================================================

    if decision not in SUPPORTED_SIGNALS:

        return _blocked_result(
            decision,
            symbol_name,
            "invalid upstream decision",
        )


    # ==================================================================
    # 2. NO_TRADE IS TERMINAL
    # ==================================================================

    if decision == "NO_TRADE":

        return _blocked_result(
            decision,
            symbol_name,
            "NO_TRADE cannot enter risk management",
        )


    # ==================================================================
    # 3. SYMBOL
    # ==================================================================

    if not symbol_name:

        return _blocked_result(
            decision,
            symbol_name,
            "symbol is required",
        )


    # ==================================================================
    # 4. ENTRY
    # ==================================================================

    entry_price = _safe_float(entry)

    if entry_price is None or entry_price <= 0:

        return _blocked_result(
            decision,
            symbol_name,
            "valid entry price is required",
        )


    # ==================================================================
    # 5. DRAWDOWN PROTECTION
    # ==================================================================

    drawdown = evaluate_account_drawdown(
        balance=account_balance,
        equity=account_equity,
        starting_balance=starting_balance,
        max_drawdown_percent=max_drawdown_percent,
        starting_day_balance=starting_day_balance,
        max_daily_loss_percent=max_daily_loss_percent,
    )


    if not _result_valid(drawdown):

        return _blocked_result(
            decision,
            symbol_name,
            "drawdown protection did not authorize risk",
            drawdown=drawdown,
        )


    # ==================================================================
    # 6. ADJUSTED RISK
    # ==================================================================

    risk_adjustment = calculate_adjusted_risk_percent(
        base_risk_percent=base_risk_percent,
        drawdown_result=drawdown,
        opportunity_score=opportunity_score,
    )


    if not _result_valid(risk_adjustment):

        return _blocked_result(
            decision,
            symbol_name,
            "risk adjustment was not authorized",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
        )


    adjusted_risk_percent = _safe_float(
        risk_adjustment.get("adjusted_risk_percent")
    )


    if (
        adjusted_risk_percent is None
        or adjusted_risk_percent <= 0
        or adjusted_risk_percent > HARD_MAX_RISK_PERCENT
    ):

        return _blocked_result(
            decision,
            symbol_name,
            "adjusted risk is invalid",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
        )


    # ==================================================================
    # 7. STRUCTURAL STOP LOSS
    # ==================================================================

    stop_result = _calculate_structural_stop_loss(
        decision=decision,
        entry_price=entry_price,
        context=context,
    )


    if not _result_valid(stop_result):

        return _blocked_result(
            decision,
            symbol_name,
            "stop loss was not authorized",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
        )


    stop_loss = _safe_float(
        stop_result.get("stop_loss")
    )


    if stop_loss is None or stop_loss <= 0:

        return _blocked_result(
            decision,
            symbol_name,
            "stop loss value is missing or invalid",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
        )


    # ==================================================================
    # 8. INDEPENDENT STOP-LOSS DIRECTION CHECK
    # ==================================================================

    if decision == "BUY" and stop_loss >= entry_price:

        return _blocked_result(
            decision,
            symbol_name,
            "BUY stop loss must be below entry",
            stop_loss=stop_result,
        )


    if decision == "SELL" and stop_loss <= entry_price:

        return _blocked_result(
            decision,
            symbol_name,
            "SELL stop loss must be above entry",
            stop_loss=stop_result,
        )


    # ==================================================================
    # 9. STRUCTURAL TAKE PROFIT
    # ==================================================================

    tp_result = _calculate_structural_take_profit(
        decision=decision,
        entry_price=entry_price,
        stop_loss=stop_loss,
        context=context,
    )


    if not _result_valid(tp_result):

        return _blocked_result(
            decision,
            symbol_name,
            "take profit was not authorized",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
            take_profit=tp_result,
        )


    take_profit = _safe_float(
        tp_result.get("take_profit")
    )


    if take_profit is None or take_profit <= 0:

        return _blocked_result(
            decision,
            symbol_name,
            "take profit value is missing or invalid",
            stop_loss=stop_result,
            take_profit=tp_result,
        )


    # ==================================================================
    # 10. INDEPENDENT TAKE-PROFIT DIRECTION CHECK
    # ==================================================================

    if decision == "BUY" and take_profit <= entry_price:

        return _blocked_result(
            decision,
            symbol_name,
            "BUY take profit must be above entry",
            stop_loss=stop_result,
            take_profit=tp_result,
        )


    if decision == "SELL" and take_profit >= entry_price:

        return _blocked_result(
            decision,
            symbol_name,
            "SELL take profit must be below entry",
            stop_loss=stop_result,
            take_profit=tp_result,
        )


    # ==================================================================
    # 11. INDEPENDENT RR SAFETY CHECK
    # ==================================================================

    rr_result = validate_risk_reward(
        signal=decision,
        entry=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )


    if not _result_valid(rr_result):

        return _blocked_result(
            decision,
            symbol_name,
            rr_result.get(
                "reason",
                "risk reward validation failed",
            ),
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
            take_profit=tp_result,
            risk_reward=rr_result,
        )


    # ==================================================================
    # 12. POSITION SIZING
    # ==================================================================

    sizing_result = _calculate_broker_aware_position_size(
        decision=decision,
        symbol_name=symbol_name,
        entry_price=entry_price,
        stop_loss=stop_loss,
        account_balance=account_balance,
        account_equity=account_equity,
        adjusted_risk_percent=adjusted_risk_percent,
        preferred_lot=preferred_lot,
        opportunity_score=opportunity_score,
        symbol_info=symbol_info,
    )


    if not _result_valid(sizing_result):

        return _blocked_result(
            decision,
            symbol_name,
            "position sizing was not authorized",
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
            take_profit=tp_result,
            risk_reward=rr_result,
            position_sizing=sizing_result,
        )


    volume = _safe_float(
        sizing_result.get("volume")
    )


    if volume is None or volume <= 0:

        return _blocked_result(
            decision,
            symbol_name,
            "position sizing returned invalid volume",
            position_sizing=sizing_result,
        )


    # ==================================================================
    # 13. PREFERRED LOT SOFT POLICY
    # ==================================================================

    preferred_result = apply_preferred_lot_policy(
        calculated_volume=volume,
        preferred_lot=preferred_lot,
    )


    if not _result_valid(preferred_result):

        return _blocked_result(
            decision,
            symbol_name,
            preferred_result.get(
                "reason",
                "preferred lot policy failed",
            ),
            position_sizing=sizing_result,
            preferred_lot=preferred_result,
        )


    # ==================================================================
    # 14. FINAL VOLUME
    # ==================================================================
    #
    # The position-sizing engine remains authoritative.
    #
    # Never replace it with preferred_lot.
    #

    final_volume = volume


    # ==================================================================
    # 15. MARGIN VERIFICATION
    # ==================================================================

    margin_result = _check_trade_margin(
        decision=decision,
        symbol_name=symbol_name,
        volume=final_volume,
        margin_safety_buffer_percent=
            margin_safety_buffer_percent,
    )


    if not _result_valid(margin_result):

        return _blocked_result(
            decision,
            symbol_name,
            margin_result.get(
                "reason",
                "margin authorization failed",
            ),
            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
            take_profit=tp_result,
            risk_reward=rr_result,
            position_sizing=sizing_result,
            preferred_lot=preferred_result,
            margin=margin_result,
        )


    # ==================================================================
    # 16. FINAL RISK CONSISTENCY CHECKS
    # ==================================================================

    checks = {

        "decision_valid":
            decision in ("BUY", "SELL"),

        "drawdown_authorized":
            _result_valid(drawdown),

        "risk_percent_valid":
            (
                adjusted_risk_percent > 0
                and adjusted_risk_percent
                    <= HARD_MAX_RISK_PERCENT
            ),

        "stop_loss_valid":
            _result_valid(stop_result)
            and (
                (
                    decision == "BUY"
                    and stop_loss < entry_price
                )
                or
                (
                    decision == "SELL"
                    and stop_loss > entry_price
                )
            ),

        "take_profit_valid":
            _result_valid(tp_result)
            and (
                (
                    decision == "BUY"
                    and take_profit > entry_price
                )
                or
                (
                    decision == "SELL"
                    and take_profit < entry_price
                )
            ),

        "rr_valid":
            (
                _result_valid(rr_result)
                and rr_result.get("rr") is not None
                and rr_result["rr"]
                    >= MIN_RR - RR_TOLERANCE
            ),

        "position_size_valid":
            (
                _result_valid(sizing_result)
                and final_volume > 0
            ),

        "preferred_lot_policy_valid":
            _result_valid(preferred_result),

        "margin_authorized":
            _result_valid(margin_result),
    }


    all_checks_passed = all(
        checks.values()
    )


    # ==================================================================
    # 17. FAIL CLOSED
    # ==================================================================

    if not all_checks_passed:

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        return _blocked_result(
            decision,
            symbol_name,
            "one or more final risk checks failed",

            checks=checks,
            failed_checks=failed_checks,

            drawdown=drawdown,
            risk_adjustment=risk_adjustment,
            stop_loss=stop_result,
            take_profit=tp_result,
            risk_reward=rr_result,
            position_sizing=sizing_result,
            preferred_lot=preferred_result,
            margin=margin_result,
        )


    # ==================================================================
    # 18. FINAL RISK-AUTHORIZED TRADE PLAN
    # ==================================================================

    trade_plan = {

        "symbol":
            symbol_name,

        "decision":
            decision,

        "entry":
            entry_price,

        "stop_loss":
            stop_loss,

        "take_profit":
            take_profit,

        "volume":
            final_volume,

        "risk_percent":
            adjusted_risk_percent,

        "risk_reward":
            rr_result["risk_reward"],

        "rr":
            rr_result["rr"],

        "minimum_rr":
            MIN_RR,

        "benchmark_rr":
            BENCHMARK_RR,

        "preferred_lot":
            preferred_lot,

        "preferred_lot_is_hard":
            False,
    }


    # ==================================================================
    # 19. RISK AUTHORIZATION RESULT
    # ==================================================================
    #
    # IMPORTANT:
    #
    # risk_authorized=True means ONLY that the risk-management layer
    # has authorized the trade plan.
    #
    # It does NOT mean:
    #
    #     - Final Gate passed
    #     - Order Builder executed
    #     - Executor executed
    #     - MT5 accepted the order
    #     - A real trade exists
    #
    # The downstream pipeline remains responsible for those stages.
    #

    return {

        "status":
            "READY",

        "risk_authorized":
            True,

        "decision":
            decision,

        "symbol":
            symbol_name,

        "trade_plan":
            trade_plan,

        "drawdown":
            drawdown,

        "risk_adjustment":
            risk_adjustment,

        "stop_loss":
            stop_result,

        "take_profit":
            tp_result,

        "risk_reward":
            rr_result,

        "position_sizing":
            sizing_result,

        "preferred_lot":
            preferred_result,

        "margin":
            margin_result,

        "checks":
            checks,

        "failed_checks":
            [],

        # --------------------------------------------------------------
        # Downstream permissions
        # --------------------------------------------------------------
        #
        # These are deliberately FALSE here.
        #
        # Final Gate owns final downstream authorization.
        #

        "execution_allowed":
            False,

        "order_builder_allowed":
            False,

        "final_gate_required":
            True,

        "final_gate_passed":
            False,

        "mt5_order_check":
            False,

        "mt5_order_send":
            False,

        "real_trade":
            False,

        "reason":
            "all risk-management checks authorized; "
            "awaiting downstream Final Gate",
    }


# ======================================================================
# COMPATIBILITY ALIASES
# ======================================================================

def manage_risk(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility alias for evaluate_risk().
    """

    return evaluate_risk(
        *args,
        **kwargs,
    )


def calculate_risk(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility alias for evaluate_risk().
    """

    return evaluate_risk(
        *args,
        **kwargs,
    )


def authorize_risk(
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility alias for evaluate_risk().
    """

    return evaluate_risk(
        *args,
        **kwargs,
    )


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW INTELLIGENT RISK MANAGER")
    print("==============================================")

    print()
    print("MODULE INFO:")

    print(
        risk_manager_info()
    )

    print()
    print("RR TEST:")

    rr = validate_risk_reward(
        signal="BUY",
        entry=4700.0,
        stop_loss=4680.0,
        take_profit=4760.0,
    )

    print(rr)

    print()
    print("RR ABOVE BENCHMARK TEST:")

    rr_above_benchmark = validate_risk_reward(
        signal="BUY",
        entry=4700.0,
        stop_loss=4680.0,
        take_profit=4770.0,
    )

    print(rr_max)

    print()
    print("RR BELOW MINIMUM TEST:")

    rr_min = validate_risk_reward(
        signal="BUY",
        entry=4700.0,
        stop_loss=4680.0,
        take_profit=4710.0,
    )

    print(rr_min)

    print()
    print("PREFERRED LOT TEST:")

    preferred = apply_preferred_lot_policy(
        calculated_volume=0.01,
        preferred_lot=0.05,
    )

    print(preferred)

    print()
    print("RISK PERCENT TEST:")

    risk = calculate_adjusted_risk_percent(
        base_risk_percent=1.0,
        drawdown_result={
            "valid": True,
            "risk_authorized": True,
            "risk_multiplier": 0.75,
        },
        opportunity_score=85,
    )

    print(risk)

    print()
    print("ZERO DRAWDOWN MULTIPLIER TEST:")

    zero_risk = calculate_adjusted_risk_percent(
        base_risk_percent=1.0,
        drawdown_result={
            "valid": True,
            "risk_authorized": True,
            "risk_multiplier": 0.0,
        },
        opportunity_score=90,
    )

    print(zero_risk)

    print()
    print("NO_TRADE TEST:")

    no_trade = evaluate_risk(
        signal="NO_TRADE",
        symbol="XAUUSD",
        entry=4700.0,
    )

    print(no_trade)

    print()
    print("==============================================")
    print("RISK MANAGER SELF-TEST COMPLETE")
    print("==============================================")


