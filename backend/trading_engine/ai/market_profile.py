"""
BALLY FLOW - AI Market Profile

Purpose
-------
Provides market-context intelligence to the AI layer.

This module summarizes existing market information into a standardized
market profile that can be consumed by the AI Confidence Engine,
Decision Engine, or other downstream analytical components.

This module MUST NOT:
    - place orders
    - execute trades
    - manage risk
    - calculate lot size
    - perform fundamental analysis
    - make the authoritative BUY / SELL / NO_TRADE decision
    - override Technical Engine or Hybrid Engine decisions

Decision authority remains downstream.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional


# ======================================================================
# CONFIGURATION
# ======================================================================

PROFILE_VERSION = "1.0.0"

SUPPORTED_TIMEFRAMES = ("H4", "H1", "M15")

VOLATILITY_LOW = 33.0
VOLATILITY_HIGH = 66.0

MOMENTUM_LOW = 33.0
MOMENTUM_HIGH = 66.0


# ======================================================================
# HELPERS
# ======================================================================

def _number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(minimum, min(maximum, value))


def _normalize_direction(value: Any) -> str:
    if value is None:
        return "UNKNOWN"

    text = str(value).strip().upper()

    if text in {
        "BUY",
        "SELL",
        "BULLISH",
        "BEARISH",
        "NEUTRAL",
        "MIXED",
    }:
        return text

    return "UNKNOWN"


def _extract(
    data: Any,
    keys: tuple[str, ...],
    default: Any = None,
) -> Any:
    """
    Extract the first available value from a dictionary.
    """

    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            return data[key]

    return default


def _extract_nested(
    data: Any,
    parent_keys: tuple[str, ...],
    child_keys: tuple[str, ...],
    default: Any = None,
) -> Any:
    """
    Extract a value from common nested market-analysis structures.
    """

    if not isinstance(data, dict):
        return default

    for parent in parent_keys:
        nested = data.get(parent)

        if not isinstance(nested, dict):
            continue

        value = _extract(
            nested,
            child_keys,
            None,
        )

        if value is not None:
            return value

    return default


def _candle_count(candles: Any) -> int:
    if isinstance(candles, dict):
        candles = candles.get("candles")

    try:
        return len(candles)
    except (TypeError, AttributeError):
        return 0


def _latest_close(candles: Any) -> Optional[float]:
    if isinstance(candles, dict):
        candles = candles.get("candles")

    if candles is None:
        return None

    try:
        sequence = list(candles)
    except TypeError:
        return None

    if not sequence:
        return None

    latest = sequence[-1]

    if isinstance(latest, dict):
        value = latest.get("close")
    else:
        value = getattr(latest, "close", None)

    if value is None:
        return None

    return _number(value, None)


def _extract_returns(candles: Any) -> list[float]:
    """
    Calculate simple close-to-close percentage changes.
    """

    if isinstance(candles, dict):
        candles = candles.get("candles")

    try:
        sequence = list(candles)
    except (TypeError, AttributeError):
        return []

    closes = []

    for candle in sequence:
        if isinstance(candle, dict):
            value = candle.get("close")
        else:
            value = getattr(candle, "close", None)

        if value is not None:
            number = _number(value, None)

            if number is not None and number > 0:
                closes.append(number)

    if len(closes) < 2:
        return []

    returns = []

    for previous, current in zip(closes, closes[1:]):
        if previous <= 0:
            continue

        returns.append(
            ((current - previous) / previous) * 100.0
        )

    return returns


# ======================================================================
# TREND PROFILE
# ======================================================================

def calculate_trend_profile(
    market_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extract and standardize trend information.

    Trend is descriptive market context, not a trade decision.
    """

    if not isinstance(market_analysis, dict):
        return {
            "direction": "UNKNOWN",
            "strength": 0.0,
        }

    direction = _extract(
        market_analysis,
        (
            "trend_direction",
            "direction",
            "trend",
        ),
    )

    if isinstance(direction, dict):
        direction = _extract(
            direction,
            (
                "direction",
                "bias",
                "trend",
            ),
            "UNKNOWN",
        )

    if direction is None:
        direction = _extract_nested(
            market_analysis,
            ("trend", "market_trend"),
            ("direction", "bias"),
            "UNKNOWN",
        )

    strength = _extract(
        market_analysis,
        (
            "trend_strength",
            "strength",
        ),
    )

    if strength is None:
        strength = _extract_nested(
            market_analysis,
            ("trend", "market_trend"),
            ("strength", "score"),
            0.0,
        )

    return {
        "direction": _normalize_direction(direction),
        "strength": round(
            _clamp(_number(strength)),
            2,
        ),
    }


# ======================================================================
# VOLATILITY PROFILE
# ======================================================================

def calculate_volatility_profile(
    market_analysis: Optional[Dict[str, Any]] = None,
    candles: Any = None,
) -> Dict[str, Any]:
    """
    Standardize volatility context.

    If an existing ATR/volatility score is available, it is preferred.
    Otherwise a simple return-dispersion estimate is used.
    """

    volatility_value = None
    atr = None

    if isinstance(market_analysis, dict):
        volatility = market_analysis.get("volatility")

        if isinstance(volatility, dict):
            atr = _extract(
                volatility,
                ("atr", "average_true_range"),
            )

            volatility_value = _extract(
                volatility,
                (
                    "score",
                    "volatility_score",
                    "confidence",
                ),
            )

        elif volatility is not None:
            volatility_value = volatility

        if volatility_value is None:
            volatility_value = _extract(
                market_analysis,
                (
                    "volatility_score",
                    "volatility",
                ),
            )

        if atr is None:
            atr = _extract(
                market_analysis,
                ("atr", "average_true_range"),
            )

    returns = _extract_returns(candles)

    if volatility_value is None and returns:
        mean = sum(returns) / len(returns)

        variance = sum(
            (value - mean) ** 2
            for value in returns
        ) / len(returns)

        standard_deviation = math.sqrt(variance)

        # Normalize typical percentage volatility into a
        # bounded contextual score.
        volatility_value = _clamp(
            standard_deviation * 20.0
        )

    score = _clamp(
        _number(volatility_value)
    )

    if score < VOLATILITY_LOW:
        regime = "LOW"
    elif score > VOLATILITY_HIGH:
        regime = "HIGH"
    else:
        regime = "NORMAL"

    return {
        "score": round(score, 2),
        "regime": regime,
        "atr": (
            round(_number(atr), 6)
            if atr is not None
            else None
        ),
    }


# ======================================================================
# MOMENTUM PROFILE
# ======================================================================

def calculate_momentum_profile(
    market_analysis: Optional[Dict[str, Any]] = None,
    candles: Any = None,
) -> Dict[str, Any]:
    """
    Standardize momentum context.
    """

    momentum = None
    direction = "UNKNOWN"

    if isinstance(market_analysis, dict):
        momentum_data = market_analysis.get("momentum")

        if isinstance(momentum_data, dict):
            momentum = _extract(
                momentum_data,
                (
                    "score",
                    "momentum_score",
                    "strength",
                ),
            )

            direction = _extract(
                momentum_data,
                (
                    "direction",
                    "bias",
                ),
                "UNKNOWN",
            )

        elif momentum_data is not None:
            momentum = momentum_data

        if momentum is None:
            momentum = _extract(
                market_analysis,
                (
                    "momentum_score",
                    "momentum",
                ),
            )

    returns = _extract_returns(candles)

    if momentum is None and returns:
        recent = returns[-20:]

        positive = sum(
            1 for value in recent
            if value > 0
        )

        negative = sum(
            1 for value in recent
            if value < 0
        )

        if positive > negative:
            direction = "BULLISH"
        elif negative > positive:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        net_return = sum(recent)

        momentum = _clamp(
            50.0 + (net_return * 10.0)
        )

    score = _clamp(
        _number(momentum)
    )

    if direction == "UNKNOWN":
        if score > MOMENTUM_HIGH:
            direction = "BULLISH"
        elif score < MOMENTUM_LOW:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

    return {
        "score": round(score, 2),
        "direction": _normalize_direction(direction),
    }


# ======================================================================
# MARKET ACTIVITY
# ======================================================================

def calculate_activity_profile(
    market_analysis: Optional[Dict[str, Any]] = None,
    candles: Any = None,
) -> Dict[str, Any]:
    """
    Estimate market activity using supplied analysis or candle volume.
    """

    activity = None
    volume_source = "unavailable"

    if isinstance(market_analysis, dict):
        activity_data = market_analysis.get("market_activity")

        if isinstance(activity_data, dict):
            activity = _extract(
                activity_data,
                (
                    "score",
                    "activity_score",
                    "quality",
                ),
            )

        elif activity_data is not None:
            activity = activity_data

        if activity is None:
            activity = _extract(
                market_analysis,
                (
                    "activity_score",
                    "market_activity_score",
                ),
            )

    if isinstance(candles, dict):
        volume = candles.get("volume") or candles.get("volumes")

        if volume is not None:
            try:
                values = [
                    _number(value)
                    for value in volume
                ]

                values = [
                    value
                    for value in values
                    if value > 0
                ]

                if values:
                    average = sum(values) / len(values)
                    recent = values[-20:]

                    recent_average = (
                        sum(recent) / len(recent)
                    )

                    if average > 0:
                        activity = _clamp(
                            (recent_average / average)
                            * 50.0
                        )

                        volume_source = "external_volume"

            except (TypeError, ValueError):
                pass

    if activity is None:
        activity = 0.0

    score = _clamp(
        _number(activity)
    )

    if score < 33.0:
        regime = "LOW"
    elif score > 66.0:
        regime = "HIGH"
    else:
        regime = "NORMAL"

    return {
        "score": round(score, 2),
        "regime": regime,
        "volume_source": volume_source,
    }


# ======================================================================
# PRICE LOCATION
# ======================================================================

def calculate_price_location(
    candles: Any = None,
) -> Dict[str, Any]:
    """
    Determine the latest price's location within the supplied range.
    """

    if isinstance(candles, dict):
        candles = candles.get("candles")

    try:
        sequence = list(candles)
    except (TypeError, AttributeError):
        sequence = []

    if not sequence:
        return {
            "position": "UNKNOWN",
            "percent": None,
            "range_high": None,
            "range_low": None,
        }

    highs = []
    lows = []

    for candle in sequence:
        if isinstance(candle, dict):
            high = candle.get("high")
            low = candle.get("low")
        else:
            high = getattr(candle, "high", None)
            low = getattr(candle, "low", None)

        if high is not None:
            highs.append(_number(high))

        if low is not None:
            lows.append(_number(low))

    current = _latest_close(sequence)

    if (
        current is None
        or not highs
        or not lows
    ):
        return {
            "position": "UNKNOWN",
            "percent": None,
            "range_high": None,
            "range_low": None,
        }

    range_high = max(highs)
    range_low = min(lows)
    distance = range_high - range_low

    if distance <= 0:
        percentage = 50.0
    else:
        percentage = (
            (current - range_low)
            / distance
        ) * 100.0

    percentage = _clamp(percentage)

    if percentage >= 66.0:
        position = "UPPER_RANGE"
    elif percentage <= 33.0:
        position = "LOWER_RANGE"
    else:
        position = "MID_RANGE"

    return {
        "position": position,
        "percent": round(percentage, 2),
        "range_high": range_high,
        "range_low": range_low,
    }


# ======================================================================
# MARKET REGIME
# ======================================================================

def determine_market_regime(
    trend: Dict[str, Any],
    volatility: Dict[str, Any],
    momentum: Dict[str, Any],
) -> str:
    """
    Determine a descriptive market regime.
    """

    direction = trend.get("direction", "UNKNOWN")
    trend_strength = _number(
        trend.get("strength")
    )

    volatility_regime = volatility.get(
        "regime",
        "NORMAL",
    )

    momentum_direction = momentum.get(
        "direction",
        "UNKNOWN",
    )

    if (
        direction in {"BULLISH", "BUY"}
        and momentum_direction in {"BULLISH", "BUY"}
        and trend_strength >= 60.0
    ):
        if volatility_regime == "HIGH":
            return "BULLISH_HIGH_VOLATILITY"

        return "BULLISH_TREND"

    if (
        direction in {"BEARISH", "SELL"}
        and momentum_direction in {"BEARISH", "SELL"}
        and trend_strength >= 60.0
    ):
        if volatility_regime == "HIGH":
            return "BEARISH_HIGH_VOLATILITY"

        return "BEARISH_TREND"

    if volatility_regime == "HIGH":
        return "HIGH_VOLATILITY"

    if (
        direction == "MIXED"
        or momentum_direction == "NEUTRAL"
    ):
        return "RANGE_OR_MIXED"

    return "TRANSITION"


# ======================================================================
# MAIN PROFILE
# ======================================================================

def analyze_market_profile(
    symbol: str,
    candles: Any = None,
    market_analysis: Optional[Dict[str, Any]] = None,
    timeframe: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a standardized AI market profile.
    """

    if not isinstance(symbol, str):
        raise TypeError("symbol must be a string")

    symbol = symbol.strip()

    if not symbol:
        raise ValueError("symbol is required")

    candle_count = _candle_count(candles)

    trend = calculate_trend_profile(
        market_analysis
    )

    volatility = calculate_volatility_profile(
        market_analysis,
        candles,
    )

    momentum = calculate_momentum_profile(
        market_analysis,
        candles,
    )

    activity = calculate_activity_profile(
        market_analysis,
        candles,
    )

    price_location = calculate_price_location(
        candles
    )

    regime = determine_market_regime(
        trend,
        volatility,
        momentum,
    )

    return {
        "status": "READY",
        "component": "ai_market_profile",
        "version": PROFILE_VERSION,

        "symbol": symbol,
        "timeframe": timeframe,

        "candle_count": candle_count,

        "trend": trend,
        "volatility": volatility,
        "momentum": momentum,
        "activity": activity,
        "price_location": price_location,

        "market_regime": regime,

        # This module provides context only.
        "signal": None,
        "decision": None,

        "decision_authority": (
            "downstream_decision_engine"
        ),

        "technical_analysis": True,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "execution": False,
        "order_placement": False,
    }


def market_profile_info() -> Dict[str, Any]:
    """
    Return public module configuration.
    """

    return {
        "name": "BALLY FLOW AI Market Profile",
        "version": PROFILE_VERSION,
        "status": "READY",

        "supported_timeframes": list(
            SUPPORTED_TIMEFRAMES
        ),

        "outputs": [
            "trend",
            "volatility",
            "momentum",
            "activity",
            "price_location",
            "market_regime",
        ],

        "decision_authority": (
            "downstream_decision_engine"
        ),

        "technical_analysis": True,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "execution": False,
        "order_placement": False,
    }


__all__ = [
    "PROFILE_VERSION",
    "SUPPORTED_TIMEFRAMES",
    "calculate_trend_profile",
    "calculate_volatility_profile",
    "calculate_momentum_profile",
    "calculate_activity_profile",
    "calculate_price_location",
    "determine_market_regime",
    "analyze_market_profile",
    "market_profile_info",
]
