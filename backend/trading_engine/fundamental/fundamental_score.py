"""
BALLY FLOW - Fundamental Score

Combines calendar and news evidence into a standardized
fundamental score.

Score range:
    -100 = strongly bearish
       0 = neutral
    +100 = strongly bullish
"""

from __future__ import annotations

from typing import Any, Dict


def _clamp(value: float, low: float = -100.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_fundamental_score(
    news_analysis: Dict[str, Any] | None = None,
    calendar_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    news_analysis = (
        news_analysis
        if isinstance(news_analysis, dict)
        else {}
    )

    calendar_analysis = (
        calendar_analysis
        if isinstance(calendar_analysis, dict)
        else {}
    )

    news_score = _safe_float(
        news_analysis.get("sentiment_score", 0.0)
    )

    news_score = _clamp(news_score)

    high_impact_count = int(
        _safe_float(
            calendar_analysis.get("high_impact_count", 0)
        )
    )

    # News supplies directional evidence.
    market_score = news_score

    if market_score >= 20.0:
        market_bias = "BULLISH"
        signal = "BUY"
    elif market_score <= -20.0:
        market_bias = "BEARISH"
        signal = "SELL"
    else:
        market_bias = "NEUTRAL"
        signal = "NEUTRAL"

    # High-impact events create risk rather than artificial direction.
    high_impact_risk = high_impact_count > 0

    if high_impact_risk:
        risk = "HIGH"
    elif abs(market_score) >= 60.0:
        risk = "LOW"
    elif abs(market_score) >= 30.0:
        risk = "MEDIUM"
    else:
        risk = "UNKNOWN"

    # Fundamental layer requires actual evidence.
    trade_allowed = (
        signal in {"BUY", "SELL"}
        and not high_impact_risk
        and news_analysis.get("article_count", 0) > 0
    )

    confidence = abs(market_score)

    if not trade_allowed:
        confidence = min(confidence, 50.0)

    if signal == "NEUTRAL":
        confidence = 0.0

    quality = "VERY_WEAK"

    if trade_allowed:
        if confidence >= 80.0:
            quality = "VERY_STRONG"
        elif confidence >= 70.0:
            quality = "STRONG"
        elif confidence >= 60.0:
            quality = "QUALIFIED"
        else:
            quality = "WEAK"

    return {
        "status": "READY",
        "signal": signal,
        "confidence": round(confidence, 2),
        "market_bias": market_bias,
        "market_score": round(market_score, 2),
        "risk": risk,
        "quality": quality,
        "trade_allowed": trade_allowed,
        "high_impact_risk": high_impact_risk,
        "high_impact_count": high_impact_count,
        "conflict": False,
        "conflict_reason": "",
    }


def score_fundamental(
    news_analysis: Dict[str, Any] | None = None,
    calendar_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return calculate_fundamental_score(
        news_analysis=news_analysis,
        calendar_analysis=calendar_analysis,
    )
