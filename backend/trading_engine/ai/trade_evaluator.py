
"""
BALLY FLOW - AI Trade Evaluator

Purpose
-------
Evaluates completed or simulated trades and produces standardized
performance evidence for the AI layer.

Responsibilities
----------------
This module:

    - evaluates trade outcomes
    - calculates basic trade-quality metrics
    - classifies trade performance
    - evaluates signal accuracy
    - evaluates risk/reward realization
    - evaluates execution outcome when supplied
    - provides feedback for adaptive learning
    - optionally records the result into Adaptive Learning
    - optionally records the pattern into Pattern Memory

This module MUST NOT:

    - generate a BUY / SELL trading decision
    - override the Decision Engine
    - perform fundamental analysis
    - calculate broker position size
    - manage account risk
    - place MT5 orders
    - execute trades
    - enable live trading

Decision authority
------------------
The evaluator is an AI feedback component.

It reports:

    decision = None

The authoritative trading decision remains downstream/upstream
according to the main BALLY FLOW architecture.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import math


# ======================================================================
# CONSTANTS
# ======================================================================

MODULE_NAME = "BALLY FLOW AI Trade Evaluator"
VERSION = "1.0.0"

SUPPORTED_MARKETS = (
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
)

SUPPORTED_TIMEFRAMES = (
    "H4",
    "H1",
    "M15",
)

VALID_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

VALID_OUTCOMES = (
    "WIN",
    "LOSS",
    "BREAKEVEN",
    "UNKNOWN",
)

MIN_EVALUATION_CONFIDENCE = 60.0


# ======================================================================
# HELPERS
# ======================================================================

def _finite(value: Any) -> bool:
    """Return True when value can be converted to a finite float."""

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    if not _finite(value):
        return default

    return float(value)


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    """Clamp a numeric value to a defined range."""

    return max(minimum, min(maximum, value))


def _normalize_signal(signal: Any) -> str:
    """Normalize a trading signal."""

    if not isinstance(signal, str):
        return "UNKNOWN"

    value = signal.strip().upper()

    if value in VALID_SIGNALS:
        return value

    return "UNKNOWN"


def _normalize_outcome(outcome: Any) -> str:
    """Normalize a trade outcome."""

    if not isinstance(outcome, str):
        return "UNKNOWN"

    value = outcome.strip().upper()

    if value in VALID_OUTCOMES:
        return value

    return "UNKNOWN"


def _normalize_market(symbol: Any) -> str:
    """Normalize a market symbol."""

    if not isinstance(symbol, str):
        return ""

    return symbol.strip().upper()


def _normalize_timeframe(timeframe: Any) -> str:
    """Normalize timeframe."""

    if not isinstance(timeframe, str):
        return ""

    return timeframe.strip().upper()


# ======================================================================
# OUTCOME CLASSIFICATION
# ======================================================================

def classify_outcome(
    pnl: Any = 0.0,
    outcome: Optional[str] = None,
) -> str:
    """
    Determine standardized trade outcome.

    Explicit outcome has priority.

    Otherwise:

        pnl > 0  -> WIN
        pnl < 0  -> LOSS
        pnl == 0 -> BREAKEVEN
    """

    if outcome is not None:
        normalized = _normalize_outcome(outcome)

        if normalized != "UNKNOWN":
            return normalized

    value = _float(pnl)

    if value > 0:
        return "WIN"

    if value < 0:
        return "LOSS"

    return "BREAKEVEN"


# ======================================================================
# SIGNAL ACCURACY
# ======================================================================

def evaluate_signal_accuracy(
    signal: Any,
    outcome: Any,
) -> Dict[str, Any]:
    """
    Evaluate whether a directional signal produced the expected outcome.

    BUY / SELL:

        WIN       -> CORRECT
        LOSS      -> INCORRECT
        BREAKEVEN -> NEUTRAL

    NO_TRADE is treated separately because it represents avoidance
    rather than directional execution.
    """

    normalized_signal = _normalize_signal(signal)
    normalized_outcome = _normalize_outcome(outcome)

    if normalized_signal == "NO_TRADE":
        return {
            "status": "READY",
            "signal": normalized_signal,
            "outcome": normalized_outcome,
            "classification": "NON_DIRECTIONAL",
            "accuracy_score": 50.0,
        }

    if normalized_signal == "UNKNOWN":
        return {
            "status": "READY",
            "signal": normalized_signal,
            "outcome": normalized_outcome,
            "classification": "UNKNOWN",
            "accuracy_score": 0.0,
        }

    if normalized_outcome == "WIN":
        classification = "CORRECT"
        accuracy_score = 100.0

    elif normalized_outcome == "LOSS":
        classification = "INCORRECT"
        accuracy_score = 0.0

    elif normalized_outcome == "BREAKEVEN":
        classification = "NEUTRAL"
        accuracy_score = 50.0

    else:
        classification = "UNKNOWN"
        accuracy_score = 0.0

    return {
        "status": "READY",
        "signal": normalized_signal,
        "outcome": normalized_outcome,
        "classification": classification,
        "accuracy_score": accuracy_score,
    }


# ======================================================================
# RISK / REWARD EVALUATION
# ======================================================================

def evaluate_risk_reward(
    planned_risk: Any = None,
    planned_reward: Any = None,
    pnl: Any = 0.0,
) -> Dict[str, Any]:
    """
    Evaluate realized performance against planned risk/reward.

    This is analytical only.

    It does not calculate or modify trading risk.
    """

    risk = _float(planned_risk, 0.0)
    reward = _float(planned_reward, 0.0)
    realized_pnl = _float(pnl, 0.0)

    planned_rr: Optional[float] = None
    realized_multiple: Optional[float] = None

    if risk > 0:
        if reward >= 0:
            planned_rr = reward / risk

        realized_multiple = realized_pnl / risk

    if realized_pnl > 0:
        performance = "POSITIVE"

    elif realized_pnl < 0:
        performance = "NEGATIVE"

    else:
        performance = "NEUTRAL"

    return {
        "status": "READY",
        "planned_risk": risk,
        "planned_reward": reward,
        "planned_rr": planned_rr,
        "realized_pnl": realized_pnl,
        "realized_r_multiple": realized_multiple,
        "performance": performance,
    }


# ======================================================================
# EXECUTION EVALUATION
# ======================================================================

def evaluate_execution(
    execution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluate supplied execution information.

    This function does not execute anything.

    Supported optional fields include:

        status
        filled
        slippage
        spread
        rejection
        execution_time_ms
    """

    if execution is None:
        execution = {}

    if not isinstance(execution, dict):
        raise TypeError("execution must be a dictionary")

    filled = execution.get("filled")

    if filled is True:
        execution_status = "FILLED"

    elif filled is False:
        execution_status = "NOT_FILLED"

    else:
        execution_status = str(
            execution.get("status", "UNKNOWN")
        ).strip().upper()

        if not execution_status:
            execution_status = "UNKNOWN"

    slippage = _float(
        execution.get("slippage"),
        0.0,
    )

    spread = _float(
        execution.get("spread"),
        0.0,
    )

    execution_time_ms = _float(
        execution.get("execution_time_ms"),
        0.0,
    )

    rejection = bool(
        execution.get("rejection", False)
    )

    if rejection:
        quality = "REJECTED"

    elif execution_status == "FILLED":
        quality = "FILLED"

    elif execution_status == "NOT_FILLED":
        quality = "NOT_FILLED"

    else:
        quality = "UNKNOWN"

    return {
        "status": "READY",
        "execution_status": execution_status,
        "quality": quality,
        "filled": filled,
        "slippage": slippage,
        "spread": spread,
        "execution_time_ms": execution_time_ms,
        "rejection": rejection,
    }


# ======================================================================
# TRADE QUALITY
# ======================================================================

def calculate_trade_quality(
    signal_accuracy: float,
    pnl: float,
    confidence: float = 0.0,
    execution_quality: str = "UNKNOWN",
) -> Dict[str, Any]:
    """
    Calculate an analytical trade-quality score.

    Components:

        45% signal accuracy
        35% outcome performance
        20% original confidence

    Execution quality is reported separately and does not
    independently manufacture a trading decision.
    """

    accuracy = _clamp(_float(signal_accuracy))
    confidence_value = _clamp(_float(confidence))

    pnl_value = _float(pnl)

    if pnl_value > 0:
        outcome_score = 100.0
    elif pnl_value < 0:
        outcome_score = 0.0
    else:
        outcome_score = 50.0

    score = (
        accuracy * 0.45
        + outcome_score * 0.35
        + confidence_value * 0.20
    )

    score = round(_clamp(score), 2)

    if score >= 80:
        quality = "EXCELLENT"

    elif score >= 65:
        quality = "GOOD"

    elif score >= 50:
        quality = "AVERAGE"

    elif score >= 35:
        quality = "WEAK"

    else:
        quality = "POOR"

    return {
        "score": score,
        "quality": quality,
        "execution_quality": execution_quality,
    }


# ======================================================================
# AI FEEDBACK
# ======================================================================

def build_learning_feedback(
    signal: str,
    outcome: str,
    pnl: float,
    confidence: float,
    trade_quality: float,
) -> Dict[str, Any]:
    """
    Produce feedback for downstream AI learning components.

    This does not alter the current trading decision.
    """

    if outcome == "WIN":
        learning_bias = "POSITIVE"

    elif outcome == "LOSS":
        learning_bias = "NEGATIVE"

    elif outcome == "BREAKEVEN":
        learning_bias = "NEUTRAL"

    else:
        learning_bias = "UNKNOWN"

    confidence_value = _clamp(confidence)
    quality_value = _clamp(trade_quality)

    if outcome == "WIN" and confidence_value >= MIN_EVALUATION_CONFIDENCE:
        feedback = "REINFORCE"

    elif outcome == "LOSS" and confidence_value >= MIN_EVALUATION_CONFIDENCE:
        feedback = "REVIEW"

    elif outcome == "LOSS":
        feedback = "LOW_CONFIDENCE_LOSS"

    elif outcome == "BREAKEVEN":
        feedback = "MONITOR"

    else:
        feedback = "INSUFFICIENT_DATA"

    return {
        "learning_bias": learning_bias,
        "feedback": feedback,
        "signal": signal,
        "outcome": outcome,
        "pnl": pnl,
        "confidence": confidence_value,
        "trade_quality": quality_value,
    }


# ======================================================================
# MAIN EVALUATOR
# ======================================================================

def evaluate_trade(
    signal: Any,
    outcome: Any = None,
    pnl: Any = 0.0,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    confidence: Any = 0.0,
    planned_risk: Any = None,
    planned_reward: Any = None,
    execution: Optional[Dict[str, Any]] = None,
    pattern: Optional[Dict[str, Any]] = None,
    record_learning: bool = False,
    record_pattern: bool = False,
) -> Dict[str, Any]:
    """
    Evaluate a completed or simulated trade.

    Parameters
    ----------
    signal:
        BUY, SELL or NO_TRADE.

    outcome:
        WIN, LOSS, BREAKEVEN or UNKNOWN.

    pnl:
        Realized profit/loss.

    symbol:
        Market symbol.

    timeframe:
        H4, H1 or M15.

    confidence:
        AI/decision confidence at the time of the trade.

    planned_risk:
        Planned monetary/unit risk.

    planned_reward:
        Planned monetary/unit reward.

    execution:
        Optional execution result.

    pattern:
        Optional pattern data for Pattern Memory.

    record_learning:
        When True, attempt to record the result in Adaptive Learning.

    record_pattern:
        When True, attempt to record the result in Pattern Memory.

    Returns
    -------
    dict
        Standardized AI trade evaluation.

    Notes
    -----
    This function never executes or places an order.
    """

    normalized_signal = _normalize_signal(signal)
    normalized_outcome = classify_outcome(
        pnl=pnl,
        outcome=outcome,
    )

    normalized_symbol = _normalize_market(symbol)
    normalized_timeframe = _normalize_timeframe(timeframe)

    pnl_value = _float(pnl)
    confidence_value = _clamp(_float(confidence))

    signal_accuracy = evaluate_signal_accuracy(
        normalized_signal,
        normalized_outcome,
    )

    risk_reward = evaluate_risk_reward(
        planned_risk=planned_risk,
        planned_reward=planned_reward,
        pnl=pnl_value,
    )

    execution_result = evaluate_execution(
        execution=execution,
    )

    quality = calculate_trade_quality(
        signal_accuracy=signal_accuracy["accuracy_score"],
        pnl=pnl_value,
        confidence=confidence_value,
        execution_quality=execution_result["quality"],
    )

    feedback = build_learning_feedback(
        signal=normalized_signal,
        outcome=normalized_outcome,
        pnl=pnl_value,
        confidence=confidence_value,
        trade_quality=quality["score"],
    )

    learning_record = None
    pattern_record = None

    # --------------------------------------------------------------
    # Optional Adaptive Learning integration
    # --------------------------------------------------------------

    if record_learning:
        try:
            from backend.trading_engine.ai.adaptive_learning import (
                record_learning_outcome,
            )

            learning_record = record_learning_outcome(
                signal=normalized_signal,
                outcome=normalized_outcome,
                pnl=pnl_value,
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
            )

        except Exception as exc:
            learning_record = {
                "status": "NOT_RECORDED",
                "error": str(exc),
            }

    # --------------------------------------------------------------
    # Optional Pattern Memory integration
    # --------------------------------------------------------------

    if record_pattern and pattern is not None:
        try:
            from backend.trading_engine.ai.pattern_memory import (
                remember_pattern,
            )

            pattern_record = remember_pattern(
                pattern=pattern,
                outcome=normalized_outcome,
                pnl=pnl_value,
                signal=normalized_signal,
            )

        except Exception as exc:
            pattern_record = {
                "status": "NOT_RECORDED",
                "error": str(exc),
            }

    return {
        "status": "READY",
        "module": MODULE_NAME,
        "version": VERSION,

        "symbol": normalized_symbol,
        "timeframe": normalized_timeframe,

        "signal": normalized_signal,
        "outcome": normalized_outcome,
        "pnl": pnl_value,
        "confidence": confidence_value,

        "signal_accuracy": signal_accuracy,

        "risk_reward": risk_reward,

        "execution": execution_result,

        "trade_quality": quality,

        "learning_feedback": feedback,

        "learning_record": learning_record,
        "pattern_record": pattern_record,

        # Architectural safety markers.
        "decision": None,
        "decision_authority": "downstream_decision_layers",

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_management": False,
        "execution_allowed": False,
        "order_placement": False,
        "mt5_order_send": False,
    }


# ======================================================================
# CONVENIENCE API
# ======================================================================

def evaluate_trade_result(
    signal: Any,
    outcome: Any = None,
    pnl: Any = 0.0,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    confidence: Any = 0.0,
    planned_risk: Any = None,
    planned_reward: Any = None,
    execution: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Simplified public API for evaluating a trade result.
    """

    return evaluate_trade(
        signal=signal,
        outcome=outcome,
        pnl=pnl,
        symbol=symbol,
        timeframe=timeframe,
        confidence=confidence,
        planned_risk=planned_risk,
        planned_reward=planned_reward,
        execution=execution,
    )


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def trade_evaluator_info() -> Dict[str, Any]:
    """
    Return module capability and architectural information.
    """

    return {
        "name": MODULE_NAME,
        "version": VERSION,
        "status": "READY",

        "supported_markets": list(SUPPORTED_MARKETS),
        "supported_timeframes": list(SUPPORTED_TIMEFRAMES),

        "supported_signals": list(VALID_SIGNALS),
        "supported_outcomes": list(VALID_OUTCOMES),

        "outputs": [
            "signal_accuracy",
            "risk_reward",
            "execution",
            "trade_quality",
            "learning_feedback",
        ],

        "adaptive_learning_integration": True,
        "pattern_memory_integration": True,

        "decision_authority": "downstream_decision_layers",

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_management": False,
        "execution": False,
        "order_placement": False,
        "mt5_order_send": False,
    }


# ======================================================================
# ALIAS
# ======================================================================

analyze_trade = evaluate_trade
