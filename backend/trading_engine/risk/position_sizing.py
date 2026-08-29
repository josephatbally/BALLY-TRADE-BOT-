"""
BALLY FLOW - Intelligent Broker-Aware Position Sizing Engine

RISK MANAGEMENT BOUNDARY
========================

This module calculates trade volume only.

PIPELINE
--------

    Decision Engine
          |
    Stop Loss Engine
          |
    Take Profit Engine
          |
    POSITION SIZING  <-- this module
          |
    Margin
          |
    Drawdown / Risk Manager
          |
    Final Gate
          |
    Execution
          |
    MT5

RESPONSIBILITIES
----------------

    - Calculate monetary risk from account balance/equity
    - Calculate risk from the actual structural stop loss
    - Calculate broker-aware volume
    - Respect broker minimum volume
    - Respect broker maximum volume
    - Respect broker volume step
    - Respect user's preferred lot as a SOFT preference
    - Adjust risk according to opportunity quality
    - Never exceed the configured hard maximum risk
    - Return a standardized position-sizing result

THIS MODULE DOES NOT
--------------------

    - generate BUY / SELL decisions
    - modify the trading direction
    - calculate technical signals
    - calculate stop loss
    - calculate take profit
    - perform order_check()
    - perform order_send()
    - place orders
    - bypass risk management
    - bypass broker constraints

IMPORTANT
---------

The user's preferred lot is NOT a hard lot.

The engine first determines the maximum safe volume from:

    account risk
    actual stop-loss distance
    broker contract specification

The preferred lot may then influence the final volume only when it
remains inside the calculated risk and broker constraints.

A preferred lot can therefore never force excessive risk.

"""

from __future__ import annotations

from typing import Any, Dict, Optional
import math


# ======================================================================
# MODULE CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Intelligent Position Sizing Engine"
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
# RISK LIMITS
# ----------------------------------------------------------------------

DEFAULT_RISK_PERCENT = 1.0

# Absolute hard ceiling.
# No opportunity-quality adjustment may exceed this.
HARD_MAX_RISK_PERCENT = 2.0

# Minimum meaningful risk allocation.
MIN_RISK_PERCENT = 0.10

# ----------------------------------------------------------------------
# PREFERRED LOT
# ----------------------------------------------------------------------
#
# None means automatic sizing.
#
# A user's preferred lot is intentionally NOT treated as a fixed lot.
#
DEFAULT_PREFERRED_LOT = None

# ----------------------------------------------------------------------
# OPPORTUNITY QUALITY
# ----------------------------------------------------------------------
#
# Quality can influence risk allocation, but never beyond the hard cap.
#
QUALITY_FLOOR = 0.50
QUALITY_CEILING = 1.00

# ----------------------------------------------------------------------
# SAFETY
# ----------------------------------------------------------------------

ALLOW_BROKER_MAX_VOLUME = True
ALLOW_BROKER_MIN_VOLUME = True

# If the broker minimum lot itself would exceed the maximum permitted
# monetary risk, the engine rejects the trade instead of forcing the
# broker minimum.
REJECT_IF_BROKER_MIN_EXCEEDS_RISK = True


# ======================================================================
# OPTIONAL MT5 IMPORT
# ======================================================================

try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True

except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        result = float(value)

        if not math.isfinite(result):
            return None

        return result

    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    """Safely convert a value to integer."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a numeric value."""

    return max(minimum, min(value, maximum))


def _normalize_down(
    value: float,
    step: float,
) -> float:
    """
    Normalize volume DOWN to broker step.

    Downward normalization is intentional because rounding upward could
    increase the actual risk.
    """

    if step <= 0:
        return value

    units = math.floor(
        (value / step) + 1e-12
    )

    return units * step


def _decimal_places(step: float) -> int:
    """Determine sensible decimal places from a volume step."""

    if step <= 0:
        return 8

    text = f"{step:.12f}".rstrip("0")

    if "." not in text:
        return 0

    return len(text.split(".")[1])


def _round_volume(
    volume: float,
    step: float,
) -> float:
    """Round normalized broker volume for clean output."""

    decimals = _decimal_places(step)

    return round(volume, decimals)


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def position_sizing_info() -> Dict[str, Any]:
    """
    Return module architecture and configuration information.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),

        "supported_timeframes": list(
            SUPPORTED_TIMEFRAMES
        ),

        "responsibilities": [
            "account_balance_aware_risk",
            "account_equity_aware_risk",
            "actual_stop_loss_distance",
            "broker_aware_volume",
            "broker_min_volume",
            "broker_max_volume",
            "broker_volume_step",
            "preferred_lot_soft_preference",
            "opportunity_quality_adjustment",
            "hard_max_risk_enforcement",
            "final_volume_normalization",
        ],

        "default_risk_percent": DEFAULT_RISK_PERCENT,

        "hard_max_risk_percent": HARD_MAX_RISK_PERCENT,

        "minimum_risk_percent": MIN_RISK_PERCENT,

        "default_preferred_lot": DEFAULT_PREFERRED_LOT,

        "preferred_lot_is_hard": False,

        "opportunity_quality_enabled": True,

        "broker_aware": True,

        "account_balance_aware": True,

        "account_equity_aware": True,

        "actual_stop_loss_based": True,

        "reject_if_broker_min_exceeds_risk":
            REJECT_IF_BROKER_MIN_EXCEEDS_RISK,

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "stop_loss_calculation": False,
        "take_profit_calculation": False,

        "margin_check": False,
        "drawdown_control": False,

        "execution": False,
        "order_builder": False,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "decision_authority":
            "upstream_decision_engine",

        "risk_authority":
            "downstream_risk_management",
    }


# ======================================================================
# ACCOUNT RISK
# ======================================================================

def calculate_risk_budget(
    account_balance: Any,
    account_equity: Any = None,
    risk_percent: Any = DEFAULT_RISK_PERCENT,
    opportunity_quality: Any = None,
) -> Dict[str, Any]:
    """
    Calculate the monetary risk budget.

    Account equity is preferred when available because it reflects the
    current account state more accurately than the original balance.

    Risk percentage is always capped by HARD_MAX_RISK_PERCENT.
    """

    balance = _safe_float(account_balance)
    equity = _safe_float(account_equity)

    if balance is None or balance <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account balance must be greater than zero",
        }

    # Use equity when valid and positive.
    capital = equity if equity is not None and equity > 0 else balance

    requested_risk = _safe_float(risk_percent)

    if requested_risk is None:
        requested_risk = DEFAULT_RISK_PERCENT

    requested_risk = max(
        MIN_RISK_PERCENT,
        requested_risk,
    )

    # Never allow configured risk to exceed the hard ceiling.
    base_risk_percent = min(
        requested_risk,
        HARD_MAX_RISK_PERCENT,
    )

    # --------------------------------------------------------------
    # Opportunity quality
    # --------------------------------------------------------------

    quality = _safe_float(opportunity_quality)

    if quality is None:
        quality_factor = 1.0
        quality_status = "NOT_PROVIDED"

    else:

        # Accept either 0-1 or 0-100 quality formats.
        if quality > 1.0:
            quality = quality / 100.0

        quality = _clamp(
            quality,
            0.0,
            1.0,
        )

        # Do not amplify risk above the requested base risk.
        #
        # Lower-quality opportunities receive reduced risk.
        # High-quality opportunities retain the requested risk.
        quality_factor = _clamp(
            quality,
            QUALITY_FLOOR,
            QUALITY_CEILING,
        )

        quality_status = "APPLIED"

    adjusted_risk_percent = (
        base_risk_percent * quality_factor
    )

    adjusted_risk_percent = _clamp(
        adjusted_risk_percent,
        MIN_RISK_PERCENT,
        HARD_MAX_RISK_PERCENT,
    )

    risk_amount = (
        capital * adjusted_risk_percent / 100.0
    )

    return {
        "status": "READY",
        "valid": True,

        "account_balance": balance,
        "account_equity": equity,
        "risk_capital": capital,

        "requested_risk_percent": requested_risk,

        "base_risk_percent": base_risk_percent,

        "opportunity_quality": quality,

        "quality_factor": quality_factor,

        "quality_status": quality_status,

        "adjusted_risk_percent":
            adjusted_risk_percent,

        "risk_amount": risk_amount,

        "hard_max_risk_percent":
            HARD_MAX_RISK_PERCENT,

        "hard_max_risk_amount":
            capital * HARD_MAX_RISK_PERCENT / 100.0,
    }


# ======================================================================
# RISK DISTANCE
# ======================================================================

def calculate_risk_distance(
    decision: str,
    entry: Any,
    stop_loss: Any,
) -> Dict[str, Any]:
    """
    Calculate the actual price distance between entry and SL.
    """

    signal = str(decision).upper().strip()

    if signal not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "decision must be BUY or SELL",
        }

    entry_price = _safe_float(entry)
    stop = _safe_float(stop_loss)

    if entry_price is None or entry_price <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "entry price must be greater than zero",
        }

    if stop is None or stop <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "stop loss must be greater than zero",
        }

    if signal == "BUY":

        if stop >= entry_price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "BUY stop loss must be below entry",
            }

    elif signal == "SELL":

        if stop <= entry_price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "SELL stop loss must be above entry",
            }

    distance = abs(
        entry_price - stop
    )

    if distance <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk distance must be greater than zero",
        }

    return {
        "status": "READY",
        "valid": True,
        "decision": signal,
        "entry": entry_price,
        "stop_loss": stop,
        "risk_distance": distance,
    }


# ======================================================================
# BROKER SPECIFICATION
# ======================================================================

def get_broker_volume_spec(
    symbol: str,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Obtain broker volume constraints.

    Uses supplied symbol_info when available.

    Otherwise queries MT5.
    """

    if symbol_info is None:

        if not MT5_AVAILABLE or mt5 is None:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "MT5 unavailable and symbol_info was not supplied",
            }

        try:
            symbol_info = mt5.symbol_info(symbol)

        except Exception as exc:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    f"symbol_info failed: {exc}",
            }

    if symbol_info is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"broker symbol specification unavailable: {symbol}",
        }

    volume_min = _safe_float(
        getattr(symbol_info, "volume_min", None)
    )

    volume_max = _safe_float(
        getattr(symbol_info, "volume_max", None)
    )

    volume_step = _safe_float(
        getattr(symbol_info, "volume_step", None)
    )

    contract_size = _safe_float(
        getattr(symbol_info, "trade_contract_size", None)
    )

    point = _safe_float(
        getattr(symbol_info, "point", None)
    )

    digits = _safe_int(
        getattr(symbol_info, "digits", None)
    )

    if volume_min is None or volume_min <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume_min is unavailable or invalid",
        }

    if volume_max is None or volume_max <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume_max is unavailable or invalid",
        }

    if volume_step is None or volume_step <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume_step is unavailable or invalid",
        }

    if volume_max < volume_min:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume_max is below volume_min",
        }

    return {
        "status": "READY",
        "valid": True,

        "symbol": symbol,

        "volume_min": volume_min,
        "volume_max": volume_max,
        "volume_step": volume_step,

        "contract_size": contract_size,
        "point": point,
        "digits": digits,
    }


# ======================================================================
# MONEY LOSS PER LOT
# ======================================================================

def calculate_loss_per_lot(
    symbol: str,
    entry: float,
    stop_loss: float,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Calculate expected monetary loss for one standard broker lot.

    First preference:

        MT5 order_calc_profit()

    This is the most broker-aware approach because it allows MT5 to
    calculate the monetary result using the broker's symbol settings.

    Fallback:

        contract_size * price_distance

    when sufficient symbol information exists.
    """

    distance_result = calculate_risk_distance(
        "BUY" if entry > stop_loss else "SELL",
        entry,
        stop_loss,
    )

    if not distance_result["valid"]:
        return distance_result

    if not MT5_AVAILABLE or mt5 is None:
        # Fallback requires symbol_info.
        if symbol_info is None:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "MT5 unavailable and symbol_info was not supplied",
            }

    # --------------------------------------------------------------
    # Broker-native profit calculation
    # --------------------------------------------------------------

    if MT5_AVAILABLE and mt5 is not None:

        try:

            action = (
                mt5.ORDER_TYPE_BUY
                if entry > stop_loss
                else mt5.ORDER_TYPE_SELL
            )

            profit = mt5.order_calc_profit(
                action,
                symbol,
                1.0,
                entry,
                stop_loss,
            )

            profit_value = _safe_float(profit)

            if profit_value is not None:

                loss_per_lot = abs(profit_value)

                if loss_per_lot > 0:

                    return {
                        "status": "READY",
                        "valid": True,
                        "method":
                            "mt5.order_calc_profit",
                        "loss_per_lot":
                            loss_per_lot,
                        "risk_distance":
                            abs(entry - stop_loss),
                    }

        except Exception:
            pass

    # --------------------------------------------------------------
    # Contract-size fallback
    # --------------------------------------------------------------

    if symbol_info is None:

        try:
            symbol_info = mt5.symbol_info(symbol)

        except Exception:
            symbol_info = None

    if symbol_info is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "unable to obtain broker contract specification",
        }

    contract_size = _safe_float(
        getattr(
            symbol_info,
            "trade_contract_size",
            None,
        )
    )

    if contract_size is None or contract_size <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker contract size unavailable",
        }

    distance = abs(
        entry - stop_loss
    )

    loss_per_lot = (
        distance * contract_size
    )

    if loss_per_lot <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "calculated loss per lot is invalid",
        }

    return {
        "status": "READY",
        "valid": True,
        "method": "contract_size_fallback",
        "loss_per_lot": loss_per_lot,
        "risk_distance": distance,
        "contract_size": contract_size,
    }


# ======================================================================
# VOLUME FROM RISK
# ======================================================================

def calculate_volume_from_risk(
    risk_amount: float,
    loss_per_lot: float,
) -> Dict[str, Any]:
    """
    Calculate theoretical volume before broker constraints.
    """

    if risk_amount <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "risk amount must be greater than zero",
        }

    if loss_per_lot <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "loss per lot must be greater than zero",
        }

    theoretical_volume = (
        risk_amount / loss_per_lot
    )

    if theoretical_volume <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "theoretical volume is invalid",
        }

    return {
        "status": "READY",
        "valid": True,
        "theoretical_volume":
            theoretical_volume,
    }


# ======================================================================
# BROKER VOLUME NORMALIZATION
# ======================================================================

def normalize_broker_volume(
    theoretical_volume: float,
    broker_spec: Dict[str, Any],
    maximum_safe_volume: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Normalize volume according to broker limits.

    The volume is always rounded DOWN to avoid increasing risk.
    """

    if not isinstance(broker_spec, dict):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "broker specification is invalid",
        }

    volume_min = _safe_float(
        broker_spec.get("volume_min")
    )

    volume_max = _safe_float(
        broker_spec.get("volume_max")
    )

    volume_step = _safe_float(
        broker_spec.get("volume_step")
    )

    if (
        volume_min is None
        or volume_max is None
        or volume_step is None
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume constraints are incomplete",
        }

    if theoretical_volume <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "theoretical volume must be greater than zero",
        }

    safe_volume = theoretical_volume

    if maximum_safe_volume is not None:

        safe_limit = _safe_float(
            maximum_safe_volume
        )

        if safe_limit is not None:
            safe_volume = min(
                safe_volume,
                safe_limit,
            )

    if ALLOW_BROKER_MAX_VOLUME:
        safe_volume = min(
            safe_volume,
            volume_max,
        )

    normalized = _normalize_down(
        safe_volume,
        volume_step,
    )

    # --------------------------------------------------------------
    # Broker minimum handling
    # --------------------------------------------------------------

    if normalized < volume_min:

        # If the minimum broker lot itself exceeds the available
        # risk capacity, reject rather than increasing risk.
        if (
            REJECT_IF_BROKER_MIN_EXCEEDS_RISK
            and maximum_safe_volume is not None
            and volume_min > maximum_safe_volume
        ):
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "broker minimum volume exceeds safe risk limit",
                "theoretical_volume":
                    theoretical_volume,
                "maximum_safe_volume":
                    maximum_safe_volume,
                "broker_min":
                    volume_min,
            }

        normalized = volume_min

    normalized = min(
        normalized,
        volume_max,
    )

    normalized = _round_volume(
        normalized,
        volume_step,
    )

    if normalized <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "normalized broker volume is invalid",
        }

    return {
        "status": "READY",
        "valid": True,

        "theoretical_volume":
            theoretical_volume,

        "normalized_volume":
            normalized,

        "broker_min":
            volume_min,

        "broker_max":
            volume_max,

        "broker_step":
            volume_step,
    }


# ======================================================================
# PREFERRED LOT APPLICATION
# ======================================================================

def apply_preferred_lot(
    calculated_volume: float,
    preferred_lot: Any,
    broker_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply the user's preferred lot as a SOFT preference.

    Rules:

        calculated volume is the risk ceiling.

        preferred lot <= calculated volume
            -> preferred lot may be used.

        preferred lot > calculated volume
            -> calculated volume remains authoritative.

    Therefore the user cannot accidentally override risk controls.
    """

    calculated = _safe_float(
        calculated_volume
    )

    if calculated is None or calculated <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "calculated volume is invalid",
        }

    preferred = _safe_float(
        preferred_lot
    )

    if preferred is None or preferred <= 0:
        return {
            "status": "READY",
            "valid": True,
            "selected_volume": calculated,
            "preferred_lot": None,
            "preference_applied": False,
            "reason":
                "automatic risk-based volume retained",
        }

    volume_min = _safe_float(
        broker_spec.get("volume_min")
    )

    volume_max = _safe_float(
        broker_spec.get("volume_max")
    )

    volume_step = _safe_float(
        broker_spec.get("volume_step")
    )

    if (
        volume_min is None
        or volume_max is None
        or volume_step is None
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "broker volume specification incomplete",
        }

    # The preferred lot is capped by the risk-calculated volume.
    selected = min(
        preferred,
        calculated,
    )

    selected = min(
        selected,
        volume_max,
    )

    selected = _normalize_down(
        selected,
        volume_step,
    )

    if selected < volume_min:

        # Do NOT automatically raise to broker minimum if doing so
        # would defeat the risk calculation.
        if calculated < volume_min:

            return {
                "status": "READY",
                "valid": True,
                "selected_volume": calculated,
                "preferred_lot": preferred,
                "preference_applied": False,
                "reason":
                    "preferred lot is below broker minimum; "
                    "risk-based volume retained",
            }

        selected = volume_min

    selected = _round_volume(
        selected,
        volume_step,
    )

    preference_applied = (
        abs(selected - preferred) < 1e-12
    )

    reason = (
        "preferred lot applied within risk limit"
        if preference_applied
        else
        "preferred lot reduced to remain within risk limit"
    )

    return {
        "status": "READY",
        "valid": True,

        "selected_volume":
            selected,

        "preferred_lot":
            preferred,

        "preference_applied":
            preference_applied,

        "reason":
            reason,
    }


# ======================================================================
# FINAL RISK VERIFICATION
# ======================================================================

def verify_final_risk(
    volume: float,
    loss_per_lot: float,
    risk_amount: float,
    hard_max_risk_amount: float,
) -> Dict[str, Any]:
    """
    Verify actual monetary risk after volume normalization.
    """

    actual_risk = (
        volume * loss_per_lot
    )

    hard_limit_passed = (
        actual_risk
        <= hard_max_risk_amount + 1e-9
    )

    requested_limit_passed = (
        actual_risk
        <= risk_amount + 1e-9
    )

    passed = (
        hard_limit_passed
        and requested_limit_passed
    )

    return {
        "status":
            "READY" if passed else "BLOCKED",

        "valid":
            passed,

        "actual_risk_amount":
            actual_risk,

        "requested_risk_amount":
            risk_amount,

        "hard_max_risk_amount":
            hard_max_risk_amount,

        "requested_limit_passed":
            requested_limit_passed,

        "hard_limit_passed":
            hard_limit_passed,

        "risk_utilization_percent": (
            (
                actual_risk
                / hard_max_risk_amount
            ) * 100.0
            if hard_max_risk_amount > 0
            else 0.0
        ),

        "reason":
            "final risk verified"
            if passed
            else
            "final volume exceeds risk authorization",
    }


# ======================================================================
# COMPLETE POSITION SIZING
# ======================================================================

def calculate_position_size(
    decision: str,
    symbol: str,
    entry: Any,
    stop_loss: Any,
    account_balance: Any,
    account_equity: Any = None,
    risk_percent: Any = DEFAULT_RISK_PERCENT,
    preferred_lot: Any = DEFAULT_PREFERRED_LOT,
    opportunity_quality: Any = None,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Complete intelligent position-sizing calculation.

    This is the primary public API.

    No order is created or sent here.
    """

    # --------------------------------------------------------------
    # 1. Validate decision
    # --------------------------------------------------------------

    signal = str(
        decision
    ).upper().strip()

    if signal not in SUPPORTED_SIGNALS:

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "unsupported trading decision",
            "decision":
                signal,
        }

    if signal == "NO_TRADE":

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": "NO_TRADE",
            "reason":
                "position sizing is unavailable for NO_TRADE",
        }

    # --------------------------------------------------------------
    # 2. Validate symbol
    # --------------------------------------------------------------

    if not isinstance(symbol, str) or not symbol.strip():

        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "symbol is required",
        }

    symbol = symbol.strip()

    # --------------------------------------------------------------
    # 3. Risk budget
    # --------------------------------------------------------------

    risk_budget = calculate_risk_budget(
        account_balance=account_balance,
        account_equity=account_equity,
        risk_percent=risk_percent,
        opportunity_quality=opportunity_quality,
    )

    if not risk_budget["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "reason":
                risk_budget["reason"],
        }

    # --------------------------------------------------------------
    # 4. Actual SL distance
    # --------------------------------------------------------------

    distance = calculate_risk_distance(
        decision=signal,
        entry=entry,
        stop_loss=stop_loss,
    )

    if not distance["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "reason":
                distance["reason"],
        }

    entry_price = distance["entry"]
    stop = distance["stop_loss"]

    # --------------------------------------------------------------
    # 5. Broker volume specification
    # --------------------------------------------------------------

    broker_spec = get_broker_volume_spec(
        symbol=symbol,
        symbol_info=symbol_info,
    )

    if not broker_spec["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "reason":
                broker_spec["reason"],
        }

    # --------------------------------------------------------------
    # 6. Monetary loss per lot
    # --------------------------------------------------------------

    loss_result = calculate_loss_per_lot(
        symbol=symbol,
        entry=entry_price,
        stop_loss=stop,
        symbol_info=symbol_info,
    )

    if not loss_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "loss_per_lot": loss_result,
            "reason":
                loss_result["reason"],
        }

    loss_per_lot = loss_result["loss_per_lot"]

    # --------------------------------------------------------------
    # 7. Calculate theoretical volume
    # --------------------------------------------------------------

    volume_result = calculate_volume_from_risk(
        risk_amount=risk_budget["risk_amount"],
        loss_per_lot=loss_per_lot,
    )

    if not volume_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "loss_per_lot": loss_result,
            "volume": volume_result,
            "reason":
                volume_result["reason"],
        }

    theoretical_volume = (
        volume_result["theoretical_volume"]
    )

    # --------------------------------------------------------------
    # 8. Maximum safe volume from hard risk ceiling
    # --------------------------------------------------------------

    hard_max_volume = (
        risk_budget["hard_max_risk_amount"]
        / loss_per_lot
    )

    maximum_safe_volume = min(
        theoretical_volume,
        hard_max_volume,
    )

    # --------------------------------------------------------------
    # 9. Broker normalization
    # --------------------------------------------------------------

    normalized_result = normalize_broker_volume(
        theoretical_volume=theoretical_volume,
        broker_spec=broker_spec,
        maximum_safe_volume=maximum_safe_volume,
    )

    if not normalized_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "loss_per_lot": loss_result,
            "theoretical_volume":
                theoretical_volume,
            "maximum_safe_volume":
                maximum_safe_volume,
            "normalization":
                normalized_result,
            "reason":
                normalized_result["reason"],
        }

    calculated_volume = (
        normalized_result["normalized_volume"]
    )

    # --------------------------------------------------------------
    # 10. Apply preferred lot softly
    # --------------------------------------------------------------

    preference_result = apply_preferred_lot(
        calculated_volume=calculated_volume,
        preferred_lot=preferred_lot,
        broker_spec=broker_spec,
    )

    if not preference_result["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "loss_per_lot": loss_result,
            "normalization": normalized_result,
            "preferred_lot":
                preferred_lot,
            "preference":
                preference_result,
            "reason":
                preference_result["reason"],
        }

    final_volume = (
        preference_result["selected_volume"]
    )

    # --------------------------------------------------------------
    # 11. Final risk verification
    # --------------------------------------------------------------

    final_risk = verify_final_risk(
        volume=final_volume,
        loss_per_lot=loss_per_lot,
        risk_amount=risk_budget["risk_amount"],
        hard_max_risk_amount=
            risk_budget["hard_max_risk_amount"],
    )

    if not final_risk["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "decision": signal,
            "symbol": symbol,
            "risk_budget": risk_budget,
            "risk_distance": distance,
            "broker": broker_spec,
            "loss_per_lot": loss_result,
            "normalization": normalized_result,
            "preference": preference_result,
            "final_risk": final_risk,
            "reason":
                final_risk["reason"],
        }

    # --------------------------------------------------------------
    # 12. Final result
    # --------------------------------------------------------------

    return {
        "status": "READY",
        "valid": True,

        "decision": signal,
        "symbol": symbol,

        "entry": entry_price,
        "stop_loss": stop,

        "risk_distance":
            distance["risk_distance"],

        "account_balance":
            risk_budget["account_balance"],

        "account_equity":
            risk_budget["account_equity"],

        "risk_capital":
            risk_budget["risk_capital"],

        "requested_risk_percent":
            risk_budget["requested_risk_percent"],

        "base_risk_percent":
            risk_budget["base_risk_percent"],

        "opportunity_quality":
            risk_budget["opportunity_quality"],

        "quality_factor":
            risk_budget["quality_factor"],

        "adjusted_risk_percent":
            risk_budget["adjusted_risk_percent"],

        "risk_amount":
            risk_budget["risk_amount"],

        "hard_max_risk_percent":
            risk_budget["hard_max_risk_percent"],

        "hard_max_risk_amount":
            risk_budget["hard_max_risk_amount"],

        "broker":
            broker_spec,

        "loss_per_lot":
            loss_per_lot,

        "loss_calculation_method":
            loss_result.get("method"),

        "theoretical_volume":
            theoretical_volume,

        "maximum_safe_volume":
            maximum_safe_volume,

        "broker_normalized_volume":
            calculated_volume,

        "preferred_lot":
            preference_result.get(
                "preferred_lot"
            ),

        "preferred_lot_applied":
            preference_result.get(
                "preference_applied"
            ),

        "volume":
            final_volume,

        "actual_risk_amount":
            final_risk["actual_risk_amount"],

        "risk_utilization_percent":
            final_risk[
                "risk_utilization_percent"
            ],

        "risk_verified": True,

        "decision_authority":
            "upstream_decision_engine",

        "risk_authority":
            "position_sizing",

        "execution_allowed":
            False,

        "mt5_order_check":
            False,

        "mt5_order_send":
            False,
    }


# ======================================================================
# COMPATIBILITY API
# ======================================================================

def calculate_lot_size(
    decision: str,
    symbol: str,
    entry: Any,
    stop_loss: Any,
    account_balance: Any,
    account_equity: Any = None,
    risk_percent: Any = DEFAULT_RISK_PERCENT,
    preferred_lot: Any = DEFAULT_PREFERRED_LOT,
    opportunity_quality: Any = None,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Compatibility alias for existing engine integrations.
    """

    return calculate_position_size(
        decision=decision,
        symbol=symbol,
        entry=entry,
        stop_loss=stop_loss,
        account_balance=account_balance,
        account_equity=account_equity,
        risk_percent=risk_percent,
        preferred_lot=preferred_lot,
        opportunity_quality=opportunity_quality,
        symbol_info=symbol_info,
    )


def position_size(
    decision: str,
    symbol: str,
    entry: Any,
    stop_loss: Any,
    account_balance: Any,
    account_equity: Any = None,
    risk_percent: Any = DEFAULT_RISK_PERCENT,
    preferred_lot: Any = DEFAULT_PREFERRED_LOT,
    opportunity_quality: Any = None,
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Short compatibility entry point.
    """

    return calculate_position_size(
        decision=decision,
        symbol=symbol,
        entry=entry,
        stop_loss=stop_loss,
        account_balance=account_balance,
        account_equity=account_equity,
        risk_percent=risk_percent,
        preferred_lot=preferred_lot,
        opportunity_quality=opportunity_quality,
        symbol_info=symbol_info,
    )


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW POSITION SIZING ENGINE")
    print("==============================================")

    print("INFO:")
    print(position_sizing_info())

    if MT5_AVAILABLE and mt5 is not None:

        try:

            if mt5.initialize():

                account = mt5.account_info()
                symbol_info = mt5.symbol_info(
                    "XAUUSD"
                )

                if account and symbol_info:

                    balance = getattr(
                        account,
                        "balance",
                        None,
                    )

                    equity = getattr(
                        account,
                        "equity",
                        None,
                    )

                    result = calculate_position_size(
                        decision="BUY",
                        symbol="XAUUSD",
                        entry=4700.0,
                        stop_loss=4685.0,
                        account_balance=balance,
                        account_equity=equity,
                        risk_percent=1.0,
                        preferred_lot=None,
                        opportunity_quality=0.85,
                        symbol_info=symbol_info,
                    )

                    print("RESULT:")
                    print(result)

                mt5.shutdown()

        except Exception as exc:

            print(
                "SELF-TEST ERROR:",
                exc,
            )