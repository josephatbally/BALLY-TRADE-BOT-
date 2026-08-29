
"""
BALLY FLOW - Market Analytics

Reusable market-condition analytics layer.

RESPONSIBILITIES
----------------
This module analyzes standardized OHLCV candle data and produces
descriptive market statistics for downstream systems.

It MAY calculate:
    - volatility
    - ATR
    - true range
    - candle/range statistics
    - trend/momentum statistics
    - volume statistics
    - price location
    - market activity
    - data quality
    - multi-timeframe analytics

It MUST NOT:
    - perform SMC detection
    - calculate technical confluence
    - make BUY / SELL / NO_TRADE decisions
    - perform fundamental analysis
    - calculate risk
    - calculate position size
    - execute trades
    - place MT5 orders

TOP-DOWN STRUCTURE
------------------
BALLY FLOW uses:

    H4 -> H1 -> M15

This module therefore supports both single-timeframe analysis and
complete top-down analytics.

INPUT
-----
Standardized candles:

    {
        "time": ...,
        "open": ...,
        "high": ...,
        "low": ...,
        "close": ...,
        "volume": ...
    }

OUTPUT
------
A deterministic dictionary containing descriptive market statistics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
import math


# =====================================================================
# CONSTANTS
# =====================================================================

DEFAULT_ATR_PERIOD = 14
DEFAULT_LOOKBACK = 20
DEFAULT_VOLUME_LOOKBACK = 20

MIN_ANALYSIS_CANDLES = 2

TOP_DOWN_TIMEFRAMES: Tuple[str, ...] = (
    "H4",
    "H1",
    "M15",
)

REQUIRED_FIELDS: Tuple[str, ...] = (
    "open",
    "high",
    "low",
    "close",
)


# =====================================================================
# BASIC HELPERS
# =====================================================================

def _finite(value: Any) -> bool:
    """Return True when value is a finite numeric value."""

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    if not _finite(value):
        return None

    return float(value)


def _safe_divide(
    numerator: float,
    denominator: float,
) -> Optional[float]:
    """Safely divide two numbers."""

    if denominator == 0:
        return None

    return numerator / denominator


def _clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    """Clamp a numeric value."""

    return max(minimum, min(maximum, value))


# =====================================================================
# CANDLE VALIDATION
# =====================================================================

def validate_candles(
    candles: Sequence[Dict[str, Any]],
    minimum: int = MIN_ANALYSIS_CANDLES,
) -> bool:
    """
    Validate standardized candles.

    Raises:
        TypeError:
            If candles are not a sequence.

        ValueError:
            If candle structure is invalid.

    Returns:
        True when valid.
    """

    if not isinstance(candles, Sequence):
        raise TypeError("candles must be a sequence")

    if len(candles) < minimum:
        return False

    previous_time = None

    for index, candle in enumerate(candles):

        if not isinstance(candle, dict):
            raise ValueError(
                f"candle {index} must be a dictionary"
            )

        for field in REQUIRED_FIELDS:

            if field not in candle:
                raise ValueError(
                    f"candle {index} missing field: {field}"
                )

            if not _finite(candle[field]):
                raise ValueError(
                    f"candle {index} has invalid {field}"
                )

        open_price = float(candle["open"])
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        if high < low:
            raise ValueError(
                f"candle {index} has high below low"
            )

        if high < open_price or high < close:
            raise ValueError(
                f"candle {index} has invalid high"
            )

        if low > open_price or low > close:
            raise ValueError(
                f"candle {index} has invalid low"
            )

        if "time" in candle and candle["time"] is not None:

            try:
                timestamp = int(candle["time"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"candle {index} has invalid time"
                ) from exc

            if (
                previous_time is not None
                and timestamp < previous_time
            ):
                raise ValueError(
                    "candles must be ordered oldest to newest"
                )

            previous_time = timestamp

    return True


# =====================================================================
# TRUE RANGE
# =====================================================================

def true_ranges(
    candles: Sequence[Dict[str, Any]],
) -> List[float]:
    """
    Calculate True Range for every candle.

    First candle:
        TR = high - low

    Following candles:
        TR = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )
    """

    if not candles:
        return []

    result: List[float] = []

    previous_close: Optional[float] = None

    for candle in candles:

        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        if previous_close is None:

            tr = high - low

        else:

            tr = max(
                high - low,
                abs(high - previous_close),
                abs(low - previous_close),
            )

        result.append(float(tr))

        previous_close = close

    return result


# =====================================================================
# ATR
# =====================================================================

def calculate_atr(
    candles: Sequence[Dict[str, Any]],
    period: int = DEFAULT_ATR_PERIOD,
) -> Optional[float]:
    """
    Calculate simple-average ATR over the requested period.

    The latest ATR is based on the most recent TR values.
    """

    if not isinstance(period, int):
        raise TypeError("period must be an integer")

    if period <= 0:
        raise ValueError("period must be greater than zero")

    if len(candles) < period:
        return None

    ranges = true_ranges(candles)

    if len(ranges) < period:
        return None

    recent = ranges[-period:]

    return float(sum(recent) / len(recent))


# =====================================================================
# RANGE ANALYTICS
# =====================================================================

def calculate_range_statistics(
    candles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate high/low/range statistics."""

    if not candles:
        return {
            "high": None,
            "low": None,
            "range": None,
            "average_range": None,
            "current_range": None,
        }

    highs = [
        float(candle["high"])
        for candle in candles
    ]

    lows = [
        float(candle["low"])
        for candle in candles
    ]

    ranges = [
        high - low
        for high, low in zip(highs, lows)
    ]

    highest = max(highs)
    lowest = min(lows)

    return {
        "high": highest,
        "low": lowest,
        "range": highest - lowest,
        "average_range": (
            sum(ranges) / len(ranges)
            if ranges
            else None
        ),
        "current_range": ranges[-1]
        if ranges
        else None,
    }


# =====================================================================
# CANDLE BODY ANALYTICS
# =====================================================================

def calculate_candle_statistics(
    candles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate candle body, wick and directional statistics.
    """

    if not candles:
        return {
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "bullish_percentage": 0.0,
            "bearish_percentage": 0.0,
            "average_body": None,
            "average_range": None,
            "average_body_ratio": None,
            "latest_direction": None,
        }

    bullish = 0
    bearish = 0
    neutral = 0

    bodies: List[float] = []
    ranges: List[float] = []
    body_ratios: List[float] = []

    for candle in candles:

        open_price = float(candle["open"])
        high = float(candle["high"])
        low = float(candle["low"])
        close = float(candle["close"])

        body = abs(close - open_price)
        candle_range = high - low

        bodies.append(body)
        ranges.append(candle_range)

        if candle_range > 0:
            body_ratios.append(
                body / candle_range
            )

        if close > open_price:
            bullish += 1

        elif close < open_price:
            bearish += 1

        else:
            neutral += 1

    total = len(candles)

    latest = candles[-1]

    if latest["close"] > latest["open"]:
        latest_direction = "BULLISH"

    elif latest["close"] < latest["open"]:
        latest_direction = "BEARISH"

    else:
        latest_direction = "NEUTRAL"

    return {
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "bullish_percentage": (
            bullish / total * 100.0
        ),
        "bearish_percentage": (
            bearish / total * 100.0
        ),
        "average_body": (
            sum(bodies) / len(bodies)
            if bodies
            else None
        ),
        "average_range": (
            sum(ranges) / len(ranges)
            if ranges
            else None
        ),
        "average_body_ratio": (
            sum(body_ratios) / len(body_ratios)
            if body_ratios
            else None
        ),
        "latest_direction": latest_direction,
    }


# =====================================================================
# MOMENTUM
# =====================================================================

def calculate_momentum(
    candles: Sequence[Dict[str, Any]],
    lookback: int = DEFAULT_LOOKBACK,
) -> Dict[str, Any]:
    """
    Calculate descriptive price momentum.

    This does not generate a trade signal.
    """

    if not isinstance(lookback, int):
        raise TypeError("lookback must be an integer")

    if lookback <= 0:
        raise ValueError(
            "lookback must be greater than zero"
        )

    if len(candles) < 2:
        return {
            "price_change": None,
            "price_change_percentage": None,
            "net_direction": None,
            "positive_candles": 0,
            "negative_candles": 0,
        }

    start_index = max(
        0,
        len(candles) - lookback,
    )

    window = candles[start_index:]

    start_price = float(window[0]["close"])
    end_price = float(window[-1]["close"])

    change = end_price - start_price

    percentage = _safe_divide(
        change,
        start_price,
    )

    positive = 0
    negative = 0

    for index in range(1, len(window)):

        previous = float(
            window[index - 1]["close"]
        )

        current = float(
            window[index]["close"]
        )

        if current > previous:
            positive += 1

        elif current < previous:
            negative += 1

    if change > 0:
        direction = "UP"

    elif change < 0:
        direction = "DOWN"

    else:
        direction = "FLAT"

    return {
        "price_change": change,
        "price_change_percentage": (
            percentage * 100.0
            if percentage is not None
            else None
        ),
        "net_direction": direction,
        "positive_candles": positive,
        "negative_candles": negative,
    }


# =====================================================================
# VOLATILITY
# =====================================================================

def calculate_volatility(
    candles: Sequence[Dict[str, Any]],
    lookback: int = DEFAULT_LOOKBACK,
    atr_period: int = DEFAULT_ATR_PERIOD,
) -> Dict[str, Any]:
    """
    Calculate descriptive volatility metrics.
    """

    if not candles:
        return {
            "atr": None,
            "average_range": None,
            "range_standard_deviation": None,
            "current_range": None,
            "current_vs_average_range": None,
            "classification": "INSUFFICIENT_DATA",
        }

    start = max(
        0,
        len(candles) - lookback,
    )

    window = candles[start:]

    ranges = [
        float(candle["high"])
        - float(candle["low"])
        for candle in window
    ]

    average_range = (
        sum(ranges) / len(ranges)
        if ranges
        else None
    )

    standard_deviation = None

    if len(ranges) >= 2 and average_range is not None:

        variance = sum(
            (value - average_range) ** 2
            for value in ranges
        ) / len(ranges)

        standard_deviation = math.sqrt(
            variance
        )

    atr = calculate_atr(
        candles,
        period=atr_period,
    )

    current_range = ranges[-1] if ranges else None

    current_ratio = None

    if (
        current_range is not None
        and average_range not in (None, 0)
    ):
        current_ratio = (
            current_range / average_range
        )

    if average_range is None:
        classification = "INSUFFICIENT_DATA"

    elif current_ratio is None:
        classification = "NORMAL"

    elif current_ratio >= 1.75:
        classification = "VERY_HIGH"

    elif current_ratio >= 1.25:
        classification = "HIGH"

    elif current_ratio <= 0.60:
        classification = "LOW"

    else:
        classification = "NORMAL"

    return {
        "atr": atr,
        "average_range": average_range,
        "range_standard_deviation": standard_deviation,
        "current_range": current_range,
        "current_vs_average_range": current_ratio,
        "classification": classification,
    }


# =====================================================================
# VOLUME ANALYTICS
# =====================================================================

def calculate_volume_statistics(
    candles: Sequence[Dict[str, Any]],
    lookback: int = DEFAULT_VOLUME_LOOKBACK,
) -> Dict[str, Any]:
    """
    Calculate volume statistics.

    Supports tick volume and real volume when supplied.
    """

    if not candles:
        return {
            "available": False,
            "volume_source": "none",
            "current_volume": None,
            "average_volume": None,
            "volume_ratio": None,
            "highest_volume": None,
            "lowest_volume": None,
        }

    start = max(
        0,
        len(candles) - lookback,
    )

    window = candles[start:]

    volumes: List[float] = []
    source_counts: Dict[str, int] = {}

    for candle in window:

        volume = candle.get("volume")

        if not _finite(volume):
            continue

        value = float(volume)

        if value < 0:
            continue

        volumes.append(value)

        source = candle.get(
            "volume_source",
            "unknown",
        )

        source_counts[source] = (
            source_counts.get(source, 0) + 1
        )

    if not volumes:

        return {
            "available": False,
            "volume_source": "none",
            "current_volume": None,
            "average_volume": None,
            "volume_ratio": None,
            "highest_volume": None,
            "lowest_volume": None,
        }

    average = sum(volumes) / len(volumes)

    current = volumes[-1]

    ratio = _safe_divide(
        current,
        average,
    )

    if "real_volume" in source_counts:
        source = "real_volume"

    elif "tick_volume" in source_counts:
        source = "tick_volume"

    else:
        source = "volume"

    return {
        "available": True,
        "volume_source": source,
        "current_volume": current,
        "average_volume": average,
        "volume_ratio": ratio,
        "highest_volume": max(volumes),
        "lowest_volume": min(volumes),
    }


# =====================================================================
# PRICE LOCATION
# =====================================================================

def calculate_price_location(
    candles: Sequence[Dict[str, Any]],
    lookback: int = DEFAULT_LOOKBACK,
) -> Dict[str, Any]:
    """
    Determine the current price position inside the recent range.

    0.0 = range low
    0.5 = equilibrium
    1.0 = range high
    """

    if not candles:
        return {
            "current_price": None,
            "range_high": None,
            "range_low": None,
            "ratio": None,
            "percentage": None,
            "classification": "INSUFFICIENT_DATA",
        }

    start = max(
        0,
        len(candles) - lookback,
    )

    window = candles[start:]

    range_high = max(
        float(candle["high"])
        for candle in window
    )

    range_low = min(
        float(candle["low"])
        for candle in window
    )

    current_price = float(
        candles[-1]["close"]
    )

    total_range = range_high - range_low

    if total_range <= 0:

        return {
            "current_price": current_price,
            "range_high": range_high,
            "range_low": range_low,
            "ratio": None,
            "percentage": None,
            "classification": "EQUILIBRIUM",
        }

    ratio = (
        current_price - range_low
    ) / total_range

    ratio = _clamp(
        ratio,
        0.0,
        1.0,
    )

    percentage = ratio * 100.0

    if ratio >= 0.80:
        classification = "UPPER_RANGE"

    elif ratio >= 0.55:
        classification = "ABOVE_EQUILIBRIUM"

    elif ratio > 0.45:
        classification = "EQUILIBRIUM"

    elif ratio > 0.20:
        classification = "BELOW_EQUILIBRIUM"

    else:
        classification = "LOWER_RANGE"

    return {
        "current_price": current_price,
        "range_high": range_high,
        "range_low": range_low,
        "ratio": ratio,
        "percentage": percentage,
        "classification": classification,
    }


# =====================================================================
# TREND DESCRIPTOR
# =====================================================================

def calculate_trend_context(
    candles: Sequence[Dict[str, Any]],
    fast_period: int = 10,
    slow_period: int = 30,
) -> Dict[str, Any]:
    """
    Describe price direction using simple moving averages.

    This is descriptive context only.

    It does not generate a trade decision.
    """

    closes = [
        float(candle["close"])
        for candle in candles
    ]

    if len(closes) < fast_period:

        return {
            "fast_average": None,
            "slow_average": None,
            "direction": "INSUFFICIENT_DATA",
            "strength": 0.0,
        }

    fast = sum(
        closes[-fast_period:]
    ) / fast_period

    if len(closes) >= slow_period:

        slow = sum(
            closes[-slow_period:]
        ) / slow_period

    else:

        slow = sum(closes) / len(closes)

    current = closes[-1]

    if fast > slow and current > fast:
        direction = "BULLISH"

    elif fast < slow and current < fast:
        direction = "BEARISH"

    else:
        direction = "MIXED"

    difference = abs(
        fast - slow
    )

    strength = (
        _safe_divide(
            difference,
            current,
        )
        or 0.0
    )

    strength = _clamp(
        strength * 10000.0,
        0.0,
        100.0,
    )

    return {
        "fast_average": fast,
        "slow_average": slow,
        "direction": direction,
        "strength": strength,
    }


# =====================================================================
# MARKET ACTIVITY
# =====================================================================

def calculate_market_activity(
    candles: Sequence[Dict[str, Any]],
    lookback: int = DEFAULT_LOOKBACK,
) -> Dict[str, Any]:
    """
    Estimate current market activity relative to recent activity.
    """

    if not candles:
        return {
            "activity_ratio": None,
            "classification": "INSUFFICIENT_DATA",
        }

    start = max(
        0,
        len(candles) - lookback,
    )

    window = candles[start:]

    ranges = [
        float(candle["high"])
        - float(candle["low"])
        for candle in window
    ]

    if len(ranges) < 2:

        return {
            "activity_ratio": None,
            "classification": "INSUFFICIENT_DATA",
        }

    baseline = (
        sum(ranges[:-1])
        / len(ranges[:-1])
    )

    current = ranges[-1]

    ratio = _safe_divide(
        current,
        baseline,
    )

    if ratio is None:
        classification = "NORMAL"

    elif ratio >= 1.75:
        classification = "EXPANSION"

    elif ratio <= 0.60:
        classification = "COMPRESSION"

    else:
        classification = "NORMAL"

    return {
        "activity_ratio": ratio,
        "classification": classification,
    }


# =====================================================================
# SINGLE-TIMEFRAME ANALYSIS
# =====================================================================

def analyze_market(
    candles: Sequence[Dict[str, Any]],
    timeframe: Optional[str] = None,
    lookback: int = DEFAULT_LOOKBACK,
    atr_period: int = DEFAULT_ATR_PERIOD,
) -> Dict[str, Any]:
    """
    Analyze one timeframe of standardized candles.

    No trading decision is produced.
    """

    if candles is None:
        raise ValueError("candles are required")

    if not isinstance(candles, Sequence):
        raise TypeError("candles must be a sequence")

    if len(candles) < MIN_ANALYSIS_CANDLES:

        return {
            "status": "INSUFFICIENT_DATA",
            "technical_only": True,
            "timeframe": timeframe,
            "candle_count": len(candles),
            "market_analytics": {},
        }

    validate_candles(
        candles,
        minimum=MIN_ANALYSIS_CANDLES,
    )

    range_statistics = (
        calculate_range_statistics(candles)
    )

    candle_statistics = (
        calculate_candle_statistics(candles)
    )

    momentum = calculate_momentum(
        candles,
        lookback=lookback,
    )

    volatility = calculate_volatility(
        candles,
        lookback=lookback,
        atr_period=atr_period,
    )

    volume = calculate_volume_statistics(
        candles,
        lookback=lookback,
    )

    price_location = calculate_price_location(
        candles,
        lookback=lookback,
    )

    trend = calculate_trend_context(
        candles
    )

    activity = calculate_market_activity(
        candles,
        lookback=lookback,
    )

    return {
        "status": "READY",
        "technical_only": True,
        "timeframe": timeframe,
        "candle_count": len(candles),

        "current_price": float(
            candles[-1]["close"]
        ),

        "range": range_statistics,
        "candles": candle_statistics,
        "momentum": momentum,
        "volatility": volatility,
        "volume": volume,
        "price_location": price_location,
        "trend": trend,
        "market_activity": activity,
    }


# =====================================================================
# TOP-DOWN ANALYSIS
# =====================================================================

def analyze_top_down(
    top_down_data: Dict[str, Any],
    lookback: int = DEFAULT_LOOKBACK,
    atr_period: int = DEFAULT_ATR_PERIOD,
) -> Dict[str, Any]:
    """
    Analyze an H4/H1/M15 top-down market snapshot.

    Expected input resembles:

        {
            "status": "READY",
            "market": "XAUUSD",
            "broker_symbol": "XAUUSD",
            "timeframes": {
                "H4": {
                    "candles": [...]
                },
                "H1": {
                    "candles": [...]
                },
                "M15": {
                    "candles": [...]
                }
            }
        }

    This function does not make a trading decision.
    """

    if not isinstance(top_down_data, dict):
        raise TypeError(
            "top_down_data must be a dictionary"
        )

    market = top_down_data.get(
        "market"
    )

    broker_symbol = top_down_data.get(
        "broker_symbol"
    )

    timeframes = top_down_data.get(
        "timeframes",
        {},
    )

    if not isinstance(timeframes, dict):
        raise TypeError(
            "timeframes must be a dictionary"
        )

    results: Dict[str, Any] = {}

    successful = 0

    for timeframe in TOP_DOWN_TIMEFRAMES:

        timeframe_data = timeframes.get(
            timeframe,
            {},
        )

        if not isinstance(
            timeframe_data,
            dict,
        ):
            results[timeframe] = {
                "status": "ERROR",
                "error": (
                    "timeframe data must be a dictionary"
                ),
            }
            continue

        candles = timeframe_data.get(
            "candles",
            [],
        )

        try:

            analysis = analyze_market(
                candles=candles,
                timeframe=timeframe,
                lookback=lookback,
                atr_period=atr_period,
            )

            results[timeframe] = analysis

            if analysis["status"] == "READY":
                successful += 1

        except Exception as exc:

            results[timeframe] = {
                "status": "ERROR",
                "timeframe": timeframe,
                "error": str(exc),
            }

    if successful == len(TOP_DOWN_TIMEFRAMES):

        status = "READY"

    elif successful > 0:

        status = "PARTIAL"

    else:

        status = "ERROR"

    return {
        "status": status,
        "technical_only": True,
        "market": market,
        "broker_symbol": broker_symbol,
        "top_down": True,
        "analysis_order": list(
            TOP_DOWN_TIMEFRAMES
        ),
        "timeframes": results,
        "timeframe_count": len(
            TOP_DOWN_TIMEFRAMES
        ),
        "successful_timeframe_count": successful,
    }


# =====================================================================
# CONVENIENCE FUNCTIONS
# =====================================================================

def analyze_h4(
    candles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze H4 candles."""

    return analyze_market(
        candles,
        timeframe="H4",
    )


def analyze_h1(
    candles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze H1 candles."""

    return analyze_market(
        candles,
        timeframe="H1",
    )


def analyze_m15(
    candles: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Analyze M15 candles."""

    return analyze_market(
        candles,
        timeframe="M15",
    )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "DEFAULT_ATR_PERIOD",
    "DEFAULT_LOOKBACK",
    "DEFAULT_VOLUME_LOOKBACK",
    "MIN_ANALYSIS_CANDLES",
    "TOP_DOWN_TIMEFRAMES",
    "validate_candles",
    "true_ranges",
    "calculate_atr",
    "calculate_range_statistics",
    "calculate_candle_statistics",
    "calculate_momentum",
    "calculate_volatility",
    "calculate_volume_statistics",
    "calculate_price_location",
    "calculate_trend_context",
    "calculate_market_activity",
    "analyze_market",
    "analyze_top_down",
    "analyze_h4",
    "analyze_h1",
    "analyze_m15",
]
