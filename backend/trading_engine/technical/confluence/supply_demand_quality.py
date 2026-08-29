
"""
BALLY FLOW - Supply / Demand Quality Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module identifies and evaluates supply and demand zones from
OHLC candle data.

The module does NOT:
    - perform fundamental analysis
    - make the final BUY / SELL / NO_TRADE decision
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - override the Decision Engine

REAL-MARKET SUPPLY / DEMAND MODEL
---------------------------------

Demand:
    A meaningful price area where strong buying displacement originates
    and price subsequently moves away from the area.

Supply:
    A meaningful price area where strong selling displacement originates
    and price subsequently moves away from the area.

A zone is NOT considered high quality merely because price moved away
from one candle.

Quality considers:

    1. Base structure
    2. Base candle count
    3. Departure/displacement
    4. Departure strength
    5. Relative range
    6. Impulsive follow-through
    7. Freshness
    8. Retests
    9. Mitigation
    10. Invalidation
    11. Zone width
    12. Optional volume
    13. Proximity to current price

ZONE STATES
-----------

    FRESH
    TESTED
    PARTIALLY_MITIGATED
    FULLY_MITIGATED
    INVALIDATED

IMPORTANT
---------

This module intentionally uses conservative technical logic.

A wick through a zone does not automatically invalidate it.

For demand:
    close below the protected lower boundary invalidates the zone.

For supply:
    close above the protected upper boundary invalidates the zone.

Candles must be ordered:

    oldest -> newest
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class SupplyDemandQuality:
    """
    Technical Supply / Demand zone detector and quality evaluator.
    """

    NAME = "BALLY FLOW Supply Demand Quality"

    DEFAULT_LOOKBACK = 30
    DEFAULT_BASE_CANDLES = 3
    DEFAULT_DEPARTURE_LOOKAHEAD = 3

    MIN_BODY_RATIO = 0.45
    MIN_DISPLACEMENT_RATIO = 1.20

    MAX_BASE_CANDLES = 3
    MAX_ZONE_WIDTH_RATIO = 1.50

    def __init__(
        self,
        lookback: int = DEFAULT_LOOKBACK,
        base_candles: int = DEFAULT_BASE_CANDLES,
        departure_lookahead: int = DEFAULT_DEPARTURE_LOOKAHEAD,
    ) -> None:

        if not isinstance(lookback, int):
            raise TypeError("lookback must be an integer")

        if lookback < 3:
            raise ValueError("lookback must be at least 3")

        if not isinstance(base_candles, int):
            raise TypeError("base_candles must be an integer")

        if base_candles < 1:
            raise ValueError(
                "base_candles must be greater than zero"
            )

        if base_candles > self.MAX_BASE_CANDLES:
            raise ValueError(
                f"base_candles must not exceed "
                f"{self.MAX_BASE_CANDLES}"
            )

        if not isinstance(departure_lookahead, int):
            raise TypeError(
                "departure_lookahead must be an integer"
            )

        if departure_lookahead < 1:
            raise ValueError(
                "departure_lookahead must be greater than zero"
            )

        self.lookback = lookback
        self.base_candles = base_candles
        self.departure_lookahead = departure_lookahead

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
        Analyze Supply / Demand zones.

        Parameters
        ----------
        candles:
            OHLC candle sequence ordered oldest -> newest.

        structure:
            Optional market-structure analysis.

        volume:
            Optional external volume sequence.

        Returns
        -------
        dict
            Standardized technical-only Supply / Demand analysis.
        """

        normalized = self._normalize_candles(candles)

        if volume is not None:
            self._attach_external_volume(
                normalized,
                volume,
            )

        minimum = max(
            self.base_candles
            + self.departure_lookahead
            + 2,
            self.lookback,
        )

        if len(normalized) < minimum:
            return self._insufficient_result(
                len(normalized)
            )

        structure_data = structure or {}

        zones = self._find_zones(
            normalized,
            structure_data,
        )

        self._evaluate_mitigation_and_invalidation(
            normalized,
            zones,
        )

        self._evaluate_retests(
            normalized,
            zones,
        )

        current_price = float(
            normalized[-1]["close"]
        )

        self._evaluate_proximity(
            zones,
            current_price,
        )

        supply = [
            zone
            for zone in zones
            if zone["type"] == "SUPPLY"
        ]

        demand = [
            zone
            for zone in zones
            if zone["type"] == "DEMAND"
        ]

        valid = [
            zone
            for zone in zones
            if zone["valid"]
        ]

        fresh = [
            zone
            for zone in valid
            if zone["state"] == "FRESH"
        ]

        mitigated = [
            zone
            for zone in valid
            if zone["state"]
            in {
                "TESTED",
                "PARTIALLY_MITIGATED",
                "FULLY_MITIGATED",
            }
        ]

        invalidated = [
            zone
            for zone in zones
            if not zone["valid"]
        ]

        high_quality = [
            zone
            for zone in valid
            if zone["quality"]["score"] >= 70.0
        ]

        last_zone = (
            zones[-1]
            if zones
            else None
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "supply_demand_quality",

            "candle_count": len(normalized),
            "lookback": self.lookback,
            "base_candles": self.base_candles,
            "departure_lookahead": (
                self.departure_lookahead
            ),

            "current_price": current_price,

            "zones": zones,

            "supply_zones": supply,
            "demand_zones": demand,

            "valid_zones": valid,
            "fresh_zones": fresh,
            "mitigated_zones": mitigated,
            "invalidated_zones": invalidated,

            "high_quality_zones": high_quality,

            "counts": {
                "total": len(zones),
                "supply": len(supply),
                "demand": len(demand),
                "valid": len(valid),
                "fresh": len(fresh),
                "mitigated": len(mitigated),
                "invalidated": len(invalidated),
                "high_quality": len(high_quality),
            },

            "nearest": self._nearest_zones(
                zones,
                current_price,
            ),

            "last_zone": last_zone,

            "structure_context": {
                "provided": bool(structure_data),
                "used": any(
                    zone["validation"]["structure_break"]
                    for zone in zones
                ),
            },
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
                        item[key] = getattr(
                            candle,
                            key,
                        )

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

        for candle, value in zip(
            candles,
            volumes,
        ):

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

        candle_range = cls._range(candle)

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

        if candle["close"] > candle["open"]:
            return "BULLISH"

        if candle["close"] < candle["open"]:
            return "BEARISH"

        return "NEUTRAL"

    @staticmethod
    def _midpoint(
        candle: Dict[str, Any],
    ) -> float:

        return (
            float(candle["high"])
            + float(candle["low"])
        ) / 2.0

    # ==============================================================
    # ZONE DETECTION
    # ==============================================================

    def _find_zones(
        self,
        candles: Sequence[Dict[str, Any]],
        structure: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        zones: List[Dict[str, Any]] = []

        start = max(
            0,
            len(candles) - self.lookback,
        )

        for index in range(
            start,
            len(candles)
            - self.departure_lookahead,
        ):

            base_end = min(
                index + self.base_candles,
                len(candles),
            )

            base = candles[
                index:base_end
            ]

            if not base:
                continue

            zone = self._evaluate_base(
                candles,
                index,
                base,
                structure,
            )

            if zone is not None:
                zones.append(zone)

        return self._deduplicate_zones(zones)

    def _evaluate_base(
        self,
        candles: Sequence[Dict[str, Any]],
        index: int,
        base: Sequence[Dict[str, Any]],
        structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        base_high = max(
            float(candle["high"])
            for candle in base
        )

        base_low = min(
            float(candle["low"])
            for candle in base
        )

        zone_range = (
            base_high - base_low
        )

        if zone_range <= 0:
            return None

        base_average_range = sum(
            self._range(candle)
            for candle in base
        ) / len(base)

        if base_average_range <= 0:
            return None

        departure = candles[
            index + len(base):
            index
            + len(base)
            + self.departure_lookahead
        ]

        if not departure:
            return None

        bullish_departure = (
            self._bullish_departure(
                base_high,
                base_average_range,
                departure,
            )
        )

        bearish_departure = (
            self._bearish_departure(
                base_low,
                base_average_range,
                departure,
            )
        )

        if not bullish_departure and not bearish_departure:
            return None

        if bullish_departure and bearish_departure:
            return None

        if bullish_departure:
            zone_type = "DEMAND"
            direction = "BUY"
            protected_level = base_low

        else:
            zone_type = "SUPPLY"
            direction = "SELL"
            protected_level = base_high

        departure_strength = (
            self._departure_strength(
                base_high,
                base_low,
                departure,
                direction,
            )
        )

        body_quality = self._base_body_quality(
            base
        )

        volume_strength = self._volume_strength(
            candles,
            index,
            len(base),
        )

        structure_break = self._structure_breaks(
            structure,
            index,
            direction,
        )

        quality_score = self._quality_score(
            departure_strength=departure_strength,
            body_quality=body_quality,
            structure_break=structure_break,
            volume_strength=volume_strength,
            base_size=len(base),
        )

        return {
            "index": index,
            "type": zone_type,
            "direction": direction,

            "zone": {
                "high": base_high,
                "low": base_low,
                "protected_level": protected_level,
                "width": zone_range,
                "midpoint": (
                    base_high + base_low
                ) / 2.0,
            },

            "base": {
                "start_index": index,
                "end_index": (
                    index + len(base) - 1
                ),
                "candle_count": len(base),
                "average_range": round(
                    base_average_range,
                    8,
                ),
                "body_quality": body_quality,
            },

            "departure": {
                "direction": direction,
                "strength": departure_strength,
                "candle_count": len(departure),
            },

            "validation": {
                "displacement": True,
                "departure_strength": (
                    departure_strength
                ),
                "structure_break": (
                    structure_break
                ),
                "volume_strength": (
                    volume_strength
                ),
                "quality_score": quality_score,
            },

            "quality": {
                "score": quality_score,
                "classification": (
                    self._quality_classification(
                        quality_score
                    )
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

            "proximity": {
                "current_price": None,
                "distance": None,
                "distance_ratio": None,
                "location": None,
            },

            "created_index": index,
        }

    # ==============================================================
    # DEPARTURE
    # ==============================================================

    @staticmethod
    def _bullish_departure(
        zone_high: float,
        base_average_range: float,
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        highest_high = max(
            float(candle["high"])
            for candle in future
        )

        highest_close = max(
            float(candle["close"])
            for candle in future
        )

        distance = max(
            highest_high - zone_high,
            highest_close - zone_high,
        )

        return (
            distance
            >= base_average_range
            * SupplyDemandQuality.MIN_DISPLACEMENT_RATIO
        )

    @staticmethod
    def _bearish_departure(
        zone_low: float,
        base_average_range: float,
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        lowest_low = min(
            float(candle["low"])
            for candle in future
        )

        lowest_close = min(
            float(candle["close"])
            for candle in future
        )

        distance = max(
            zone_low - lowest_low,
            zone_low - lowest_close,
        )

        return (
            distance
            >= base_average_range
            * SupplyDemandQuality.MIN_DISPLACEMENT_RATIO
        )

    @staticmethod
    def _departure_strength(
        zone_high: float,
        zone_low: float,
        future: Sequence[Dict[str, Any]],
        direction: str,
    ) -> float:

        zone_range = (
            zone_high - zone_low
        )

        if zone_range <= 0:
            return 0.0

        if direction == "BUY":

            extreme = max(
                float(candle["high"])
                for candle in future
            )

            distance = (
                extreme - zone_high
            )

        else:

            extreme = min(
                float(candle["low"])
                for candle in future
            )

            distance = (
                zone_low - extreme
            )

        ratio = (
            max(distance, 0.0)
            / zone_range
        )

        return round(
            min(
                ratio * 40.0,
                100.0,
            ),
            2,
        )

    # ==============================================================
    # BASE QUALITY
    # ==============================================================

    @classmethod
    def _base_body_quality(
        cls,
        base: Sequence[Dict[str, Any]],
    ) -> float:

        if not base:
            return 0.0

        ratios = [
            cls._body_ratio(candle)
            for candle in base
        ]

        average = (
            sum(ratios)
            / len(ratios)
        )

        return round(
            max(
                0.0,
                min(
                    average * 100.0,
                    100.0,
                ),
            ),
            2,
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

        bos = structure.get("bos", [])

        if not isinstance(bos, list):
            return False

        for event in bos:

            if not isinstance(event, dict):
                continue

            event_index = event.get(
                "index"
            )

            if not isinstance(
                event_index,
                int,
            ):
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
    # VOLUME
    # ==============================================================

    @staticmethod
    def _volume_strength(
        candles: Sequence[Dict[str, Any]],
        index: int,
        base_size: int,
    ) -> Optional[float]:

        end = index + base_size

        values: List[float] = []

        for candle in candles[
            max(0, index - 20):
            index
        ]:

            if "volume" not in candle:
                continue

            try:
                values.append(
                    float(candle["volume"])
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

        current_values: List[float] = []

        for candle in candles[
            index:end
        ]:

            if "volume" not in candle:
                continue

            try:
                current_values.append(
                    float(candle["volume"])
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

        if not current_values:
            return None

        current_average = (
            sum(current_values)
            / len(current_values)
        )

        ratio = (
            current_average
            / average
        )

        return round(
            min(
                max(
                    ratio * 50.0,
                    0.0,
                ),
                100.0,
            ),
            2,
        )

    # ==============================================================
    # QUALITY SCORE
    # ==============================================================

    @staticmethod
    def _quality_score(
        departure_strength: float,
        body_quality: float,
        structure_break: bool,
        volume_strength: Optional[float],
        base_size: int,
    ) -> float:

        score = 0.0

        # Departure is the primary quality factor.
        score += (
            min(
                max(
                    departure_strength,
                    0.0,
                ),
                100.0,
            )
            * 0.50
        )

        # Base characteristics.
        score += (
            min(
                max(
                    body_quality,
                    0.0,
                ),
                100.0,
            )
            * 0.15
        )

        # Structure confirmation.
        if structure_break:
            score += 20.0

        # Optional volume confirmation.
        if volume_strength is not None:
            score += (
                min(
                    max(
                        volume_strength,
                        0.0,
                    ),
                    100.0,
                )
                * 0.10
            )

        # Smaller bases are generally more precise.
        if base_size == 1:
            score += 5.0
        elif base_size == 2:
            score += 3.0

        return round(
            min(score, 100.0),
            2,
        )

    @staticmethod
    def _quality_classification(
        score: float,
    ) -> str:

        if score >= 80.0:
            return "HIGH"

        if score >= 70.0:
            return "GOOD"

        if score >= 50.0:
            return "MODERATE"

        return "WEAK"

    # ==============================================================
    # MITIGATION / INVALIDATION
    # ==============================================================

    def _evaluate_mitigation_and_invalidation(
        self,
        candles: Sequence[Dict[str, Any]],
        zones: List[Dict[str, Any]],
    ) -> None:

        for zone in zones:

            start = zone["created_index"]

            zone_high = float(
                zone["zone"]["high"]
            )

            zone_low = float(
                zone["zone"]["low"]
            )

            direction = zone["direction"]

            zone_range = max(
                zone_high - zone_low,
                0.0,
            )

            touches = 0
            deepest_penetration = 0.0

            invalidated = False
            invalidation_index = None
            invalidation_price = None

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

                # Demand invalidation:
                # close below the lower boundary.
                if direction == "BUY":

                    if close < zone_low:

                        invalidated = True
                        invalidation_index = index
                        invalidation_price = close
                        break

                # Supply invalidation:
                # close above the upper boundary.
                else:

                    if close > zone_high:

                        invalidated = True
                        invalidation_index = index
                        invalidation_price = close
                        break

            if invalidated:

                zone["valid"] = False
                zone["state"] = "INVALIDATED"

                zone["invalidation"] = {
                    "invalidated": True,
                    "index": invalidation_index,
                    "price": invalidation_price,
                    "reason": (
                        "closed beyond protected "
                        "supply/demand boundary"
                    ),
                }

            else:

                zone["valid"] = True

                if touches == 0:
                    state = "FRESH"

                elif deepest_penetration >= 1.0:
                    state = "FULLY_MITIGATED"

                elif touches == 1:
                    state = "TESTED"

                else:
                    state = "PARTIALLY_MITIGATED"

                zone["state"] = state

            zone["mitigation"] = {
                "touched": touches > 0,
                "touch_count": touches,
                "penetration_ratio": round(
                    deepest_penetration,
                    4,
                ),
                "state": (
                    zone["state"]
                    if zone["valid"]
                    else "INVALIDATED"
                ),
            }

    # ==============================================================
    # RETESTS
    # ==============================================================

    def _evaluate_retests(
        self,
        candles: Sequence[Dict[str, Any]],
        zones: List[Dict[str, Any]],
    ) -> None:

        for zone in zones:

            if not zone["valid"]:
                continue

            zone_high = float(
                zone["zone"]["high"]
            )

            zone_low = float(
                zone["zone"]["low"]
            )

            direction = zone["direction"]

            created_index = zone[
                "created_index"
            ]

            retests: List[Dict[str, Any]] = []

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

            zone["retests"] = retests

    # ==============================================================
    # PROXIMITY
    # ==============================================================

    @staticmethod
    def _evaluate_proximity(
        zones: List[Dict[str, Any]],
        current_price: float,
    ) -> None:

        for zone in zones:

            high = float(
                zone["zone"]["high"]
            )

            low = float(
                zone["zone"]["low"]
            )

            width = max(
                high - low,
                0.0,
            )

            if low <= current_price <= high:

                distance = 0.0
                distance_ratio = 0.0
                location = "INSIDE_ZONE"

            elif current_price < low:

                distance = low - current_price

                distance_ratio = (
                    distance / width
                    if width > 0
                    else None
                )

                location = "BELOW_ZONE"

            else:

                distance = (
                    current_price - high
                )

                distance_ratio = (
                    distance / width
                    if width > 0
                    else None
                )

                location = "ABOVE_ZONE"

            zone["proximity"] = {
                "current_price": current_price,
                "distance": round(
                    distance,
                    8,
                ),
                "distance_ratio": (
                    round(
                        distance_ratio,
                        4,
                    )
                    if distance_ratio is not None
                    else None
                ),
                "location": location,
            }

    # ==============================================================
    # NEAREST ZONES
    # ==============================================================

    @staticmethod
    def _nearest_zones(
        zones: Sequence[Dict[str, Any]],
        current_price: float,
    ) -> Dict[str, Any]:

        valid = [
            zone
            for zone in zones
            if zone["valid"]
        ]

        supply = [
            zone
            for zone in valid
            if zone["type"] == "SUPPLY"
        ]

        demand = [
            zone
            for zone in valid
            if zone["type"] == "DEMAND"
        ]

        def distance(
            zone: Dict[str, Any],
        ) -> float:

            high = float(
                zone["zone"]["high"]
            )

            low = float(
                zone["zone"]["low"]
            )

            if low <= current_price <= high:
                return 0.0

            if current_price < low:
                return low - current_price

            return current_price - high

        nearest_supply = (
            min(
                supply,
                key=distance,
            )
            if supply
            else None
        )

        nearest_demand = (
            min(
                demand,
                key=distance,
            )
            if demand
            else None
        )

        return {
            "nearest_supply": nearest_supply,
            "nearest_demand": nearest_demand,
        }

    # ==============================================================
    # DEDUPLICATION
    # ==============================================================

    @staticmethod
    def _deduplicate_zones(
        zones: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        result: List[Dict[str, Any]] = []

        for zone in zones:

            duplicate = False

            for existing in result:

                if (
                    existing["type"]
                    != zone["type"]
                ):
                    continue

                high_a = float(
                    existing["zone"]["high"]
                )

                low_a = float(
                    existing["zone"]["low"]
                )

                high_b = float(
                    zone["zone"]["high"]
                )

                low_b = float(
                    zone["zone"]["low"]
                )

                overlap_high = min(
                    high_a,
                    high_b,
                )

                overlap_low = max(
                    low_a,
                    low_b,
                )

                overlap = max(
                    overlap_high
                    - overlap_low,
                    0.0,
                )

                smaller = min(
                    high_a - low_a,
                    high_b - low_b,
                )

                if (
                    smaller > 0
                    and overlap / smaller >= 0.80
                ):
                    duplicate = True

                    if (
                        zone["quality"]["score"]
                        > existing["quality"]["score"]
                    ):
                        result.remove(existing)
                        result.append(zone)

                    break

            if not duplicate:
                result.append(zone)

        result.sort(
            key=lambda item: item["created_index"]
        )

        return result

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
            "component": "supply_demand_quality",

            "candle_count": candle_count,
            "lookback": self.lookback,
            "base_candles": self.base_candles,
            "departure_lookahead": (
                self.departure_lookahead
            ),

            "current_price": None,

            "zones": [],
            "supply_zones": [],
            "demand_zones": [],
            "valid_zones": [],
            "fresh_zones": [],
            "mitigated_zones": [],
            "invalidated_zones": [],
            "high_quality_zones": [],

            "counts": {
                "total": 0,
                "supply": 0,
                "demand": 0,
                "valid": 0,
                "fresh": 0,
                "mitigated": 0,
                "invalidated": 0,
                "high_quality": 0,
            },

            "nearest": {
                "nearest_supply": None,
                "nearest_demand": None,
            },

            "last_zone": None,

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_supply_demand_quality(
    candles: Any,
    structure: Optional[Dict[str, Any]] = None,
    volume: Optional[Any] = None,
    lookback: int = (
        SupplyDemandQuality.DEFAULT_LOOKBACK
    ),
    base_candles: int = (
        SupplyDemandQuality.DEFAULT_BASE_CANDLES
    ),
    departure_lookahead: int = (
        SupplyDemandQuality.DEFAULT_DEPARTURE_LOOKAHEAD
    ),
) -> Dict[str, Any]:

    analyzer = SupplyDemandQuality(
        lookback=lookback,
        base_candles=base_candles,
        departure_lookahead=departure_lookahead,
    )

    return analyzer.analyze(
        candles=candles,
        structure=structure,
        volume=volume,
    )


# ==================================================================
# COMPATIBILITY ALIAS
# ==================================================================

SupplyDemand = SupplyDemandQuality
