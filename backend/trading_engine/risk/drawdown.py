"""
BALLY FLOW - Intelligent Drawdown Risk Engine

ACCOUNT-LEVEL RISK CONTROL
==========================

This module is responsible for protecting the trading account from
excessive drawdown.

PIPELINE
--------

    Decision Engine
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
    Risk Manager
          |
    Final Gate
          |
    Execution

IMPORTANT
---------

This module DOES NOT:

    - generate BUY / SELL decisions
    - modify BUY / SELL decisions
    - perform technical analysis
    - perform fundamental analysis
    - calculate stop loss
    - calculate take profit
    - calculate lot size
    - perform margin calculation
    - build orders
    - communicate with MT5 order_send()
    - place trades

It only determines whether account-level drawdown permits the
proposed trade risk.

INTELLIGENT RISK BEHAVIOUR
--------------------------

The engine does not immediately stop trading whenever drawdown
appears.

Instead it uses progressive protection:

    NORMAL
       |
       v
    CAUTION
       |
       v
    REDUCED RISK
       |
       v
    HIGH RISK
       |
       v
    HARD BLOCK

This allows the Risk Manager / Position Sizing Engine to reduce
risk intelligently while protecting the account.

The drawdown engine therefore controls AUTHORIZATION and RISK
MULTIPLIER, not position size directly.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, date


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Intelligent Drawdown Risk Engine"
VERSION = "1.0.0"

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

# ----------------------------------------------------------------------
# ACCOUNT DRAWDOWN LIMITS
# ----------------------------------------------------------------------

# Normal maximum account drawdown.
DEFAULT_MAX_DRAWDOWN_PERCENT = 20.0

# Drawdown at which risk reduction begins.
CAUTION_DRAWDOWN_PERCENT = 5.0

# Drawdown at which stronger risk reduction begins.
REDUCED_RISK_DRAWDOWN_PERCENT = 10.0

# Drawdown at which trading becomes highly restricted.
HIGH_RISK_DRAWDOWN_PERCENT = 15.0

# Absolute hard block.
HARD_BLOCK_DRAWDOWN_PERCENT = 20.0

# ----------------------------------------------------------------------
# DAILY LOSS LIMITS
# ----------------------------------------------------------------------

DEFAULT_MAX_DAILY_LOSS_PERCENT = 5.0

DAILY_CAUTION_PERCENT = 2.0
DAILY_REDUCED_RISK_PERCENT = 3.0
DAILY_HIGH_RISK_PERCENT = 4.0

# ----------------------------------------------------------------------
# RISK MULTIPLIERS
# ----------------------------------------------------------------------

# These multipliers do not change the lot directly.
# Position sizing may consume this value later.

NORMAL_RISK_MULTIPLIER = 1.00
CAUTION_RISK_MULTIPLIER = 0.75
REDUCED_RISK_MULTIPLIER = 0.50
HIGH_RISK_MULTIPLIER = 0.25
BLOCK_RISK_MULTIPLIER = 0.00

# ----------------------------------------------------------------------
# EQUITY SAFETY
# ----------------------------------------------------------------------

# If equity falls below this percentage of balance, account is under
# significant pressure.
MIN_EQUITY_RATIO_PERCENT = 80.0

# ----------------------------------------------------------------------
# DATA QUALITY
# ----------------------------------------------------------------------

MIN_VALID_BALANCE = 0.0
MIN_VALID_EQUITY = 0.0


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        number = float(value)

        if number != number:  # NaN
            return None

        return number

    except (TypeError, ValueError):
        return None


def _safe_percent(
    numerator: float,
    denominator: float,
) -> Optional[float]:
    """Safely calculate a percentage."""

    if denominator <= 0:
        return None

    return (numerator / denominator) * 100.0


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a value inside a specified range."""

    return max(minimum, min(value, maximum))


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def drawdown_info() -> Dict[str, Any]:
    """
    Return architecture and configuration information.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "supported_signals": list(SUPPORTED_SIGNALS),

        "responsibilities": [
            "account_balance_monitoring",
            "account_equity_monitoring",
            "current_drawdown_calculation",
            "daily_loss_monitoring",
            "drawdown_regime_classification",
            "progressive_risk_reduction",
            "hard_drawdown_block",
            "account_equity_safety_check",
            "risk_authorization",
        ],

        "default_max_drawdown_percent":
            DEFAULT_MAX_DRAWDOWN_PERCENT,

        "caution_drawdown_percent":
            CAUTION_DRAWDOWN_PERCENT,

        "reduced_risk_drawdown_percent":
            REDUCED_RISK_DRAWDOWN_PERCENT,

        "high_risk_drawdown_percent":
            HIGH_RISK_DRAWDOWN_PERCENT,

        "hard_block_drawdown_percent":
            HARD_BLOCK_DRAWDOWN_PERCENT,

        "default_max_daily_loss_percent":
            DEFAULT_MAX_DAILY_LOSS_PERCENT,

        "risk_multipliers": {
            "NORMAL": NORMAL_RISK_MULTIPLIER,
            "CAUTION": CAUTION_RISK_MULTIPLIER,
            "REDUCED_RISK": REDUCED_RISK_MULTIPLIER,
            "HIGH_RISK": HIGH_RISK_MULTIPLIER,
            "BLOCK": BLOCK_RISK_MULTIPLIER,
        },

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "decision_generation": False,
        "decision_override": False,

        "stop_loss_calculation": False,
        "take_profit_calculation": False,
        "position_sizing": False,
        "margin_check": False,

        "execution": False,
        "order_builder": False,
        "mt5_order_check": False,
        "mt5_order_send": False,

        "lot_modification": False,

        "risk_management": True,

        "decision_authority": "upstream_decision_engine",
        "risk_authority": "downstream_risk_management",

        "drawdown_authority": "this_module",
    }


# ======================================================================
# CURRENT DRAWDOWN
# ======================================================================

def calculate_current_drawdown(
    balance: Any,
    equity: Any,
) -> Dict[str, Any]:
    """
    Calculate current equity drawdown relative to account balance.

    Formula:

        drawdown = (balance - equity) / balance * 100

    Positive value means equity is below balance.

    Negative value means equity is above balance and therefore there
    is no current drawdown.
    """

    balance_value = _safe_float(balance)
    equity_value = _safe_float(equity)

    if balance_value is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid account balance",
        }

    if equity_value is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid account equity",
        }

    if balance_value <= MIN_VALID_BALANCE:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account balance must be greater than zero",
        }

    if equity_value < MIN_VALID_EQUITY:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account equity cannot be negative",
        }

    equity_difference = balance_value - equity_value

    raw_drawdown = (
        equity_difference / balance_value
    ) * 100.0

    # Only positive loss relative to balance is considered drawdown.
    drawdown_percent = max(0.0, raw_drawdown)

    equity_ratio = (
        equity_value / balance_value
    ) * 100.0

    return {
        "status": "READY",
        "valid": True,

        "balance": balance_value,
        "equity": equity_value,

        "equity_difference": equity_difference,

        "drawdown_percent": round(
            drawdown_percent,
            4,
        ),

        "equity_ratio_percent": round(
            equity_ratio,
            4,
        ),

        "in_drawdown": drawdown_percent > 0.0,

        "profitable_equity": equity_value > balance_value,
    }


# ======================================================================
# DAILY LOSS
# ======================================================================

def calculate_daily_loss(
    starting_day_balance: Any,
    current_equity: Any,
) -> Dict[str, Any]:
    """
    Calculate loss relative to the starting balance of the trading day.

    This function intentionally accepts the daily starting balance
    from the caller rather than inventing it.
    """

    start_balance = _safe_float(starting_day_balance)
    equity = _safe_float(current_equity)

    if start_balance is None or start_balance <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid starting day balance",
        }

    if equity is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid current equity",
        }

    loss_amount = max(
        0.0,
        start_balance - equity,
    )

    loss_percent = (
        loss_amount / start_balance
    ) * 100.0

    return {
        "status": "READY",
        "valid": True,

        "starting_day_balance": start_balance,
        "current_equity": equity,

        "daily_loss_amount": round(
            loss_amount,
            4,
        ),

        "daily_loss_percent": round(
            loss_percent,
            4,
        ),

        "daily_loss_active": loss_amount > 0.0,
    }


# ======================================================================
# DRAWDOWN REGIME
# ======================================================================

def classify_drawdown(
    drawdown_percent: Any,
    daily_loss_percent: Any = 0.0,
    max_drawdown_percent: float =
        DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_daily_loss_percent: float =
        DEFAULT_MAX_DAILY_LOSS_PERCENT,
) -> Dict[str, Any]:
    """
    Classify account risk according to current drawdown and daily loss.

    The more severe condition always wins.
    """

    drawdown = _safe_float(drawdown_percent)
    daily_loss = _safe_float(daily_loss_percent)

    max_dd = _safe_float(max_drawdown_percent)
    max_daily = _safe_float(max_daily_loss_percent)

    if drawdown is None or drawdown < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid drawdown percentage",
        }

    if daily_loss is None or daily_loss < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid daily loss percentage",
        }

    if max_dd is None or max_dd <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid maximum drawdown",
        }

    if max_daily is None or max_daily <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid maximum daily loss",
        }

    # --------------------------------------------------------------
    # HARD BLOCK
    # --------------------------------------------------------------

    if (
        drawdown >= max_dd
        or drawdown >= HARD_BLOCK_DRAWDOWN_PERCENT
        or daily_loss >= max_daily
    ):
        return {
            "status": "READY",
            "valid": True,
            "regime": "BLOCK",
            "risk_multiplier": BLOCK_RISK_MULTIPLIER,
            "authorization": False,
            "reason": "maximum account or daily drawdown exceeded",
        }

    # --------------------------------------------------------------
    # HIGH RISK
    # --------------------------------------------------------------

    if (
        drawdown >= HIGH_RISK_DRAWDOWN_PERCENT
        or daily_loss >= DAILY_HIGH_RISK_PERCENT
    ):
        return {
            "status": "READY",
            "valid": True,
            "regime": "HIGH_RISK",
            "risk_multiplier": HIGH_RISK_MULTIPLIER,
            "authorization": True,
            "reason": "account is under high drawdown pressure",
        }

    # --------------------------------------------------------------
    # REDUCED RISK
    # --------------------------------------------------------------

    if (
        drawdown >= REDUCED_RISK_DRAWDOWN_PERCENT
        or daily_loss >= DAILY_REDUCED_RISK_PERCENT
    ):
        return {
            "status": "READY",
            "valid": True,
            "regime": "REDUCED_RISK",
            "risk_multiplier": REDUCED_RISK_MULTIPLIER,
            "authorization": True,
            "reason": "account drawdown requires reduced risk",
        }

    # --------------------------------------------------------------
    # CAUTION
    # --------------------------------------------------------------

    if (
        drawdown >= CAUTION_DRAWDOWN_PERCENT
        or daily_loss >= DAILY_CAUTION_PERCENT
    ):
        return {
            "status": "READY",
            "valid": True,
            "regime": "CAUTION",
            "risk_multiplier": CAUTION_RISK_MULTIPLIER,
            "authorization": True,
            "reason": "account drawdown requires caution",
        }

    # --------------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------------

    return {
        "status": "READY",
        "valid": True,
        "regime": "NORMAL",
        "risk_multiplier": NORMAL_RISK_MULTIPLIER,
        "authorization": True,
        "reason": "account drawdown is within normal range",
    }


# ======================================================================
# EQUITY SAFETY
# ======================================================================

def check_equity_safety(
    balance: Any,
    equity: Any,
    minimum_equity_ratio_percent:
        float = MIN_EQUITY_RATIO_PERCENT,
) -> Dict[str, Any]:
    """
    Verify that equity has not fallen below the configured
    percentage of account balance.
    """

    balance_value = _safe_float(balance)
    equity_value = _safe_float(equity)
    minimum_ratio = _safe_float(
        minimum_equity_ratio_percent
    )

    if balance_value is None or balance_value <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "safe": False,
            "reason": "invalid balance",
        }

    if equity_value is None or equity_value < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "safe": False,
            "reason": "invalid equity",
        }

    if minimum_ratio is None or not (
        0.0 < minimum_ratio <= 100.0
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "safe": False,
            "reason": "invalid minimum equity ratio",
        }

    equity_ratio = (
        equity_value / balance_value
    ) * 100.0

    safe = equity_ratio >= minimum_ratio

    return {
        "status": "READY",
        "valid": True,
        "safe": safe,

        "balance": balance_value,
        "equity": equity_value,

        "equity_ratio_percent": round(
            equity_ratio,
            4,
        ),

        "minimum_equity_ratio_percent":
            minimum_ratio,

        "reason": (
            "equity remains above safety threshold"
            if safe
            else "equity has fallen below safety threshold"
        ),
    }


# ======================================================================
# INTELLIGENT RISK MULTIPLIER
# ======================================================================

def calculate_risk_multiplier(
    drawdown_percent: Any,
    daily_loss_percent: Any = 0.0,
    max_drawdown_percent: float =
        DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_daily_loss_percent: float =
        DEFAULT_MAX_DAILY_LOSS_PERCENT,
) -> Dict[str, Any]:
    """
    Calculate the account-level risk multiplier.

    This is deliberately separate from position sizing.

    Example:

        NORMAL       -> 1.00
        CAUTION      -> 0.75
        REDUCED_RISK -> 0.50
        HIGH_RISK    -> 0.25
        BLOCK        -> 0.00
    """

    classification = classify_drawdown(
        drawdown_percent=drawdown_percent,
        daily_loss_percent=daily_loss_percent,
        max_drawdown_percent=max_drawdown_percent,
        max_daily_loss_percent=max_daily_loss_percent,
    )

    if not classification["valid"]:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_multiplier": 0.0,
            "classification": classification,
        }

    return {
        "status": "READY",
        "valid": True,

        "regime": classification["regime"],

        "risk_multiplier": classification[
            "risk_multiplier"
        ],

        "authorization": classification[
            "authorization"
        ],

        "reason": classification["reason"],
    }


# ======================================================================
# COMPLETE DRAWDOWN AUTHORIZATION
# ======================================================================

def evaluate_drawdown(
    balance: Any,
    equity: Any,
    starting_day_balance: Optional[Any] = None,
    max_drawdown_percent: float =
        DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_daily_loss_percent: float =
        DEFAULT_MAX_DAILY_LOSS_PERCENT,
    minimum_equity_ratio_percent:
        float = MIN_EQUITY_RATIO_PERCENT,
) -> Dict[str, Any]:
    """
    Complete intelligent account-level drawdown evaluation.

    This is the main API intended for Risk Manager integration.
    """

    # --------------------------------------------------------------
    # 1. Current account drawdown
    # --------------------------------------------------------------

    current = calculate_current_drawdown(
        balance=balance,
        equity=equity,
    )

    if not current["valid"]:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "risk_multiplier": 0.0,
            "reason": current["reason"],
            "current_drawdown": current,
        }

    # --------------------------------------------------------------
    # 2. Daily loss
    # --------------------------------------------------------------

    if starting_day_balance is None:

        daily = {
            "status": "NOT_AVAILABLE",
            "valid": True,
            "daily_loss_amount": None,
            "daily_loss_percent": 0.0,
            "daily_loss_active": False,
            "reason": "daily starting balance not supplied",
        }

    else:

        daily = calculate_daily_loss(
            starting_day_balance=starting_day_balance,
            current_equity=equity,
        )

        if not daily["valid"]:
            return {
                "status": "BLOCKED",
                "valid": False,
                "risk_authorized": False,
                "risk_multiplier": 0.0,
                "reason": daily["reason"],
                "current_drawdown": current,
                "daily_loss": daily,
            }

    # --------------------------------------------------------------
    # 3. Equity safety
    # --------------------------------------------------------------

    equity_safety = check_equity_safety(
        balance=balance,
        equity=equity,
        minimum_equity_ratio_percent=
            minimum_equity_ratio_percent,
    )

    if not equity_safety["valid"]:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "risk_multiplier": 0.0,
            "reason": equity_safety["reason"],
            "current_drawdown": current,
            "daily_loss": daily,
            "equity_safety": equity_safety,
        }

    # --------------------------------------------------------------
    # 4. Risk classification
    # --------------------------------------------------------------

    daily_loss_percent = daily.get(
        "daily_loss_percent",
        0.0,
    )

    multiplier = calculate_risk_multiplier(
        drawdown_percent=current[
            "drawdown_percent"
        ],
        daily_loss_percent=daily_loss_percent,
        max_drawdown_percent=max_drawdown_percent,
        max_daily_loss_percent=max_daily_loss_percent,
    )

    if not multiplier["valid"]:
        return {
            "status": "BLOCKED",
            "valid": False,
            "risk_authorized": False,
            "risk_multiplier": 0.0,
            "reason": multiplier.get(
                "reason",
                "drawdown classification failed",
            ),
        }

    # --------------------------------------------------------------
    # 5. Combine account-level protections
    # --------------------------------------------------------------

    regime = multiplier["regime"]

    risk_authorized = bool(
        multiplier["authorization"]
        and equity_safety["safe"]
    )

    risk_multiplier = float(
        multiplier["risk_multiplier"]
    )

    # Equity safety failure is a hard protection.
    if not equity_safety["safe"]:
        risk_authorized = False
        risk_multiplier = 0.0
        regime = "BLOCK"

    # --------------------------------------------------------------
    # 6. Final result
    # --------------------------------------------------------------

    return {
        "status": "READY",
        "valid": True,

        "risk_authorized": risk_authorized,

        "regime": regime,

        "risk_multiplier": round(
            risk_multiplier,
            4,
        ),

        "balance": current["balance"],
        "equity": current["equity"],

        "current_drawdown_percent":
            current["drawdown_percent"],

        "equity_ratio_percent":
            current["equity_ratio_percent"],

        "daily_loss_percent":
            daily_loss_percent,

        "daily_loss_amount":
            daily.get("daily_loss_amount"),

        "max_drawdown_percent":
            max_drawdown_percent,

        "max_daily_loss_percent":
            max_daily_loss_percent,

        "equity_safety": equity_safety,

        "current_drawdown": current,

        "daily_loss": daily,

        "reason": (
            "drawdown risk authorized"
            if risk_authorized
            else "drawdown protection blocked risk"
        ),

        "timestamp": datetime.utcnow().isoformat(
            timespec="seconds"
        ) + "Z",
    }


# ======================================================================
# COMPATIBILITY API
# ======================================================================

def check_drawdown(
    balance: Any,
    equity: Any,
    starting_day_balance: Optional[Any] = None,
    max_drawdown_percent: float =
        DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_daily_loss_percent: float =
        DEFAULT_MAX_DAILY_LOSS_PERCENT,
    minimum_equity_ratio_percent:
        float = MIN_EQUITY_RATIO_PERCENT,
) -> Dict[str, Any]:
    """
    Compatibility API for Risk Manager.
    """

    return evaluate_drawdown(
        balance=balance,
        equity=equity,
        starting_day_balance=starting_day_balance,
        max_drawdown_percent=max_drawdown_percent,
        max_daily_loss_percent=max_daily_loss_percent,
        minimum_equity_ratio_percent=
            minimum_equity_ratio_percent,
    )


def authorize_drawdown(
    balance: Any,
    equity: Any,
    starting_day_balance: Optional[Any] = None,
    max_drawdown_percent: float =
        DEFAULT_MAX_DRAWDOWN_PERCENT,
    max_daily_loss_percent: float =
        DEFAULT_MAX_DAILY_LOSS_PERCENT,
    minimum_equity_ratio_percent:
        float = MIN_EQUITY_RATIO_PERCENT,
) -> Dict[str, Any]:
    """
    Explicit authorization API.
    """

    return evaluate_drawdown(
        balance=balance,
        equity=equity,
        starting_day_balance=starting_day_balance,
        max_drawdown_percent=max_drawdown_percent,
        max_daily_loss_percent=max_daily_loss_percent,
        minimum_equity_ratio_percent=
            minimum_equity_ratio_percent,
    )


# ======================================================================
# MODULE SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW INTELLIGENT DRAWDOWN ENGINE")
    print("==============================================")

    print("\nMODULE INFO:")
    print(drawdown_info())

    print("\nNORMAL ACCOUNT TEST:")

    normal = evaluate_drawdown(
        balance=1000.0,
        equity=990.0,
        starting_day_balance=1000.0,
    )

    print(normal)

    print("\nCAUTION TEST:")

    caution = evaluate_drawdown(
        balance=1000.0,
        equity=940.0,
        starting_day_balance=1000.0,
    )

    print(caution)

    print("\nREDUCED RISK TEST:")

    reduced = evaluate_drawdown(
        balance=1000.0,
        equity=890.0,
        starting_day_balance=1000.0,
    )

    print(reduced)

    print("\nHIGH RISK TEST:")

    high = evaluate_drawdown(
        balance=1000.0,
        equity=840.0,
        starting_day_balance=1000.0,
    )

    print(high)

    print("\nHARD BLOCK TEST:")

    blocked = evaluate_drawdown(
        balance=1000.0,
        equity=790.0,
        starting_day_balance=1000.0,
    )

    print(blocked)