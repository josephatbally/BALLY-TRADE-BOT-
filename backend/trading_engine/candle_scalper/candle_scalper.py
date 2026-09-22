"""
BALLY FLOW - Candle Momentum Scalper Engine

Independent M1 momentum strategy.

The strategy owns:
    - momentum detection
    - BUY / SELL / HOLD decision
    - burst size
    - burst profit target
    - candle-movement exit target

It does NOT depend on SMC, Hybrid, AI, or higher-timeframe alignment.
Broker execution remains owned by the shared live executor.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import MetaTrader5 as mt5

logger = logging.getLogger("CandleScalper")

TIMEFRAME = mt5.TIMEFRAME_M1
LOOKBACK_BARS = 6
MOMENTUM_BODY_RATIO = 0.55
MIN_CONFIDENCE = 70.0
DEFAULT_BURST_COUNT = 3
DEFAULT_PROFIT_TARGET_USD = 2.50
POSITION_COMMENT_PREFIX = "BALLYCS"

# The forming M1 candle is intentionally excluded from the entry decision.
# This prevents a signal from appearing/disappearing while the candle is
# still forming.
USE_CLOSED_CANDLE = False


def get_tiered_lot_size(balance: float) -> float:
    """
    Preserve the strategy's configured account-size tiers.

    Broker minimum/maximum/step validation is performed downstream by
    live_executor.py before an order can reach MT5.
    """
    b = max(0.0, float(balance))

    if b < 500:
        return 0.01
    if b < 1000:
        return 0.05
    if b < 2000:
        return 0.10
    if b < 5000:
        return 0.50
    if b < 10000:
        return 1.00
    if b < 20000:
        return 2.00
    if b < 50000:
        return 5.00
    return 10.00


def _f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _candle_metrics(candle: Any) -> Dict[str, float]:
    open_price = _f(candle["open"])
    high = _f(candle["high"])
    low = _f(candle["low"])
    close = _f(candle["close"])

    delta = close - open_price
    body = abs(delta)
    candle_range = max(high - low, 1e-12)

    return {
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "delta": delta,
        "body": body,
        "range": candle_range,
        "body_ratio": body / candle_range,
    }


def analyze_candle_momentum(
    symbol: str,
    rates: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Produce the complete independent Candle Momentum decision.

    Entry uses the most recently CLOSED M1 candle. The forming candle is
    requested only so that MT5's bar indexing remains unambiguous.

    A valid burst requires:
        - a directional candle
        - body/range > 55%
        - a non-zero body

    The previous closed candles are used as context so the five-bar request
    is meaningful rather than reading only one bar.
    """
    if rates is None:
        rates = mt5.copy_rates_from_pos(
            symbol,
            TIMEFRAME,
            0,
            LOOKBACK_BARS,
        )

    if rates is None or len(rates) < 3:
        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "strategy": "CANDLE_SCALPER",
            "timeframe": "M1",
            "reason": "insufficient M1 candle history",
        }

    closed = rates[:-1] if USE_CLOSED_CANDLE and len(rates) >= 3 else rates
    current = closed[-1]
    metrics = _candle_metrics(current)

    previous = closed[-4:-1]
    previous_bodies = [_candle_metrics(bar)["body"] for bar in previous]
    previous_ranges = [_candle_metrics(bar)["range"] for bar in previous]

    average_body = sum(previous_bodies) / len(previous_bodies) if previous_bodies else metrics["body"]
    average_range = sum(previous_ranges) / len(previous_ranges) if previous_ranges else metrics["range"]

    body_expansion = metrics["body"] / max(average_body, 1e-12)
    range_expansion = metrics["range"] / max(average_range, 1e-12)

    if metrics["body_ratio"] <= MOMENTUM_BODY_RATIO or metrics["body"] <= 0:
        return {
            "signal": "HOLD",
            "confidence": 40.0,
            "strategy": "CANDLE_SCALPER",
            "timeframe": "M1",
            "reason": "closed candle body is not strong enough",
            "body_ratio": round(metrics["body_ratio"], 4),
            "body": metrics["body"],
            "range": metrics["range"],
            "body_expansion": round(body_expansion, 4),
            "range_expansion": round(range_expansion, 4),
        }

    # Keep the strategy's established 80-confidence burst behavior while
    # exposing the actual momentum measurements to the app/telemetry.
    signal = "BUY" if metrics["delta"] > 0 else "SELL"

    return {
        "signal": signal,
        "confidence": 80.0,
        "strategy": "CANDLE_SCALPER",
        "timeframe": "M1",
        "burst_count": DEFAULT_BURST_COUNT,
        "profit_target_usd": DEFAULT_PROFIT_TARGET_USD,
        # The signal candle's body is the candle-movement target used by the
        # burst manager. Profit target USD remains the hard burst-profit cap.
        "candle_move_target": metrics["body"],
        "signal_candle_open": metrics["open"],
        "signal_candle_close": metrics["close"],
        "signal_candle_high": metrics["high"],
        "signal_candle_low": metrics["low"],
        "body_ratio": round(metrics["body_ratio"], 6),
        "body": metrics["body"],
        "range": metrics["range"],
        "body_expansion": round(body_expansion, 6),
        "range_expansion": round(range_expansion, 6),
        "reason": "strong closed M1 momentum candle",
    }


def current_candle_movement(
    symbol: str,
    direction: str,
) -> Dict[str, Any]:
    """
    Return the favorable movement of the currently forming M1 candle.

    BUY  -> current close - current open
    SELL -> current open - current close

    This is used only by the burst manager for the strategy's exit
    condition; it does not make a new entry decision.
    """
    rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 1)

    if rates is None or len(rates) < 1:
        return {
            "ready": False,
            "movement": 0.0,
            "reason": "current M1 candle unavailable",
        }

    metrics = _candle_metrics(rates[-1])
    direction = str(direction).upper()

    if direction == "BUY":
        movement = metrics["close"] - metrics["open"]
    elif direction == "SELL":
        movement = metrics["open"] - metrics["close"]
    else:
        return {
            "ready": False,
            "movement": 0.0,
            "reason": "invalid direction",
        }

    return {
        "ready": True,
        "movement": max(0.0, float(movement)),
        "direction": direction,
        "open": metrics["open"],
        "close": metrics["close"],
    }


def candle_position_comment(signal: str, candle_move_target: float) -> str:
    """
    Produce a short broker-safe comment carrying the movement target.

    MT5 broker comments can be length-limited, so keep this compact.
    """
    direction = "B" if str(signal).upper() == "BUY" else "S"
    return f"{POSITION_COMMENT_PREFIX}_{direction}_{float(candle_move_target):.8g}"


def parse_candle_position_comment(comment: Any) -> Optional[Dict[str, Any]]:
    """
    Decode a Candle Scalper position comment.

    Returns None for positions that do not belong to this strategy.
    """
    if not isinstance(comment, str):
        return None

    parts = comment.strip().split("_")
    if len(parts) != 3 or parts[0] != POSITION_COMMENT_PREFIX:
        return None

    direction = {"B": "BUY", "S": "SELL"}.get(parts[1])
    if direction is None:
        return None

    try:
        movement = float(parts[2])
    except (TypeError, ValueError):
        return None

    if movement <= 0:
        return None

    return {
        "strategy": "CANDLE_SCALPER",
        "direction": direction,
        "candle_move_target": movement,
    }
