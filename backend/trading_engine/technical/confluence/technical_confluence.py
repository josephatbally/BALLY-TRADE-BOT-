"""
BALLY TRADE BOT - Technical Confluence
======================================

TECHNICAL-ONLY CONFLUENCE AGGREGATOR

This module aggregates the existing technical-analysis components into
standardized confluence metrics.

IMPORTANT ARCHITECTURE
----------------------

TechnicalConfluence:

    - DOES NOT retrieve market data
    - DOES NOT generate an independent trading signal
    - DOES NOT decide BUY / SELL / NO_TRADE
    - DOES NOT execute orders
    - DOES NOT manage account risk

The authoritative BUY / SELL / NO_TRADE decision remains the
responsibility of the Decision Engine.

TechnicalConfluence only answers:

    "How much bullish and bearish technical evidence exists?"

and:

    "How complete and high-quality is the technical analysis?"

COMPONENTS
----------

    1. Market Structure
    2. BOS / CHoCH
    3. Liquidity
    4. Order Blocks
    5. Fair Value Gaps
    6. Breaker Blocks
    7. Premium / Discount
    8. Supply / Demand
    9. Volume Profile

BOS / CHoCH is derived from the Market Structure result when an
independent BOS/CHoCH component is not supplied.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import math


# =====================================================================
# DIRECTION CONSTANTS
# =====================================================================

BUY = "BUY"
SELL = "SELL"

BULLISH = "BULLISH"
BEARISH = "BEARISH"

READY = "READY"


# =====================================================================
# GENERAL HELPERS
# =====================================================================

def _finite(value: Any) -> bool:
    """Return True when value is a finite number."""

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    if _finite(value):
        return float(value)

    return float(default)


def _clamp(
    value: float,
    low: float = 0.0,
    high: float = 100.0,
) -> float:
    """Clamp a value to a numeric range."""

    return max(
        low,
        min(
            high,
            float(value),
        ),
    )


def _text(value: Any) -> str:
    """Normalize arbitrary text."""

    if value is None:
        return ""

    return str(value).strip().upper()


def _safe_dict(value: Any) -> Dict[str, Any]:
    """Return a dictionary or an empty dictionary."""

    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    """Return a list for supported collection values."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    return []


# =====================================================================
# DIRECTION NORMALIZATION
# =====================================================================

def _normalize_direction(
    value: Any,
) -> Optional[str]:
    """
    Normalize common technical directional labels.

    Returns:

        BUY
        SELL
        None
    """

    text = _text(value)

    if text in {
        "BUY",
        "BULL",
        "BULLISH",
        "LONG",
        "UP",
        "UPTREND",
    }:
        return BUY

    if text in {
        "SELL",
        "BEAR",
        "BEARISH",
        "SHORT",
        "DOWN",
        "DOWNTREND",
    }:
        return SELL

    return None


def _count_directional_items(
    value: Any,
) -> int:
    """
    Count directional technical objects.

    Supports lists, tuples, sets, dictionaries and numeric counts.
    """

    if value is None:
        return 0

    if isinstance(value, bool):
        return int(value)

    if _finite(value):
        return max(
            0,
            int(_float(value)),
        )

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return len(value)

    if isinstance(value, dict):

        count = value.get(
            "count"
        )

        if _finite(count):
            return max(
                0,
                int(_float(count)),
            )

        return len(value)

    return 0


# =====================================================================
# GENERIC COMPONENT DIRECTION EXTRACTION
# =====================================================================

def _explicit_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract an explicit direction from common fields.
    """

    for key in (
        "direction",
        "bias",
        "trend",
        "signal",
        "side",
        "dominant_direction",
        "market_direction",
    ):
        direction = _normalize_direction(
            component.get(key)
        )

        if direction is not None:
            return direction

    return None


def _count_fields_direction(
    component: Dict[str, Any],
    bullish_keys: Tuple[str, ...],
    bearish_keys: Tuple[str, ...],
) -> Tuple[Optional[str], float, float]:
    """
    Compare bullish and bearish evidence counts.

    Returns:

        direction
        bullish_count
        bearish_count
    """

    bullish_count = 0.0
    bearish_count = 0.0

    for key in bullish_keys:

        bullish_count += (
            _count_directional_items(
                component.get(key)
            )
        )

    for key in bearish_keys:

        bearish_count += (
            _count_directional_items(
                component.get(key)
            )
        )

    if bullish_count > bearish_count:

        return (
            BUY,
            bullish_count,
            bearish_count,
        )

    if bearish_count > bullish_count:

        return (
            SELL,
            bullish_count,
            bearish_count,
        )

    return (
        None,
        bullish_count,
        bearish_count,
    )


# =====================================================================
# COMPONENT DIRECTION EXTRACTORS
# =====================================================================

def _market_structure_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """Extract directional evidence from market structure."""

    direction = _normalize_direction(
        component.get("bias")
    )

    if direction is not None:
        return direction

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    return None


def _bos_choch_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract BOS / CHoCH direction.

    The primary source is the latest structural event.
    """

    last_event = _safe_dict(
        component.get("last_event")
    )

    direction = _normalize_direction(
        last_event.get("direction")
    )

    if direction is not None:
        return direction

    bos = _safe_list(
        component.get("bos")
    )

    choch = _safe_list(
        component.get("choch")
    )

    buy_count = 0
    sell_count = 0

    for event in bos + choch:

        if not isinstance(event, dict):
            continue

        direction = _normalize_direction(
            event.get("direction")
        )

        if direction == BUY:
            buy_count += 1

        elif direction == SELL:
            sell_count += 1

    if buy_count > sell_count:
        return BUY

    if sell_count > buy_count:
        return SELL

    return None


def _liquidity_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """Extract liquidity directional evidence."""

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    direction, _, _ = _count_fields_direction(
        component,
        (
            "bullish_sweeps",
            "buy_side_sweeps",
            "sell_side_liquidity_sweeps",
            "bullish_liquidity_events",
        ),
        (
            "bearish_sweeps",
            "sell_side_sweeps",
            "buy_side_liquidity_sweeps",
            "bearish_liquidity_events",
        ),
    )

    return direction


def _order_block_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """Extract Order Block directional evidence."""

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    direction, _, _ = _count_fields_direction(
        component,
        (
            "bullish_order_blocks",
            "valid_bullish_order_blocks",
            "fresh_bullish_order_blocks",
            "active_bullish_order_blocks",
        ),
        (
            "bearish_order_blocks",
            "valid_bearish_order_blocks",
            "fresh_bearish_order_blocks",
            "active_bearish_order_blocks",
        ),
    )

    return direction


def _fvg_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """Extract Fair Value Gap directional evidence."""

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    direction, _, _ = _count_fields_direction(
        component,
        (
            "bullish_fvgs",
            "bullish_fvg",
            "valid_bullish_fvgs",
            "fresh_bullish_fvgs",
        ),
        (
            "bearish_fvgs",
            "bearish_fvg",
            "valid_bearish_fvgs",
            "fresh_bearish_fvgs",
        ),
    )

    return direction


def _breaker_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """Extract Breaker Block directional evidence."""

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    direction, _, _ = _count_fields_direction(
        component,
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

    return direction


def _premium_discount_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract Premium / Discount context.

    Discount supports bullish opportunity context.
    Premium supports bearish opportunity context.
    """

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    for key in (
        "zone",
        "current_zone",
        "position",
        "state",
        "location",
    ):

        value = _text(
            component.get(key)
        )

        if value in {
            "DISCOUNT",
            "DEEP_DISCOUNT",
        }:
            return BUY

        if value in {
            "PREMIUM",
            "DEEP_PREMIUM",
        }:
            return SELL

    return None


def _supply_demand_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract Supply / Demand directional evidence.

    Demand = bullish context.
    Supply = bearish context.
    """

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    direction, _, _ = _count_fields_direction(
        component,
        (
            "demand_zones",
            "fresh_demand_zones",
            "valid_demand_zones",
            "bullish_zones",
        ),
        (
            "supply_zones",
            "fresh_supply_zones",
            "valid_supply_zones",
            "bearish_zones",
        ),
    )

    if direction is not None:
        return direction

    zone_type = _text(
        component.get("zone_type")
    )

    if zone_type == "DEMAND":
        return BUY

    if zone_type == "SUPPLY":
        return SELL

    return None


def _volume_profile_direction(
    component: Dict[str, Any],
) -> Optional[str]:
    """
    Extract directional evidence from Volume Profile.

    Volume Profile is contextual and therefore lower authority.
    """

    direction = _explicit_direction(
        component
    )

    if direction is not None:
        return direction

    for key in (
        "value_area_bias",
        "profile_bias",
        "acceptance_direction",
    ):

        direction = _normalize_direction(
            component.get(key)
        )

        if direction is not None:
            return direction

    return None


# =====================================================================
# COMPONENT WEIGHTS
# =====================================================================

COMPONENT_WEIGHTS = {
    "market_structure": 1.00,
    "bos_choch": 0.90,
    "liquidity": 0.90,
    "order_blocks": 0.80,
    "fvg": 0.70,
    "breaker_blocks": 0.70,
    "premium_discount": 0.45,
    "supply_demand": 0.80,
    "volume_profile": 0.40,
}


# =====================================================================
# TECHNICAL CONFLUENCE
# =====================================================================

class TechnicalConfluence:
    """
    Aggregate existing technical-analysis components.

    This class calculates standardized technical evidence and quality
    metrics but NEVER makes the final trading decision.
    """

    COMPONENTS = (
        "market_structure",
        "bos_choch",
        "liquidity",
        "order_blocks",
        "fvg",
        "breaker_blocks",
        "premium_discount",
        "supply_demand",
        "volume_profile",
    )

    def __init__(self) -> None:

        self.name = (
            "BALLY TRADE BOT Technical Confluence"
        )

    # =================================================================
    # PUBLIC API
    # =================================================================

    def calculate(
        self,
        technical_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate standardized technical confluence.

        This method:

            - aggregates existing technical component results
            - extracts directional evidence
            - calculates bullish evidence
            - calculates bearish evidence
            - calculates core confluence
            - calculates enhanced technical quality

        It DOES NOT:

            - generate a final BUY decision
            - generate a final SELL decision
            - generate NO_TRADE
            - retrieve market data
            - execute orders
        """

        if technical_data is None:
            technical_data = {}

        if not isinstance(
            technical_data,
            dict,
        ):
            raise TypeError(
                "technical_data must be a dictionary"
            )

        # -------------------------------------------------------------
        # COMPONENT COLLECTION
        # -------------------------------------------------------------

        components = {
            component:
                technical_data.get(component)
            for component in self.COMPONENTS
        }

        # BOS / CHoCH is naturally produced by MarketStructure.
        # Preserve compatibility with an explicitly supplied component,
        # but derive it when absent.
        if components["bos_choch"] is None:

            structure = _safe_dict(
                components["market_structure"]
            )

            if structure:

                components["bos_choch"] = {
                    "status":
                        structure.get(
                            "status",
                            READY,
                        ),

                    "technical_only": True,

                    "component":
                        "bos_choch",

                    "bos":
                        structure.get(
                            "bos",
                            [],
                        ),

                    "choch":
                        structure.get(
                            "choch",
                            [],
                        ),

                    "last_event":
                        structure.get(
                            "last_event"
                        ),
                }

        # -------------------------------------------------------------
        # AVAILABILITY
        # -------------------------------------------------------------

        available_components = [
            name
            for name, value in components.items()
            if value is not None
        ]

        unavailable_components = [
            name
            for name, value in components.items()
            if value is None
        ]

        component_count = len(
            self.COMPONENTS
        )

        available_component_count = len(
            available_components
        )

        completeness = (
            available_component_count
            / component_count
            if component_count > 0
            else 0.0
        )

        # -------------------------------------------------------------
        # DIRECTIONAL EVIDENCE
        # -------------------------------------------------------------

        extractors = {
            "market_structure":
                _market_structure_direction,

            "bos_choch":
                _bos_choch_direction,

            "liquidity":
                _liquidity_direction,

            "order_blocks":
                _order_block_direction,

            "fvg":
                _fvg_direction,

            "breaker_blocks":
                _breaker_direction,

            "premium_discount":
                _premium_discount_direction,

            "supply_demand":
                _supply_demand_direction,

            "volume_profile":
                _volume_profile_direction,
        }

        component_scores: Dict[
            str,
            Dict[str, Any]
        ] = {}

        bullish_score = 0.0
        bearish_score = 0.0

        directional_component_count = 0

        for component_name in self.COMPONENTS:

            component = components.get(
                component_name
            )

            weight = _float(
                COMPONENT_WEIGHTS.get(
                    component_name,
                    0.0,
                )
            )

            component_dict = _safe_dict(
                component
            )

            direction: Optional[str] = None

            if component_dict:

                extractor = extractors.get(
                    component_name
                )

                if extractor is not None:

                    try:

                        direction = extractor(
                            component_dict
                        )

                    except Exception:

                        # A malformed component must not crash
                        # the entire technical analysis.
                        direction = None

            bullish_points = 0.0
            bearish_points = 0.0

            if direction == BUY:

                bullish_points = weight

                bullish_score += (
                    bullish_points
                )

                directional_component_count += 1

            elif direction == SELL:

                bearish_points = weight

                bearish_score += (
                    bearish_points
                )

                directional_component_count += 1

            component_scores[
                component_name
            ] = {
                "available":
                    component is not None,

                "direction":
                    direction,

                "weight":
                    round(
                        weight,
                        4,
                    ),

                "bullish_points":
                    round(
                        bullish_points,
                        4,
                    ),

                "bearish_points":
                    round(
                        bearish_points,
                        4,
                    ),
            }

        # -------------------------------------------------------------
        # WEIGHT TOTALS
        # -------------------------------------------------------------

        total_possible_weight = sum(
            _float(
                COMPONENT_WEIGHTS.get(
                    component,
                    0.0,
                )
            )
            for component in self.COMPONENTS
        )

        directional_weight = (
            bullish_score
            + bearish_score
        )

        if directional_weight > 0:

            dominant_score = max(
                bullish_score,
                bearish_score,
            )

            dominant_direction = (
                BUY
                if bullish_score > bearish_score
                else SELL
                if bearish_score > bullish_score
                else None
            )

            directional_dominance = (
                dominant_score
                / directional_weight
            )

        else:

            dominant_score = 0.0

            dominant_direction = None

            directional_dominance = 0.0

        # -------------------------------------------------------------
        # CORE CONFLUENCE SCORE
        # -------------------------------------------------------------
        #
        # Core confluence measures:
        #
        #     1. Directional dominance
        #     2. Directional evidence coverage
        #     3. Technical component completeness
        #
        # It is NOT a BUY/SELL decision.
        # -------------------------------------------------------------

        if total_possible_weight > 0:

            directional_coverage = (
                directional_weight
                / total_possible_weight
            )

        else:

            directional_coverage = 0.0

        core_confluence_score = (
            directional_dominance
            * directional_coverage
            * completeness
            * 100.0
        )

        core_confluence_score = _clamp(
            core_confluence_score
        )

        # -------------------------------------------------------------
        # ENHANCED QUALITY SCORE
        # -------------------------------------------------------------
        #
        # Enhanced quality rewards:
        #
        #     - completeness
        #     - directional coverage
        #     - directional agreement
        #
        # Supply/Demand and Volume Profile participate naturally
        # through their registered component weights.
        # -------------------------------------------------------------

        enhanced_quality_score = (
            (
                completeness
                * 35.0
            )
            +
            (
                directional_coverage
                * 35.0
            )
            +
            (
                directional_dominance
                * 30.0
            )
        )

        enhanced_quality_score = _clamp(
            enhanced_quality_score
        )

        # -------------------------------------------------------------
        # NORMALIZED DIRECTIONAL SCORES
        # -------------------------------------------------------------

        if total_possible_weight > 0:

            bullish_score_normalized = (
                bullish_score
                / total_possible_weight
                * 100.0
            )

            bearish_score_normalized = (
                bearish_score
                / total_possible_weight
                * 100.0
            )

        else:

            bullish_score_normalized = 0.0

            bearish_score_normalized = 0.0

        # -------------------------------------------------------------
        # QUALITY LABEL
        # -------------------------------------------------------------

        if enhanced_quality_score >= 80:

            quality = "HIGH"

        elif enhanced_quality_score >= 60:

            quality = "MEDIUM"

        elif enhanced_quality_score > 0:

            quality = "LOW"

        else:

            quality = "UNAVAILABLE"

        # -------------------------------------------------------------
        # RETURN
        # -------------------------------------------------------------

        return {
            "status": READY,

            "technical_only": True,

            "component_count":
                component_count,

            "available_component_count":
                available_component_count,

            "unavailable_component_count":
                len(
                    unavailable_components
                ),

            "available_components":
                available_components,

            "unavailable_components":
                unavailable_components,

            "completeness":
                round(
                    completeness * 100.0,
                    4,
                ),

            "directional_component_count":
                directional_component_count,

            "dominant_direction":
                dominant_direction,

            "directional_dominance":
                round(
                    directional_dominance * 100.0,
                    4,
                ),

            "directional_coverage":
                round(
                    directional_coverage * 100.0,
                    4,
                ),

            # ---------------------------------------------------------
            # PRIMARY SCORES
            # ---------------------------------------------------------

            "core_confluence_score":
                round(
                    core_confluence_score,
                    4,
                ),

            "enhanced_quality_score":
                round(
                    enhanced_quality_score,
                    4,
                ),

            "quality":
                quality,

            # ---------------------------------------------------------
            # DIRECTIONAL EVIDENCE
            # ---------------------------------------------------------

            "bullish_score":
                round(
                    bullish_score_normalized,
                    4,
                ),

            "bearish_score":
                round(
                    bearish_score_normalized,
                    4,
                ),

            "raw_bullish_weight":
                round(
                    bullish_score,
                    4,
                ),

            "raw_bearish_weight":
                round(
                    bearish_score,
                    4,
                ),

            "total_possible_weight":
                round(
                    total_possible_weight,
                    4,
                ),

            # ---------------------------------------------------------
            # COMPONENT DETAILS
            # ---------------------------------------------------------

            "component_scores":
                component_scores,

            "components":
                components,
        }