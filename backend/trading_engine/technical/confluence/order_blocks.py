
"""
BALLY FLOW - Technical Order Block Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module identifies and evaluates institutional-style Order Blocks
from OHLC candle data.

The module does NOT:
    - perform fundamental analysis
    - perform hybrid decision-making
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - make the final BUY / SELL / NO_TRADE decision

ORDER BLOCK CONCEPT
-------------------

A bullish order block is generally treated as the final meaningful
bearish candle or bearish candle cluster preceding a strong bullish
displacement that subsequently breaks meaningful market structure.

A bearish order block is generally treated as the final meaningful
bullish candle or bullish candle cluster preceding a strong bearish
displacement that subsequently breaks meaningful market structure.

A candle is NOT automatically an Order Block simply because it is
opposite in color to the following candle.

VALIDATION FACTORS
------------------

The implementation evaluates:

    1. Candle direction
    2. Candle body/range characteristics
    3. Displacement after the candidate
    4. Structural break after the candidate
    5. Follow-through
    6. Zone boundaries
    7. Freshness
    8. Mitigation
    9. Invalidation
    10. Retest information
    11. Relative strength
    12. Optional volume information

ZONE LOGIC
----------

Bullish Order Block:
    zone_high = candidate candle high
    zone_low  = candidate candle low

Bearish Order Block:
    zone_high = candidate candle high
    zone_low  = candidate candle low

The complete candle range is retained because wick information can
matter when evaluating liquidity interaction and invalidation.

MITIGATION
----------

An Order Block can remain structurally valid after price revisits it.

The module distinguishes:

    FRESH
    PARTIALLY_MITIGATED
    FULLY_MITIGATED

INVALIDATION
------------

An Order Block is considered invalid when price closes decisively
through the protected boundary of the zone in the direction that
contradicts the Order Block.

A wick through a zone does not automatically invalidate the block.

This distinction is important because real markets frequently probe
liquidity beyond a zone before continuing in the intended direction.

INPUT
-----

Candles may be supplied as:

    {
        "open": 123.0,
        "high": 125.0,
        "low": 121.0,
        "close": 124.0
    }

or objects exposing:

    .open
    .high
    .low
    .close

Optional fields are supported:

    volume
    tick_volume
    time
    timestamp

Candles must be ordered oldest -> newest.

TECHNICAL ONLY
--------------

Every result contains:

    "technical_only": True
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class OrderBlocks:
    """
    Technical Order Block detector and evaluator.
    """

    NAME = "BALLY FLOW Order Blocks"

    DEFAULT_LOOKBACK = 2
    DEFAULT_DISPLACEMENT_LOOKAHEAD = 3

    MIN_BODY_RATIO = 0.45
    MIN_DISPLACEMENT_RATIO = 1.20

    def __init__(
        self,
        lookback: int = DEFAULT_LOOKBACK,
        displacement_lookahead: int = DEFAULT_DISPLACEMENT_LOOKAHEAD,
    ) -> None:

        if not isinstance(lookback, int):
            raise TypeError("lookback must be an integer")

        if lookback < 1:
            raise ValueError("lookback must be greater than zero")

        if not isinstance(displacement_lookahead, int):
            raise TypeError(
                "displacement_lookahead must be an integer"
            )

        if displacement_lookahead < 1:
            raise ValueError(
                "displacement_lookahead must be greater than zero"
            )

        self.lookback = lookback
        self.displacement_lookahead = displacement_lookahead

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def analyze(
        self,
        candles: Any,
        structure: Optional[Dict[str, Any]] = None,
        volume: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Analyze Order Blocks from candle data.

        Parameters
        ----------
        candles:
            OHLC candle sequence.

        structure:
            Optional output from MarketStructure.

        volume:
            Optional external volume sequence.

        Returns
        -------
        dict
            Standardized technical-only Order Block analysis.
        """

        normalized = self._normalize_candles(candles)

        if volume is not None:
            self._attach_external_volume(normalized, volume)

        minimum = max(
            self.lookback * 2 + 3,
            self.displacement_lookahead + 3,
        )

        if len(normalized) < minimum:
            return self._insufficient_result(len(normalized))

        structure_data = structure or {}

        candidates = self._find_candidates(normalized)

        order_blocks: List[Dict[str, Any]] = []

        for candidate in candidates:
            block = self._evaluate_candidate(
                normalized,
                candidate,
                structure_data,
            )

            if block is not None:
                order_blocks.append(block)

        self._evaluate_mitigation_and_invalidation(
            normalized,
            order_blocks,
        )

        self._evaluate_retests(
            normalized,
            order_blocks,
        )

        bullish = [
            block
            for block in order_blocks
            if block["direction"] == "BUY"
        ]

        bearish = [
            block
            for block in order_blocks
            if block["direction"] == "SELL"
        ]

        valid = [
            block
            for block in order_blocks
            if block["valid"]
        ]

        fresh = [
            block
            for block in valid
            if block["state"] == "FRESH"
        ]

        mitigated = [
            block
            for block in valid
            if block["state"] in {
                "PARTIALLY_MITIGATED",
                "FULLY_MITIGATED",
            }
        ]

        invalidated = [
            block
            for block in order_blocks
            if not block["valid"]
        ]

        last_block = (
            order_blocks[-1]
            if order_blocks
            else None
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "order_blocks",
            "candle_count": len(normalized),
            "lookback": self.lookback,
            "displacement_lookahead": self.displacement_lookahead,

            "order_blocks": order_blocks,

            "bullish_order_blocks": bullish,
            "bearish_order_blocks": bearish,

            "valid_order_blocks": valid,
            "fresh_order_blocks": fresh,
            "mitigated_order_blocks": mitigated,
            "invalidated_order_blocks": invalidated,

            "counts": {
                "total": len(order_blocks),
                "bullish": len(bullish),
                "bearish": len(bearish),
                "valid": len(valid),
                "fresh": len(fresh),
                "mitigated": len(mitigated),
                "invalidated": len(invalidated),
            },

            "last_order_block": last_block,
        }

    # ==============================================================
    # NORMALIZATION
    # ==============================================================

    @staticmethod
    def _normalize_candles(
        candles: Any,
    ) -> List[Dict[str, Any]]:

        if candles is None:
            raise ValueError("candles are required")

        if isinstance(candles, dict):
            candles = candles.get("candles")

        if candles is None:
            raise ValueError("candles are required")

        try:
            sequence = list(candles)
        except TypeError as exc:
            raise TypeError(
                "candles must be an iterable"
            ) from exc

        normalized: List[Dict[str, Any]] = []

        for index, candle in enumerate(sequence):

            if isinstance(candle, dict):

                try:
                    open_price = candle["open"]
                    high = candle["high"]
                    low = candle["low"]
                    close = candle["close"]
                except KeyError as exc:
                    raise ValueError(
                        f"candle {index} is missing OHLC field: {exc}"
                    ) from exc

                item: Dict[str, Any] = {
                    "open": float(open_price),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                }

                for key in (
                    "volume",
                    "tick_volume",
                    "time",
                    "timestamp",
                ):
                    if key in candle:
                        item[key] = candle[key]

            else:

                try:
                    item = {
                        "open": float(
                            getattr(candle, "open")
                        ),
                        "high": float(
                            getattr(candle, "high")
                        ),
                        "low": float(
                            getattr(candle, "low")
                        ),
                        "close": float(
                            getattr(candle, "close")
                        ),
                    }

                except AttributeError as exc:
                    raise ValueError(
                        f"candle {index} does not expose OHLC fields"
                    ) from exc

                for key in (
                    "volume",
                    "tick_volume",
                    "time",
                    "timestamp",
                ):
                    if hasattr(candle, key):
                        item[key] = getattr(candle, key)

            if item["high"] < item["low"]:
                raise ValueError(
                    f"candle {index} has high below low"
                )

            if item["high"] < item["open"]:
                raise ValueError(
                    f"candle {index} has high below open"
                )

            if item["high"] < item["close"]:
                raise ValueError(
                    f"candle {index} has high below close"
                )

            if item["low"] > item["open"]:
                raise ValueError(
                    f"candle {index} has low above open"
                )

            if item["low"] > item["close"]:
                raise ValueError(
                    f"candle {index} has low above close"
                )

            normalized.append(item)

        return normalized

    @staticmethod
    def _attach_external_volume(
        candles: List[Dict[str, Any]],
        volume: Any,
    ) -> None:

        try:
            volumes = list(volume)
        except TypeError as exc:
            raise TypeError(
                "volume must be an iterable"
            ) from exc

        if len(volumes) != len(candles):
            raise ValueError(
                "volume length must match candle count"
            )

        for candle, value in zip(candles, volumes):

            try:
                candle["volume"] = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "volume contains non-numeric data"
                ) from exc

    # ==============================================================
    # CANDLE CHARACTERISTICS
    # ==============================================================

    @staticmethod
    def _range(candle: Dict[str, Any]) -> float:
        return max(
            float(candle["high"]) - float(candle["low"]),
            0.0,
        )

    @staticmethod
    def _body(candle: Dict[str, Any]) -> float:
        return abs(
            float(candle["close"])
            - float(candle["open"])
        )

    @classmethod
    def _body_ratio(
        cls,
        candle: Dict[str, Any],
    ) -> float:

        candle_range = cls._range(candle)

        if candle_range <= 0:
            return 0.0

        return cls._body(candle) / candle_range

    @staticmethod
    def _direction(
        candle: Dict[str, Any],
    ) -> str:

        if candle["close"] > candle["open"]:
            return "BULLISH"

        if candle["close"] < candle["open"]:
            return "BEARISH"

        return "NEUTRAL"

    # ==============================================================
    # CANDIDATE DETECTION
    # ==============================================================

    def _find_candidates(
        self,
        candles: Sequence[Dict[str, Any]],
    ) -> List[int]:

        candidates: List[int] = []

        for index in range(
            0,
            len(candles) - self.displacement_lookahead,
        ):

            candle = candles[index]

            direction = self._direction(candle)

            if direction not in {
                "BULLISH",
                "BEARISH",
            }:
                continue

            body_ratio = self._body_ratio(candle)

            # Very weak candles are less reliable as institutional
            # origin candles.
            if body_ratio < self.MIN_BODY_RATIO:
                continue

            future = candles[
                index + 1:
                index + 1 + self.displacement_lookahead
            ]

            if not future:
                continue

            if direction == "BEARISH":
                if self._bullish_displacement(
                    candle,
                    future,
                ):
                    candidates.append(index)

            elif direction == "BULLISH":
                if self._bearish_displacement(
                    candle,
                    future,
                ):
                    candidates.append(index)

        return candidates

    # ==============================================================
    # DISPLACEMENT
    # ==============================================================

    def _bullish_displacement(
        self,
        origin: Dict[str, Any],
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        origin_range = self._range(origin)

        if origin_range <= 0:
            return False

        highest_close = max(
            float(candle["close"])
            for candle in future
        )

        highest_high = max(
            float(candle["high"])
            for candle in future
        )

        displacement_distance = max(
            highest_close - float(origin["high"]),
            highest_high - float(origin["high"]),
        )

        return (
            displacement_distance
            >= origin_range * self.MIN_DISPLACEMENT_RATIO
        )

    def _bearish_displacement(
        self,
        origin: Dict[str, Any],
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        origin_range = self._range(origin)

        if origin_range <= 0:
            return False

        lowest_close = min(
            float(candle["close"])
            for candle in future
        )

        lowest_low = min(
            float(candle["low"])
            for candle in future
        )

        displacement_distance = max(
            float(origin["low"]) - lowest_close,
            float(origin["low"]) - lowest_low,
        )

        return (
            displacement_distance
            >= origin_range * self.MIN_DISPLACEMENT_RATIO
        )

    # ==============================================================
    # STRUCTURAL RELATIONSHIP
    # ==============================================================

    @staticmethod
    def _structure_breaks(
        structure: Dict[str, Any],
        candidate_index: int,
        direction: str,
    ) -> bool:

        bos = structure.get("bos", [])

        if not isinstance(bos, list):
            return False

        for event in bos:

            if not isinstance(event, dict):
                continue

            event_index = event.get("index")

            if not isinstance(event_index, int):
                continue

            if event_index <= candidate_index:
                continue

            event_direction = event.get(
                "direction"
            )

            if direction == "BUY":
                if event_direction == "BUY":
                    return True

            elif direction == "SELL":
                if event_direction == "SELL":
                    return True

        return False

    # ==============================================================
    # CANDIDATE EVALUATION
    # ==============================================================

    def _evaluate_candidate(
        self,
        candles: Sequence[Dict[str, Any]],
        index: int,
        structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        candle = candles[index]

        direction = self._direction(candle)

        if direction == "BEARISH":
            block_direction = "BUY"

        elif direction == "BULLISH":
            block_direction = "SELL"

        else:
            return None

        future = candles[
            index + 1:
            index + 1 + self.displacement_lookahead
        ]

        if not future:
            return None

        if block_direction == "BUY":
            displacement = self._bullish_displacement(
                candle,
                future,
            )
        else:
            displacement = self._bearish_displacement(
                candle,
                future,
            )

        if not displacement:
            return None

        structure_break = self._structure_breaks(
            structure,
            index,
            block_direction,
        )

        body_ratio = self._body_ratio(candle)

        candle_range = self._range(candle)

        displacement_strength = self._calculate_displacement_strength(
            candle,
            future,
            block_direction,
        )

        volume_strength = self._volume_strength(
            candles,
            index,
        )

        score = self._quality_score(
            body_ratio=body_ratio,
            displacement_strength=displacement_strength,
            structure_break=structure_break,
            volume_strength=volume_strength,
        )

        if block_direction == "BUY":
            protected_level = candle["low"]
        else:
            protected_level = candle["high"]

        return {
            "index": index,
            "direction": block_direction,

            "type": (
                "BULLISH_ORDER_BLOCK"
                if block_direction == "BUY"
                else "BEARISH_ORDER_BLOCK"
            ),

            "origin": {
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "direction": direction,
                "body_ratio": body_ratio,
                "range": candle_range,
            },

            "zone": {
                "high": candle["high"],
                "low": candle["low"],
                "protected_level": protected_level,
            },

            "validation": {
                "displacement": displacement,
                "displacement_strength": displacement_strength,
                "structure_break": structure_break,
                "volume_strength": volume_strength,
                "quality_score": score,
            },

            "state": "FRESH",
            "valid": True,

            "mitigation": {
                "touched": False,
                "touch_count": 0,
                "penetration_ratio": 0.0,
                "state": "FRESH",
            },

            "invalidation": {
                "invalidated": False,
                "index": None,
                "price": None,
                "reason": None,
            },

            "retests": [],

            "created_index": index,
        }

    # ==============================================================
    # DISPLACEMENT STRENGTH
    # ==============================================================

    def _calculate_displacement_strength(
        self,
        origin: Dict[str, Any],
        future: Sequence[Dict[str, Any]],
        direction: str,
    ) -> float:

        origin_range = self._range(origin)

        if origin_range <= 0:
            return 0.0

        if direction == "BUY":

            extreme = max(
                float(candle["high"])
                for candle in future
            )

            distance = (
                extreme
                - float(origin["high"])
            )

        else:

            extreme = min(
                float(candle["low"])
                for candle in future
            )

            distance = (
                float(origin["low"])
                - extreme
            )

        ratio = distance / origin_range

        return round(
            max(0.0, min(ratio * 50.0, 100.0)),
            2,
        )

    # ==============================================================
    # VOLUME
    # ==============================================================

    @staticmethod
    def _volume_strength(
        candles: Sequence[Dict[str, Any]],
        index: int,
    ) -> Optional[float]:

        if "volume" not in candles[index]:
            return None

        try:
            current_volume = float(
                candles[index]["volume"]
            )
        except (TypeError, ValueError):
            return None

        previous = candles[
            max(0, index - 20):
            index
        ]

        values: List[float] = []

        for candle in previous:

            if "volume" not in candle:
                continue

            try:
                values.append(
                    float(candle["volume"])
                )
            except (TypeError, ValueError):
                continue

        if not values:
            return None

        average = sum(values) / len(values)

        if average <= 0:
            return None

        ratio = current_volume / average

        return round(
            max(0.0, min(ratio * 50.0, 100.0)),
            2,
        )

    # ==============================================================
    # QUALITY
    # ==============================================================

    @staticmethod
    def _quality_score(
        body_ratio: float,
        displacement_strength: float,
        structure_break: bool,
        volume_strength: Optional[float],
    ) -> float:

        score = 0.0

        score += min(
            max(body_ratio, 0.0),
            1.0,
        ) * 20.0

        score += (
            min(
                max(displacement_strength, 0.0),
                100.0,
            )
            * 0.50
        )

        if structure_break:
            score += 20.0

        if volume_strength is not None:
            score += (
                min(
                    max(volume_strength, 0.0),
                    100.0,
                )
                * 0.10
            )

        return round(
            min(score, 100.0),
            2,
        )

    # ==============================================================
    # MITIGATION / INVALIDATION
    # ==============================================================

    def _evaluate_mitigation_and_invalidation(
        self,
        candles: Sequence[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
    ) -> None:

        for block in blocks:

            start = block["created_index"]

            zone_high = float(
                block["zone"]["high"]
            )

            zone_low = float(
                block["zone"]["low"]
            )

            direction = block["direction"]

            touches = 0
            deepest_penetration = 0.0

            invalidated = False
            invalidation_index = None
            invalidation_price = None

            zone_range = max(
                zone_high - zone_low,
                0.0,
            )

            for index in range(
                start + 1,
                len(candles),
            ):

                candle = candles[index]

                high = float(candle["high"])
                low = float(candle["low"])
                close = float(candle["close"])

                overlaps = (
                    high >= zone_low
                    and low <= zone_high
                )

                if overlaps:

                    touches += 1

                    if direction == "BUY":

                        penetration = max(
                            0.0,
                            zone_high - low,
                        )

                    else:

                        penetration = max(
                            0.0,
                            high - zone_low,
                        )

                    if zone_range > 0:

                        ratio = (
                            penetration
                            / zone_range
                        )

                        deepest_penetration = max(
                            deepest_penetration,
                            min(ratio, 1.0),
                        )

                # Close-based invalidation.
                if direction == "BUY":

                    if close < zone_low:

                        invalidated = True
                        invalidation_index = index
                        invalidation_price = close
                        break

                else:

                    if close > zone_high:

                        invalidated = True
                        invalidation_index = index
                        invalidation_price = close
                        break

            if invalidated:

                block["valid"] = False
                block["state"] = "INVALIDATED"

                block["invalidation"] = {
                    "invalidated": True,
                    "index": invalidation_index,
                    "price": invalidation_price,
                    "reason": (
                        "closed beyond protected "
                        "order-block boundary"
                    ),
                }

            else:

                block["valid"] = True

                if touches == 0:

                    state = "FRESH"

                elif deepest_penetration >= 1.0:

                    state = "FULLY_MITIGATED"

                else:

                    state = "PARTIALLY_MITIGATED"

                block["state"] = state

            block["mitigation"] = {
                "touched": touches > 0,
                "touch_count": touches,
                "penetration_ratio": round(
                    deepest_penetration,
                    4,
                ),
                "state": block["state"]
                if block["valid"]
                else "INVALIDATED",
            }

    # ==============================================================
    # RETESTS
    # ==============================================================

    def _evaluate_retests(
        self,
        candles: Sequence[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
    ) -> None:

        for block in blocks:

            if not block["valid"]:
                continue

            zone_high = float(
                block["zone"]["high"]
            )

            zone_low = float(
                block["zone"]["low"]
            )

            direction = block["direction"]

            created_index = block[
                "created_index"
            ]

            retests: List[Dict[str, Any]] = []

            for index in range(
                created_index + 1,
                len(candles),
            ):

                candle = candles[index]

                high = float(candle["high"])
                low = float(candle["low"])
                close = float(candle["close"])

                touched = (
                    high >= zone_low
                    and low <= zone_high
                )

                if not touched:
                    continue

                if direction == "BUY":

                    rejection = (
                        close > zone_high
                    )

                else:

                    rejection = (
                        close < zone_low
                    )

                retests.append(
                    {
                        "index": index,
                        "high": high,
                        "low": low,
                        "close": close,
                        "rejection": rejection,
                    }
                )

            block["retests"] = retests

    # ==============================================================
    # INSUFFICIENT DATA
    # ==============================================================

    def _insufficient_result(
        self,
        candle_count: int,
    ) -> Dict[str, Any]:

        return {
            "status": "INSUFFICIENT_DATA",
            "technical_only": True,
            "component": "order_blocks",
            "candle_count": candle_count,
            "lookback": self.lookback,
            "displacement_lookahead": (
                self.displacement_lookahead
            ),

            "order_blocks": [],
            "bullish_order_blocks": [],
            "bearish_order_blocks": [],
            "valid_order_blocks": [],
            "fresh_order_blocks": [],
            "mitigated_order_blocks": [],
            "invalidated_order_blocks": [],

            "counts": {
                "total": 0,
                "bullish": 0,
                "bearish": 0,
                "valid": 0,
                "fresh": 0,
                "mitigated": 0,
                "invalidated": 0,
            },

            "last_order_block": None,
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_order_blocks(
    candles: Any,
    structure: Optional[Dict[str, Any]] = None,
    volume: Optional[Any] = None,
    lookback: int = OrderBlocks.DEFAULT_LOOKBACK,
    displacement_lookahead: int = (
        OrderBlocks.DEFAULT_DISPLACEMENT_LOOKAHEAD
    ),
) -> Dict[str, Any]:

    analyzer = OrderBlocks(
        lookback=lookback,
        displacement_lookahead=(
            displacement_lookahead
        ),
    )

    return analyzer.analyze(
        candles=candles,
        structure=structure,
        volume=volume,
    )


# ==================================================================
# COMPATIBILITY ALIAS
# ==================================================================

OrderBlock = OrderBlocks