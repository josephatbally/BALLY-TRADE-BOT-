"""
BALLY FLOW - AI Confidence Engine

Combines technical confidence with market-condition context.

The AI Confidence Engine does NOT:
- make the final BUY / SELL / NO_TRADE decision
- perform fundamental analysis
- manage risk
- calculate lot size
- execute trades
- place MT5 orders

Market conditions are a SOFT confidence input.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


TECHNICAL_WEIGHT = 0.70
MARKET_CONDITIONS_WEIGHT = 0.30
MIN_AI_CONFIDENCE = 60.0


def _number(value: Any, default: float = 0.0) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default

    if value != value:
        return default

    if value in (float("inf"), float("-inf")):
        return default

    return value


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(minimum, min(maximum, value))


def _extract_confidence(
    data: Any,
    default: float = 0.0,
) -> float:
    """
    Extract confidence from standardized or common result structures.
    """

    if data is None:
        return default

    if isinstance(data, (int, float)):
        return _clamp(_number(data, default))

    if not isinstance(data, dict):
        return default

    keys = (
        "confidence",
        "score",
        "technical_confidence",
        "market_conditions_confidence",
        "market_condition_confidence",
        "ai_confidence",
    )

    for key in keys:
        if key in data:
            return _clamp(_number(data[key], default))

    nested_keys = (
        "analysis",
        "result",
        "confluence",
        "technical_confluence",
    )

    for key in nested_keys:
        nested = data.get(key)

        if isinstance(nested, dict):
            for confidence_key in keys:
                if confidence_key in nested:
                    return _clamp(
                        _number(
                            nested[confidence_key],
                            default,
                        )
                    )

    return default


def _extract_signal(data: Any) -> str:
    """
    Extract a non-authoritative signal/bias for informational purposes.
    """

    if not isinstance(data, dict):
        return "NEUTRAL"

    for key in (
        "signal",
        "decision",
        "direction",
        "bias",
    ):
        value = data.get(key)

        if value is None:
            continue

        value = str(value).strip().upper()

        if value in {
            "BUY",
            "SELL",
            "NO_TRADE",
            "NEUTRAL",
        }:
            return value

    return "NEUTRAL"


def calculate_ai_confidence(
    technical_confidence: float,
    market_conditions_confidence: float = 0.0,
) -> float:
    """
    Calculate weighted AI confidence.

    Technical analysis contributes 70%.
    Market conditions contribute 30%.

    Market conditions do NOT independently block a setup.
    """

    technical = _clamp(
        _number(technical_confidence)
    )

    market_conditions = _clamp(
        _number(market_conditions_confidence)
    )

    result = (
        technical * TECHNICAL_WEIGHT
        + market_conditions * MARKET_CONDITIONS_WEIGHT
    )

    return round(
        _clamp(result),
        2,
    )


def run_ai_confidence(
    technical_analysis: Optional[Dict[str, Any]] = None,
    market_conditions: Optional[Dict[str, Any]] = None,
    *,
    technical_confidence: Optional[float] = None,
    market_conditions_confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run the AI confidence layer.

    This produces confidence evidence for the Decision Engine.
    It does NOT produce the authoritative trading decision.
    """

    if technical_confidence is None:
        technical_confidence = _extract_confidence(
            technical_analysis
        )

    if market_conditions_confidence is None:
        market_conditions_confidence = _extract_confidence(
            market_conditions
        )

    technical = _clamp(
        _number(technical_confidence)
    )

    conditions = _clamp(
        _number(market_conditions_confidence)
    )

    ai_confidence = calculate_ai_confidence(
        technical,
        conditions,
    )

    return {
        "status": "READY",
        "engine": "BALLY FLOW AI Confidence Engine",

        "technical_confidence": round(
            technical,
            2,
        ),

        "market_conditions_confidence": round(
            conditions,
            2,
        ),

        "technical_weight": TECHNICAL_WEIGHT,
        "market_conditions_weight": MARKET_CONDITIONS_WEIGHT,

        "ai_confidence": ai_confidence,

        "minimum_confidence": MIN_AI_CONFIDENCE,

        "confidence_pass": (
            ai_confidence >= MIN_AI_CONFIDENCE
        ),

        "technical_signal": _extract_signal(
            technical_analysis
        ),

        "market_conditions_signal": _extract_signal(
            market_conditions
        ),

        "market_conditions_soft_input": True,

        "trade_blocked_by_market_conditions_alone": False,

        "decision": None,

        "decision_authority": "decision_engine",

        "risk_management": False,
        "execution": False,
        "order_placement": False,
    }


def calculate_confidence(
    technical_analysis: Optional[Dict[str, Any]] = None,
    market_conditions: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Convenience API returning only AI confidence.
    """

    result = run_ai_confidence(
        technical_analysis=technical_analysis,
        market_conditions=market_conditions,
    )

    return result["ai_confidence"]


def confidence_passes(
    confidence: float,
    minimum_confidence: float = MIN_AI_CONFIDENCE,
) -> bool:
    """
    Check whether AI confidence reaches the configured threshold.
    """

    return (
        _clamp(_number(confidence))
        >= _clamp(
            _number(
                minimum_confidence,
                MIN_AI_CONFIDENCE,
            )
        )
    )


def ai_confidence_info() -> Dict[str, Any]:
    """
    Return AI Confidence Engine configuration and architecture.
    """

    return {
        "name": "BALLY FLOW AI Confidence Engine",
        "status": "READY",

        "technical_weight": TECHNICAL_WEIGHT,
        "market_conditions_weight": MARKET_CONDITIONS_WEIGHT,

        "minimum_confidence": MIN_AI_CONFIDENCE,

        "supported_inputs": [
            "technical_analysis",
            "market_conditions",
        ],

        "market_conditions_role": (
            "soft_confidence_input"
        ),

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
    "TECHNICAL_WEIGHT",
    "MARKET_CONDITIONS_WEIGHT",
    "MIN_AI_CONFIDENCE",
    "calculate_ai_confidence",
    "calculate_confidence",
    "run_ai_confidence",
    "confidence_passes",
    "ai_confidence_info",
]
