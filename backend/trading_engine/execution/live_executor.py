
"""
BALLY FLOW - Live MT5 Executor

AUTHORITATIVE MT5 EXECUTION BOUNDARY
====================================

This is the ONLY execution-layer module allowed to communicate
with MetaTrader 5 for:

    - symbol_info()
    - symbol_select()
    - symbol_info_tick()
    - order_check()
    - order_send()

PIPELINE

    Decision Engine
          |
    Risk Management
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
          |
    order_check()
          |
    order_send()
          |
       BROKER

IMPORTANT
---------
This module NEVER:

    - generates a BUY/SELL decision
    - changes the decision
    - performs technical analysis
    - performs fundamental analysis
    - performs hybrid analysis
    - calculates position size
    - replaces risk management
    - bypasses the final gate
    - invents an order
    - reverses direction

It consumes an already-authorized order.

REAL TRADING
------------
The module is capable of genuine MT5 execution.

All live switches remain FALSE by default.

A real order can only reach mt5.order_send() when
ALL live-execution switches are enabled.
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

NAME = "BALLY FLOW Live Executor"
VERSION = "1.1.0"

# ----------------------------------------------------------------------
# HARD LIVE-TRADING SWITCHES
# ----------------------------------------------------------------------

LIVE_TRADING = False
EXECUTION_ENABLED = False
ALLOW_ORDER_SEND = False
EXECUTION_CONFIRMATION = False

# ----------------------------------------------------------------------
# DEVELOPMENT SAFETY
# ----------------------------------------------------------------------

DRY_RUN = True

# ----------------------------------------------------------------------
# MT5 SETTINGS
# ----------------------------------------------------------------------

MAGIC_NUMBER = 20260817
COMMENT = "BALLY_TRADES_BOT"
DEFAULT_DEVIATION = 20

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _result_to_dict(result: Any) -> Dict[str, Any]:
    if result is None:
        return {}

    try:
        return result._asdict()
    except AttributeError:
        return {"result": str(result)}


def _get_retcode(result: Any) -> Optional[int]:
    if result is None:
        return None

    try:
        return int(result.retcode)
    except (AttributeError, TypeError, ValueError):
        return None


def _mt5_last_error() -> Any:
    if not MT5_AVAILABLE or mt5 is None:
        return None

    try:
        return mt5.last_error()
    except Exception:
        return None


# ======================================================================
# LIVE EXECUTION SWITCH
# ======================================================================

def live_execution_enabled() -> bool:
    """
    True ONLY when every production execution switch is enabled.
    """

    return bool(
        LIVE_TRADING
        and EXECUTION_ENABLED
        and ALLOW_ORDER_SEND
        and EXECUTION_CONFIRMATION
        and not DRY_RUN
    )


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def live_executor_info() -> Dict[str, Any]:

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "mt5_available": MT5_AVAILABLE,

        "supported_signals": list(SUPPORTED_SIGNALS),

        "pipeline_position": [
            "executor",
            "live_executor",
            "mt5.order_check",
            "mt5.order_send",
        ],

        "responsibilities": [
            "receive_authorized_order",
            "connect_to_mt5",
            "validate_symbol",
            "validate_market_tick",
            "validate_broker_constraints",
            "select_broker_supported_filling_mode",
            "normalize_price",
            "normalize_volume",
            "build_mt5_request",
            "perform_mt5_order_check",
            "perform_mt5_order_send",
            "return_execution_result",
        ],

        "live_trading": LIVE_TRADING,
        "execution_enabled": EXECUTION_ENABLED,
        "allow_order_send": ALLOW_ORDER_SEND,
        "execution_confirmation": EXECUTION_CONFIRMATION,
        "dry_run": DRY_RUN,

        "order_check_owner": "live_executor.py",
        "order_send_owner": "live_executor.py",

        "direct_mt5_order_send_elsewhere": False,

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_management": False,
        "position_sizing": False,

        "real_trade_capable": True,

        "live_order_send_currently_allowed":
            live_execution_enabled(),
    }


# ======================================================================
# AUTHORIZED ORDER VALIDATION
# ======================================================================

def validate_authorized_order(
    order: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    if not isinstance(order, dict):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "order must be a dictionary",
        }

    decision = str(
        order.get("decision")
        or order.get("signal")
        or ""
    ).upper().strip()

    if decision not in SUPPORTED_SIGNALS:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "invalid decision",
            "decision": decision,
        }

    if decision == "NO_TRADE":
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "NO_TRADE cannot reach MT5",
            "decision": decision,
        }

    symbol = order.get("symbol")

    if not isinstance(symbol, str) or not symbol.strip():
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "symbol is required",
            "decision": decision,
        }

    symbol = symbol.strip()

    volume = _safe_float(order.get("volume"))

    if volume is None or volume <= 0:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "volume must be greater than zero",
            "decision": decision,
        }

    stop_loss = _safe_float(
        order.get("stop_loss", order.get("sl"))
    )

    take_profit = _safe_float(
        order.get("take_profit", order.get("tp"))
    )

    if stop_loss is None or take_profit is None:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "stop_loss and take_profit are required",
            "decision": decision,
        }

    entry = _safe_float(
        order.get("entry", order.get("price"))
    )

    if entry is not None:

        if decision == "BUY":

            if stop_loss >= entry:
                return {
                    "status": "BLOCKED",
                    "valid": False,
                    "reason":
                        "BUY stop_loss must be below entry",
                    "decision": decision,
                }

            if take_profit <= entry:
                return {
                    "status": "BLOCKED",
                    "valid": False,
                    "reason":
                        "BUY take_profit must be above entry",
                    "decision": decision,
                }

        elif decision == "SELL":

            if stop_loss <= entry:
                return {
                    "status": "BLOCKED",
                    "valid": False,
                    "reason":
                        "SELL stop_loss must be above entry",
                    "decision": decision,
                }

            if take_profit >= entry:
                return {
                    "status": "BLOCKED",
                    "valid": False,
                    "reason":
                        "SELL take_profit must be below entry",
                    "decision": decision,
                }

    # --------------------------------------------------------------
    # FINAL GATE
    # --------------------------------------------------------------

    if gate is not None:

        if not isinstance(gate, dict):
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason": "gate must be a dictionary",
            }

        gate_passed = (
            gate.get("gate") == "PASS"
            and gate.get("allowed") is True
        )

        if not gate_passed:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "final execution gate did not pass",
                "decision": decision,
            }

    return {
        "status": "READY",
        "valid": True,
        "reason": "authorized order validated",
        "decision": decision,
        "symbol": symbol,
        "volume": volume,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "entry": entry,
    }


# ======================================================================
# MT5 INITIALIZATION
# ======================================================================

def initialize_mt5() -> Dict[str, Any]:
    if MT5_AVAILABLE and mt5 is not None:
        try:
            if mt5.terminal_info() is not None:
                return {"status": "READY", "initialized": True, "terminal": "MetaTrader 5"}
        except Exception:
            pass

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "initialized": False,
            "reason":
                "MetaTrader5 Python package is unavailable",
        }

    try:
        initialized = mt5.initialize()

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "initialized": False,
            "reason":
                f"MT5 initialization exception: {exc}",
            "last_error": _mt5_last_error(),
        }

    if not initialized:
        return {
            "status": "BLOCKED",
            "initialized": False,
            "reason": "MT5 initialization failed",
            "last_error": _mt5_last_error(),
        }

    return {
        "status": "READY",
        "initialized": True,
        "terminal": "MetaTrader 5",
        "last_error": _mt5_last_error(),
    }


# ======================================================================
# SYMBOL PREPARATION
# ======================================================================

def prepare_symbol(symbol: str) -> Dict[str, Any]:

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason": "MT5 unavailable",
        }

    if not isinstance(symbol, str) or not symbol.strip():
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason": "symbol is required",
        }

    symbol = symbol.strip()

    try:
        info = mt5.symbol_info(symbol)

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason":
                f"symbol_info failed: {exc}",
        }

    if info is None:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason":
                f"symbol not found: {symbol}",
        }

    visible = bool(
        getattr(info, "visible", False)
    )

    if not visible:

        try:
            selected = mt5.symbol_select(
                symbol,
                True,
            )

        except Exception as exc:
            return {
                "status": "BLOCKED",
                "ready": False,
                "reason":
                    f"symbol_select exception: {exc}",
            }

        if not selected:
            return {
                "status": "BLOCKED",
                "ready": False,
                "reason":
                    f"unable to select symbol: {symbol}",
            }

        # Refresh symbol information after selection.
        try:
            info = mt5.symbol_info(symbol)
        except Exception:
            pass

    return {
        "status": "READY",
        "ready": True,
        "symbol": symbol,
        "symbol_info": info,
    }


# ======================================================================
# MARKET TICK
# ======================================================================

def get_market_tick(symbol: str) -> Dict[str, Any]:

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason": "MT5 unavailable",
        }

    try:
        tick = mt5.symbol_info_tick(symbol)

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason":
                f"symbol_info_tick failed: {exc}",
        }

    if tick is None:
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason":
                f"no live tick available for {symbol}",
        }

    bid = _safe_float(
        getattr(tick, "bid", None)
    )

    ask = _safe_float(
        getattr(tick, "ask", None)
    )

    if (
        bid is None
        or ask is None
        or bid <= 0
        or ask <= 0
        or ask < bid
    ):
        return {
            "status": "BLOCKED",
            "ready": False,
            "reason":
                f"invalid live tick for {symbol}",
        }

    return {
        "status": "READY",
        "ready": True,
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "spread": ask - bid,
    }


# ======================================================================
# PRICE NORMALIZATION
# ======================================================================

def normalize_price(
    price: float,
    symbol_info: Any,
) -> float:

    digits = _safe_int(
        getattr(symbol_info, "digits", None)
    )

    if digits is None:
        digits = 2

    return round(float(price), digits)


# ======================================================================
# VOLUME NORMALIZATION
# ======================================================================

def normalize_volume(
    volume: float,
    symbol_info: Any,
) -> Dict[str, Any]:

    volume = float(volume)

    minimum = _safe_float(
        getattr(symbol_info, "volume_min", None)
    )

    maximum = _safe_float(
        getattr(symbol_info, "volume_max", None)
    )

    step = _safe_float(
        getattr(symbol_info, "volume_step", None)
    )

    if minimum is None or minimum <= 0:
        minimum = volume

    if maximum is None or maximum <= 0:
        maximum = volume

    if step is None or step <= 0:
        step = minimum

    if volume < minimum:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"volume {volume} is below broker minimum "
                f"{minimum}",
            "requested_volume": volume,
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
        }

    if volume > maximum:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                f"volume {volume} exceeds broker maximum "
                f"{maximum}",
            "requested_volume": volume,
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
        }

    # Determine decimal precision from the broker step.
    step_text = f"{step:.12f}".rstrip("0")

    if "." in step_text:
        decimals = len(
            step_text.split(".")[1]
        )
    else:
        decimals = 0

    # Round DOWN to a valid broker step.
    steps = int(
        (volume - minimum) / step
    )

    normalized = minimum + (
        steps * step
    )

    normalized = round(
        normalized,
        decimals,
    )

    if normalized < minimum:
        normalized = minimum

    if normalized > maximum:
        normalized = maximum

    return {
        "status": "READY",
        "valid": True,
        "requested_volume": volume,
        "volume": normalized,
        "minimum": minimum,
        "maximum": maximum,
        "step": step,
    }


# ======================================================================
# BROKER FILLING MODE
# ======================================================================

def get_supported_filling_modes(
    symbol_info: Any,
) -> list[int]:
    """
    Translate MT5 symbol_info.filling_mode capability flags
    into actual ORDER_FILLING_* constants.

    IMPORTANT:

    symbol_info.filling_mode is a BITMASK.

    It must NOT be passed directly as type_filling.
    """

    if not MT5_AVAILABLE or mt5 is None:
        return []

    raw_mode = _safe_int(
        getattr(
            symbol_info,
            "filling_mode",
            None,
        )
    )

    if raw_mode is None:
        raw_mode = 0

    supported: list[int] = []

    # MT5 filling flags:
    # FOK = 1
    # IOC = 2
    # RETURN = 4
    #
    # We use getattr() so this remains compatible with
    # different MetaTrader5 Python package versions.

    fok_flag = _safe_int(
        getattr(
            mt5,
            "SYMBOL_FILLING_FOK",
            1,
        )
    )

    ioc_flag = _safe_int(
        getattr(
            mt5,
            "SYMBOL_FILLING_IOC",
            2,
        )
    )

    if fok_flag is not None and raw_mode & fok_flag:
        supported.append(
            getattr(
                mt5,
                "ORDER_FILLING_FOK",
                0,
            )
        )

    if ioc_flag is not None and raw_mode & ioc_flag:
        supported.append(
            getattr(
                mt5,
                "ORDER_FILLING_IOC",
                1,
            )
        )

    # RETURN is not always supported for market execution.
    # It is therefore considered only when explicitly available.
    return_flag = _safe_int(
        getattr(
            mt5,
            "SYMBOL_FILLING_RETURN",
            4,
        )
    )

    if (
        return_flag is not None
        and raw_mode & return_flag
        and hasattr(mt5, "ORDER_FILLING_RETURN")
    ):
        supported.append(
            mt5.ORDER_FILLING_RETURN
        )

    # Remove duplicates while preserving order.
    result = []

    for mode in supported:
        if mode not in result:
            result.append(mode)

    return result


def _get_filling_mode(
    symbol_info: Any,
) -> Optional[int]:
    """
    Select the broker-supported filling mode.

    Preference:

        1. FOK
        2. IOC
        3. RETURN

    This is NOT a blind hard-coded IOC fallback.
    """

    supported = get_supported_filling_modes(
        symbol_info
    )

    if not supported:
        return None

    # Prefer FOK.
    if (
        hasattr(mt5, "ORDER_FILLING_FOK")
        and mt5.ORDER_FILLING_FOK in supported
    ):
        return mt5.ORDER_FILLING_FOK

    # Then IOC.
    if (
        hasattr(mt5, "ORDER_FILLING_IOC")
        and mt5.ORDER_FILLING_IOC in supported
    ):
        return mt5.ORDER_FILLING_IOC

    # Finally RETURN if available.
    if (
        hasattr(mt5, "ORDER_FILLING_RETURN")
        and mt5.ORDER_FILLING_RETURN in supported
    ):
        return mt5.ORDER_FILLING_RETURN

    return supported[0]


def get_filling_mode_details(
    symbol_info: Any,
) -> Dict[str, Any]:

    raw_mode = _safe_int(
        getattr(
            symbol_info,
            "filling_mode",
            None,
        )
    )

    supported = get_supported_filling_modes(
        symbol_info
    )

    selected = _get_filling_mode(
        symbol_info
    )

    names = {}

    if MT5_AVAILABLE and mt5 is not None:

        if hasattr(mt5, "ORDER_FILLING_FOK"):
            names[
                mt5.ORDER_FILLING_FOK
            ] = "FOK"

        if hasattr(mt5, "ORDER_FILLING_IOC"):
            names[
                mt5.ORDER_FILLING_IOC
            ] = "IOC"

        if hasattr(mt5, "ORDER_FILLING_RETURN"):
            names[
                mt5.ORDER_FILLING_RETURN
            ] = "RETURN"

    return {
        "raw_symbol_filling_mode": raw_mode,
        "supported_modes": supported,
        "supported_mode_names": [
            names.get(mode, str(mode))
            for mode in supported
        ],
        "selected_mode": selected,
        "selected_mode_name":
            names.get(
                selected,
                str(selected)
                if selected is not None
                else None,
            ),
    }


# ======================================================================
# STOP / TAKE PROFIT VALIDATION
# ======================================================================

def validate_execution_prices(
    decision: str,
    price: float,
    stop_loss: float,
    take_profit: float,
    symbol_info: Any,
) -> Dict[str, Any]:
    """
    Validate SL/TP against the ACTUAL live execution price.

    This prevents a stale Order Builder entry from being
    blindly used at the broker.
    """

    decision = decision.upper()

    point = _safe_float(
        getattr(symbol_info, "point", None)
    )

    if point is None or point <= 0:
        point = 0.00001

    stops_level = _safe_float(
        getattr(
            symbol_info,
            "trade_stops_level",
            None,
        )
    )

    if stops_level is None or stops_level < 0:
        stops_level = 0

    minimum_distance = (
        stops_level * point
    )

    if decision == "BUY":

        if stop_loss >= price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "BUY stop_loss must be below live Ask",
            }

        if take_profit <= price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "BUY take_profit must be above live Ask",
            }

        sl_distance = price - stop_loss
        tp_distance = take_profit - price

    elif decision == "SELL":

        if stop_loss <= price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "SELL stop_loss must be above live Bid",
            }

        if take_profit >= price:
            return {
                "status": "BLOCKED",
                "valid": False,
                "reason":
                    "SELL take_profit must be below live Bid",
            }

        sl_distance = stop_loss - price
        tp_distance = price - take_profit

    else:
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason": "unsupported decision",
        }

    if (
        minimum_distance > 0
        and sl_distance < minimum_distance
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "stop_loss is inside broker minimum "
                "stop distance",
            "minimum_distance": minimum_distance,
            "actual_distance": sl_distance,
        }

    if (
        minimum_distance > 0
        and tp_distance < minimum_distance
    ):
        return {
            "status": "BLOCKED",
            "valid": False,
            "reason":
                "take_profit is inside broker minimum "
                "stop distance",
            "minimum_distance": minimum_distance,
            "actual_distance": tp_distance,
        }

    return {
        "status": "READY",
        "valid": True,
        "minimum_distance": minimum_distance,
        "stop_loss_distance": sl_distance,
        "take_profit_distance": tp_distance,
    }


# ======================================================================
# ORDER TYPE
# ======================================================================

def _get_order_type(
    decision: str,
) -> Optional[int]:

    if not MT5_AVAILABLE or mt5 is None:
        return None

    if decision == "BUY":
        return mt5.ORDER_TYPE_BUY

    if decision == "SELL":
        return mt5.ORDER_TYPE_SELL

    return None


# ======================================================================
# BUILD MT5 REQUEST
# ======================================================================

def build_mt5_request(
    order: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a broker-aware MT5 market-order request.

    No order_check/order_send is performed here.
    """

    if not MT5_AVAILABLE or mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is unavailable"
        )

    decision = str(
        order.get("decision")
        or order.get("signal")
        or ""
    ).upper().strip()

    symbol = str(
        order["symbol"]
    ).strip()

    symbol_info = mt5.symbol_info(
        symbol
    )

    if symbol_info is None:
        raise ValueError(
            f"MT5 symbol unavailable: {symbol}"
        )

    tick = mt5.symbol_info_tick(
        symbol
    )

    if tick is None:
        raise ValueError(
            f"MT5 live tick unavailable: {symbol}"
        )

    # --------------------------------------------------------------
    # Actual market side
    # --------------------------------------------------------------

    if decision == "BUY":
        raw_price = _safe_float(
            getattr(tick, "ask", None)
        )

    elif decision == "SELL":
        raw_price = _safe_float(
            getattr(tick, "bid", None)
        )

    else:
        raise ValueError(
            f"unsupported decision: {decision}"
        )

    if raw_price is None or raw_price <= 0:
        raise ValueError(
            f"invalid execution price for {symbol}"
        )

    price = normalize_price(
        raw_price,
        symbol_info,
    )

    # --------------------------------------------------------------
    # Volume
    # --------------------------------------------------------------

    raw_volume = _safe_float(
        order["volume"]
    )

    if raw_volume is None or raw_volume <= 0:
        raise ValueError(
            "invalid order volume"
        )

    volume_result = normalize_volume(
        raw_volume,
        symbol_info,
    )

    if not volume_result["valid"]:
        raise ValueError(
            volume_result["reason"]
        )

    volume = volume_result["volume"]

    # --------------------------------------------------------------
    # SL / TP
    # --------------------------------------------------------------

    stop_loss = _safe_float(
        order.get(
            "stop_loss",
            order.get("sl"),
        )
    )

    take_profit = _safe_float(
        order.get(
            "take_profit",
            order.get("tp"),
        )
    )

    if (
        stop_loss is None
        or take_profit is None
    ):
        raise ValueError(
            "SL and TP are required"
        )

    stop_loss = normalize_price(
        stop_loss,
        symbol_info,
    )

    take_profit = normalize_price(
        take_profit,
        symbol_info,
    )

    price_validation = validate_execution_prices(
        decision=decision,
        price=price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        symbol_info=symbol_info,
    )

    if not price_validation["valid"]:
        raise ValueError(
            price_validation["reason"]
        )

    # --------------------------------------------------------------
    # Filling mode
    # --------------------------------------------------------------

    filling_mode = _get_filling_mode(
        symbol_info
    )

    if filling_mode is None:
        raise ValueError(
            "broker does not advertise a supported "
            "MT5 filling mode"
        )

    # --------------------------------------------------------------
    # Request
    # --------------------------------------------------------------

    request = {
        "action": mt5.TRADE_ACTION_DEAL,

        "symbol": symbol,

        "volume": volume,

        "type": _get_order_type(
            decision
        ),

        "price": price,

        "sl": stop_loss,

        "tp": take_profit,

        "deviation": int(order.get("deviation") or 20),

        "magic": int(order.get("magic_number") or 100001),

        "comment": str(
            order.get(
                "comment",
                COMMENT,
            )
        ),

        "type_time": mt5.ORDER_TIME_GTC,

        "type_filling": filling_mode,
    }

    return request


# ======================================================================
# MT5 ORDER CHECK
# ======================================================================

def check_mt5_order(
    request: Dict[str, Any],
) -> Dict[str, Any]:

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "checked": False,
            "passed": False,
            "reason": "MT5 unavailable",
        }

    try:
        result = mt5.order_check(
            request
        )

    except Exception as exc:
        return {
            "status": "BLOCKED",
            "checked": False,
            "passed": False,
            "reason":
                f"MT5 order_check exception: {exc}",
            "last_error": _mt5_last_error(),
        }

    if result is None:
        return {
            "status": "BLOCKED",
            "checked": True,
            "passed": False,
            "reason":
                "MT5 order_check returned None",
            "last_error": _mt5_last_error(),
        }

    retcode = _get_retcode(
        result
    )

    # MT5 order_check success is normally retcode 0.
    passed = retcode == 0

    return {
        "status":
            "READY" if passed else "BLOCKED",

        "checked": True,

        "passed": passed,

        "retcode": retcode,

        "comment":
            getattr(
                result,
                "comment",
                None,
            ),

        "balance":
            getattr(
                result,
                "balance",
                None,
            ),

        "equity":
            getattr(
                result,
                "equity",
                None,
            ),

        "profit":
            getattr(
                result,
                "profit",
                None,
            ),

        "margin":
            getattr(
                result,
                "margin",
                None,
            ),

        "margin_free":
            getattr(
                result,
                "margin_free",
                None,
            ),

        "margin_level":
            getattr(
                result,
                "margin_level",
                None,
            ),

        "result":
            _result_to_dict(result),
    }


# ======================================================================
# MT5 ORDER SEND
# ======================================================================

def send_mt5_order(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """
    REAL MT5 ORDER SEND.

    This is the ONLY function that calls mt5.order_send().
    """

    if not live_execution_enabled():

        return {
            "status": "BLOCKED",
            "sent": False,
            "executed": False,
            "reason":
                "live order_send blocked because "
                "live execution switches are not "
                "all enabled",

            "live_trading": LIVE_TRADING,
            "execution_enabled":
                EXECUTION_ENABLED,
            "allow_order_send":
                ALLOW_ORDER_SEND,
            "execution_confirmation":
                EXECUTION_CONFIRMATION,
            "dry_run": DRY_RUN,
        }

    if not MT5_AVAILABLE or mt5 is None:
        return {
            "status": "BLOCKED",
            "sent": False,
            "executed": False,
            "reason": "MT5 unavailable",
        }

    try:
        result = mt5.order_send(
            request
        )

    except Exception as exc:
        return {
            "status": "FAILED",
            "sent": False,
            "executed": False,
            "reason":
                f"MT5 order_send exception: {exc}",
            "last_error": _mt5_last_error(),
        }

    if result is None:
        return {
            "status": "FAILED",
            "sent": False,
            "executed": False,
            "reason":
                "MT5 order_send returned None",
            "last_error": _mt5_last_error(),
        }

    retcode = _get_retcode(
        result
    )

    successful_retcodes = {
        getattr(
            mt5,
            "TRADE_RETCODE_DONE",
            10009,
        ),

        getattr(
            mt5,
            "TRADE_RETCODE_DONE_PARTIAL",
            10010,
        ),
    }

    executed = (
        retcode in successful_retcodes
    )

    return {
        "status":
            "EXECUTED"
            if executed
            else "REJECTED",

        "sent": True,

        "executed": executed,

        "retcode": retcode,

        "deal":
            getattr(
                result,
                "deal",
                None,
            ),

        "order":
            getattr(
                result,
                "order",
                None,
            ),

        "volume":
            getattr(
                result,
                "volume",
                None,
            ),

        "price":
            getattr(
                result,
                "price",
                None,
            ),

        "comment":
            getattr(
                result,
                "comment",
                None,
            ),

        "request":
            _result_to_dict(
                getattr(
                    result,
                    "request",
                    None,
                )
            ),

        "result":
            _result_to_dict(result),
    }


# ======================================================================
# COMPLETE LIVE EXECUTION
# ======================================================================

def execute_live_trade(
    order: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Complete authoritative live execution pipeline.

    authorization
        ↓
    MT5 initialization
        ↓
    symbol preparation
        ↓
    live tick
        ↓
    broker-aware request
        ↓
    order_check
        ↓
    order_send
        ↓
    broker
    """

    # --------------------------------------------------------------
    # 1. Authorization
    # --------------------------------------------------------------

    validation = validate_authorized_order(
        order=order,
        gate=gate,
    )

    if not validation["valid"]:

        return {
            "status": "BLOCKED",
            "authorized": False,
            "live_executor": True,
            "mt5_order_check": False,
            "mt5_order_send": False,
            "validation": validation,
            "reason":
                validation["reason"],
        }

    decision = validation["decision"]
    symbol = validation["symbol"]

    # --------------------------------------------------------------
    # 2. MT5 initialization
    # --------------------------------------------------------------

    initialization = initialize_mt5()

    if not initialization["initialized"]:

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "initialization":
                initialization,
            "mt5_order_check": False,
            "mt5_order_send": False,
        }

    # --------------------------------------------------------------
    # 3. Symbol preparation
    # --------------------------------------------------------------

    symbol_result = prepare_symbol(
        symbol
    )

    if not symbol_result["ready"]:

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "mt5_order_check": False,
            "mt5_order_send": False,
        }

    symbol_info = symbol_result[
        "symbol_info"
    ]

    # --------------------------------------------------------------
    # 4. Live tick
    # --------------------------------------------------------------

    tick_result = get_market_tick(
        symbol
    )

    if not tick_result["ready"]:

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "tick":
                tick_result,
            "mt5_order_check": False,
            "mt5_order_send": False,
        }

    # --------------------------------------------------------------
    # 5. Broker filling-mode diagnostics
    # --------------------------------------------------------------

    filling_details = (
        get_filling_mode_details(
            symbol_info
        )
    )

    if (
        filling_details[
            "selected_mode"
        ] is None
    ):

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "tick":
                tick_result,
            "filling_mode":
                filling_details,
            "mt5_order_check": False,
            "mt5_order_send": False,
            "reason":
                "no broker-supported filling mode",
        }

    # --------------------------------------------------------------
    # 6. Build request
    # --------------------------------------------------------------

    try:

        request = build_mt5_request(
            order
        )

    except (
        ValueError,
        RuntimeError,
    ) as exc:

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "tick":
                tick_result,
            "filling_mode":
                filling_details,
            "mt5_order_check": False,
            "mt5_order_send": False,
            "reason": str(exc),
        }

    # --------------------------------------------------------------
    # 7. MT5 order_check
    # --------------------------------------------------------------

    check_result = check_mt5_order(
        request
    )

    if not check_result["passed"]:

        return {
            "status": "BLOCKED",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "request": request,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "tick":
                tick_result,
            "filling_mode":
                filling_details,
            "mt5_order_check":
                check_result,
            "mt5_order_send": False,
            "reason":
                "MT5 order_check failed",
        }

    # --------------------------------------------------------------
    # 8. DRY RUN
    # --------------------------------------------------------------

    if DRY_RUN:

        return {
            "status": "DRY_RUN",
            "authorized": True,
            "decision": decision,
            "symbol": symbol,
            "request": request,
            "initialization":
                initialization,
            "symbol":
                symbol_result,
            "tick":
                tick_result,
            "filling_mode":
                filling_details,
            "mt5_order_check":
                check_result,
            "mt5_order_send": False,
            "live_executor_allowed":
                False,
            "real_trade": False,
            "reason":
                "DRY_RUN is enabled",
        }

    # --------------------------------------------------------------
    # 9. REAL MT5 ORDER SEND
    # --------------------------------------------------------------

    send_result = send_mt5_order(
        request
    )

    return {
        "status":
            send_result["status"],

        "authorized": True,

        "decision": decision,

        "symbol": symbol,

        "request": request,

        "initialization":
            initialization,

        "symbol":
            symbol_result,

        "tick":
            tick_result,

        "filling_mode":
            filling_details,

        "mt5_order_check":
            check_result,

        "mt5_order_send":
            send_result,

        "live_executor_allowed":
            live_execution_enabled(),

        "real_trade":
            bool(
                send_result.get(
                    "executed"
                )
            ),
    }


# ======================================================================
# COMPATIBILITY API
# ======================================================================

def execute(
    order: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    return execute_live_trade(
        order=order,
        gate=gate,
    )


def execute_order(
    order: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    return execute_live_trade(
        order=order,
        gate=gate,
    )


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW LIVE EXECUTOR")
    print("==============================================")

    print("INFO:")
    print(live_executor_info())

    test_order = {
        "symbol": "XAUUSD",
        "decision": "BUY",
        "order_type": "BUY",
        "volume": 0.01,
        "entry": 4700.0,
        "stop_loss": 4680.0,
        "take_profit": 4760.0,
        "magic_number": MAGIC_NUMBER,
        "comment": COMMENT,
        "deviation": DEFAULT_DEVIATION,
    }

    test_gate = {
        "gate": "PASS",
        "allowed": True,
        "execution_allowed": True,
    }

    result = execute_live_trade(
        order=test_order,
        gate=test_gate,
    )

    print("RESULT:")
    print(result)


# ======================================================================
# POSITION CLOSING (owned by live_executor)
# ======================================================================

def close_position(ticket: int) -> Dict[str, Any]:
    """
    Close a single open position by ticket.
    Uses mt5.order_send with TRADE_ACTION_DEAL and position ticket.
    """
    if not MT5_AVAILABLE or mt5 is None:
        return {"status": "FAILED", "reason": "MT5 unavailable"}

    try:
        positions = mt5.positions_get(ticket=ticket)
    except Exception as exc:
        return {"status": "FAILED", "reason": f"positions_get exception: {exc}"}

    if not positions:
        return {"status": "FAILED", "reason": f"Position {ticket} not found"}

    pos = positions[0]

    close_type = (
        mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY
        else mt5.ORDER_TYPE_BUY
    )

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": ticket,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": close_type,
        "price": mt5.symbol_info_tick(pos.symbol).bid
        if close_type == mt5.ORDER_TYPE_SELL
        else mt5.symbol_info_tick(pos.symbol).ask,
        "deviation": 20,
        "magic": pos.magic,
        "comment": f"BALLY close #{ticket}",
        "type_time": mt5.ORDER_TIME_GTC,
    }

    try:
        result = mt5.order_send(request)
    except Exception as exc:
        return {"status": "FAILED", "reason": f"order_send exception: {exc}"}

    if result is None:
        return {"status": "FAILED", "reason": "order_send returned None"}

    retcode = getattr(result, "retcode", None)
    if retcode in (mt5.TRADE_RETCODE_DONE, 10009):
        return {
            "status": "OK",
            "ticket": ticket,
            "message": f"Position {ticket} closed",
        }

    return {
        "status": "FAILED",
        "retcode": retcode,
        "comment": getattr(result, "comment", "close rejected"),
    }


def close_all_positions() -> Dict[str, Any]:
    """
    Close every open position (emergency flush).
    """
    if not MT5_AVAILABLE or mt5 is None:
        return {"status": "FAILED", "reason": "MT5 unavailable"}

    try:
        positions = mt5.positions_get()
    except Exception as exc:
        return {"status": "FAILED", "reason": f"positions_get exception: {exc}"}

    if not positions:
        return {"status": "OK", "closed_count": 0, "message": "No positions to close"}

    closed = 0
    for pos in positions:
        res = close_position(pos.ticket)
        if res.get("status") == "OK":
            closed += 1

    return {
        "status": "OK",
        "closed_count": closed,
        "message": f"Closed {closed} of {len(positions)} positions",
    }
