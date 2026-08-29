
"""
BALLY FLOW - Decision Engine

AUTHORITATIVE DECISION LAYER
=============================

This module is the authoritative decision layer between analysis
and downstream trade planning / risk / execution.

ARCHITECTURE
------------

    MARKET DATA
         |
         v
    SCANNER
         |
         v
    TECHNICAL ENGINE
      H4 / H1 / M15
         |
         v
    TECHNICAL EVIDENCE
         |
         v
    DECISION ENGINE
      /          \
 TECHNICAL      HYBRID
    |              |
    v              v
 BUY/SELL/NO_TRADE
         |
         v
    DOWNSTREAM
    TRADE PLAN
    RISK
    EXECUTION

IMPORTANT
---------

TechnicalEngine performs technical analysis but MUST NOT make the
final trading decision.

TechnicalConfluence aggregates technical components but does not
itself decide BUY / SELL / NO_TRADE.

This module performs that final analytical decision.

This module MUST NOT:

    - retrieve market data directly
    - perform MT5 order execution
    - call order_send()
    - calculate broker lot size
    - manage account risk
    - place orders
    - perform technical analysis itself
    - silently use fundamental analysis in Technical Mode

MODES
-----

TECHNICAL:
    Technical evidence only.

HYBRID:
    Technical evidence + supplied fundamental evidence.

There are intentionally only two supported application modes.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple
import math


# =====================================================================
# PUBLIC CONSTANTS
# =====================================================================

BUY = "BUY"
SELL = "SELL"
NO_TRADE = "NO_TRADE"

TECHNICAL = "technical"
HYBRID = "hybrid"

SUPPORTED_MODES = (
    TECHNICAL,
    HYBRID,
)

TOP_DOWN_TIMEFRAMES = (
    "H4",
    "H1",
    "M15",
)

# Top-down weighting.
#
# H4 establishes the broad directional environment.
# H1 confirms the directional structure.
# M15 is the entry/trigger timeframe.
#
# The weights deliberately give higher authority to H4/H1 than M15.
TIMEFRAME_WEIGHTS = {
    "H4": 0.45,
    "H1": 0.35,
    "M15": 0.20,
}

# Minimum confidence required before a directional decision can be
# considered trade-eligible.
DEFAULT_DECISION_THRESHOLD = 70.0

# Minimum directional alignment required for a normal technical
# decision.
DEFAULT_ALIGNMENT_THRESHOLD = 0.60

# A technical result must contain these core components before the
# decision engine considers the analysis structurally complete.
REQUIRED_TECHNICAL_COMPONENTS = (
    "market_structure",
    "liquidity",
    "order_blocks",
    "fvg",
    "breaker_blocks",
    "premium_discount",
    "supply_demand",
    "volume_profile",
)

# Components carrying the strongest directional information.
PRIMARY_DIRECTIONAL_COMPONENTS = (
    "market_structure",
    "liquidity",
    "order_blocks",
    "fvg",
    "breaker_blocks",
    "supply_demand",
)

# Components that primarily provide contextual confirmation.
CONTEXT_COMPONENTS = (
    "premium_discount",
    "volume_profile",
)


# =====================================================================
# GENERAL HELPERS
# =====================================================================

def _finite(value: Any) -> bool:
    """Return True when value is a finite numeric value."""

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    if _finite(value):
        return float(value)

    return float(default)


def _clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:
    """Clamp a numeric value."""

    return max(low, min(high, float(value)))


def _text(value: Any) -> str:
    """Normalize arbitrary text."""

    if value is None:
        return ""

    return str(value).strip().upper()


def _as_list(value: Any) -> List[Any]:
    """Safely convert supported values to a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, Iterable) and not isinstance(
        value,
        (str, bytes, dict),
    ):
        try:
            return list(value)
        except TypeError:
            return []

    return []


def _get(
    mapping: Any,
    key: str,
    default: Any = None,
) -> Any:
    """Safe dictionary/object lookup."""

    if isinstance(mapping, dict):
        return mapping.get(key, default)

    return getattr(mapping, key, default)


# =====================================================================
# MODE VALIDATION
# =====================================================================

def normalize_mode(mode: Any) -> str:
    """
    Normalize and validate application mode.

    Only TECHNICAL and HYBRID are supported.
    """

    normalized = _text(mode).lower()

    if normalized not in SUPPORTED_MODES:
        raise ValueError(
            f"unsupported decision mode: {mode!r}. "
            f"Supported modes: {SUPPORTED_MODES}"
        )

    return normalized


# =====================================================================
# TECHNICAL INPUT EXTRACTION
# =====================================================================

def _extract_analysis(
    technical_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract the standardized analysis dictionary produced by
    TechnicalEngine.
    """

    if not isinstance(technical_result, dict):
        raise TypeError(
            "technical_result must be a dictionary"
        )

    analysis = technical_result.get("analysis")

    if not isinstance(analysis, dict):
        raise ValueError(
            "technical_result is missing analysis"
        )

    return analysis


def _validate_technical_result(
    technical_result: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Validate the structural completeness of a TechnicalEngine result.
    """

    reasons: List[str] = []

    if not isinstance(technical_result, dict):
        return False, ["technical result is not a dictionary"]

    if technical_result.get("status") not in (
        None,
        "READY",
    ):
        reasons.append(
            f"technical analysis status is "
            f"{technical_result.get('status')}"
        )

    analysis = technical_result.get("analysis")

    if not isinstance(analysis, dict):
        reasons.append("technical analysis map is missing")
        return False, reasons

    for component in REQUIRED_TECHNICAL_COMPONENTS:

        if component not in analysis:
            reasons.append(
                f"missing technical component: {component}"
            )
            continue

        if analysis.get(component) is None:
            reasons.append(
                f"technical component unavailable: {component}"
            )

    return len(reasons) == 0, reasons


# =====================================================================
# DIRECTION EXTRACTION
# =====================================================================

def _normalize_direction(value: Any) -> Optional[str]:
    """
    Normalize a directional value.

    Accepted examples:

        BUY
        SELL
        BULLISH
        BEARISH
        LONG
        SHORT
    """

    normalized = _text(value)

    if normalized in (
        BUY,
        "BULLISH",
        "LONG",
        "UP",
    ):
        return BUY

    if normalized in (
        SELL,
        "BEARISH",
        "SHORT",
        "DOWN",
    ):
        return SELL

    return None

def _structure_direction(
    structure: Dict[str, Any],
) -> Optional[str]:
    """
    Extract directional bias from MarketStructure.

    Explicit bias has highest priority.

    A confirmed latest structural event is used as a fallback.

    No direction is manufactured from raw swing geometry alone.
    """

    if not isinstance(structure, dict):
        return None

    for key in (
        "bias",
        "direction",
        "signal",
        "initial_bias",
    ):
        direction = _normalize_direction(
            structure.get(key)
        )

        if direction is not None:
            return direction

    latest_event = structure.get(
        "last_event"
    )

    direction = _event_direction(
        latest_event
    )

    if direction is not None:
        return direction

    return None


def _event_direction(
    event: Any,
) -> Optional[str]:
    """
    Extract direction from BOS / CHOCH event representations.

    Supports dictionaries and common textual representations.
    """

    if isinstance(event, dict):

        for key in (
            "direction",
            "bias",
            "type",
            "side",
            "signal",
        ):

            direction = _normalize_direction(
                event.get(key)
            )

            if direction is not None:
                return direction

    return _normalize_direction(event)


def _extract_event_directions(
    component: Dict[str, Any],
    *keys: str,
) -> List[str]:
    """
    Extract BUY/SELL directions from event collections.
    """

    directions: List[str] = []

    for key in keys:

        value = component.get(key)

        for item in _as_list(value):

            direction = _event_direction(item)

            if direction is not None:
                directions.append(direction)

    return directions


# =====================================================================
# LIQUIDITY EVIDENCE
# =====================================================================

def _sweep_direction(
    sweep: Any,
) -> Optional[str]:
    """
    Interpret a liquidity sweep.

    A sell-side liquidity sweep generally provides bullish evidence.

    A buy-side liquidity sweep generally provides bearish evidence.

    Explicit direction fields, when present, take priority.
    """

    if isinstance(sweep, dict):

        for key in (
            "direction",
            "bias",
            "signal",
            "side",
        ):

            direction = _normalize_direction(
                sweep.get(key)
            )

            if direction is not None:
                return direction

        liquidity_side = _text(
            sweep.get("liquidity_side")
            or sweep.get("swept_side")
            or sweep.get("side")
        )

        if "SELL" in liquidity_side:
            return BUY

        if "BUY" in liquidity_side:
            return SELL

    text = _text(sweep)

    if "SELL" in text:
        return BUY

    if "BUY" in text:
        return SELL

    return None

def _liquidity_direction(
    liquidity: Dict[str, Any],
) -> Optional[str]:
    """
    Determine directional liquidity evidence.

    Priority:
        1. Explicit standardized direction.
        2. Most recent sweep.
        3. Historical sweeps.

    A liquidity pool by itself is NOT treated as directional evidence.
    A confirmed sweep is required for directional liquidity evidence.
    """

    if not isinstance(liquidity, dict):
        return None

    # ---------------------------------------------------------------
    # Explicit standardized direction
    # ---------------------------------------------------------------

    direction = _normalize_direction(
        liquidity.get("direction")
        or liquidity.get("bias")
    )

    if direction is not None:
        return direction

    # ---------------------------------------------------------------
    # Most recent sweep
    # ---------------------------------------------------------------

    last_sweep = liquidity.get("last_sweep")

    direction = _sweep_direction(last_sweep)

    if direction is not None:
        return direction

    # ---------------------------------------------------------------
    # Historical sweeps
    # ---------------------------------------------------------------

    directions: List[str] = []

    for sweep in _as_list(
        liquidity.get("sweeps")
    ):

        direction = _sweep_direction(sweep)

        if direction is not None:
            directions.append(direction)

    if directions:
        return directions[-1]

    return None

# =====================================================================
# ORDER BLOCK / FVG / BREAKER EVIDENCE
# =====================================================================

def _component_direction(
    component: Dict[str, Any],
    bullish_keys: Tuple[str, ...],
    bearish_keys: Tuple[str, ...],
) -> Optional[str]:
    """
    Determine component direction from explicit directional
    collections.

    The most direct evidence is preferred.
    """

    for key in bullish_keys:

        values = _as_list(component.get(key))

        if values:
            return BUY

    for key in bearish_keys:

        values = _as_list(component.get(key))

        if values:
            return SELL

    last_keys = (
        "last_order_block",
        "last_fvg",
        "last_breaker",
        "nearest",
        "last_zone",
    )

    for key in last_keys:

        item = component.get(key)

        if isinstance(item, dict):

            direction = _normalize_direction(
                item.get("direction")
                or item.get("bias")
                or item.get("side")
            )

            if direction is not None:
                return direction

    return None

def _order_block_direction(
    order_blocks: Dict[str, Any],
) -> Optional[str]:
    """
    Extract Order Block directional evidence.

    Priority:
        1. Explicit standardized direction.
        2. Fresh/valid bullish or bearish blocks.

    A directional field is accepted because TechnicalEngine can
    standardize the component before it reaches the Decision Engine.
    """

    if not isinstance(order_blocks, dict):
        return None

    direction = _normalize_direction(
        order_blocks.get("direction")
        or order_blocks.get("bias")
    )

    if direction is not None:
        return direction

    return _component_direction(
        order_blocks,
        (
            "fresh_bullish_order_blocks",
            "bullish_order_blocks",
            "valid_bullish_order_blocks",
        ),
        (
            "fresh_bearish_order_blocks",
            "bearish_order_blocks",
            "valid_bearish_order_blocks",
        ),
    )

def _fvg_direction(
    fvg: Dict[str, Any],
) -> Optional[str]:
    """
    Extract Fair Value Gap directional evidence.

    Priority:
        1. Explicit standardized direction.
        2. Fresh/valid bullish or bearish FVGs.
    """

    if not isinstance(fvg, dict):
        return None

    direction = _normalize_direction(
        fvg.get("direction")
        or fvg.get("bias")
    )

    if direction is not None:
        return direction

    return _component_direction(
        fvg,
        (
            "fresh_bullish_fvgs",
            "bullish_fvgs",
            "valid_bullish_fvgs",
        ),
        (
            "fresh_bearish_fvgs",
            "bearish_fvgs",
            "valid_bearish_fvgs",
        ),
    )


def _breaker_direction(
    breaker: Dict[str, Any],
) -> Optional[str]:
    """Extract Breaker Block directional evidence."""

    return _component_direction(
        breaker,
        (
            "fresh_bullish_breaker_blocks",
            "bullish_breaker_blocks",
            "valid_bullish_breaker_blocks",
        ),
        (
            "fresh_bearish_breaker_blocks",
            "bearish_breaker_blocks",
            "valid_bearish_breaker_blocks",
        ),
    )


# =====================================================================
# SUPPLY / DEMAND EVIDENCE
# =====================================================================
def _supply_demand_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Determine direction from Supply / Demand quality.

    Priority:
        1. Explicit standardized direction.
        2. Nearest zone.
        3. Exclusive demand/supply zones.

    Demand -> BUY
    Supply -> SELL

    Ambiguous supply + demand remains neutral.
    """

    if not isinstance(component, dict):
        return None

    # ---------------------------------------------------------------
    # Explicit standardized direction
    # ---------------------------------------------------------------

    direction = _normalize_direction(
        component.get("direction")
        or component.get("bias")
    )

    if direction is not None:
        return direction

    # ---------------------------------------------------------------
    # Nearest zone
    # ---------------------------------------------------------------

    nearest = component.get("nearest")

    if isinstance(nearest, dict):

        zone_type = _text(
            nearest.get("type")
            or nearest.get("zone_type")
            or nearest.get("side")
        )

        if "DEMAND" in zone_type:
            return BUY

        if "SUPPLY" in zone_type:
            return SELL

        direction = _normalize_direction(
            nearest.get("direction")
            or nearest.get("bias")
        )

        if direction is not None:
            return direction

    # ---------------------------------------------------------------
    # Zone collections
    # ---------------------------------------------------------------

    demand = _as_list(
        component.get("demand_zones")
    )

    supply = _as_list(
        component.get("supply_zones")
    )

    if demand and not supply:
        return BUY

    if supply and not demand:
        return SELL

    return None

# =====================================================================
# PREMIUM / DISCOUNT EVIDENCE
# =====================================================================
def _premium_discount_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Premium/Discount is contextual rather than a standalone trigger.

    Discount -> BUY
    Premium  -> SELL
    Equilibrium -> neutral

    Explicit standardized direction is accepted when supplied.
    """

    if not isinstance(component, dict):
        return None

    # ---------------------------------------------------------------
    # Explicit standardized direction
    # ---------------------------------------------------------------

    direction = _normalize_direction(
        component.get("direction")
        or component.get("bias")
    )

    if direction is not None:
        return direction

    # ---------------------------------------------------------------
    # Position / zone
    # ---------------------------------------------------------------

    position = _text(
        component.get("position")
        or component.get("zone")
    )

    if position == "DISCOUNT":
        return BUY

    if position == "PREMIUM":
        return SELL

    return None

# =====================================================================
# VOLUME PROFILE EVIDENCE
# =====================================================================

def _volume_profile_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract directional context from Volume Profile.

    This intentionally remains conservative.

    Volume Profile is supporting evidence, not a standalone signal.
    """

    location = _text(
        component.get("price_location")
    )

    acceptance = _text(
        component.get("acceptance")
    )

    quality = _text(
        component.get("quality")
    )

    # Explicit directional information, if supplied by the module.
    for value in (
        component.get("direction"),
        component.get("bias"),
        component.get("signal"),
    ):

        direction = _normalize_direction(value)

        if direction is not None:
            return direction

    # Do not manufacture a BUY/SELL direction from generic
    # HIGH/LOW/NORMAL volume terminology.
    #
    # This function therefore returns None unless the component
    # explicitly supplies direction.
    _ = location
    _ = acceptance
    _ = quality

    return None


# =====================================================================
# COMPONENT EVIDENCE
# =====================================================================
def extract_component_evidence(
    analysis: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Extract standardized directional evidence from all technical
    components.

    This function does NOT generate a trading signal.

    It only translates evidence already produced by the TechnicalEngine
    into a common format consumed by the Decision Engine.

    Component authority / strength:

        market_structure : 1.00
        bos_choch        : 0.90
        liquidity        : 0.90
        order_blocks     : 0.80
        fvg              : 0.70
        breaker_blocks   : 0.70
        premium_discount : 0.45
        supply_demand    : 0.80
        volume_profile   : 0.40

    Missing or neutral evidence remains direction=None.
    """

    if not isinstance(analysis, dict):
        analysis = {}

    structure = analysis.get("market_structure")
    liquidity = analysis.get("liquidity")
    order_blocks = analysis.get("order_blocks")
    fvg = analysis.get("fvg")
    breakers = analysis.get("breaker_blocks")
    premium_discount = analysis.get("premium_discount")
    supply_demand = analysis.get("supply_demand")
    volume_profile = analysis.get("volume_profile")

    if not isinstance(structure, dict):
        structure = {}

    if not isinstance(liquidity, dict):
        liquidity = {}

    if not isinstance(order_blocks, dict):
        order_blocks = {}

    if not isinstance(fvg, dict):
        fvg = {}

    if not isinstance(breakers, dict):
        breakers = {}

    if not isinstance(premium_discount, dict):
        premium_discount = {}

    if not isinstance(supply_demand, dict):
        supply_demand = {}

    if not isinstance(volume_profile, dict):
        volume_profile = {}

    # ---------------------------------------------------------------
    # BOS / CHoCH
    # ---------------------------------------------------------------

    bos_events = _as_list(
        structure.get("bos")
    )

    choch_events = _as_list(
        structure.get("choch")
    )

    structural_events = [
        *bos_events,
        *choch_events,
    ]

    latest_event = structure.get(
        "last_event"
    )

    if latest_event is None and structural_events:
        latest_event = structural_events[-1]

    bos_choch_direction = _event_direction(
        latest_event
    )

    # ---------------------------------------------------------------
    # STANDARDIZED EVIDENCE
    # ---------------------------------------------------------------

    evidence = {
        "market_structure": {
            "direction": _structure_direction(
                structure
            ),
            "strength": 1.00,
        },

        "bos_choch": {
            "direction": bos_choch_direction,
            "strength": 0.90,
        },

        "liquidity": {
            "direction": _liquidity_direction(
                liquidity
            ),
            "strength": 0.90,
        },

        "order_blocks": {
            "direction": _order_block_direction(
                order_blocks
            ),
            "strength": 0.80,
        },

        "fvg": {
            "direction": _fvg_direction(
                fvg
            ),
            "strength": 0.70,
        },

        "breaker_blocks": {
            "direction": _breaker_direction(
                breakers
            ),
            "strength": 0.70,
        },

        "premium_discount": {
            "direction": _premium_discount_direction(
                premium_discount
            ),
            "strength": 0.45,
        },

        "supply_demand": {
            "direction": _supply_demand_direction(
                supply_demand
            ),
            "strength": 0.80,
        },

        "volume_profile": {
            "direction": _volume_profile_direction(
                volume_profile
            ),
            "strength": 0.40,
        },
    }

    return evidence
# =====================================================================
# TIMEFRAME SCORING
# =====================================================================

def _score_timeframe(
    timeframe: str,
    technical_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Score directional technical evidence for one timeframe.

    IMPORTANT
    ---------
    This function does NOT generate a trading signal.

    It only aggregates directional evidence already produced by the
    TechnicalEngine components.

    Confidence measures directional evidence coverage against the
    total possible technical evidence.

    Alignment measures dominant directional evidence relative to
    opposing directional evidence.

    This prevents a single component from producing artificial
    100% confidence when the remaining technical components are neutral
    or unavailable.
    """

    analysis = _extract_analysis(
        technical_result
    )

    evidence = extract_component_evidence(
        analysis
    )

    buy_score = 0.0
    sell_score = 0.0
    total_possible_strength = 0.0
    available_directional_strength = 0.0

    component_directions: Dict[
        str,
        Optional[str],
    ] = {}

    component_scores: Dict[
        str,
        Dict[str, Any],
    ] = {}

    # ---------------------------------------------------------------
    # Aggregate all nine technical evidence components.
    # ---------------------------------------------------------------

    for component, record in evidence.items():

        if not isinstance(record, dict):
            continue

        direction = record.get(
            "direction"
        )

        strength = _float(
            record.get(
                "strength"
            ),
            0.0,
        )

        strength = max(
            0.0,
            strength,
        )

        component_directions[
            component
        ] = direction

        # Every defined component contributes to the maximum
        # possible evidence capacity, even when it is neutral.
        total_possible_strength += strength

        bullish_points = 0.0
        bearish_points = 0.0

        if direction == BUY:

            bullish_points = strength
            buy_score += strength
            available_directional_strength += strength

        elif direction == SELL:

            bearish_points = strength
            sell_score += strength
            available_directional_strength += strength

        component_scores[
            component
        ] = {
            "direction": direction,
            "strength": round(
                strength,
                4,
            ),
            "bullish_points": round(
                bullish_points,
                4,
            ),
            "bearish_points": round(
                bearish_points,
                4,
            ),
        }

    # ---------------------------------------------------------------
    # Determine dominant direction.
    # ---------------------------------------------------------------

    if buy_score > sell_score:

        direction = BUY

        dominant_score = buy_score
        opposing_score = sell_score

    elif sell_score > buy_score:

        direction = SELL

        dominant_score = sell_score
        opposing_score = buy_score

    else:

        direction = None

        dominant_score = 0.0
        opposing_score = 0.0

    # ---------------------------------------------------------------
    # Directional confidence.
    #
    # This is intentionally measured against ALL possible technical
    # evidence, not merely the evidence that happened to be directional.
    # ---------------------------------------------------------------

    if (
        direction is None
        or total_possible_strength <= 0.0
    ):

        directional_confidence = 0.0

    else:

        directional_confidence = (
            dominant_score
            / total_possible_strength
        ) * 100.0

    # ---------------------------------------------------------------
    # Directional coverage.
    #
    # Percentage of all available directional evidence that supports
    # the dominant direction.
    # ---------------------------------------------------------------

    if (
        direction is None
        or available_directional_strength <= 0.0
    ):

        directional_dominance = 0.0

    else:

        directional_dominance = (
            dominant_score
            / available_directional_strength
        ) * 100.0

    # ---------------------------------------------------------------
    # Alignment.
    #
    # 1.0 means all directional evidence agrees.
    #
    # 0.5 means equal BUY and SELL directional evidence.
    # ---------------------------------------------------------------

    directional_total = (
        dominant_score
        + opposing_score
    )

    if directional_total > 0.0:

        alignment = (
            dominant_score
            / directional_total
        )

    else:

        alignment = 0.0

    # ---------------------------------------------------------------
    # Market structure is the highest-authority directional component.
    #
    # A conflict reduces confidence, but structure does not blindly
    # override the aggregate evidence.
    # ---------------------------------------------------------------

    structure_direction = component_directions.get(
        "market_structure"
    )

    structure_conflict = (
        structure_direction is not None
        and direction is not None
        and structure_direction != direction
    )

    if structure_conflict:

        directional_confidence *= 0.70

    # ---------------------------------------------------------------
    # Component completeness.
    # ---------------------------------------------------------------

    component_count = len(
        evidence
    )

    available_component_count = sum(
        1
        for record in evidence.values()
        if isinstance(record, dict)
        and record.get("direction") is not None
    )

    if component_count > 0:

        directional_component_coverage = (
            available_component_count
            / component_count
        ) * 100.0

    else:

        directional_component_coverage = 0.0

    # ---------------------------------------------------------------
    # Result.
    # ---------------------------------------------------------------

    return {
        "status": "READY",

        "timeframe": timeframe,

        "direction": direction,

        "buy_score": round(
            buy_score,
            4,
        ),

        "sell_score": round(
            sell_score,
            4,
        ),

        "total_possible_strength": round(
            total_possible_strength,
            4,
        ),

        "available_directional_strength": round(
            available_directional_strength,
            4,
        ),

        "dominant_score": round(
            dominant_score,
            4,
        ),

        "opposing_score": round(
            opposing_score,
            4,
        ),

        "directional_confidence": round(
            _clamp(
                directional_confidence
            ),
            4,
        ),

        "directional_dominance": round(
            _clamp(
                directional_dominance
            ),
            4,
        ),

        "alignment": round(
            _clamp(
                alignment,
                0.0,
                1.0,
            ),
            6,
        ),

        "directional_component_coverage": round(
            _clamp(
                directional_component_coverage
            ),
            4,
        ),

        "structure_direction":
            structure_direction,

        "structure_conflict":
            structure_conflict,

        "component_directions":
            component_directions,

        "component_scores":
            component_scores,

        "evidence":
            evidence,
    }

# =====================================================================
# TOP-DOWN AGGREGATION
# =====================================================================
def _aggregate_top_down(
    timeframe_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate H4 -> H1 -> M15 directional evidence.

    Timeframe authority:

        H4  = 45%
        H1  = 35%
        M15 = 20%

    H4 has the highest directional authority.
    H1 confirms the higher-timeframe structure.
    M15 provides entry-direction confirmation.

    The aggregation uses fixed timeframe weights.

    IMPORTANT
    ---------
    Missing or neutral directional evidence is NOT renormalized away.
    This prevents incomplete evidence from artificially becoming a
    high-confidence decision.
    """

    weighted_buy = 0.0
    weighted_sell = 0.0

    total_weight = 0.0

    directions: Dict[
        str,
        Optional[str],
    ] = {}

    timeframe_confidence: Dict[
        str,
        float,
    ] = {}

    timeframe_alignment: Dict[
        str,
        float,
    ] = {}

    # ---------------------------------------------------------------
    # Process every required timeframe.
    # ---------------------------------------------------------------

    for timeframe in TOP_DOWN_TIMEFRAMES:

        result = timeframe_results.get(
            timeframe
        )

        weight = _float(
            TIMEFRAME_WEIGHTS.get(
                timeframe,
                0.0,
            ),
            0.0,
        )

        if weight <= 0.0:
            continue

        total_weight += weight

        if not isinstance(result, dict):

            directions[
                timeframe
            ] = None

            timeframe_confidence[
                timeframe
            ] = 0.0

            timeframe_alignment[
                timeframe
            ] = 0.0

            continue

        direction = result.get(
            "direction"
        )

        confidence = _float(
            result.get(
                "directional_confidence"
            ),
            0.0,
        )

        confidence = _clamp(
            confidence
        )

        directions[
            timeframe
        ] = direction

        timeframe_confidence[
            timeframe
        ] = round(
            confidence,
            4,
        )

        timeframe_alignment[
            timeframe
        ] = _clamp(
            _float(
                result.get(
                    "alignment"
                ),
                0.0,
            ),
            0.0,
            1.0,
        )

        # Convert confidence back into directional contribution.
        normalized_strength = (
            confidence / 100.0
        )

        if direction == BUY:

            weighted_buy += (
                weight
                * normalized_strength
            )

        elif direction == SELL:

            weighted_sell += (
                weight
                * normalized_strength
            )

    # ---------------------------------------------------------------
    # No valid timeframe weighting.
    # ---------------------------------------------------------------

    if total_weight <= 0.0:

        return {
            "direction": None,
            "confidence": 0.0,
            "weighted_buy": 0.0,
            "weighted_sell": 0.0,
            "alignment": 0.0,
            "directions": directions,
            "available_weight": 0.0,
            "timeframe_confidence":
                timeframe_confidence,
            "timeframe_alignment":
                timeframe_alignment,
        }

    # ---------------------------------------------------------------
    # Normalize against the FIXED total timeframe weight.
    #
    # Do not divide by only the directional/available weight.
    # ---------------------------------------------------------------

    buy_normalized = (
        weighted_buy
        / total_weight
    )

    sell_normalized = (
        weighted_sell
        / total_weight
    )

    # ---------------------------------------------------------------
    # Determine dominant top-down direction.
    # ---------------------------------------------------------------

    if buy_normalized > sell_normalized:

        direction = BUY

        dominant = buy_normalized
        opposing = sell_normalized

    elif sell_normalized > buy_normalized:

        direction = SELL

        dominant = sell_normalized
        opposing = buy_normalized

    else:

        direction = None

        dominant = 0.0
        opposing = 0.0

    # ---------------------------------------------------------------
    # Final top-down confidence.
    # ---------------------------------------------------------------

    confidence = _clamp(
        dominant * 100.0
    )

    # ---------------------------------------------------------------
    # Top-down directional alignment.
    #
    # This intentionally ignores neutral evidence when measuring
    # agreement between BUY and SELL evidence.
    # ---------------------------------------------------------------

    directional_total = (
        dominant
        + opposing
    )

    if directional_total > 0.0:

        alignment = (
            dominant
            / directional_total
        )

    else:

        alignment = 0.0

    # ---------------------------------------------------------------
    # Directional coverage.
    #
    # Measures how much weighted timeframe evidence actually supports
    # the dominant direction.
    # ---------------------------------------------------------------

    directional_coverage = (
        dominant * 100.0
    )

    # ---------------------------------------------------------------
    # Result.
    # ---------------------------------------------------------------

    return {
        "direction":
            direction,

        "confidence":
            round(
                confidence,
                4,
            ),

        "weighted_buy":
            round(
                buy_normalized,
                6,
            ),

        "weighted_sell":
            round(
                sell_normalized,
                6,
            ),

        "alignment":
            round(
                _clamp(
                    alignment,
                    0.0,
                    1.0,
                ),
                6,
            ),

        "directional_coverage":
            round(
                _clamp(
                    directional_coverage
                ),
                4,
            ),

        "directions":
            directions,

        "available_weight":
            round(
                total_weight,
                6,
            ),

        "timeframe_confidence":
            timeframe_confidence,

        "timeframe_alignment":
            timeframe_alignment,
    }

# =====================================================================
# TOP-DOWN CONFIRMATION
# =====================================================================

def _top_down_confirmation(
    timeframe_results: Dict[str, Dict[str, Any]],
    direction: Optional[str],
) -> Dict[str, Any]:
    """
    Evaluate the H4/H1/M15 relationship.

    H4:
        Primary directional bias.

    H1:
        Confirmation.

    M15:
        Entry confirmation.

    A missing M15 trigger does not necessarily destroy the broader
    directional analysis, but it prevents the result from becoming
    trade-eligible.
    """

    if direction is None:
        return {
            "confirmed": False,
            "h4_aligned": False,
            "h1_aligned": False,
            "m15_aligned": False,
            "entry_confirmed": False,
        }

    h4 = timeframe_results.get(
        "H4",
        {},
    )

    h1 = timeframe_results.get(
        "H1",
        {},
    )

    m15 = timeframe_results.get(
        "M15",
        {},
    )

    h4_direction = h4.get(
        "direction"
    )

    h1_direction = h1.get(
        "direction"
    )

    m15_direction = m15.get(
        "direction"
    )

    h4_aligned = (
        h4_direction == direction
    )

    h1_aligned = (
        h1_direction == direction
    )

    m15_aligned = (
        m15_direction == direction
    )

    return {
        "confirmed": (
            h4_aligned
            and h1_aligned
        ),

        "h4_aligned": h4_aligned,

        "h1_aligned": h1_aligned,

        "m15_aligned": m15_aligned,

        "entry_confirmed": (
            h4_aligned
            and h1_aligned
            and m15_aligned
        ),
    }


# =====================================================================
# CONFLUENCE COMPLETENESS
# =====================================================================

def _confluence_status(
    analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Read the existing TechnicalConfluence aggregator result.

    The component count is used as a completeness check only.

    It is NOT treated as a trading score.
    """

    confluence = analysis.get(
        "technical_confluence"
    )

    if not isinstance(confluence, dict):
        return {
            "available": False,
            "component_count": 0,
            "available_component_count": 0,
            "completeness": 0.0,
        }

    total = int(
        _float(
            confluence.get(
                "component_count"
            ),
            0.0,
        )
    )

    available = int(
        _float(
            confluence.get(
                "available_component_count"
            ),
            0.0,
        )
    )

    if total <= 0:
        completeness = 0.0

    else:
        completeness = (
            available / total
        )

    return {
        "available": True,
        "component_count": total,
        "available_component_count": available,
        "completeness": round(
            _clamp(
                completeness * 100.0
            ),
            4,
        ),
    }


# =====================================================================
# TECHNICAL DECISION
# =====================================================================

def technical_decision(
    technical_data: Dict[str, Dict[str, Any]],
    symbol: Optional[str] = None,
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    alignment_threshold: float = DEFAULT_ALIGNMENT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Make the authoritative TECHNICAL MODE decision.

    Parameters
    ----------
    technical_data:
        Mapping containing H4, H1 and M15 TechnicalEngine results.

        Example:

            {
                "H4": {...},
                "H1": {...},
                "M15": {...},
            }

    symbol:
        Optional market symbol.

    decision_threshold:
        Minimum confidence required for a directional decision.

    alignment_threshold:
        Minimum weighted directional alignment.

    Returns
    -------
    dict
        Standardized technical decision.

    Important
    ---------
    This function does not execute anything.
    """

    if not isinstance(technical_data, dict):
        raise TypeError(
            "technical_data must be a dictionary"
        )

    threshold = _clamp(
        decision_threshold,
        0.0,
        100.0,
    )

    alignment_minimum = max(
        0.0,
        min(
            1.0,
            float(alignment_threshold),
        ),
    )

    timeframe_results: Dict[str, Dict[str, Any]] = {}

    validation_errors: Dict[str, List[str]] = {}

    # ---------------------------------------------------------------
    # Analyze each timeframe independently.
    # ---------------------------------------------------------------

    for timeframe in TOP_DOWN_TIMEFRAMES:

        result = technical_data.get(
            timeframe
        )

        if result is None:

            validation_errors[timeframe] = [
                "technical timeframe result is missing"
            ]

            continue

        valid, errors = _validate_technical_result(
            result
        )

        if not valid:
            validation_errors[timeframe] = errors
            continue

        timeframe_results[timeframe] = _score_timeframe(
            timeframe,
            result,
        )

    # ---------------------------------------------------------------
    # Require all three top-down timeframes.
    # ---------------------------------------------------------------

    missing = [
        timeframe
        for timeframe in TOP_DOWN_TIMEFRAMES
        if timeframe not in timeframe_results
    ]

    if missing:

        return {
            "status": "NO_TRADE",
            "mode": TECHNICAL,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": 0.0,
            "trade_allowed": False,
            "reason": (
                "Incomplete top-down technical analysis"
            ),
            "reasons": [
                f"missing or invalid timeframe: {tf}"
                for tf in missing
            ],
            "validation_errors": validation_errors,
            "timeframes": timeframe_results,
            "top_down": {},
            "confluence": {},
            "decision_authority": "decision_engine",
        }

    # ---------------------------------------------------------------
    # Aggregate H4/H1/M15.
    # ---------------------------------------------------------------

    top_down = _aggregate_top_down(
        timeframe_results
    )

    direction = top_down.get(
        "direction"
    )

    confirmation = _top_down_confirmation(
        timeframe_results,
        direction,
    )

    # ---------------------------------------------------------------
    # Confluence completeness.
    #
    # Use the H4 confluence as the primary completeness reference.
    # We also expose all timeframe values.
    # ---------------------------------------------------------------

    confluence = {}

    for timeframe in TOP_DOWN_TIMEFRAMES:

        result = technical_data[timeframe]

        analysis = _extract_analysis(
            result
        )

        confluence[timeframe] = _confluence_status(
            analysis
        )

    # ---------------------------------------------------------------
    # Decision reasons.
    # ---------------------------------------------------------------

    reasons: List[str] = []

    if direction is None:

        reasons.append(
            "technical evidence is directionally balanced"
        )

    else:

        reasons.append(
            f"top-down technical direction: {direction}"
        )

    if confirmation.get(
        "h4_aligned"
    ):
        reasons.append(
            f"H4 confirms {direction}"
        )

    else:
        reasons.append(
            "H4 does not confirm the dominant direction"
        )

    if confirmation.get(
        "h1_aligned"
    ):
        reasons.append(
            f"H1 confirms {direction}"
        )

    else:
        reasons.append(
            "H1 does not confirm the dominant direction"
        )

    if confirmation.get(
        "m15_aligned"
    ):
        reasons.append(
            f"M15 confirms {direction} entry direction"
        )

    else:
        reasons.append(
            "M15 does not confirm the entry direction"
        )

    confidence = _float(
        top_down.get(
            "confidence"
        ),
        0.0,
    )

    alignment = _float(
        top_down.get(
            "alignment"
        ),
        0.0,
    )

    # ---------------------------------------------------------------
    # Hard decision gates.
    # ---------------------------------------------------------------

    trade_allowed = True
    final_decision = direction

    if direction is None:

        final_decision = NO_TRADE
        trade_allowed = False

    elif confidence < threshold:

        final_decision = NO_TRADE
        trade_allowed = False

        reasons.append(
            f"confidence below threshold "
            f"({confidence:.2f} < {threshold:.2f})"
        )

    elif alignment < alignment_minimum:

        final_decision = NO_TRADE
        trade_allowed = False

        reasons.append(
            f"top-down alignment below threshold "
            f"({alignment:.2f} < "
            f"{alignment_minimum:.2f})"
        )

    elif not confirmation.get(
        "h4_aligned"
    ):

        final_decision = NO_TRADE
        trade_allowed = False

        reasons.append(
            "H4 primary directional confirmation failed"
        )

    elif not confirmation.get(
        "h1_aligned"
    ):

        final_decision = NO_TRADE
        trade_allowed = False

        reasons.append(
            "H1 directional confirmation failed"
        )

    elif not confirmation.get(
        "m15_aligned"
    ):

        final_decision = NO_TRADE
        trade_allowed = False

        reasons.append(
            "M15 entry confirmation failed"
        )

    else:

        reasons.append(
            "technical decision passed top-down confirmation"
        )

    # ---------------------------------------------------------------
    # Final standardized result.
    # ---------------------------------------------------------------

    return {
        "status": (
            "READY"
            if final_decision != NO_TRADE
            else "NO_TRADE"
        ),

        "mode": TECHNICAL,

        "symbol": symbol,

        "decision": final_decision,

        "direction": (
            final_decision
            if final_decision in (
                BUY,
                SELL,
            )
            else None
        ),

        "confidence": round(
            confidence,
            4,
        ),

        "alignment": round(
            alignment,
            6,
        ),

        "trade_allowed": trade_allowed,

        "reason": (
            reasons[-1]
            if reasons
            else "technical decision completed"
        ),

        "reasons": reasons,

        "timeframes": timeframe_results,

        "top_down": {
            **top_down,
            "confirmation": confirmation,
        },

        "confluence": confluence,

        "validation_errors": validation_errors,

        "decision_authority": "decision_engine",

        "execution_authority": (
            "downstream_execution_pipeline"
        ),
    }


# =====================================================================
# HYBRID DECISION
# =====================================================================

def hybrid_decision(
    technical_data: Dict[str, Dict[str, Any]],
    fundamental_data: Optional[Dict[str, Any]] = None,
    symbol: Optional[str] = None,
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    alignment_threshold: float = DEFAULT_ALIGNMENT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Make the HYBRID MODE decision.

    Technical analysis remains the primary market-direction source.

    Fundamental analysis is supplied by the Fundamental Engine and
    is consumed only in HYBRID mode.

    The exact fundamental contract is intentionally flexible because
    the Fundamental Engine is a separate subsystem.

    If no fundamental result is supplied, Hybrid Mode does NOT
    silently become Technical Mode. It returns NO_TRADE.

    No execution occurs here.
    """

    technical = technical_decision(
        technical_data=technical_data,
        symbol=symbol,
        decision_threshold=decision_threshold,
        alignment_threshold=alignment_threshold,
    )

    if fundamental_data is None:

        return {
            "status": "NO_TRADE",
            "mode": HYBRID,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": 0.0,
            "trade_allowed": False,
            "reason": (
                "Hybrid Mode requires fundamental analysis"
            ),
            "reasons": [
                "technical analysis available",
                "fundamental analysis unavailable",
                "hybrid decision cannot be completed",
            ],
            "technical": technical,
            "fundamental": None,
            "decision_authority": "decision_engine",
            "execution_authority": (
                "downstream_execution_pipeline"
            ),
        }

    # ---------------------------------------------------------------
    # Fundamental interpretation.
    #
    # We deliberately support several common standardized fields
    # without coupling the Decision Engine to a particular
    # Fundamental Engine implementation.
    # ---------------------------------------------------------------

    fundamental_direction = _normalize_direction(
        fundamental_data.get("direction")
        if isinstance(fundamental_data, dict)
        else None
    )

    if fundamental_direction is None and isinstance(
        fundamental_data,
        dict,
    ):

        fundamental_direction = _normalize_direction(
            fundamental_data.get("bias")
        )

    if fundamental_direction is None and isinstance(
        fundamental_data,
        dict,
    ):

        fundamental_direction = _normalize_direction(
            fundamental_data.get("signal")
        )

    fundamental_confidence = 0.0

    if isinstance(
        fundamental_data,
        dict,
    ):

        fundamental_confidence = _clamp(
            _float(
                fundamental_data.get(
                    "confidence",
                    fundamental_data.get(
                        "score",
                        0.0,
                    ),
                ),
                0.0,
            )
        )

    technical_direction = technical.get(
        "direction"
    )

    technical_confidence = _float(
        technical.get(
            "confidence"
        ),
        0.0,
    )

    reasons = list(
        technical.get(
            "reasons",
            [],
        )
    )

    # ---------------------------------------------------------------
    # Fundamental hard-block support.
    #
    # The Fundamental Engine may explicitly prohibit trading.
    # ---------------------------------------------------------------

    fundamental_trade_allowed = True

    if isinstance(
        fundamental_data,
        dict,
    ):

        if fundamental_data.get(
            "trade_allowed"
        ) is False:
            fundamental_trade_allowed = False

        if fundamental_data.get(
            "blocked"
        ) is True:
            fundamental_trade_allowed = False

        if fundamental_data.get(
            "status"
        ) in (
            "BLOCKED",
            "NO_TRADE",
        ):
            fundamental_trade_allowed = False

    if not fundamental_trade_allowed:

        return {
            "status": "NO_TRADE",
            "mode": HYBRID,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": 0.0,
            "trade_allowed": False,
            "reason": (
                "Fundamental analysis blocks the trade"
            ),
            "reasons": reasons + [
                "fundamental trade permission is false"
            ],
            "technical": technical,
            "fundamental": fundamental_data,
            "decision_authority": "decision_engine",
            "execution_authority": (
                "downstream_execution_pipeline"
            ),
        }

    # ---------------------------------------------------------------
    # Direction agreement.
    # ---------------------------------------------------------------

    if (
        technical_direction is None
        or fundamental_direction is None
    ):

        return {
            "status": "NO_TRADE",
            "mode": HYBRID,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": 0.0,
            "trade_allowed": False,
            "reason": (
                "Hybrid direction could not be confirmed"
            ),
            "reasons": reasons + [
                "technical and fundamental direction "
                "must both be available"
            ],
            "technical": technical,
            "fundamental": fundamental_data,
            "decision_authority": "decision_engine",
            "execution_authority": (
                "downstream_execution_pipeline"
            ),
        }

    if technical_direction != fundamental_direction:

        return {
            "status": "NO_TRADE",
            "mode": HYBRID,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": 0.0,
            "trade_allowed": False,
            "reason": (
                "Technical and fundamental directions conflict"
            ),
            "reasons": reasons + [
                (
                    f"technical={technical_direction}, "
                    f"fundamental={fundamental_direction}"
                )
            ],
            "technical": technical,
            "fundamental": fundamental_data,
            "decision_authority": "decision_engine",
            "execution_authority": (
                "downstream_execution_pipeline"
            ),
        }

    # ---------------------------------------------------------------
    # Hybrid confidence.
    #
    # Technical evidence remains dominant.
    # ---------------------------------------------------------------

    hybrid_confidence = (
        technical_confidence * 0.70
        + fundamental_confidence * 0.30
    )

    hybrid_confidence = _clamp(
        hybrid_confidence
    )

    if hybrid_confidence < decision_threshold:

        return {
            "status": "NO_TRADE",
            "mode": HYBRID,
            "symbol": symbol,
            "decision": NO_TRADE,
            "direction": None,
            "confidence": round(
                hybrid_confidence,
                4,
            ),
            "trade_allowed": False,
            "reason": (
                "Hybrid confidence below threshold"
            ),
            "reasons": reasons + [
                (
                    f"hybrid confidence "
                    f"{hybrid_confidence:.2f} "
                    f"< {decision_threshold:.2f}"
                )
            ],
            "technical": technical,
            "fundamental": fundamental_data,
            "decision_authority": "decision_engine",
            "execution_authority": (
                "downstream_execution_pipeline"
            ),
        }

    reasons.append(
        (
            f"technical and fundamental analysis agree "
            f"on {technical_direction}"
        )
    )

    return {
        "status": "READY",
        "mode": HYBRID,
        "symbol": symbol,
        "decision": technical_direction,
        "direction": technical_direction,
        "confidence": round(
            hybrid_confidence,
            4,
        ),
        "trade_allowed": True,
        "reason": (
            "Hybrid technical/fundamental confirmation passed"
        ),
        "reasons": reasons,
        "technical": technical,
        "fundamental": fundamental_data,
        "decision_authority": "decision_engine",
        "execution_authority": (
            "downstream_execution_pipeline"
        ),
    }


# =====================================================================
# GENERAL DECISION DISPATCHER
# =====================================================================

def decide(
    mode: str,
    technical_data: Dict[str, Dict[str, Any]],
    fundamental_data: Optional[Dict[str, Any]] = None,
    symbol: Optional[str] = None,
    decision_threshold: float = DEFAULT_DECISION_THRESHOLD,
    alignment_threshold: float = DEFAULT_ALIGNMENT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Authoritative decision dispatcher.

    TECHNICAL:
        technical data only.

    HYBRID:
        technical + fundamental data.

    The function never executes trades.
    """

    normalized_mode = normalize_mode(
        mode
    )

    if normalized_mode == TECHNICAL:

        return technical_decision(
            technical_data=technical_data,
            symbol=symbol,
            decision_threshold=decision_threshold,
            alignment_threshold=alignment_threshold,
        )

    return hybrid_decision(
        technical_data=technical_data,
        fundamental_data=fundamental_data,
        symbol=symbol,
        decision_threshold=decision_threshold,
        alignment_threshold=alignment_threshold,
    )


# =====================================================================
# CONVENIENCE API
# =====================================================================

def make_technical_decision(
    technical_data: Dict[str, Dict[str, Any]],
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience wrapper for Technical Mode."""

    return technical_decision(
        technical_data=technical_data,
        symbol=symbol,
    )


def make_hybrid_decision(
    technical_data: Dict[str, Dict[str, Any]],
    fundamental_data: Optional[Dict[str, Any]] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience wrapper for Hybrid Mode."""

    return hybrid_decision(
        technical_data=technical_data,
        fundamental_data=fundamental_data,
        symbol=symbol,
    )


# =====================================================================
# MODULE INFORMATION
# =====================================================================

def decision_engine_info() -> Dict[str, Any]:
    """
    Return a machine-readable description of the Decision Engine.
    """

    return {
        "name": "BALLY FLOW Decision Engine",
        "status": "READY",
        "modes": list(SUPPORTED_MODES),
        "timeframes": list(TOP_DOWN_TIMEFRAMES),
        "analysis_order": list(TOP_DOWN_TIMEFRAMES),
        "timeframe_weights": dict(
            TIMEFRAME_WEIGHTS
        ),
        "decision_threshold": (
            DEFAULT_DECISION_THRESHOLD
        ),
        "alignment_threshold": (
            DEFAULT_ALIGNMENT_THRESHOLD
        ),
        "decisions": [
            BUY,
            SELL,
            NO_TRADE,
        ],
        "technical_authority": True,
        "fundamental_analysis": True,
        "execution": False,
        "risk_management": False,
        "order_placement": False,
    }


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "BUY",
    "SELL",
    "NO_TRADE",
    "TECHNICAL",
    "HYBRID",
    "SUPPORTED_MODES",
    "TOP_DOWN_TIMEFRAMES",
    "TIMEFRAME_WEIGHTS",
    "DEFAULT_DECISION_THRESHOLD",
    "DEFAULT_ALIGNMENT_THRESHOLD",
    "normalize_mode",
    "extract_component_evidence",
    "technical_decision",
    "hybrid_decision",
    "decide",
    "make_technical_decision",
    "make_hybrid_decision",
    "decision_engine_info",
]