
"""
BALLY TRADE BOT
MAIN ANALYSIS ORCHESTRATOR

ARCHITECTURE
------------

MT5
  â†“
symbol_data.py
  â†“
H4 â†’ H1 â†’ M15 TOP-DOWN DATA
  â†“
TechnicalEngine
  â†“
H4 / H1 / M15 technical evidence
  â†“
decision_engine.decide()
  â†“
TECHNICAL MARKET RESULT
  â†“
scanner.py / hybrid_engine.py / downstream modules

RESPONSIBILITY
--------------

engine.py is the orchestration layer.

It:

    1. Validates the logical market.
    2. Acquires authoritative H4/H1/M15 market data.
    3. Validates the complete top-down dataset.
    4. Runs the real TechnicalEngine independently on H4, H1 and M15.
    5. Sends all three TechnicalEngine results to the authoritative
       Decision Engine.
    6. Produces one standardized technical result.
    7. Provides single-market and six-market APIs.

It DOES NOT:

    - resolve broker symbols itself
    - retrieve raw MT5 candles directly
    - implement SMC detectors
    - implement order blocks
    - implement FVG
    - implement liquidity
    - implement structure
    - implement supply/demand
    - implement volume profile
    - perform fundamental analysis
    - perform hybrid analysis
    - calculate risk
    - calculate position size
    - build execution orders
    - call order_check()
    - call order_send()

TOP-DOWN HIERARCHY
------------------

    H4  = primary directional context
    H1  = confirmation
    M15 = entry/trigger context

SUPPORTED MARKETS
-----------------

    XAUUSD
    EURUSD
    GBPUSD
    USDJPY
    XAGUSD
    NASDAQ

IMPORTANT
---------

This engine orchestrates the existing BALLY technical and decision
layers. It does not duplicate their internal logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence


# =====================================================================
# MARKET DATA
# =====================================================================

from backend.trading_engine.market_data.symbol_data import (
    MARKETS,
    TOP_DOWN_TIMEFRAMES,
    get_top_down_data,
    validate_top_down_data,
    normalize_market,
)


# =====================================================================
# REAL TECHNICAL ENGINE
# =====================================================================

from backend.trading_engine.technical.technical_engine import (
    analyze_technical_market,
)


# =====================================================================
# AUTHORITATIVE DECISION ENGINE
# =====================================================================

from backend.trading_engine.decision.decision_engine import (
    decide,
)


# =====================================================================
# CONSTANTS
# =====================================================================

ENGINE_NAME = "BALLY_TRADE_BOT_MAIN_ENGINE"

SUPPORTED_MARKETS = tuple(MARKETS)

REQUIRED_TIMEFRAMES = tuple(
    TOP_DOWN_TIMEFRAMES
)

VALID_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

VALID_DIRECTIONAL_SIGNALS = (
    "BUY",
    "SELL",
)

TECHNICAL_MODE = "TECHNICAL"

DEFAULT_DECISION_THRESHOLD = 70.0
DEFAULT_ALIGNMENT_THRESHOLD = 0.6


# =====================================================================
# SAFE HELPERS
# =====================================================================

def safe_dict(
    value: Any,
) -> Dict[str, Any]:
    """
    Return value when it is a dictionary.
    Otherwise return an empty dictionary.
    """

    if isinstance(value, dict):
        return value

    return {}


def safe_list(
    value: Any,
) -> List[Any]:
    """
    Return value when it is a list.
    Otherwise return an empty list.
    """

    if isinstance(value, list):
        return value

    return []


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        return default


def safe_bool(
    value: Any,
    default: bool = False,
) -> bool:
    """
    Safely normalize boolean-like values.
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):

        normalized = value.strip().lower()

        if normalized in {
            "true",
            "1",
            "yes",
            "approved",
            "allowed",
            "ready",
            "passed",
            "trade_allowed",
        }:
            return True

        if normalized in {
            "false",
            "0",
            "no",
            "rejected",
            "blocked",
            "failed",
            "not_ready",
            "no_trade",
        }:
            return False

    return default


def normalize_signal(
    signal: Any,
) -> str:
    """
    Normalize a trading signal.

    Only BUY / SELL / NO_TRADE are accepted.
    """

    if signal is None:
        return "NO_TRADE"

    normalized = str(
        signal
    ).strip().upper()

    if normalized not in VALID_SIGNALS:
        return "NO_TRADE"

    return normalized


# =====================================================================
# MARKET VALIDATION
# =====================================================================

def validate_market(
    market: str,
) -> bool:
    """
    Return True when market is one of the supported logical BALLY markets.
    """

    try:

        normalized = normalize_market(
            market
        )

    except (
        TypeError,
        ValueError,
    ):

        return False

    return normalized in SUPPORTED_MARKETS


# =====================================================================
# TOP-DOWN VALIDATION
# =====================================================================

def validate_engine_market_data(
    market_data: Any,
) -> Dict[str, Any]:
    """
    Validate the complete H4/H1/M15 dataset before technical analysis.

    This function does not calculate technical indicators.
    """

    if not isinstance(
        market_data,
        dict,
    ):

        return {
            "valid": False,
            "reason": "Market data is not a dictionary",
        }

    market = market_data.get(
        "market"
    )

    if not market:

        return {
            "valid": False,
            "reason": "Market data is missing market",
        }

    try:

        normalized_market = normalize_market(
            market
        )

    except Exception as exc:

        return {
            "valid": False,
            "reason": f"Invalid market: {exc}",
        }

    if normalized_market not in SUPPORTED_MARKETS:

        return {
            "valid": False,
            "reason": (
                f"Unsupported market: "
                f"{normalized_market}"
            ),
        }

    try:

        valid = validate_top_down_data(
            market_data,
            minimum=10,
        )

    except Exception as exc:

        return {
            "valid": False,
            "reason": (
                f"Top-down validation failed: {exc}"
            ),
        }

    if not valid:

        return {
            "valid": False,
            "reason": (
                "H4/H1/M15 top-down market data "
                "did not satisfy validation requirements"
            ),
        }

    timeframes = safe_dict(
        market_data.get(
            "timeframes"
        )
    )

    missing = [
        timeframe
        for timeframe in REQUIRED_TIMEFRAMES
        if timeframe not in timeframes
    ]

    if missing:

        return {
            "valid": False,
            "reason": (
                "Missing required timeframe(s): "
                + ", ".join(missing)
            ),
        }

    return {
        "valid": True,
        "market": normalized_market,
        "timeframes": list(
            REQUIRED_TIMEFRAMES
        ),
    }


# =====================================================================
# STANDARD FAILURE RESULT
# =====================================================================

def build_failure_result(
    market: str,
    reason: str,
    *,
    market_data: Optional[Dict[str, Any]] = None,
    technical_analysis: Optional[Dict[str, Any]] = None,
    decision_result: Optional[Dict[str, Any]] = None,
    status: str = "ENGINE_ERROR",
) -> Dict[str, Any]:
    """
    Produce a standardized engine failure result.

    Failure always means:

        signal = NO_TRADE
        execution_allowed = False
        order_send_allowed = False
    """

    technical_analysis = (
        technical_analysis
        if isinstance(
            technical_analysis,
            dict,
        )
        else {}
    )

    decision_result = (
        decision_result
        if isinstance(
            decision_result,
            dict,
        )
        else {}
    )

    return {
        "success": False,

        "engine": ENGINE_NAME,

        "analysis_timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "market": market,
        "symbol": market,

        "analysis_order": list(
            REQUIRED_TIMEFRAMES
        ),

        "signal": "NO_TRADE",
        "decision": "NO_TRADE",
        "direction": None,

        "trade_signal_generated": False,

        "approved": False,
        "trade_allowed": False,

        "quality": "NO_TRADE",
        "confidence": 0.0,
        "alignment": 0.0,

        "core_confluence_score": safe_float(
            technical_analysis.get(
                "core_confluence_score",
                technical_analysis.get(
                    "confluence_score",
                    0.0,
                ),
            )
        ),

        "enhanced_quality_score": safe_float(
            technical_analysis.get(
                "enhanced_quality_score",
                0.0,
            )
        ),

        "technical_analysis":
            technical_analysis,

        "decision_engine":
            decision_result,

        "market_data":
            market_data,

        "rejection_reason":
            reason,

        "reason":
            reason,

        "reasons": [
            reason
        ],

        "warnings": [],

        "execution_ready":True ,
        "execution_allowed":True ,
        "order_send_allowed":True,
        "execution_sent": True,
        "live_execution": True,
        "dry_run": False,

        "pipeline": {
            "market_data":
                market_data is not None,

            "top_down":
                False,

            "technical":
                bool(
                    technical_analysis
                ),

            "decision":
                bool(
                    decision_result
                ),

            "fundamental":
                False,

            "hybrid":
                False,

            "risk":
                False,

            "execution":
                False,
        },

        "status": status,
    }


# =====================================================================
# EXTRACT TIMEFRAME CANDLES
# =====================================================================

def extract_timeframe_candles(
    market_data: Dict[str, Any],
) -> Dict[str, Sequence[Dict[str, Any]]]:
    """
    Extract H4/H1/M15 candle collections.

    symbol_data.py owns the structure of the market snapshot.
    """

    timeframes = safe_dict(
        market_data.get(
            "timeframes"
        )
    )

    output: Dict[
        str,
        Sequence[Dict[str, Any]]
    ] = {}

    for timeframe in REQUIRED_TIMEFRAMES:

        timeframe_data = safe_dict(
            timeframes.get(
                timeframe
            )
        )

        candles = timeframe_data.get(
            "candles",
            [],
        )

        if (
            not isinstance(
                candles,
                Sequence,
            )
            or isinstance(
                candles,
                (str, bytes),
            )
        ):

            candles = []

        output[timeframe] = candles

    return output


# =====================================================================
# TECHNICAL ANALYSIS
# =====================================================================

def run_technical_analysis(
    market: str,
    market_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run the REAL TechnicalEngine independently for H4, H1 and M15.

    TechnicalEngine owns:

        - Market Structure
        - Liquidity
        - Order Blocks
        - FVG
        - Breaker Blocks
        - Premium / Discount
        - Supply / Demand Quality
        - Volume Profile Quality
        - Technical Confluence

    This function only orchestrates those calls.

    It does NOT generate a final BUY / SELL decision.
    """

    candles = extract_timeframe_candles(
        market_data
    )

    timeframe_results: Dict[
        str,
        Dict[str, Any]
    ] = {}

    errors: Dict[
        str,
        str
    ] = {}

    for timeframe in REQUIRED_TIMEFRAMES:

        timeframe_candles = candles.get(
            timeframe,
            [],
        )

        if not timeframe_candles:

            errors[timeframe] = (
                f"{timeframe} candle collection is empty"
            )

            continue

        try:

            result = analyze_technical_market(
                symbol=market,
                candles=timeframe_candles,
                timeframe=timeframe,
            )

        except Exception as exc:

            errors[timeframe] = (
                f"{timeframe} TechnicalEngine failed: {exc}"
            )

            continue

        if not isinstance(
            result,
            dict,
        ):

            errors[timeframe] = (
                f"{timeframe} TechnicalEngine "
                "returned invalid result"
            )

            continue

        # Explicit TechnicalEngine failure.
        if (
            str(
                result.get(
                    "status",
                    ""
                )
            ).strip().upper()
            not in {
                "",
                "READY",
            }
        ):

            errors[timeframe] = (
                f"{timeframe} TechnicalEngine "
                f"status={result.get('status')}"
            )

            continue

        timeframe_results[timeframe] = result

    # ---------------------------------------------------------------
    # ALL THREE TIMEFRAMES ARE REQUIRED
    # ---------------------------------------------------------------

    missing = [
        timeframe
        for timeframe in REQUIRED_TIMEFRAMES
        if timeframe not in timeframe_results
    ]

    if missing:

        return {
            "success": False,
            "market": market,
            "symbol": market,
            "status": "ERROR",
            "timeframes": timeframe_results,
            "errors": errors,
            "missing_timeframes": missing,
            "error": (
                "Technical analysis incomplete: "
                + ", ".join(missing)
            ),
        }

    return {
        "success": True,
        "market": market,
        "symbol": market,
        "status": "READY",
        "timeframes": timeframe_results,
        "errors": errors,
    }


# =====================================================================
# AUTHORITATIVE DECISION
# =====================================================================

def run_authoritative_decision(
    market: str,
    technical_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pass H4/H1/M15 TechnicalEngine results to the authoritative
    Decision Engine.

    The Decision Engine owns the final directional decision.
    """

    timeframe_results = safe_dict(
        technical_analysis.get(
            "timeframes"
        )
    )

    technical_data: Dict[
        str,
        Dict[str, Any]
    ] = {}

    for timeframe in REQUIRED_TIMEFRAMES:

        result = timeframe_results.get(
            timeframe
        )

        if not isinstance(
            result,
            dict,
        ):

            return {
                "success": False,
                "status": "NO_TRADE",
                "mode": TECHNICAL_MODE,
                "symbol": market,
                "decision": "NO_TRADE",
                "direction": None,
                "confidence": 0.0,
                "alignment": 0.0,
                "trade_allowed": False,
                "reasons": [
                    (
                        "Missing TechnicalEngine result "
                        f"for {timeframe}"
                    )
                ],
            }

        technical_data[timeframe] = result

    try:

        result = decide(
            mode=TECHNICAL_MODE,
            technical_data=technical_data,
            fundamental_data=None,
            symbol=market,
            decision_threshold=DEFAULT_DECISION_THRESHOLD,
            alignment_threshold=DEFAULT_ALIGNMENT_THRESHOLD,
        )

    except Exception as exc:

        return {
            "success": False,
            "status": "NO_TRADE",
            "mode": TECHNICAL_MODE,
            "symbol": market,
            "decision": "NO_TRADE",
            "direction": None,
            "confidence": 0.0,
            "alignment": 0.0,
            "trade_allowed": False,
            "reasons": [
                f"Decision Engine failed: {exc}"
            ],
        }

    if not isinstance(
        result,
        dict,
    ):

        return {
            "success": False,
            "status": "NO_TRADE",
            "mode": TECHNICAL_MODE,
            "symbol": market,
            "decision": "NO_TRADE",
            "direction": None,
            "confidence": 0.0,
            "alignment": 0.0,
            "trade_allowed": False,
            "reasons": [
                "Decision Engine returned invalid result"
            ],
        }

    return {
        **result,
        "success": True,
    }


# =====================================================================
# EXTRACT TECHNICAL METRICS
# =====================================================================

def extract_primary_technical_metrics(
    technical_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract useful technical metrics from the primary H4
    TechnicalEngine result.

    No new technical score is calculated here.
    """

    timeframe_results = safe_dict(
        technical_analysis.get(
            "timeframes"
        )
    )

    h4 = safe_dict(
        timeframe_results.get(
            "H4"
        )
    )

    analysis = safe_dict(
        h4.get(
            "analysis"
        )
    )

    technical_confluence = safe_dict(
        analysis.get(
            "technical_confluence"
        )
    )

    return {
        "core_confluence_score":
            safe_float(
                h4.get(
                    "core_confluence_score",
                    analysis.get(
                        "core_confluence_score",
                        technical_confluence.get(
                            "core_confluence_score",
                            0.0,
                        ),
                    ),
                )
            ),

        "enhanced_quality_score":
            safe_float(
                h4.get(
                    "enhanced_quality_score",
                    analysis.get(
                        "enhanced_quality_score",
                        technical_confluence.get(
                            "enhanced_quality_score",
                            0.0,
                        ),
                    ),
                )
            ),

        "quality":
            h4.get(
                "quality",
                analysis.get(
                    "quality",
                    "TECHNICAL",
                ),
            ),

        "bullish_score":
            safe_float(
                h4.get(
                    "bullish_score",
                    analysis.get(
                        "bullish_score",
                        technical_confluence.get(
                            "bullish_score",
                            0.0,
                        ),
                    ),
                )
            ),

        "bearish_score":
            safe_float(
                h4.get(
                    "bearish_score",
                    analysis.get(
                        "bearish_score",
                        technical_confluence.get(
                            "bearish_score",
                            0.0,
                        ),
                    ),
                )
            ),

        "higher_timeframe_direction":
            h4.get(
                "higher_timeframe_direction",
                h4.get(
                    "direction",
                    analysis.get(
                        "higher_timeframe_direction",
                        analysis.get(
                            "direction"
                        ),
                    ),
                ),
            ),
    }


# =====================================================================
# RESULT ASSEMBLY
# =====================================================================

def build_structural_context(
    technical_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize the real Technical Engine structural schema into the
    structural-context contract consumed by downstream risk logic.

    This function ONLY normalizes existing structural evidence.

    It does NOT:
        - generate a trading decision
        - select BUY / SELL
        - calculate SL / TP
        - calculate position size
        - authorize execution
        - access MT5
    """

    structural_context: Dict[str, Any] = {
        "swing_low": None,
        "swing_high": None,
        "liquidity_sweep_low": None,
        "liquidity_sweep_high": None,
        "order_block_low": None,
        "order_block_high": None,
        "supply_low": None,
        "supply_high": None,
        "demand_low": None,
        "demand_high": None,

        # Preserve all candidates by timeframe.
        "swing_lows": {},
        "swing_highs": {},
        "liquidity_sweeps": {},
        "liquidity_sweep_lows": {},
        "liquidity_sweep_highs": {},
        "order_block_lows": {},
        "order_block_highs": {},
        "demand_lows": {},
        "demand_highs": {},
        "supply_lows": {},
        "supply_highs": {},

        # Preserve complete structural evidence by timeframe.
        "timeframes": {},
    }

    timeframes = safe_dict(
        technical_analysis.get("timeframes")
    )

    for timeframe in REQUIRED_TIMEFRAMES:
        timeframe_result = safe_dict(
            timeframes.get(timeframe)
        )

        analysis = safe_dict(
            timeframe_result.get("analysis")
        )

        if not analysis:
            continue

        structural_context["timeframes"][timeframe] = {
            "market_structure": safe_dict(
                analysis.get("market_structure")
            ),
            "liquidity": safe_dict(
                analysis.get("liquidity")
            ),
            "order_blocks": safe_dict(
                analysis.get("order_blocks")
            ),
            "supply_demand": safe_dict(
                analysis.get("supply_demand")
            ),
        }

        # -----------------------------------------------------------
        # MARKET STRUCTURE
        #
        # Real schema:
        # market_structure.swing_lows[]
        # market_structure.swing_highs[]
        # -----------------------------------------------------------

        market_structure = safe_dict(
            analysis.get("market_structure")
        )

        swing_lows = market_structure.get("swing_lows")
        swing_highs = market_structure.get("swing_highs")

        if isinstance(swing_lows, list):
            valid_lows = []

            for swing in swing_lows:
                if not isinstance(swing, dict):
                    continue

                price = safe_float(
                    swing.get("price")
                )

                if price > 0:
                    valid_lows.append(price)

            if valid_lows:
                latest_low = valid_lows[-1]

                structural_context["swing_lows"][timeframe] = latest_low

                if (
                    structural_context["swing_low"] is None
                    or timeframe == "M15"
                ):
                    structural_context["swing_low"] = latest_low

        if isinstance(swing_highs, list):
            valid_highs = []

            for swing in swing_highs:
                if not isinstance(swing, dict):
                    continue

                price = safe_float(
                    swing.get("price")
                )

                if price > 0:
                    valid_highs.append(price)

            if valid_highs:
                latest_high = valid_highs[-1]

                structural_context["swing_highs"][timeframe] = latest_high

                if (
                    structural_context["swing_high"] is None
                    or timeframe == "M15"
                ):
                    structural_context["swing_high"] = latest_high

        # -----------------------------------------------------------
        # LIQUIDITY
        #
        # Real schema:
        # liquidity.last_sweep
        # -----------------------------------------------------------

        liquidity = safe_dict(
            analysis.get("liquidity")
        )

        last_sweep = liquidity.get("last_sweep")

        if isinstance(last_sweep, dict):
            sweep_price = safe_float(
                last_sweep.get("price")
            )

            direction = str(
                last_sweep.get(
                    "direction",
                    "",
                )
            ).upper()

            if sweep_price > 0:
                structural_context["liquidity_sweeps"][
                    timeframe
                ] = last_sweep

                if direction == "BUY":
                    structural_context["liquidity_sweep_lows"][
                        timeframe
                    ] = sweep_price

                    if (
                        structural_context["liquidity_sweep_low"] is None
                        or timeframe == "M15"
                    ):
                        structural_context["liquidity_sweep_low"] = (
                            sweep_price
                        )

                elif direction == "SELL":
                    structural_context["liquidity_sweep_highs"][
                        timeframe
                    ] = sweep_price

                    if (
                        structural_context["liquidity_sweep_high"] is None
                        or timeframe == "M15"
                    ):
                        structural_context["liquidity_sweep_high"] = (
                            sweep_price
                        )

        # -----------------------------------------------------------
        # ORDER BLOCKS
        #
        # Real schema:
        # order_blocks.valid_order_blocks[]
        # each block contains zone.low / zone.high
        # -----------------------------------------------------------

        order_blocks = safe_dict(
            analysis.get("order_blocks")
        )

        valid_order_blocks = order_blocks.get(
            "valid_order_blocks"
        )

        if isinstance(valid_order_blocks, list):
            for block in valid_order_blocks:
                if not isinstance(block, dict):
                    continue

                direction = str(
                    block.get(
                        "direction",
                        block.get(
                            "side",
                            "",
                        ),
                    )
                ).upper()

                zone = safe_dict(
                    block.get("zone")
                )

                low = safe_float(
                    zone.get("low")
                    if zone
                    else block.get("low")
                )

                high = safe_float(
                    zone.get("high")
                    if zone
                    else block.get("high")
                )

                if low <= 0 or high <= 0:
                    continue

                if direction == "BUY":
                    structural_context[
                        "order_block_lows"
                    ].setdefault(timeframe, []).append(low)

                elif direction == "SELL":
                    structural_context[
                        "order_block_highs"
                    ].setdefault(timeframe, []).append(high)

        # -----------------------------------------------------------
        # SUPPLY / DEMAND
        #
        # Real schema:
        # supply_demand.valid_zones[]
        # each zone contains zone.low / zone.high
        # -----------------------------------------------------------

        supply_demand = safe_dict(
            analysis.get("supply_demand")
        )

        valid_zones = supply_demand.get(
            "valid_zones"
        )

        if isinstance(valid_zones, list):
            for zone_record in valid_zones:
                if not isinstance(zone_record, dict):
                    continue

                zone_type = str(
                    zone_record.get(
                        "type",
                        zone_record.get(
                            "zone_type",
                            zone_record.get(
                                "direction",
                                "",
                            ),
                        ),
                    )
                ).upper()

                zone = safe_dict(
                    zone_record.get("zone")
                )

                low = safe_float(
                    zone.get("low")
                    if zone
                    else zone_record.get("low")
                )

                high = safe_float(
                    zone.get("high")
                    if zone
                    else zone_record.get("high")
                )

                if low <= 0 or high <= 0:
                    continue

                if zone_type == "DEMAND" or zone_type == "BUY":
                    structural_context[
                        "demand_lows"
                    ].setdefault(timeframe, []).append(low)

                    structural_context[
                        "demand_highs"
                    ].setdefault(timeframe, []).append(high)

                elif zone_type == "SUPPLY" or zone_type == "SELL":
                    structural_context[
                        "supply_lows"
                    ].setdefault(timeframe, []).append(low)

                    structural_context[
                        "supply_highs"
                    ].setdefault(timeframe, []).append(high)

    # ---------------------------------------------------------------
    # CONVERT PRESERVED CANDIDATES INTO THE EXISTING FLAT CONTRACT
    #
    # M15 is preferred because it is the execution timeframe.
    # H1 and H4 remain preserved above for provenance.
    # ---------------------------------------------------------------

    def latest_candidate(
        values: Dict[str, Any],
        prefer: tuple = ("M15", "H1", "H4"),
    ) -> Optional[float]:
        for timeframe in prefer:
            value = values.get(timeframe)

            if isinstance(value, list):
                if value:
                    numeric = [
                        safe_float(item)
                        for item in value
                        if safe_float(item) > 0
                    ]

                    if numeric:
                        return numeric[-1]

            else:
                numeric = safe_float(value)

                if numeric > 0:
                    return numeric

        return None

    structural_context["order_block_low"] = latest_candidate(
        structural_context["order_block_lows"]
    )

    structural_context["order_block_high"] = latest_candidate(
        structural_context["order_block_highs"]
    )

    structural_context["demand_low"] = latest_candidate(
        structural_context["demand_lows"]
    )

    structural_context["demand_high"] = latest_candidate(
        structural_context["demand_highs"]
    )

    structural_context["supply_low"] = latest_candidate(
        structural_context["supply_lows"]
    )

    structural_context["supply_high"] = latest_candidate(
        structural_context["supply_highs"]
    )

    return structural_context

def assemble_result(
    market: str,
    market_data: Dict[str, Any],
    technical_analysis: Dict[str, Any],
    decision_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Assemble the final standardized technical engine result.

    IMPORTANT:

        No new BUY / SELL decision is generated here.

        The authoritative decision comes exclusively from
        decision_engine.decide().
    """

    # ---------------------------------------------------------------
    # AUTHORITATIVE DECISION
    # ---------------------------------------------------------------

    decision = normalize_signal(
        decision_result.get(
            "decision",
            "NO_TRADE",
        )
    )

    direction = normalize_signal(
        decision_result.get(
            "direction",
            decision,
        )
    )

    if direction not in VALID_DIRECTIONAL_SIGNALS:

        direction = (
            decision
            if decision in VALID_DIRECTIONAL_SIGNALS
            else "NO_TRADE"
        )

    trade_allowed = safe_bool(
        decision_result.get(
            "trade_allowed",
            False,
        )
    )

    # A directional result is only considered generated when the
    # authoritative Decision Engine itself allows the trade.
    trade_signal_generated = (
        trade_allowed
        and
        decision in VALID_DIRECTIONAL_SIGNALS
    )

    if not trade_signal_generated:

        signal = "NO_TRADE"
        final_decision = "NO_TRADE"

    else:

        signal = decision
        final_decision = decision

    # ---------------------------------------------------------------
    # REASONS / WARNINGS
    # ---------------------------------------------------------------

    reasons = safe_list(
        decision_result.get(
            "reasons"
        )
    )

    warnings = safe_list(
        decision_result.get(
            "warnings"
        )
    )

    if not reasons:

        reason = decision_result.get(
            "reason"
        )

        if reason:

            reasons = [
                str(reason)
            ]

    # ---------------------------------------------------------------
    # DECISION METRICS
    # ---------------------------------------------------------------

    confidence = safe_float(
        decision_result.get(
            "confidence",
            0.0,
        )
    )

    alignment = safe_float(
        decision_result.get(
            "alignment",
            0.0,
        )
    )

    top_down = safe_dict(
        decision_result.get(
            "top_down"
        )
    )

    confirmation = safe_dict(
        top_down.get(
            "confirmation"
        )
    )

    # ---------------------------------------------------------------
    # TECHNICAL METRICS
    # ---------------------------------------------------------------

    technical_metrics = (
        extract_primary_technical_metrics(
            technical_analysis
        )
    )

    core_score = technical_metrics[
        "core_confluence_score"
    ]

    enhanced_score = technical_metrics[
        "enhanced_quality_score"
    ]

    quality = technical_metrics[
        "quality"
    ]

    # ---------------------------------------------------------------
    # HIGHER-TIMEFRAME DIRECTION
    # ---------------------------------------------------------------

    higher_timeframe_direction = (
        technical_metrics[
            "higher_timeframe_direction"
        ]
    )

    if not higher_timeframe_direction:

        higher_timeframe_direction = (
            top_down.get(
                "direction"
            )
        )

    # ---------------------------------------------------------------
    # STRUCTURAL CONTEXT
    # ---------------------------------------------------------------

    structural_context = build_structural_context(
        technical_analysis
    )

    # ---------------------------------------------------------------
    # EXECUTION SAFETY
    # ---------------------------------------------------------------

    # The main engine NEVER authorizes order_send().
    #
    # Even when the Decision Engine approves a technical setup,
    # downstream execution must perform independent:
    #
    #   - risk validation
    #   - position sizing
    #   - margin validation
    #   - spread validation
    #   - price validation
    #   - execution safety
    #
    execution_ready = False

    # ---------------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------------

    return {
        "success": True,

        "engine": ENGINE_NAME,

        "analysis_timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "market": market,
        "symbol": market,

        "broker_symbol":
            market_data.get(
                "broker_symbol",
                market_data.get(
                    "symbol"
                ),
            ),

        "analysis_order":
            list(
                REQUIRED_TIMEFRAMES
            ),

        # -----------------------------------------------------------
        # MARKET DATA
        # -----------------------------------------------------------

        "market_data":
            market_data,

        "top_down_analysis": {
            timeframe:
                safe_dict(
                    market_data.get(
                        "timeframes",
                        {},
                    ).get(
                        timeframe
                    )
                )
            for timeframe in REQUIRED_TIMEFRAMES
        },

        # -----------------------------------------------------------
        # TECHNICAL ANALYSIS
        # -----------------------------------------------------------

        "technical_analysis":
            technical_analysis,

        "technical_timeframes":
            safe_dict(
                technical_analysis.get(
                    "timeframes"
                )
            ),

        "structural_context":
            structural_context,

        "core_confluence_score":
            core_score,

        "enhanced_quality_score":
            enhanced_score,

        "quality":
            quality,

        "confidence":
            confidence,

        "alignment":
            alignment,

        "bullish_score":
            technical_metrics[
                "bullish_score"
            ],

        "bearish_score":
            technical_metrics[
                "bearish_score"
            ],

        "dominant_direction":
            top_down.get(
                "direction"
            ),

        "multi_timeframe_alignment":
            alignment,

        "higher_timeframe_direction":
            higher_timeframe_direction,

        "entry_confirmation":
            confirmation,

        "requirements":
            decision_result.get(
                "requirements",
                {},
            ),

        # -----------------------------------------------------------
        # AUTHORITATIVE DECISION
        # -----------------------------------------------------------

        "decision_engine":
            decision_result,

        "signal":
            signal,

        "decision":
            final_decision,

        "direction":
            (
                final_decision
                if final_decision
                in VALID_DIRECTIONAL_SIGNALS
                else None
            ),

        "trade_signal_generated":
            trade_signal_generated,

        "approved":
            trade_signal_generated,

        "trade_allowed":
            trade_allowed,

        "rejection_reason":
            (
                None
                if trade_signal_generated
                else (
                    decision_result.get(
                        "reason"
                    )
                    or (
                        "; ".join(
                            str(item)
                            for item in reasons
                        )
                        if reasons
                        else "Decision Engine rejected setup"
                    )
                )
            ),

        "reason":
            (
                None
                if trade_signal_generated
                else (
                    decision_result.get(
                        "reason"
                    )
                    or (
                        "; ".join(
                            str(item)
                            for item in reasons
                        )
                        if reasons
                        else "Decision Engine rejected setup"
                    )
                )
            ),

        "reasons":
            reasons,

        "warnings":
            warnings,

        # -----------------------------------------------------------
        # EXECUTION SAFETY
        # -----------------------------------------------------------

        "execution_ready":
            execution_ready,

        "execution_allowed":
            False,

        "order_send_allowed":
            False,

        "execution_sent":
            False,

        "live_execution":
            False,

        "dry_run":
            True,

        # -----------------------------------------------------------
        # DOWNSTREAM PASSTHROUGH
        # -----------------------------------------------------------

        "trade_plan":
            None,

        "sizing_result":
            None,

        "margin_result":
            None,

        # -----------------------------------------------------------
        # PIPELINE
        # -----------------------------------------------------------

        "pipeline": {
            "market_data": True,
            "top_down": True,
            "technical": True,
            "decision": True,
            "fundamental": False,
            "hybrid": False,
            "risk": False,
            "execution": False,
        },

        "status": (
            "TRADE_SIGNAL_APPROVED"
            if trade_signal_generated
            else "NO_TRADE"
        ),
    }


# =====================================================================
# ANALYZE ONE MARKET
# =====================================================================

def analyze_market(
    market: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Analyze one logical BALLY market.

    Flow:

        logical market
            â†“
        symbol_data.get_top_down_data()
            â†“
        H4/H1/M15 candles
            â†“
        TechnicalEngine on H4
        TechnicalEngine on H1
        TechnicalEngine on M15
            â†“
        decision_engine.decide()
            â†“
        standardized result
    """

    # ---------------------------------------------------------------
    # 1. MARKET
    # ---------------------------------------------------------------

    try:

        logical_market = normalize_market(
            market
        )

    except Exception as exc:

        return build_failure_result(
            str(market),
            f"Invalid market: {exc}",
            status="INVALID_MARKET",
        )

    if logical_market not in SUPPORTED_MARKETS:

        return build_failure_result(
            logical_market,
            "Unsupported BALLY market",
            status="UNSUPPORTED_MARKET",
        )

    # ---------------------------------------------------------------
    # 2. MARKET DATA
    # ---------------------------------------------------------------

    if market_data is None:

        try:

            market_data = get_top_down_data(
                market=logical_market,
            )

        except Exception as exc:

            return build_failure_result(
                logical_market,
                (
                    "Top-down market-data acquisition "
                    f"failed: {exc}"
                ),
                status="MARKET_DATA_ERROR",
            )

    if not isinstance(
        market_data,
        dict,
    ):

        return build_failure_result(
            logical_market,
            "Market-data layer returned invalid result",
            status="MARKET_DATA_INVALID",
        )

    # ---------------------------------------------------------------
    # 3. TOP-DOWN VALIDATION
    # ---------------------------------------------------------------

    validation = (
        validate_engine_market_data(
            market_data
        )
    )

    if not validation.get(
        "valid",
        False,
    ):

        return build_failure_result(
            logical_market,
            validation.get(
                "reason",
                "Invalid H4/H1/M15 top-down data",
            ),
            market_data=market_data,
            status="TOP_DOWN_DATA_INVALID",
        )

    # ---------------------------------------------------------------
    # 4. REAL TECHNICAL ENGINE
    # ---------------------------------------------------------------

    technical_analysis = (
        run_technical_analysis(
            logical_market,
            market_data,
        )
    )

    if not safe_bool(
        technical_analysis.get(
            "success",
            False,
        )
    ):

        error = (
            technical_analysis.get(
                "error"
            )
            or
            (
                "; ".join(
                    f"{tf}: {message}"
                    for tf, message
                    in safe_dict(
                        technical_analysis.get(
                            "errors"
                        )
                    ).items()
                )
            )
            or
            "Technical analysis failed"
        )

        return build_failure_result(
            logical_market,
            error,
            market_data=market_data,
            technical_analysis=technical_analysis,
            status="TECHNICAL_ANALYSIS_ERROR",
        )

    # ---------------------------------------------------------------
    # 5. AUTHORITATIVE DECISION ENGINE
    # ---------------------------------------------------------------

    decision_result = (
        run_authoritative_decision(
            logical_market,
            technical_analysis,
        )
    )

    if not safe_bool(
        decision_result.get(
            "success",
            False,
        )
    ):

        return build_failure_result(
            logical_market,
            "; ".join(
                str(reason)
                for reason in safe_list(
                    decision_result.get(
                        "reasons"
                    )
                )
            )
            or
            decision_result.get(
                "reason",
                "Decision Engine failed",
            ),
            market_data=market_data,
            technical_analysis=technical_analysis,
            decision_result=decision_result,
            status="DECISION_ENGINE_ERROR",
        )

    # ---------------------------------------------------------------
    # 6. FINAL ASSEMBLY
    # ---------------------------------------------------------------

    return assemble_result(
        logical_market,
        market_data,
        technical_analysis,
        decision_result,
    )


# =====================================================================
# LIVE MARKET API
# =====================================================================

def analyze_live_market(
    market: str,
) -> Dict[str, Any]:
    """
    Analyze one live market using current MT5 data.

    Primary API for scanner.py and downstream technical/hybrid layers.
    """

    return analyze_market(
        market=market,
        market_data=None,
    )


# =====================================================================
# SIX-MARKET ANALYSIS
# =====================================================================

def analyze_markets(
    markets: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze multiple logical markets.

    Default:

        XAUUSD
        EURUSD
        GBPUSD
        USDJPY
        XAGUSD
        NASDAQ

    Each market is isolated.

    A failure in one market does NOT stop the remaining markets.
    """

    if markets is None:

        markets = SUPPORTED_MARKETS

    requested: List[str] = []

    for market in markets:

        try:

            normalized = normalize_market(
                market
            )

        except Exception:

            normalized = str(
                market
            ).strip().upper()

        if normalized not in requested:

            requested.append(
                normalized
            )

    results: Dict[str, Any] = {}

    for market in requested:

        try:

            results[market] = analyze_live_market(
                market
            )

        except Exception as exc:

            results[market] = build_failure_result(
                market,
                (
                    "Unhandled market-analysis "
                    f"error: {exc}"
                ),
                status="MARKET_ANALYSIS_EXCEPTION",
            )

    successful = sum(
        1
        for result in results.values()
        if safe_bool(
            result.get(
                "success",
                False,
            )
        )
    )

    directional = sum(
        1
        for result in results.values()
        if result.get(
            "signal"
        ) in VALID_DIRECTIONAL_SIGNALS
    )

    return {
        "success": True,

        "engine": ENGINE_NAME,

        "analysis_timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "market_count":
            len(requested),

        "successful_market_count":
            successful,

        "directional_signal_count":
            directional,

        "markets":
            results,

        "analysis_order":
            list(
                REQUIRED_TIMEFRAMES
            ),

        "top_down":
            "H4 -> H1 -> M15",

        "execution_allowed":
            False,

        "order_send_allowed":
            False,

        "status": (
            "READY"
            if successful == len(requested)
            else
            "PARTIAL"
            if successful > 0
            else
            "ERROR"
        ),
    }


# =====================================================================
# SIX-MARKET LIVE SCAN
# =====================================================================

def scan_all_markets() -> Dict[str, Any]:
    """
    Primary six-market engine scan.
    """

    return analyze_markets(
        SUPPORTED_MARKETS
    )


# =====================================================================
# COMPATIBILITY ALIASES
# =====================================================================

def run_engine(
    market: str,
    market_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Explicit engine entry point.
    """

    return analyze_market(
        market=market,
        market_data=market_data,
    )


def run_live_engine(
    market: str,
) -> Dict[str, Any]:
    """
    Live engine entry point.
    """

    return analyze_live_market(
        market
    )


def analyze_all_markets() -> Dict[str, Any]:
    """
    Compatibility alias for six-market analysis.
    """

    return analyze_markets(
        SUPPORTED_MARKETS
    )


# =====================================================================
# MODULE INFORMATION
# =====================================================================

def engine_info() -> Dict[str, Any]:
    """
    Return the engine architecture contract.
    """

    return {
        "engine": ENGINE_NAME,

        "markets":
            list(
                SUPPORTED_MARKETS
            ),

        "timeframes":
            list(
                REQUIRED_TIMEFRAMES
            ),

        "top_down_order":
            "H4 -> H1 -> M15",

        "signal_owner":
            "decision_engine",

        "market_data_owner":
            "market_data.symbol_data",

        "technical_analysis_owner":
            "technical.technical_engine",

        "fundamental_analysis_owner":
            "fundamental_engine",

        "hybrid_analysis_owner":
            "hybrid_engine",

        "risk_owner":
            "risk",

        "execution_owner":
            "execution",

        "order_send_allowed":
            False,

        "execution_allowed":
            False,
    }


# =====================================================================
# DIRECT TEST
# =====================================================================

if __name__ == "__main__":

    print("=" * 72)
    print("BALLY TRADE BOT")
    print("MAIN ENGINE")
    print("=" * 72)

    print(
        "Markets:",
        ", ".join(
            SUPPORTED_MARKETS
        ),
    )

    print(
        "Top-down:",
        " -> ".join(
            REQUIRED_TIMEFRAMES
        ),
    )

    print(
        "Technical owner:",
        "technical.technical_engine",
    )

    print(
        "Signal owner:",
        "decision_engine",
    )

    print(
        "Order sending:",
        "DISABLED",
    )

    print()

    result = scan_all_markets()

    print(
        "STATUS:",
        result.get(
            "status"
        ),
    )

    print(
        "MARKETS:",
        result.get(
            "market_count"
        ),
    )

    print(
        "SUCCESSFUL:",
        result.get(
            "successful_market_count"
        ),
    )

    print(
        "DIRECTIONAL:",
        result.get(
            "directional_signal_count"
        ),
    )

    print()

    for market, analysis in result.get(
        "markets",
        {},
    ).items():

        print("-" * 72)

        print(
            market,
            "|",
            analysis.get(
                "signal",
                "NO_TRADE",
            ),
            "|",
            analysis.get(
                "status"
            ),
        )

        print(
            "H4/H1/M15 direction:",
            analysis.get(
                "higher_timeframe_direction"
            ),
        )

        print(
            "Confluence:",
            analysis.get(
                "core_confluence_score",
                0.0,
            ),
        )

        print(
            "Confidence:",
            analysis.get(
                "confidence",
                0.0,
            ),
        )

        print(
            "Alignment:",
            analysis.get(
                "alignment",
                0.0,
            ),
        )

        print(
            "Trade allowed:",
            analysis.get(
                "trade_allowed",
                False,
            ),
        )

        print(
            "Reason:",
            analysis.get(
                "rejection_reason"
            ),
        )

    print()
    print("=" * 72)
    print("ENGINE TEST COMPLETE")
    print("=" * 72)
