
"""
BALLY FLOW - HYBRID ENGINE
==========================

Purpose
-------
Combines the authoritative Technical Engine result with the
authoritative Fundamental Engine result and independently produces:

    BUY
    SELL
    NO_TRADE

ARCHITECTURAL RULES
-------------------

1. Technical Engine owns technical analysis.
2. Fundamental Engine owns fundamental/news analysis.
3. Hybrid Engine owns the HYBRID decision.
4. Hybrid Engine does NOT perform technical execution.
5. Hybrid Engine does NOT perform risk management.
6. Hybrid Engine does NOT calculate position size.
7. Hybrid Engine does NOT call MT5 order_check().
8. Hybrid Engine does NOT call MT5 order_send().
9. Hybrid Engine does NOT require technical execution_ready.
10. Execution readiness belongs to the downstream execution layer.

PIPELINE
--------

    Technical Result
           +
    Fundamental Result
           |
           v
    HYBRID ENGINE
           |
           +--> alignment
           +--> conflict detection
           +--> fundamental risk protection
           +--> weighted confidence
           +--> hybrid quality
           |
           v
    HYBRID DECISION
    BUY / SELL / NO_TRADE
           |
           v
    AI / DECISION VALIDATION
           |
           v
    RISK MANAGEMENT
           |
           v
    EXECUTION
           |
           v
    MT5

IMPORTANT
---------

"trade_allowed" in this module means:

    The HYBRID ANALYSIS considers the opportunity valid.

It does NOT mean:

    MT5 order placement is authorized.

The execution layer must independently validate and authorize
any actual order.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ==============================================================
# CONFIGURATION
# ==============================================================

ENGINE_NAME = "BALLY FLOW Hybrid Engine"
ENGINE_VERSION = "1.0.0"

SUPPORTED_MARKETS = (
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
)

SUPPORTED_MODES = (
    "technical",
    "hybrid",
)

VALID_SIGNALS = (
    "BUY",
    "SELL",
)

ALL_DECISIONS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

# Hybrid confidence weighting.
TECHNICAL_WEIGHT = 0.60
FUNDAMENTAL_WEIGHT = 0.40

# Minimum combined confidence for a directional hybrid decision.
HYBRID_CONFIDENCE_THRESHOLD = 70.0

# Fundamental risk states that block a hybrid trade.
HIGH_RISK_LEVELS = (
    "EXTREME",
    "VERY_HIGH",
    "HIGH",
)

# Fundamental NEUTRAL does not create a directional hybrid signal.
REQUIRE_FUNDAMENTAL_ALIGNMENT = True


# ==============================================================
# SAFE HELPERS
# ==============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default

        number = float(value)

        if number != number:
            return default

        return number

    except (TypeError, ValueError):
        return default


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_bool(value: Any, default: bool = False) -> bool:

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):

        value = value.strip().lower()

        if value in {
            "true",
            "1",
            "yes",
            "y",
            "approved",
            "allowed",
            "ready",
            "passed",
        }:
            return True

        if value in {
            "false",
            "0",
            "no",
            "n",
            "rejected",
            "blocked",
            "failed",
            "not_ready",
        }:
            return False

    return default


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def normalize_symbol(symbol: Any) -> str:

    if symbol is None:
        return ""

    return str(symbol).strip().upper()


def normalize_signal(signal: Any) -> str:

    if signal is None:
        return "NEUTRAL"

    return str(signal).strip().upper()


def normalize_risk(risk: Any) -> str:

    if risk is None:
        return "UNKNOWN"

    return str(risk).strip().upper()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==============================================================
# MARKET VALIDATION
# ==============================================================

def validate_market(symbol: Any) -> bool:
    return normalize_symbol(symbol) in SUPPORTED_MARKETS


# ==============================================================
# RESULT EXTRACTION
# ==============================================================

def extract_technical_values(
    technical_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize technical-engine output.

    This function extracts analytical information only.

    It intentionally does NOT use execution_ready as a hybrid gate.
    """

    result = safe_dict(technical_result)

    if not result:
        return {
            "signal": "NO_TRADE",
            "confidence": 0.0,
            "quality": "NO_TRADE",
            "market_state": "UNKNOWN",
            "analysis_ready": False,
            "technical_analysis": {},
            "market_conditions": {},
        }

    confidence = result.get("confidence")

    if confidence is None:
        confidence = result.get("ai_confidence_percent")

    if confidence is None:
        ai_confidence = safe_dict(
            result.get("ai_confidence")
        )

        confidence = ai_confidence.get(
            "confidence",
            0.0,
        )

    return {
        "signal": normalize_signal(
            result.get(
                "signal",
                "NO_TRADE",
            )
        ),

        "confidence": clamp(
            safe_float(confidence),
            0.0,
            100.0,
        ),

        "quality": str(
            result.get(
                "quality",
                "NO_TRADE",
            )
        ).strip().upper(),

        "market_state": str(
            result.get(
                "market_state",
                "UNKNOWN",
            )
        ).strip().upper(),

        "analysis_ready": safe_bool(
            result.get(
                "analysis_ready",
                True,
            ),
            True,
        ),

        "technical_analysis": result.get(
            "technical_analysis",
            result,
        ),

        "market_conditions": safe_dict(
            result.get(
                "market_conditions",
                {},
            )
        ),
    }


def extract_fundamental_values(
    fundamental_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Normalize fundamental-engine output.
    """

    result = safe_dict(fundamental_result)

    if not result:
        return {
            "signal": "NEUTRAL",
            "confidence": 0.0,
            "risk": "UNKNOWN",
            "trade_allowed": False,
            "quality": "VERY_WEAK",
            "market_bias": "NEUTRAL",
            "market_score": 0.0,
            "conflict": False,
            "conflict_reason": "",
            "high_impact_risk": False,
            "high_impact_count": 0,
        }

    signal = result.get(
        "signal",
        result.get(
            "fundamental_signal",
            "NEUTRAL",
        ),
    )

    return {
        "signal": normalize_signal(signal),

        "confidence": clamp(
            safe_float(
                result.get(
                    "confidence",
                    0.0,
                )
            ),
            0.0,
            100.0,
        ),

        "risk": normalize_risk(
            result.get(
                "risk_level",
                result.get(
                    "risk",
                    result.get(
                        "news_risk",
                        "UNKNOWN",
                    ),
                ),
            )
        ),

        "trade_allowed": safe_bool(
            result.get(
                "trade_allowed",
                False,
            )
        ),

        "quality": str(
            result.get(
                "quality",
                "VERY_WEAK",
            )
        ).strip().upper(),

        "market_bias": normalize_signal(
            result.get(
                "market_bias",
                "NEUTRAL",
            )
        ),

        "market_score": safe_float(
            result.get(
                "market_score",
                0.0,
            )
        ),

        "conflict": safe_bool(
            result.get(
                "conflict",
                False,
            )
        ),

        "conflict_reason": str(
            result.get(
                "conflict_reason",
                "",
            )
        ),

        "high_impact_risk": safe_bool(
            result.get(
                "high_impact_risk",
                False,
            )
        ),

        "high_impact_count": result.get(
            "high_impact_count",
            0,
        ),
    }


# ==============================================================
# HYBRID ALIGNMENT
# ==============================================================

def determine_alignment(
    technical_signal: Any,
    fundamental_signal: Any,
) -> str:
    """
    Determine relationship between technical and fundamental direction.
    """

    technical_signal = normalize_signal(
        technical_signal
    )

    fundamental_signal = normalize_signal(
        fundamental_signal
    )

    if (
        technical_signal == "BUY"
        and fundamental_signal == "BUY"
    ):
        return "BUY_ALIGNED"

    if (
        technical_signal == "SELL"
        and fundamental_signal == "SELL"
    ):
        return "SELL_ALIGNED"

    if (
        technical_signal in VALID_SIGNALS
        and fundamental_signal in VALID_SIGNALS
    ):
        return "CONFLICT"

    if (
        technical_signal in VALID_SIGNALS
        and fundamental_signal == "NEUTRAL"
    ):
        return "FUNDAMENTAL_NEUTRAL"

    if (
        fundamental_signal in VALID_SIGNALS
        and technical_signal not in VALID_SIGNALS
    ):
        return "TECHNICAL_NEUTRAL"

    return "NEUTRAL"


# ==============================================================
# HYBRID DECISION
# ==============================================================

def determine_hybrid_signal(
    technical_signal: Any,
    fundamental_signal: Any,
    alignment: str,
) -> str:
    """
    HYBRID ENGINE'S AUTHORITATIVE DIRECTION.

    Only fully aligned BUY or SELL conditions can produce
    a directional hybrid decision.
    """

    if alignment == "BUY_ALIGNED":
        return "BUY"

    if alignment == "SELL_ALIGNED":
        return "SELL"

    return "NO_TRADE"


# ==============================================================
# HYBRID CONFIDENCE
# ==============================================================

def calculate_hybrid_confidence(
    technical_confidence: Any,
    fundamental_confidence: Any,
    alignment: str,
) -> float:
    """
    Calculate weighted hybrid confidence.

    Technical = 60%
    Fundamental = 40%

    No alignment means no directional confidence.
    """

    technical_confidence = clamp(
        safe_float(technical_confidence),
        0.0,
        100.0,
    )

    fundamental_confidence = clamp(
        safe_float(fundamental_confidence),
        0.0,
        100.0,
    )

    if alignment not in {
        "BUY_ALIGNED",
        "SELL_ALIGNED",
    }:
        return 0.0

    confidence = (
        technical_confidence * TECHNICAL_WEIGHT
        +
        fundamental_confidence * FUNDAMENTAL_WEIGHT
    )

    return round(
        clamp(
            confidence,
            0.0,
            100.0,
        ),
        2,
    )


# ==============================================================
# HYBRID QUALITY
# ==============================================================

def determine_hybrid_quality(
    hybrid_signal: str,
    hybrid_confidence: float,
    alignment: str,
    fundamental_risk: str,
) -> str:

    if hybrid_signal == "NO_TRADE":

        if alignment == "CONFLICT":
            return "CONFLICT"

        if fundamental_risk in HIGH_RISK_LEVELS:
            return "HIGH_NEWS_RISK"

        if alignment == "FUNDAMENTAL_NEUTRAL":
            return "FUNDAMENTAL_NEUTRAL"

        if alignment == "TECHNICAL_NEUTRAL":
            return "TECHNICAL_NEUTRAL"

        return "NO_TRADE"

    if hybrid_confidence >= 85.0:
        return "VERY_STRONG"

    if hybrid_confidence >= 75.0:
        return "STRONG"

    if hybrid_confidence >= HYBRID_CONFIDENCE_THRESHOLD:
        return "QUALIFIED"

    return "WEAK"


# ==============================================================
# HYBRID PERMISSION
# ==============================================================

def determine_hybrid_permission(
    technical_values: Dict[str, Any],
    fundamental_values: Dict[str, Any],
    alignment: str,
    hybrid_signal: str,
    hybrid_confidence: float,
) -> Dict[str, Any]:
    """
    Determines whether the HYBRID opportunity is valid.

    IMPORTANT:

    This is NOT execution authorization.

    No technical execution_ready check is performed here.
    """

    technical_values = safe_dict(
        technical_values
    )

    fundamental_values = safe_dict(
        fundamental_values
    )

    technical_signal = normalize_signal(
        technical_values.get(
            "signal",
            "NO_TRADE",
        )
    )

    fundamental_signal = normalize_signal(
        fundamental_values.get(
            "signal",
            "NEUTRAL",
        )
    )

    fundamental_risk = normalize_risk(
        fundamental_values.get(
            "risk",
            "UNKNOWN",
        )
    )

    # ----------------------------------------------------------
    # Technical analysis must provide a directional signal.
    # ----------------------------------------------------------

    if technical_signal not in VALID_SIGNALS:
        return {
            "allowed": False,
            "reason": (
                "Technical analysis did not produce "
                "a directional signal"
            ),
        }

    # ----------------------------------------------------------
    # Fundamental conflict is a hard hybrid block.
    # ----------------------------------------------------------

    if safe_bool(
        fundamental_values.get(
            "conflict",
            False,
        )
    ):
        return {
            "allowed": False,
            "reason": (
                "Fundamental analysis reports "
                "an internal conflict"
            ),
        }

    # ----------------------------------------------------------
    # High-impact fundamental risk protection.
    # ----------------------------------------------------------

    if fundamental_risk in HIGH_RISK_LEVELS:
        return {
            "allowed": False,
            "reason": (
                "Fundamental risk level is "
                f"{fundamental_risk}"
            ),
        }

    if safe_bool(
        fundamental_values.get(
            "high_impact_risk",
            False,
        )
    ):
        return {
            "allowed": False,
            "reason": (
                "High-impact fundamental risk is active"
            ),
        }

    # ----------------------------------------------------------
    # Fundamental engine must permit the opportunity.
    # ----------------------------------------------------------

    if not safe_bool(
        fundamental_values.get(
            "trade_allowed",
            False,
        )
    ):
        return {
            "allowed": False,
            "reason": (
                "Fundamental engine does not permit "
                "the hybrid opportunity"
            ),
        }

    # ----------------------------------------------------------
    # Full technical/fundamental directional alignment.
    # ----------------------------------------------------------

    if REQUIRE_FUNDAMENTAL_ALIGNMENT:

        if alignment not in {
            "BUY_ALIGNED",
            "SELL_ALIGNED",
        }:
            return {
                "allowed": False,
                "reason": (
                    "Technical and fundamental signals "
                    "are not aligned"
                ),
            }

    # ----------------------------------------------------------
    # Hybrid engine must have its own valid decision.
    # ----------------------------------------------------------

    if hybrid_signal not in VALID_SIGNALS:
        return {
            "allowed": False,
            "reason": (
                "Hybrid engine produced NO_TRADE"
            ),
        }

    # ----------------------------------------------------------
    # Confidence gate.
    # ----------------------------------------------------------

    if hybrid_confidence < HYBRID_CONFIDENCE_THRESHOLD:
        return {
            "allowed": False,
            "reason": (
                f"Hybrid confidence "
                f"{hybrid_confidence:.2f}% is below "
                f"the required "
                f"{HYBRID_CONFIDENCE_THRESHOLD:.2f}%"
            ),
        }

    return {
        "allowed": True,
        "reason": (
            "Technical and fundamental conditions "
            "are aligned and meet hybrid requirements"
        ),
    }


# ==============================================================
# FAILURE RESULT
# ==============================================================

def hybrid_failure_result(
    symbol: str,
    status: str,
    reason: str,
) -> Dict[str, Any]:

    return {
        "success": False,

        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,

        "symbol": normalize_symbol(symbol),

        "timestamp": utc_timestamp(),

        "status": status,

        "technical_signal": "NO_TRADE",
        "technical_confidence": 0.0,

        "fundamental_signal": "NEUTRAL",
        "fundamental_confidence": 0.0,

        "alignment": "NEUTRAL",

        "hybrid_signal": "NO_TRADE",
        "hybrid_confidence": 0.0,
        "hybrid_quality": "NO_TRADE",

        "signal": "NO_TRADE",
        "confidence": 0.0,
        "quality": "BLOCKED",

        "trade_allowed": False,

        "permission_reason": reason,
        "rejection_reason": reason,

        # Explicit execution separation.
        "execution_allowed": False,
        "order_send_allowed": False,
        "execution_sent": False,

        "pipeline": {
            "technical": False,
            "fundamental": False,
            "hybrid": False,
            "execution": False,
        },
    }


# ==============================================================
# MAIN HYBRID ENGINE
# ==============================================================

def analyze_hybrid_market(
    symbol: str,
    technical_result: Optional[Dict[str, Any]] = None,
    fundamental_result: Optional[Dict[str, Any]] = None,
    provider: Any = None,
) -> Dict[str, Any]:
    """
    Main Hybrid Engine API.

    Preferred usage:

        analyze_hybrid_market(
            symbol="XAUUSD",
            technical_result=technical_result,
            fundamental_result=fundamental_result,
        )

    The caller should normally provide already-computed results
    from the Technical and Fundamental engines.

    This prevents duplicate analysis.

    If results are omitted, the engine attempts to obtain them
    lazily for backward compatibility.
    """

    symbol = normalize_symbol(symbol)

    # ----------------------------------------------------------
    # MARKET VALIDATION
    # ----------------------------------------------------------

    if not validate_market(symbol):

        return hybrid_failure_result(
            symbol,
            "INVALID_MARKET",
            f"Unsupported market: {symbol}",
        )

    # ----------------------------------------------------------
    # TECHNICAL RESULT
    # ----------------------------------------------------------

    if technical_result is None:

        try:

            # Lazy import prevents architectural circular imports.
            from backend.trading_engine.technical.technical_engine import (
                analyze_technical_market,
            )

            from backend.trading_engine.market_data.symbol_data import (
                get_top_down_data,
            )

            market_data = get_top_down_data(
                symbol
            )

            if not isinstance(
                market_data,
                dict,
            ):
                return hybrid_failure_result(
                    symbol,
                    "TECHNICAL_DATA_INVALID",
                    "Technical market data is invalid",
                )

            timeframes = safe_dict(
                market_data.get(
                    "timeframes"
                )
            )

            # --------------------------------------------------
            # Run Technical Engine across H4/H1/M15.
            # --------------------------------------------------

            technical_results = {}

            for timeframe in (
                "H4",
                "H1",
                "M15",
            ):

                timeframe_data = safe_dict(
                    timeframes.get(
                        timeframe
                    )
                )

                candles = timeframe_data.get(
                    "candles"
                )

                if candles:

                    technical_results[
                        timeframe
                    ] = analyze_technical_market(
                        symbol=symbol,
                        candles=candles,
                        timeframe=timeframe,
                    )

            technical_result = build_multi_timeframe_technical_result(
                symbol,
                technical_results,
            )

        except Exception as exc:

            return hybrid_failure_result(
                symbol,
                "TECHNICAL_ENGINE_FAILED",
                f"Technical engine error: {exc}",
            )

    # ----------------------------------------------------------
    # VALIDATE TECHNICAL RESULT
    # ----------------------------------------------------------

    if not isinstance(
        technical_result,
        dict,
    ):

        return hybrid_failure_result(
            symbol,
            "TECHNICAL_RESULT_INVALID",
            "Technical engine returned an invalid result",
        )

    technical_values = extract_technical_values(
        technical_result
    )

    # ----------------------------------------------------------
    # MARKET CLOSED
    # ----------------------------------------------------------

    market_state = str(
        technical_values.get(
            "market_state",
            "UNKNOWN",
        )
    ).upper()

    if market_state == "MARKET_CLOSED":

        return hybrid_failure_result(
            symbol,
            "MARKET_CLOSED",
            "Market is closed",
        )

    # ----------------------------------------------------------
    # FUNDAMENTAL RESULT
    # ----------------------------------------------------------

    if fundamental_result is None:

        try:

            from backend.trading_engine.fundamental.fundamental_engine import (
                run_fundamental_engine,
            )

            fundamental_result = run_fundamental_engine(
                symbol=symbol,
                provider=provider,
            )

        except Exception as exc:

            return hybrid_failure_result(
                symbol,
                "FUNDAMENTAL_ENGINE_FAILED",
                f"Fundamental engine error: {exc}",
            )

    # ----------------------------------------------------------
    # VALIDATE FUNDAMENTAL RESULT
    # ----------------------------------------------------------

    if not isinstance(
        fundamental_result,
        dict,
    ):

        return hybrid_failure_result(
            symbol,
            "FUNDAMENTAL_RESULT_INVALID",
            "Fundamental engine returned an invalid result",
        )

    fundamental_values = extract_fundamental_values(
        fundamental_result
    )

    # ==========================================================
    # SIGNALS
    # ==========================================================

    technical_signal = normalize_signal(
        technical_values.get(
            "signal",
            "NO_TRADE",
        )
    )

    technical_confidence = clamp(
        safe_float(
            technical_values.get(
                "confidence",
                0.0,
            )
        ),
        0.0,
        100.0,
    )

    fundamental_signal = normalize_signal(
        fundamental_values.get(
            "signal",
            "NEUTRAL",
        )
    )

    fundamental_confidence = clamp(
        safe_float(
            fundamental_values.get(
                "confidence",
                0.0,
            )
        ),
        0.0,
        100.0,
    )

    # ==========================================================
    # ALIGNMENT
    # ==========================================================

    alignment = determine_alignment(
        technical_signal,
        fundamental_signal,
    )

    # ==========================================================
    # HYBRID ENGINE'S OWN DECISION
    # ==========================================================

    hybrid_signal = determine_hybrid_signal(
        technical_signal,
        fundamental_signal,
        alignment,
    )

    # ==========================================================
    # HYBRID CONFIDENCE
    # ==========================================================

    hybrid_confidence = calculate_hybrid_confidence(
        technical_confidence,
        fundamental_confidence,
        alignment,
    )

    # ==========================================================
    # FUNDAMENTAL RISK
    # ==========================================================

    fundamental_risk = normalize_risk(
        fundamental_values.get(
            "risk",
            "UNKNOWN",
        )
    )

    # ==========================================================
    # QUALITY
    # ==========================================================

    hybrid_quality = determine_hybrid_quality(
        hybrid_signal,
        hybrid_confidence,
        alignment,
        fundamental_risk,
    )

    # ==========================================================
    # HYBRID PERMISSION
    # ==========================================================

    permission = determine_hybrid_permission(
        technical_values=technical_values,
        fundamental_values=fundamental_values,
        alignment=alignment,
        hybrid_signal=hybrid_signal,
        hybrid_confidence=hybrid_confidence,
    )

    trade_allowed = safe_bool(
        permission.get(
            "allowed",
            False,
        )
    )

    permission_reason = str(
        permission.get(
            "reason",
            "Hybrid opportunity rejected",
        )
    )

    # ==========================================================
    # FINAL HYBRID DECISION
    # ==========================================================

    final_signal = (
        hybrid_signal
        if trade_allowed
        else "NO_TRADE"
    )

    final_confidence = (
        hybrid_confidence
        if trade_allowed
        else 0.0
    )

    final_quality = (
        hybrid_quality
        if trade_allowed
        else "BLOCKED"
    )

    # ==========================================================
    # STATUS
    # ==========================================================

    if trade_allowed:

        status = "HYBRID_DECISION_READY"

    elif alignment == "CONFLICT":

        status = "HYBRID_SIGNAL_CONFLICT"

    elif fundamental_risk in HIGH_RISK_LEVELS:

        status = "HYBRID_NEWS_RISK_BLOCKED"

    elif safe_bool(
        fundamental_values.get(
            "high_impact_risk",
            False,
        )
    ):

        status = "HYBRID_HIGH_IMPACT_RISK_BLOCKED"

    elif technical_signal not in VALID_SIGNALS:

        status = "HYBRID_TECHNICAL_NO_TRADE"

    elif fundamental_signal == "NEUTRAL":

        status = "HYBRID_FUNDAMENTAL_NEUTRAL"

    elif not safe_bool(
        fundamental_values.get(
            "trade_allowed",
            False,
        )
    ):

        status = "HYBRID_FUNDAMENTAL_BLOCKED"

    elif hybrid_confidence < HYBRID_CONFIDENCE_THRESHOLD:

        status = "HYBRID_CONFIDENCE_BLOCKED"

    else:

        status = "HYBRID_NO_TRADE"

    # ==========================================================
    # FINAL RESULT
    # ==========================================================

    return {
        "success": True,

        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,

        "symbol": symbol,

        "timestamp": utc_timestamp(),

        "status": status,

        # ------------------------------------------------------
        # TECHNICAL
        # ------------------------------------------------------

        "technical_signal": technical_signal,

        "technical_confidence": technical_confidence,

        "technical_quality": technical_values.get(
            "quality",
            "NO_TRADE",
        ),

        "technical_analysis": technical_result,

        "technical_result": technical_result,

        # ------------------------------------------------------
        # FUNDAMENTAL
        # ------------------------------------------------------

        "fundamental_signal": fundamental_signal,

        "fundamental_confidence": fundamental_confidence,

        "fundamental_quality": fundamental_values.get(
            "quality",
            "VERY_WEAK",
        ),

        "fundamental_risk": fundamental_risk,

        "fundamental_trade_allowed": safe_bool(
            fundamental_values.get(
                "trade_allowed",
                False,
            )
        ),

        "fundamental_analysis": fundamental_result,

        "fundamental_result": fundamental_result,

        "fundamental_market_bias": fundamental_values.get(
            "market_bias",
            "NEUTRAL",
        ),

        "fundamental_market_score": fundamental_values.get(
            "market_score",
            0.0,
        ),

        "fundamental_conflict": safe_bool(
            fundamental_values.get(
                "conflict",
                False,
            )
        ),

        "fundamental_conflict_reason": fundamental_values.get(
            "conflict_reason",
            "",
        ),

        "high_impact_risk": safe_bool(
            fundamental_values.get(
                "high_impact_risk",
                False,
            )
        ),

        "high_impact_count": fundamental_values.get(
            "high_impact_count",
            0,
        ),

        # ------------------------------------------------------
        # HYBRID
        # ------------------------------------------------------

        "alignment": alignment,

        "signals_aligned": alignment in {
            "BUY_ALIGNED",
            "SELL_ALIGNED",
        },

        "hybrid_signal": hybrid_signal,

        "hybrid_confidence": hybrid_confidence,

        "hybrid_quality": hybrid_quality,

        "technical_weight": TECHNICAL_WEIGHT,

        "fundamental_weight": FUNDAMENTAL_WEIGHT,

        "hybrid_confidence_threshold": (
            HYBRID_CONFIDENCE_THRESHOLD
        ),

        # ------------------------------------------------------
        # AUTHORITATIVE HYBRID DECISION
        # ------------------------------------------------------

        "signal": final_signal,

        "confidence": final_confidence,

        "quality": final_quality,

        "decision": final_signal,

        "decision_authority": "hybrid_engine",

        "trade_allowed": trade_allowed,

        "permission_reason": permission_reason,

        "rejection_reason": (
            None
            if trade_allowed
            else permission_reason
        ),

        # ------------------------------------------------------
        # EXECUTION SEPARATION
        # ------------------------------------------------------

        "execution_allowed": False,

        "order_send_allowed": False,

        "execution_sent": False,

        "live_execution": False,

        "dry_run": True,

        "execution_authority": (
            "downstream_execution_layer"
        ),

        # ------------------------------------------------------
        # PIPELINE
        # ------------------------------------------------------

        "pipeline": {
            "market_data": True,
            "technical": True,
            "fundamental": True,
            "hybrid": True,
            "ai": False,
            "risk_management": False,
            "execution": False,
            "order_placement": False,
        },
    }


# ==============================================================
# MULTI-TIMEFRAME TECHNICAL AGGREGATION
# ==============================================================

def build_multi_timeframe_technical_result(
    symbol: str,
    timeframe_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a compact technical result for Hybrid Engine use.

    H4  = 45%
    H1  = 35%
    M15 = 20%

    This does NOT replace the authoritative Technical Engine.
    It only creates the input contract required by Hybrid Engine.
    """

    weights = {
        "H4": 0.45,
        "H1": 0.35,
        "M15": 0.20,
    }

    directional_scores = {
        "BUY": 0.0,
        "SELL": 0.0,
    }

    confidence_total = 0.0
    confidence_weight = 0.0

    valid_timeframes = 0

    for timeframe, weight in weights.items():

        result = safe_dict(
            timeframe_results.get(
                timeframe
            )
        )

        if not result:
            continue

        signal = normalize_signal(
            result.get(
                "signal",
                "NO_TRADE",
            )
        )

        confidence = clamp(
            safe_float(
                result.get(
                    "confidence",
                    result.get(
                        "ai_confidence_percent",
                        0.0,
                    ),
                )
            ),
            0.0,
            100.0,
        )

        if signal in VALID_SIGNALS:

            directional_scores[
                signal
            ] += weight

            confidence_total += (
                confidence * weight
            )

            confidence_weight += weight

        valid_timeframes += 1

    if (
        directional_scores["BUY"]
        > directional_scores["SELL"]
    ):
        signal = "BUY"

    elif (
        directional_scores["SELL"]
        > directional_scores["BUY"]
    ):
        signal = "SELL"

    else:
        signal = "NO_TRADE"

    confidence = (
        confidence_total / confidence_weight
        if confidence_weight > 0.0
        else 0.0
    )

    return {
        "symbol": normalize_symbol(symbol),

        "signal": signal,

        "confidence": round(
            confidence,
            2,
        ),

        "quality": (
            "QUALIFIED"
            if confidence >= 70.0
            else "NO_TRADE"
        ),

        "analysis_ready": (
            valid_timeframes > 0
        ),

        "timeframes": timeframe_results,

        "technical_analysis": {
            "timeframes": timeframe_results,
            "directional_scores": directional_scores,
        },

        "market_state": "OPEN",

        "market_conditions": {},
    }


# ==============================================================
# COMPATIBILITY ALIASES
# ==============================================================

def analyze_market(
    symbol: str,
    technical_result: Optional[Dict[str, Any]] = None,
    fundamental_result: Optional[Dict[str, Any]] = None,
    provider: Any = None,
) -> Dict[str, Any]:

    return analyze_hybrid_market(
        symbol=symbol,
        technical_result=technical_result,
        fundamental_result=fundamental_result,
        provider=provider,
    )


def run_hybrid_engine(
    symbol: str,
    technical_result: Optional[Dict[str, Any]] = None,
    fundamental_result: Optional[Dict[str, Any]] = None,
    provider: Any = None,
) -> Dict[str, Any]:

    return analyze_hybrid_market(
        symbol=symbol,
        technical_result=technical_result,
        fundamental_result=fundamental_result,
        provider=provider,
    )


# ==============================================================
# ENGINE INFORMATION
# ==============================================================

def hybrid_engine_info() -> Dict[str, Any]:

    return {
        "name": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "status": "READY",

        "supported_markets": list(
            SUPPORTED_MARKETS
        ),

        "supported_modes": list(
            SUPPORTED_MODES
        ),

        "technical_weight": TECHNICAL_WEIGHT,

        "fundamental_weight": FUNDAMENTAL_WEIGHT,

        "confidence_threshold": (
            HYBRID_CONFIDENCE_THRESHOLD
        ),

        "decisions": list(
            ALL_DECISIONS
        ),

        "decision_authority": "hybrid_engine",

        "technical_analysis": True,

        "fundamental_analysis": True,

        "hybrid_decision": True,

        "risk_management": False,

        "execution": False,

        "order_placement": False,

        "mt5_order_check": False,

        "mt5_order_send": False,
    }


# ==============================================================
# ALL MARKETS
# ==============================================================

def analyze_all_markets(
    technical_results: Optional[Dict[str, Dict[str, Any]]] = None,
    fundamental_results: Optional[Dict[str, Dict[str, Any]]] = None,
    provider: Any = None,
) -> Dict[str, Any]:
    """
    Analyze every supported market.

    Precomputed technical/fundamental results are preferred.
    """

    technical_results = (
        technical_results
        if isinstance(
            technical_results,
            dict,
        )
        else {}
    )

    fundamental_results = (
        fundamental_results
        if isinstance(
            fundamental_results,
            dict,
        )
        else {}
    )

    results = {}

    for symbol in SUPPORTED_MARKETS:

        results[symbol] = analyze_hybrid_market(
            symbol=symbol,

            technical_result=technical_results.get(
                symbol
            ),

            fundamental_result=fundamental_results.get(
                symbol
            ),

            provider=provider,
        )

    return {
        "success": True,

        "engine": ENGINE_NAME,

        "timestamp": utc_timestamp(),

        "market_count": len(
            SUPPORTED_MARKETS
        ),

        "markets": results,
    }


# ==============================================================
# DIRECT TEST
# ==============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("BALLY FLOW")
    print("HYBRID ENGINE")
    print("=" * 70)

    print()

    print(
        "ENGINE:",
        ENGINE_NAME,
    )

    print(
        "VERSION:",
        ENGINE_VERSION,
    )

    print(
        "DECISION AUTHORITY:",
        "HYBRID ENGINE",
    )

    print(
        "EXECUTION:",
        "DISABLED",
    )

    print(
        "ORDER PLACEMENT:",
        "DISABLED",
    )

    print()

    print(
        hybrid_engine_info()
    )

    print()

    print("=" * 70)
