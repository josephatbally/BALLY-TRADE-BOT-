"""
BALLY FLOW - Risk Margin Engine

AUTHORITATIVE MARGIN VERIFICATION LAYER
=======================================

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
    Margin Check
          |
    Risk Manager
          |
    Final Gate
          |
    Execution Pipeline

RESPONSIBILITY
--------------

This module verifies whether an already-sized trade has sufficient
account free margin to proceed.

This module DOES NOT:

    - generate BUY / SELL decisions
    - modify the trading direction
    - calculate technical analysis
    - calculate fundamental analysis
    - calculate stop loss
    - calculate take profit
    - calculate position size
    - silently reduce volume
    - override risk limits
    - perform order_check()
    - perform order_send()
    - place trades

The broker's actual MT5 margin calculation is authoritative.

MARGIN SAFETY
-------------

A configurable free-margin safety buffer is applied.

The trade is allowed only when:

    required_margin <= free_margin_after_buffer

The safety buffer is NOT a substitute for broker margin rules.

REAL TRADING
------------

This module is capable of validating real MT5 account conditions,
but it never sends an order.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


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
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Risk Margin Engine"
VERSION = "1.0.0"

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

DEFAULT_SAFETY_BUFFER_PERCENT = 10.0

MIN_SAFETY_BUFFER_PERCENT = 0.0
MAX_SAFETY_BUFFER_PERCENT = 50.0


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    try:
        number = float(value)

    except (TypeError, ValueError):
        return None

    if number != number:
        return None

    return number


def _safe_int(value: Any) -> Optional[int]:
    """Safely convert a value to integer."""

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def _normalize_signal(signal: Any) -> str:
    """Normalize BUY / SELL / NO_TRADE."""

    return str(signal or "").upper().strip()


def _result_to_dict(result: Any) -> Dict[str, Any]:
    """Safely convert MT5 namedtuple results."""

    if result is None:
        return {}

    try:
        return result._asdict()

    except AttributeError:
        return {
            "result": str(result),
        }


def _mt5_last_error() -> Any:
    """Safely return MT5 last error."""

    if not MT5_AVAILABLE or mt5 is None:
        return None

    try:
        return mt5.last_error()

    except Exception:
        return None


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def margin_info() -> Dict[str, Any]:
    """
    Return margin engine architecture and configuration.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "mt5_available": MT5_AVAILABLE,

        "supported_signals": list(SUPPORTED_SIGNALS),

        "responsibilities": [
            "account_free_margin_verification",
            "broker_margin_calculation",
            "required_margin_calculation",
            "free_margin_safety_buffer",
            "margin_level_observation",
            "margin_authorization",
        ],

        "default_safety_buffer_percent":
            DEFAULT_SAFETY_BUFFER_PERCENT,

        "minimum_safety_buffer_percent":
            MIN_SAFETY_BUFFER_PERCENT,

        "maximum_safety_buffer_percent":
            MAX_SAFETY_BUFFER_PERCENT,

        "uses_mt5_order_calc_margin": True,

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "stop_loss_calculation": False,
        "take_profit_calculation": False,
        "position_sizing": False,

        "risk_management": True,

        "drawdown_control": False,

        "execution": False,
        "order_builder": False,

        "mt5_order_check": False,
        "mt5_order_send": False,
        "order_placement": False,

        "decision_authority":
            "upstream_decision_engine",

        "risk_authority":
            "downstream_risk_management",

        "margin_authorization":
            "this_module",

        "volume_modification":
            False,
    }


# ======================================================================
# SIGNAL VALIDATION
# ======================================================================

def _get_mt5_order_type(signal: str) -> Optional[int]:
    """
    Convert BUY / SELL into MT5 order type.
    """

    if not MT5_AVAILABLE or mt5 is None:
        return None

    if signal == "BUY":
        return mt5.ORDER_TYPE_BUY

    if signal == "SELL":
        return mt5.ORDER_TYPE_SELL

    return None


# ======================================================================
# ACCOUNT INFORMATION
# ======================================================================

def get_account_margin_state(
    account_info: Any = None,
) -> Dict[str, Any]:
    """
    Obtain the current account margin state.

    If account_info is supplied, it is used directly.
    Otherwise MT5 account_info() is queried.
    """

    if account_info is None:

        if not MT5_AVAILABLE or mt5 is None:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "MetaTrader5 package is unavailable",
            }

        try:
            account_info = mt5.account_info()

        except Exception as exc:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    f"MT5 account_info failed: {exc}",
                "last_error": _mt5_last_error(),
            }

    if account_info is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "MT5 account information unavailable",
        }

    balance = _safe_float(
        getattr(account_info, "balance", None)
    )

    equity = _safe_float(
        getattr(account_info, "equity", None)
    )

    margin = _safe_float(
        getattr(account_info, "margin", None)
    )

    margin_free = _safe_float(
        getattr(account_info, "margin_free", None)
    )

    margin_level = _safe_float(
        getattr(account_info, "margin_level", None)
    )

    if balance is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account balance unavailable",
        }

    if equity is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account equity unavailable",
        }

    if margin_free is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account free margin unavailable",
        }

    if margin_free < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "account free margin is negative",
            "balance": balance,
            "equity": equity,
            "margin": margin,
            "margin_free": margin_free,
            "margin_level": margin_level,
        }

    return {
        "status": "READY",
        "valid": True,
        "balance": balance,
        "equity": equity,
        "margin": margin,
        "margin_free": margin_free,
        "margin_level": margin_level,
    }


# ======================================================================
# SAFETY BUFFER
# ======================================================================

def calculate_margin_buffer(
    free_margin: float,
    safety_buffer_percent:
        float = DEFAULT_SAFETY_BUFFER_PERCENT,
) -> Dict[str, Any]:
    """
    Calculate the free-margin safety buffer.

    The buffer is based on CURRENT free margin.

    Example:

        free margin = 1000
        buffer = 10%

        buffer amount = 100
        usable margin = 900
    """

    free_margin = _safe_float(free_margin)

    if free_margin is None or free_margin < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid free margin",
        }

    safety_buffer_percent = _safe_float(
        safety_buffer_percent
    )

    if safety_buffer_percent is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid safety buffer percentage",
        }

    if (
        safety_buffer_percent < MIN_SAFETY_BUFFER_PERCENT
        or safety_buffer_percent > MAX_SAFETY_BUFFER_PERCENT
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "safety buffer percentage out of range",
            "minimum": MIN_SAFETY_BUFFER_PERCENT,
            "maximum": MAX_SAFETY_BUFFER_PERCENT,
        }

    buffer_amount = (
        free_margin
        * safety_buffer_percent
        / 100.0
    )

    usable_margin = free_margin - buffer_amount

    return {
        "status": "READY",
        "valid": True,
        "free_margin": free_margin,
        "safety_buffer_percent":
            safety_buffer_percent,
        "safety_buffer_amount":
            buffer_amount,
        "usable_free_margin":
            usable_margin,
    }


# ======================================================================
# BROKER MARGIN CALCULATION
# ======================================================================

def calculate_required_margin(
    signal: str,
    symbol: str,
    volume: float,
    price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate required margin using MT5's broker-aware
    order_calc_margin().

    No order is sent.
    """

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "MetaTrader5 package is unavailable",
        }

    signal = _normalize_signal(signal)

    if signal not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "signal must be BUY or SELL",
        }

    if not isinstance(symbol, str) or not symbol.strip():
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "symbol is required",
        }

    symbol = symbol.strip()

    volume = _safe_float(volume)

    if volume is None or volume <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "volume must be greater than zero",
        }

    order_type = _get_mt5_order_type(signal)

    if order_type is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "unable to resolve MT5 order type",
        }

    # --------------------------------------------------------------
    # Symbol validation
    # --------------------------------------------------------------

    try:
        symbol_info = mt5.symbol_info(symbol)

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"MT5 symbol_info failed: {exc}",
        }

    if symbol_info is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"symbol not found: {symbol}",
        }

    # --------------------------------------------------------------
    # Current price
    # --------------------------------------------------------------

    if price is None:

        try:
            tick = mt5.symbol_info_tick(symbol)

        except Exception as exc:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    f"MT5 symbol_info_tick failed: {exc}",
                "last_error": _mt5_last_error(),
            }

        if tick is None:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    f"live tick unavailable: {symbol}",
            }

        if signal == "BUY":
            price = _safe_float(
                getattr(tick, "ask", None)
            )

        else:
            price = _safe_float(
                getattr(tick, "bid", None)
            )

    else:
        price = _safe_float(price)

    if price is None or price <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid execution price",
        }

    # --------------------------------------------------------------
    # Broker margin calculation
    # --------------------------------------------------------------

    try:
        required_margin = mt5.order_calc_margin(
            order_type,
            symbol,
            volume,
            price,
        )

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"MT5 order_calc_margin failed: {exc}",
            "last_error": _mt5_last_error(),
        }

    required_margin = _safe_float(
        required_margin
    )

    if required_margin is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "MT5 returned invalid required margin",
            "last_error": _mt5_last_error(),
        }

    if required_margin < 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "MT5 returned negative required margin",
        }

    return {
        "status": "READY",
        "valid": True,

        "signal": signal,
        "symbol": symbol,

        "volume": volume,
        "price": price,

        "required_margin":
            required_margin,

        "method":
            "mt5.order_calc_margin",

        "broker_aware":
            True,
    }


# ======================================================================
# COMPLETE MARGIN CHECK
# ======================================================================

def check_margin(
    signal: str,
    symbol: str,
    volume: float,
    price: Optional[float] = None,
    account_info: Any = None,
    safety_buffer_percent:
        float = DEFAULT_SAFETY_BUFFER_PERCENT,
) -> Dict[str, Any]:
    """
    Complete margin authorization check.

    PASS requires:

        valid account
        +
        valid signal
        +
        valid volume
        +
        broker margin calculation
        +
        required margin <= usable free margin

    This function never modifies volume.
    """

    signal = _normalize_signal(signal)

    # --------------------------------------------------------------
    # NO TRADE
    # --------------------------------------------------------------

    if signal == "NO_TRADE":
        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "reason":
                "NO_TRADE cannot pass margin authorization",
            "decision": signal,
        }

    if signal not in ("BUY", "SELL"):
        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "reason": "invalid signal",
            "decision": signal,
        }

    # --------------------------------------------------------------
    # Account state
    # --------------------------------------------------------------

    account = get_account_margin_state(
        account_info=account_info
    )

    if not account["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "decision": signal,
            "account": account,
            "reason": account["reason"],
        }

    # --------------------------------------------------------------
    # Margin buffer
    # --------------------------------------------------------------

    buffer = calculate_margin_buffer(
        free_margin=account["margin_free"],
        safety_buffer_percent=safety_buffer_percent,
    )

    if not buffer["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "decision": signal,
            "account": account,
            "buffer": buffer,
            "reason": buffer["reason"],
        }

    # --------------------------------------------------------------
    # Required broker margin
    # --------------------------------------------------------------

    required = calculate_required_margin(
        signal=signal,
        symbol=symbol,
        volume=volume,
        price=price,
    )

    if not required["valid"]:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,
            "decision": signal,
            "account": account,
            "buffer": buffer,
            "required_margin": required,
            "reason": required["reason"],
        }

    required_margin = required["required_margin"]
    usable_margin = buffer["usable_free_margin"]

    # --------------------------------------------------------------
    # Authorization comparison
    # --------------------------------------------------------------

    margin_remaining = (
        usable_margin - required_margin
    )

    passed = (
        required_margin <= usable_margin
    )

    if not passed:

        return {
            "status": "BLOCKED",
            "valid": False,
            "margin_authorized": False,

            "decision": signal,
            "symbol": symbol,
            "volume": required["volume"],
            "price": required["price"],

            "account_balance":
                account["balance"],

            "account_equity":
                account["equity"],

            "free_margin":
                account["margin_free"],

            "current_margin":
                account["margin"],

            "margin_level":
                account["margin_level"],

            "required_margin":
                required_margin,

            "safety_buffer_percent":
                buffer["safety_buffer_percent"],

            "safety_buffer_amount":
                buffer["safety_buffer_amount"],

            "usable_free_margin":
                usable_margin,

            "margin_remaining":
                margin_remaining,

            "broker_margin_method":
                required["method"],

            "reason":
                "insufficient free margin after safety buffer",
        }

    # --------------------------------------------------------------
    # PASS
    # --------------------------------------------------------------

    return {
        "status": "READY",
        "valid": True,
        "margin_authorized": True,

        "decision": signal,
        "symbol": symbol,

        "volume": required["volume"],
        "price": required["price"],

        "account_balance":
            account["balance"],

        "account_equity":
            account["equity"],

        "free_margin":
            account["margin_free"],

        "current_margin":
            account["margin"],

        "margin_level":
            account["margin_level"],

        "required_margin":
            required_margin,

        "safety_buffer_percent":
            buffer["safety_buffer_percent"],

        "safety_buffer_amount":
            buffer["safety_buffer_amount"],

        "usable_free_margin":
            usable_margin,

        "margin_remaining":
            margin_remaining,

        "broker_margin_method":
            required["method"],

        "reason":
            "sufficient free margin after safety buffer",
    }


# ======================================================================
# COMPATIBILITY API
# ======================================================================

def validate_margin(
    signal: str,
    symbol: str,
    volume: float,
    price: Optional[float] = None,
    account_info: Any = None,
    safety_buffer_percent:
        float = DEFAULT_SAFETY_BUFFER_PERCENT,
) -> Dict[str, Any]:
    """
    Compatibility alias for check_margin().
    """

    return check_margin(
        signal=signal,
        symbol=symbol,
        volume=volume,
        price=price,
        account_info=account_info,
        safety_buffer_percent=safety_buffer_percent,
    )


def margin_check(
    signal: str,
    symbol: str,
    volume: float,
    price: Optional[float] = None,
    account_info: Any = None,
    safety_buffer_percent:
        float = DEFAULT_SAFETY_BUFFER_PERCENT,
) -> Dict[str, Any]:
    """
    Compatibility alias.
    """

    return check_margin(
        signal=signal,
        symbol=symbol,
        volume=volume,
        price=price,
        account_info=account_info,
        safety_buffer_percent=safety_buffer_percent,
    )


# ======================================================================
# MODULE SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW RISK MARGIN ENGINE")
    print("==============================================")

    print("INFO:")
    print(margin_info())

    if MT5_AVAILABLE and mt5 is not None:

        initialized = mt5.initialize()

        print(
            "MT5 INITIALIZATION:",
            "SUCCESS" if initialized else "FAILED",
        )

        if initialized:

            result = check_margin(
                signal="BUY",
                symbol="XAUUSD",
                volume=0.01,
                safety_buffer_percent=10.0,
            )

            print("MARGIN RESULT:")
            print(result)

            mt5.shutdown()

    else:

        print(
            "MT5 package unavailable; "
            "live margin test skipped."
        )