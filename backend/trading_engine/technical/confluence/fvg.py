"""
BALLY FLOW - Technical Fair Value Gap Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module identifies and evaluates Fair Value Gaps (FVGs) from
OHLC candle data.

The module does NOT:
    - perform fundamental analysis
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - make the final BUY / SELL / NO_TRADE decision

FVG CONCEPT
-----------

A bullish FVG is a three-candle imbalance where:

    third candle low > first candle high

A bearish FVG is a three-candle imbalance where:

    third candle high < first candle low

The middle candle represents the displacement leg.

A simple three-candle price separation is not automatically treated
as a high-quality FVG. The implementation also evaluates:

    - middle-candle direction
    - middle-candle body/range
    - gap size
    - displacement
    - optional structure confirmation
    - optional volume information
    - mitigation
    - invalidation
    - retests

MITIGATION
----------

An FVG may be revisited without immediately becoming invalid.

States:

    FRESH
    PARTIALLY_MITIGATED
    FULLY_MITIGATED
    INVALIDATED

A wick entering the FVG is mitigation, not automatically invalidation.

Invalidation occurs when price closes beyond the far boundary of the
imbalance in the direction that defeats the FVG.

TECHNICAL ONLY
--------------

Every result contains:

    "technical_only": True
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class FairValueGaps:
    """
    Technical Fair Value Gap detector and evaluator.
    """

    NAME = "BALLY FLOW Fair Value Gaps"

    DEFAULT_MIN_GAP_RATIO = 0.10
    DEFAULT_MIN_MIDDLE_BODY_RATIO = 0.45
    DEFAULT_MIN_DISPLACEMENT_RATIO = 0.50

    MIN_GAP_RATIO = DEFAULT_MIN_GAP_RATIO
    MIN_MIDDLE_BODY_RATIO = DEFAULT_MIN_MIDDLE_BODY_RATIO
    MIN_DISPLACEMENT_RATIO = DEFAULT_MIN_DISPLACEMENT_RATIO

    def __init__(
        self,
        min_gap_ratio: float = DEFAULT_MIN_GAP_RATIO,
        min_middle_body_ratio: float = DEFAULT_MIN_MIDDLE_BODY_RATIO,
        min_displacement_ratio: float = DEFAULT_MIN_DISPLACEMENT_RATIO,
    ) -> None:

        self.min_gap_ratio = self._validate_ratio(
            min_gap_ratio,
            "min_gap_ratio",
            allow_zero=False,
        )

        self.min_middle_body_ratio = self._validate_ratio(
            min_middle_body_ratio,
            "min_middle_body_ratio",
            allow_zero=True,
        )

        self.min_displacement_ratio = self._validate_ratio(
            min_displacement_ratio,
            "min_displacement_ratio",
            allow_zero=True,
        )

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
        Analyze Fair Value Gaps.

        Candles must be ordered:

            oldest -> newest

        Parameters
        ----------
        candles:
            OHLC candle sequence.

        structure:
            Optional market-structure output.

        volume:
            Optional external volume sequence matching candle count.

        Returns
        -------
        dict
            Standardized technical-only FVG analysis.
        """

        normalized = self._normalize_candles(candles)

        if volume is not None:
            self._attach_external_volume(
                normalized,
                volume,
            )

        if len(normalized) < 3:
            return self._insufficient_result(
                len(normalized)
            )

        structure_data = (
            structure
            if isinstance(structure, dict)
            else {}
        )

        gaps: List[Dict[str, Any]] = []

        for index in range(
            len(normalized) - 2
        ):

            gap = self._evaluate_candidate(
                normalized,
                index,
                structure_data,
            )

            if gap is not None:
                gaps.append(gap)

        self._evaluate_mitigation_and_invalidation(
            normalized,
            gaps,
        )

        self._evaluate_retests(
            normalized,
            gaps,
        )

        bullish = [
            gap
            for gap in gaps
            if gap["direction"] == "BUY"
        ]

        bearish = [
            gap
            for gap in gaps
            if gap["direction"] == "SELL"
        ]

        valid = [
            gap
            for gap in gaps
            if gap["valid"]
        ]

        fresh = [
            gap
            for gap in valid
            if gap["state"] == "FRESH"
        ]

        mitigated = [
            gap
            for gap in valid
            if gap["state"] in {
                "PARTIALLY_MITIGATED",
                "FULLY_MITIGATED",
            }
        ]

        invalidated = [
            gap
            for gap in gaps
            if not gap["valid"]
        ]

        last_gap = (
            gaps[-1]
            if gaps
            else None
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "fair_value_gaps",

            "candle_count": len(normalized),

            "min_gap_ratio": (
                self.min_gap_ratio
            ),

            "min_middle_body_ratio": (
                self.min_middle_body_ratio
            ),

            "min_displacement_ratio": (
                self.min_displacement_ratio
            ),

            "fair_value_gaps": gaps,

            # Compatibility alias.
            "fvgs": gaps,

            "bullish_fvgs": bullish,

            "bearish_fvgs": bearish,

            "valid_fvgs": valid,

            "fresh_fvgs": fresh,

            "mitigated_fvgs": mitigated,

            "invalidated_fvgs": invalidated,

            "counts": {
                "total": len(gaps),
                "bullish": len(bullish),
                "bearish": len(bearish),
                "valid": len(valid),
                "fresh": len(fresh),
                "mitigated": len(mitigated),
                "invalidated": len(invalidated),
            },

            "last_fvg": last_gap,
        }

    # ==============================================================
    # VALIDATION
    # ==============================================================

    @staticmethod
    def _validate_ratio(
        value: float,
        name: str,
        allow_zero: bool,
    ) -> float:

        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
        ):
            raise TypeError(
                f"{name} must be numeric"
            )

        value = float(value)

        if value < 0:
            raise ValueError(
                f"{name} cannot be negative"
            )

        if not allow_zero and value == 0:
            raise ValueError(
                f"{name} must be greater than zero"
            )

        return value

    # ==============================================================
    # NORMALIZATION
    # ==============================================================

    @staticmethod
    def _normalize_candles(
        candles: Any,
    ) -> List[Dict[str, Any]]:

        if candles is None:
            raise ValueError(
                "candles are required"
            )

        if isinstance(candles, dict):
            candles = candles.get(
                "candles"
            )

        if candles is None:
            raise ValueError(
                "candles are required"
            )

        try:
            sequence = list(candles)

        except TypeError as exc:
            raise TypeError(
                "candles must be an iterable"
            ) from exc

        normalized: List[Dict[str, Any]] = []

        for index, candle in enumerate(
            sequence
        ):

            if isinstance(candle, dict):

                try:
                    item = {
                        "open": float(
                            candle["open"]
                        ),
                        "high": float(
                            candle["high"]
                        ),
                        "low": float(
                            candle["low"]
                        ),
                        "close": float(
                            candle["close"]
                        ),
                    }

                except KeyError as exc:
                    raise ValueError(
                        f"candle {index} is missing "
                        f"OHLC field: {exc}"
                    ) from exc

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
                            candle.open
                        ),
                        "high": float(
                            candle.high
                        ),
                        "low": float(
                            candle.low
                        ),
                        "close": float(
                            candle.close
                        ),
                    }

                except AttributeError as exc:
                    raise ValueError(
                        f"candle {index} does not "
                        "expose OHLC fields"
                    ) from exc

                for key in (
                    "volume",
                    "tick_volume",
                    "time",
                    "timestamp",
                ):

                    if hasattr(
                        candle,
                        key,
                    ):
                        item[key] = getattr(
                            candle,
                            key,
                        )

            if item["high"] < item["low"]:
                raise ValueError(
                    f"candle {index} has "
                    "high below low"
                )

            if (
                item["high"]
                < item["open"]
            ):
                raise ValueError(
                    f"candle {index} has "
                    "high below open"
                )

            if (
                item["high"]
                < item["close"]
            ):
                raise ValueError(
                    f"candle {index} has "
                    "high below close"
                )

            if (
                item["low"]
                > item["open"]
            ):
                raise ValueError(
                    f"candle {index} has "
                    "low above open"
                )

            if (
                item["low"]
                > item["close"]
            ):
                raise ValueError(
                    f"candle {index} has "
                    "low above close"
                )

            normalized.append(item)

        return normalized

    # ==============================================================
    # EXTERNAL VOLUME
    # ==============================================================

    @staticmethod
    def _attach_external_volume(
        candles: List[Dict[str, Any]],
        volume: Any,
    ) -> None:

        try:
            values = list(volume)

        except TypeError as exc:
            raise TypeError(
                "volume must be an iterable"
            ) from exc

        if len(values) != len(candles):
            raise ValueError(
                "volume length must match "
                "candle count"
            )

        for candle, value in zip(
            candles,
            values,
        ):

            try:
                candle["volume"] = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise ValueError(
                    "volume contains "
                    "non-numeric data"
                ) from exc

    # ==============================================================
    # CANDLE CHARACTERISTICS
    # ==============================================================

    @staticmethod
    def _range(
        candle: Dict[str, Any],
    ) -> float:

        return max(
            float(candle["high"])
            - float(candle["low"]),
            0.0,
        )

    @staticmethod
    def _body(
        candle: Dict[str, Any],
    ) -> float:

        return abs(
            float(candle["close"])
            - float(candle["open"])
        )

    @classmethod
    def _body_ratio(
        cls,
        candle: Dict[str, Any],
    ) -> float:

        candle_range = cls._range(
            candle
        )

        if candle_range <= 0:
            return 0.0

        return (
            cls._body(candle)
            / candle_range
        )

    @staticmethod
    def _direction(
        candle: Dict[str, Any],
    ) -> str:

        if (
            candle["close"]
            > candle["open"]
        ):
            return "BULLISH"

        if (
            candle["close"]
            < candle["open"]
        ):
            return "BEARISH"

        return "NEUTRAL"

    # ==============================================================
    # FVG CANDIDATE
    # ==============================================================

    def _evaluate_candidate(
        self,
        candles: Sequence[Dict[str, Any]],
        index: int,
        structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        first = candles[index]

        middle = candles[
            index + 1
        ]

        third = candles[
            index + 2
        ]

        first_range = self._range(
            first
        )

        middle_range = self._range(
            middle
        )

        third_range = self._range(
            third
        )

        if (
            first_range <= 0
            or middle_range <= 0
            or third_range <= 0
        ):
            return None

        middle_body_ratio = (
            self._body_ratio(middle)
        )

        if (
            middle_body_ratio
            < self.min_middle_body_ratio
        ):
            return None

        direction: Optional[str] = None

        gap_low = 0.0
        gap_high = 0.0

        # ----------------------------------------------------------
        # BULLISH FVG
        # ----------------------------------------------------------

        if (
            float(third["low"])
            > float(first["high"])
        ):

            direction = "BUY"

            gap_low = float(
                first["high"]
            )

            gap_high = float(
                third["low"]
            )

        # ----------------------------------------------------------
        # BEARISH FVG
        # ----------------------------------------------------------

        elif (
            float(third["high"])
            < float(first["low"])
        ):

            direction = "SELL"

            gap_low = float(
                third["high"]
            )

            gap_high = float(
                first["low"]
            )

        if direction is None:
            return None

        gap_size = (
            gap_high
            - gap_low
        )

        if gap_size <= 0:
            return None

        reference_range = max(
            first_range,
            middle_range,
            third_range,
        )

        if reference_range <= 0:
            return None

        gap_ratio = (
            gap_size
            / reference_range
        )

        if (
            gap_ratio
            < self.min_gap_ratio
        ):
            return None

        middle_direction = (
            self._direction(middle)
        )

        # A bullish FVG should be produced
        # by bullish displacement.
        if (
            direction == "BUY"
            and middle_direction
            != "BULLISH"
        ):
            return None

        # A bearish FVG should be produced
        # by bearish displacement.
        if (
            direction == "SELL"
            and middle_direction
            != "BEARISH"
        ):
            return None

        displacement_strength = (
            self._displacement_strength(
                first,
                middle,
                third,
                direction,
            )
        )

        if (
            displacement_strength
            < self.min_displacement_ratio
        ):
            return None

        structure_break = (
            self._structure_breaks(
                structure,
                index + 1,
                direction,
            )
        )

        volume_strength = (
            self._volume_strength(
                candles,
                index + 1,
            )
        )

        quality_score = (
            self._quality_score(
                gap_ratio=gap_ratio,
                middle_body_ratio=(
                    middle_body_ratio
                ),
                displacement_strength=(
                    displacement_strength
                ),
                structure_break=(
                    structure_break
                ),
                volume_strength=(
                    volume_strength
                ),
            )
        )

        return {
            "index": index + 1,

            "direction": direction,

            "type": (
                "BULLISH_FVG"
                if direction == "BUY"
                else "BEARISH_FVG"
            ),

            "origin": {
                "first_index": index,
                "middle_index": index + 1,
                "third_index": index + 2,

                "first_candle": {
                    "open": first["open"],
                    "high": first["high"],
                    "low": first["low"],
                    "close": first["close"],
                },

                "middle_candle": {
                    "open": middle["open"],
                    "high": middle["high"],
                    "low": middle["low"],
                    "close": middle["close"],
                },

                "third_candle": {
                    "open": third["open"],
                    "high": third["high"],
                    "low": third["low"],
                    "close": third["close"],
                },

                "middle_direction": (
                    middle_direction
                ),

                "middle_body_ratio": round(
                    middle_body_ratio,
                    6,
                ),
            },

            "zone": {
                "high": gap_high,
                "low": gap_low,

                "size": round(
                    gap_size,
                    10,
                ),

                "midpoint": round(
                    (
                        gap_high
                        + gap_low
                    ) / 2.0,
                    10,
                ),
            },

            "validation": {
                "gap_ratio": round(
                    gap_ratio,
                    6,
                ),

                "displacement_strength": round(
                    displacement_strength,
                    6,
                ),

                "structure_break": (
                    structure_break
                ),

                "volume_strength": (
                    volume_strength
                ),

                "quality_score": (
                    quality_score
                ),
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

            "created_index": index + 2,
        }

    # ==============================================================
    # DISPLACEMENT
    # ==============================================================

    @classmethod
    def _displacement_strength(
        cls,
        first: Dict[str, Any],
        middle: Dict[str, Any],
        third: Dict[str, Any],
        direction: str,
    ) -> float:

        reference_range = max(
            cls._range(first),
            cls._range(middle),
            cls._range(third),
        )

        if reference_range <= 0:
            return 0.0

        if direction == "BUY":

            distance = max(
                0.0,

                float(
                    middle["close"]
                )
                - float(
                    first["high"]
                ),

                float(
                    third["close"]
                )
                - float(
                    first["high"]
                ),
            )

        elif direction == "SELL":

            distance = max(
                0.0,

                float(
                    first["low"]
                )
                - float(
                    middle["close"]
                ),

                float(
                    first["low"]
                )
                - float(
                    third["close"]
                ),
            )

        else:
            return 0.0

        return (
            distance
            / reference_range
        )

    # ==============================================================
    # STRUCTURE
    # ==============================================================

    @staticmethod
    def _structure_breaks(
        structure: Dict[str, Any],
        candidate_index: int,
        direction: str,
    ) -> bool:

        bos = structure.get(
            "bos",
            [],
        )

        if not isinstance(
            bos,
            list,
        ):
            return False

        for event in bos:

            if not isinstance(
                event,
                dict,
            ):
                continue

            event_index = event.get(
                "index"
            )

            if not isinstance(
                event_index,
                int,
            ):
                continue

            if (
                event_index
                <= candidate_index
            ):
                continue

            if (
                event.get("direction")
                == direction
            ):
                return True

        return False

    # ==============================================================
    # VOLUME
    # ==============================================================

    @staticmethod
    def _volume_strength(
        candles: Sequence[Dict[str, Any]],
        index: int,
    ) -> Optional[float]:

        if (
            index < 0
            or index >= len(candles)
        ):
            return None

        if "volume" not in candles[index]:
            return None

        try:
            current_volume = float(
                candles[index]["volume"]
            )

        except (
            TypeError,
            ValueError,
        ):
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
                    float(
                        candle["volume"]
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

        if not values:
            return None

        average = (
            sum(values)
            / len(values)
        )

        if average <= 0:
            return None

        ratio = (
            current_volume
            / average
        )

        return round(
            max(
                0.0,
                min(
                    ratio * 50.0,
                    100.0,
                ),
            ),
            2,
        )

    # ==============================================================
    # QUALITY
    # ==============================================================

    @staticmethod
    def _quality_score(
        gap_ratio: float,
        middle_body_ratio: float,
        displacement_strength: float,
        structure_break: bool,
        volume_strength: Optional[float],
    ) -> float:

        score = 0.0

        score += (
            min(
                max(
                    gap_ratio,
                    0.0,
                ),
                1.0,
            )
            * 20.0
        )

        score += (
            min(
                max(
                    middle_body_ratio,
                    0.0,
                ),
                1.0,
            )
            * 20.0
        )

        score += (
            min(
                max(
                    displacement_strength,
                    0.0,
                ),
                2.0,
            )
            / 2.0
            * 40.0
        )

        if structure_break:
            score += 15.0

        if volume_strength is not None:

            score += (
                min(
                    max(
                        volume_strength,
                        0.0,
                    ),
                    100.0,
                )
                * 0.05
            )

        return round(
            min(
                score,
                100.0,
            ),
            2,
        )

    # ==============================================================
    # MITIGATION / INVALIDATION
    # ==============================================================

    def _evaluate_mitigation_and_invalidation(
        self,
        candles: Sequence[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
    ) -> None:

        for gap in gaps:

            start = int(
                gap["created_index"]
            )

            zone_high = float(
                gap["zone"]["high"]
            )

            zone_low = float(
                gap["zone"]["low"]
            )

            direction = gap[
                "direction"
            ]

            zone_range = max(
                zone_high - zone_low,
                0.0,
            )

            touches = 0
            deepest_penetration = 0.0

            invalidated = False
            invalidation_index = None
            invalidation_price = None

            # Only candles AFTER the three-candle
            # FVG formation are allowed to mitigate
            # or invalidate the FVG.
            for index in range(
                start + 1,
                len(candles),
            ):

                candle = candles[index]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )

                close = float(
                    candle["close"]
                )

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
                            min(
                                ratio,
                                1.0,
                            ),
                        )

                # --------------------------------------------------
                # Close-based invalidation
                # --------------------------------------------------

                if (
                    direction == "BUY"
                    and close < zone_low
                ):

                    invalidated = True
                    invalidation_index = index
                    invalidation_price = close
                    break

                if (
                    direction == "SELL"
                    and close > zone_high
                ):

                    invalidated = True
                    invalidation_index = index
                    invalidation_price = close
                    break

            if invalidated:

                gap["valid"] = False

                gap["state"] = (
                    "INVALIDATED"
                )

                gap["invalidation"] = {
                    "invalidated": True,
                    "index": (
                        invalidation_index
                    ),
                    "price": (
                        invalidation_price
                    ),
                    "reason": (
                        "closed beyond far "
                        "FVG boundary"
                    ),
                }

            else:

                gap["valid"] = True

                if touches == 0:

                    state = "FRESH"

                elif (
                    deepest_penetration
                    >= 1.0
                ):

                    state = (
                        "FULLY_MITIGATED"
                    )

                else:

                    state = (
                        "PARTIALLY_MITIGATED"
                    )

                gap["state"] = state

            gap["mitigation"] = {
                "touched": touches > 0,

                "touch_count": touches,

                "penetration_ratio": round(
                    deepest_penetration,
                    4,
                ),

                "state": (
                    gap["state"]
                    if gap["valid"]
                    else "INVALIDATED"
                ),
            }

    # ==============================================================
    # RETESTS
    # ==============================================================

    def _evaluate_retests(
        self,
        candles: Sequence[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
    ) -> None:

        for gap in gaps:

            if not gap["valid"]:
                continue

            zone_high = float(
                gap["zone"]["high"]
            )

            zone_low = float(
                gap["zone"]["low"]
            )

            direction = gap[
                "direction"
            ]

            created_index = int(
                gap["created_index"]
            )

            retests: List[
                Dict[str, Any]
            ] = []

            for index in range(
                created_index + 1,
                len(candles),
            ):

                candle = candles[index]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )

                close = float(
                    candle["close"]
                )

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

            gap["retests"] = retests

    # ==============================================================
    # INSUFFICIENT DATA
    # ==============================================================

    def _insufficient_result(
        self,
        candle_count: int,
    ) -> Dict[str, Any]:

        return {
            "status": (
                "INSUFFICIENT_DATA"
            ),

            "technical_only": True,

            "component": (
                "fair_value_gaps"
            ),

            "candle_count": candle_count,

            "min_gap_ratio": (
                self.min_gap_ratio
            ),

            "min_middle_body_ratio": (
                self.min_middle_body_ratio
            ),

            "min_displacement_ratio": (
                self.min_displacement_ratio
            ),

            "fair_value_gaps": [],

            "fvgs": [],

            "bullish_fvgs": [],

            "bearish_fvgs": [],

            "valid_fvgs": [],

            "fresh_fvgs": [],

            "mitigated_fvgs": [],

            "invalidated_fvgs": [],

            "counts": {
                "total": 0,
                "bullish": 0,
                "bearish": 0,
                "valid": 0,
                "fresh": 0,
                "mitigated": 0,
                "invalidated": 0,
            },

            "last_fvg": None,
        }


# ==============================================================
# CONVENIENCE API
# ==============================================================

def analyze_fvgs(
    candles: Any,
    structure: Optional[
        Dict[str, Any]
    ] = None,
    volume: Optional[Any] = None,
    min_gap_ratio: float = (
        FairValueGaps.DEFAULT_MIN_GAP_RATIO
    ),
    min_middle_body_ratio: float = (
        FairValueGaps.DEFAULT_MIN_MIDDLE_BODY_RATIO
    ),
    min_displacement_ratio: float = (
        FairValueGaps.DEFAULT_MIN_DISPLACEMENT_RATIO
    ),
) -> Dict[str, Any]:

    analyzer = FairValueGaps(
        min_gap_ratio=min_gap_ratio,
        min_middle_body_ratio=(
            min_middle_body_ratio
        ),
        min_displacement_ratio=(
            min_displacement_ratio
        ),
    )

    return analyzer.analyze(
        candles=candles,
        structure=structure,
        volume=volume,
    )


# ==============================================================
# COMPATIBILITY ALIASES
# ==============================================================

FVG = FairValueGaps

FairValueGap = FairValueGaps

analyze_fvg = analyze_fvgs