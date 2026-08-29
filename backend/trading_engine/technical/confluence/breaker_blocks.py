
"""
BALLY FLOW - Technical Breaker Block Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module identifies and evaluates institutional-style Breaker Blocks
from OHLC candle data.

A breaker block is not simply a broken support/resistance level.

In SMC/ICT-style market analysis, a breaker generally develops when:

    1. A meaningful opposing order-block structure exists.
    2. Price violates that structure.
    3. The violation is confirmed by a meaningful close/displacement.
    4. The former order-block area subsequently becomes a potential
       opposite-side reaction zone.
    5. Price may later retest that flipped zone.

The detector therefore evaluates:

    - origin candle
    - original order-block direction
    - structural failure
    - displacement
    - break confirmation
    - zone boundaries
    - protected boundary
    - retests
    - mitigation
    - invalidation
    - freshness
    - quality
    - optional volume

TECHNICAL ONLY
--------------

This module does NOT:

    - perform fundamental analysis
    - perform hybrid decision-making
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - generate the final BUY / SELL / NO_TRADE decision

INPUT
-----

Candles may be supplied as dictionaries:

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

Optional fields:

    volume
    tick_volume
    time
    timestamp

Candles must be ordered oldest -> newest.

BREAKER LOGIC
-------------

Bullish breaker:

    A prior bearish/order-block area is broken to the upside.
    The failed bearish zone may subsequently act as support.

Bearish breaker:

    A prior bullish/order-block area is broken to the downside.
    The failed bullish zone may subsequently act as resistance.

IMPORTANT
---------

A wick through the zone alone does not automatically create a breaker.

The implementation requires a confirmed close beyond the protected
boundary and meaningful displacement.

A later retest is recorded separately and does not need to occur for
the breaker itself to be identified.

RESULT CONTRACT
---------------

Every result contains:

    "technical_only": True

The public result provides:

    breaker_blocks
    bullish_breaker_blocks
    bearish_breaker_blocks
    valid_breaker_blocks
    fresh_breaker_blocks
    mitigated_breaker_blocks
    invalidated_breaker_blocks
    counts
    last_breaker
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class BreakerBlocks:
    """
    Technical Breaker Block detector and evaluator.
    """

    NAME = "BALLY FLOW Breaker Blocks"

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
        order_blocks: Optional[Any] = None,
        volume: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Analyze Breaker Blocks from candle data.

        Parameters
        ----------
        candles:
            OHLC candle sequence.

        structure:
            Optional MarketStructure output.

        order_blocks:
            Optional OrderBlocks analysis output.

        volume:
            Optional external volume sequence.

        Returns
        -------
        dict
            Standardized technical-only Breaker Block analysis.
        """

        normalized = self._normalize_candles(candles)

        if volume is not None:
            self._attach_external_volume(
                normalized,
                volume,
            )

        minimum = max(
            self.lookback * 2 + 3,
            self.displacement_lookahead + 3,
        )

        if len(normalized) < minimum:
            return self._insufficient_result(
                len(normalized)
            )

        structure_data = structure or {}

        source_blocks = self._normalize_order_blocks(
            order_blocks
        )

        candidates = self._find_candidates(
            normalized,
            source_blocks,
        )

        breaker_blocks: List[Dict[str, Any]] = []

        for candidate in candidates:

            breaker = self._evaluate_candidate(
                normalized,
                candidate,
                structure_data,
            )

            if breaker is not None:
                breaker_blocks.append(
                    breaker
                )

        self._evaluate_retests(
            normalized,
            breaker_blocks,
        )

        self._evaluate_mitigation_and_invalidation(
            normalized,
            breaker_blocks,
        )

        bullish = [
            block
            for block in breaker_blocks
            if block["direction"] == "BUY"
        ]

        bearish = [
            block
            for block in breaker_blocks
            if block["direction"] == "SELL"
        ]

        valid = [
            block
            for block in breaker_blocks
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
            for block in breaker_blocks
            if not block["valid"]
        ]

        last_breaker = (
            breaker_blocks[-1]
            if breaker_blocks
            else None
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "breaker_blocks",

            "candle_count": len(normalized),
            "lookback": self.lookback,
            "displacement_lookahead": (
                self.displacement_lookahead
            ),

            "breaker_blocks": breaker_blocks,

            "bullish_breaker_blocks": bullish,
            "bearish_breaker_blocks": bearish,

            "valid_breaker_blocks": valid,
            "fresh_breaker_blocks": fresh,
            "mitigated_breaker_blocks": mitigated,
            "invalidated_breaker_blocks": invalidated,

            "counts": {
                "total": len(breaker_blocks),
                "bullish": len(bullish),
                "bearish": len(bearish),
                "valid": len(valid),
                "fresh": len(fresh),
                "mitigated": len(mitigated),
                "invalidated": len(invalidated),
            },

            "last_breaker": last_breaker,
        }

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
                    open_price = candle["open"]
                    high = candle["high"]
                    low = candle["low"]
                    close = candle["close"]
                except KeyError as exc:
                    raise ValueError(
                        f"candle {index} is missing "
                        f"OHLC field: {exc}"
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
                            getattr(
                                candle,
                                "open",
                            )
                        ),
                        "high": float(
                            getattr(
                                candle,
                                "high",
                            )
                        ),
                        "low": float(
                            getattr(
                                candle,
                                "low",
                            )
                        ),
                        "close": float(
                            getattr(
                                candle,
                                "close",
                            )
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
                    if hasattr(candle, key):
                        item[key] = getattr(
                            candle,
                            key,
                        )

            if item["high"] < item["low"]:
                raise ValueError(
                    f"candle {index} has high "
                    "below low"
                )

            if item["high"] < item["open"]:
                raise ValueError(
                    f"candle {index} has high "
                    "below open"
                )

            if item["high"] < item["close"]:
                raise ValueError(
                    f"candle {index} has high "
                    "below close"
                )

            if item["low"] > item["open"]:
                raise ValueError(
                    f"candle {index} has low "
                    "above open"
                )

            if item["low"] > item["close"]:
                raise ValueError(
                    f"candle {index} has low "
                    "above close"
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
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "volume contains non-numeric data"
                ) from exc

    # ==============================================================
    # ORDER BLOCK INPUT
    # ==============================================================

    @staticmethod
    def _normalize_order_blocks(
        order_blocks: Any,
    ) -> List[Dict[str, Any]]:

        if order_blocks is None:
            return []

        if isinstance(
            order_blocks,
            dict,
        ):

            if "order_blocks" in order_blocks:
                order_blocks = (
                    order_blocks[
                        "order_blocks"
                    ]
                )

            elif "valid_order_blocks" in order_blocks:
                order_blocks = (
                    order_blocks[
                        "valid_order_blocks"
                    ]
                )

            else:
                return []

        try:
            sequence = list(
                order_blocks
            )
        except TypeError:
            return []

        result: List[Dict[str, Any]] = []

        for block in sequence:

            if not isinstance(
                block,
                dict,
            ):
                continue

            if "zone" not in block:
                continue

            if "direction" not in block:
                continue

            result.append(block)

        return result

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
        order_blocks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        candidates: List[Dict[str, Any]] = []

        # ----------------------------------------------------------
        # Preferred path:
        # Use actual Order Block output when supplied.
        # ----------------------------------------------------------

        for block in order_blocks:

            if not block.get(
                "valid",
                True,
            ):
                # A source OB that is already invalidated may be
                # exactly what creates a breaker, so it is retained.
                pass

            direction = block.get(
                "direction"
            )

            if direction not in {
                "BUY",
                "SELL",
            }:
                continue

            zone = block.get(
                "zone"
            )

            if not isinstance(
                zone,
                dict,
            ):
                continue

            try:
                zone_high = float(
                    zone["high"]
                )
                zone_low = float(
                    zone["low"]
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            try:
                created_index = int(
                    block.get(
                        "created_index",
                        block.get(
                            "index",
                            -1,
                        ),
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if created_index < 0:
                continue

            if created_index >= len(
                candles
            ):
                continue

            candidates.append(
                {
                    "source": "ORDER_BLOCK",
                    "index": created_index,
                    "original_direction": direction,
                    "zone_high": zone_high,
                    "zone_low": zone_low,
                    "source_block": block,
                }
            )

        # ----------------------------------------------------------
        # Fallback path:
        # Identify potential order-block origin candles directly.
        #
        # This keeps BreakerBlocks independently usable while the
        # TechnicalConfluence layer can still pass real OB output.
        # ----------------------------------------------------------

        if not candidates:

            for index in range(
                0,
                len(candles)
                - self.displacement_lookahead,
            ):

                candle = candles[index]

                body_ratio = (
                    self._body_ratio(candle)
                )

                if body_ratio < self.MIN_BODY_RATIO:
                    continue

                direction = (
                    self._direction(candle)
                )

                if direction == "BEARISH":

                    if self._bullish_displacement(
                        candle,
                        candles[
                            index + 1:
                            index + 1
                            + self.displacement_lookahead
                        ],
                    ):

                        candidates.append(
                            {
                                "source": "CANDLE",
                                "index": index,
                                "original_direction": "BUY",
                                "zone_high": float(
                                    candle["high"]
                                ),
                                "zone_low": float(
                                    candle["low"]
                                ),
                                "source_block": None,
                            }
                        )

                elif direction == "BULLISH":

                    if self._bearish_displacement(
                        candle,
                        candles[
                            index + 1:
                            index + 1
                            + self.displacement_lookahead
                        ],
                    ):

                        candidates.append(
                            {
                                "source": "CANDLE",
                                "index": index,
                                "original_direction": "SELL",
                                "zone_high": float(
                                    candle["high"]
                                ),
                                "zone_low": float(
                                    candle["low"]
                                ),
                                "source_block": None,
                            }
                        )

        return candidates

    # ==============================================================
    # BREAKER EVALUATION
    # ==============================================================

    def _evaluate_candidate(
        self,
        candles: Sequence[Dict[str, Any]],
        candidate: Dict[str, Any],
        structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        origin_index = candidate["index"]

        zone_high = float(
            candidate["zone_high"]
        )

        zone_low = float(
            candidate["zone_low"]
        )

        original_direction = (
            candidate["original_direction"]
        )

        if zone_high <= zone_low:
            return None

        # ----------------------------------------------------------
        # A failed BUY order block becomes a bearish breaker.
        # A failed SELL order block becomes a bullish breaker.
        # ----------------------------------------------------------

        if original_direction == "BUY":

            breaker_direction = "SELL"
            protected_level = zone_high

        elif original_direction == "SELL":

            breaker_direction = "BUY"
            protected_level = zone_low

        else:
            return None

        break_index = self._find_confirmed_break(
            candles=candles,
            start_index=origin_index + 1,
            zone_high=zone_high,
            zone_low=zone_low,
            original_direction=original_direction,
            breaker_direction=breaker_direction,
        )

        if break_index is None:
            return None

        break_candle = candles[
            break_index
        ]

        displacement = self._break_displacement(
            candles=candles,
            origin_index=origin_index,
            break_index=break_index,
            zone_high=zone_high,
            zone_low=zone_low,
            direction=breaker_direction,
        )

        if displacement <= 0:
            return None

        displacement_strength = (
            self._displacement_strength(
                candles=candles,
                origin_index=origin_index,
                break_index=break_index,
                zone_high=zone_high,
                zone_low=zone_low,
                direction=breaker_direction,
            )
        )

        structure_break = (
            self._structure_breaks(
                structure=structure,
                break_index=break_index,
                direction=breaker_direction,
            )
        )

        body_ratio = (
            self._body_ratio(
                break_candle
            )
        )

        volume_strength = (
            self._volume_strength(
                candles,
                break_index,
            )
        )

        quality_score = (
            self._quality_score(
                body_ratio=body_ratio,
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

        origin_candle = candles[
            origin_index
        ]

        return {
            "index": break_index,

            "direction": breaker_direction,

            "type": (
                "BULLISH_BREAKER_BLOCK"
                if breaker_direction == "BUY"
                else "BEARISH_BREAKER_BLOCK"
            ),

            "source": candidate["source"],

            "origin": {
                "index": origin_index,
                "open": origin_candle[
                    "open"
                ],
                "high": origin_candle[
                    "high"
                ],
                "low": origin_candle[
                    "low"
                ],
                "close": origin_candle[
                    "close"
                ],
                "direction": (
                    self._direction(
                        origin_candle
                    )
                ),
                "original_order_block_direction": (
                    original_direction
                ),
                "body_ratio": (
                    self._body_ratio(
                        origin_candle
                    )
                ),
            },

            "break": {
                "index": break_index,
                "open": break_candle[
                    "open"
                ],
                "high": break_candle[
                    "high"
                ],
                "low": break_candle[
                    "low"
                ],
                "close": break_candle[
                    "close"
                ],
                "displacement": displacement,
                "displacement_strength": (
                    displacement_strength
                ),
                "structure_break": (
                    structure_break
                ),
            },

            "zone": {
                "high": zone_high,
                "low": zone_low,
                "protected_level": (
                    protected_level
                ),
            },

            "validation": {
                "confirmed_break": True,
                "displacement": True,
                "displacement_strength": (
                    displacement_strength
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

            "created_index": break_index,
            "source_index": origin_index,
        }

    # ==============================================================
    # CONFIRMED BREAK
    # ==============================================================

    def _find_confirmed_break(
        self,
        candles: Sequence[Dict[str, Any]],
        start_index: int,
        zone_high: float,
        zone_low: float,
        original_direction: str,
        breaker_direction: str,
    ) -> Optional[int]:

        for index in range(
            start_index,
            len(candles),
        ):

            candle = candles[index]

            close = float(
                candle["close"]
            )

            body_ratio = (
                self._body_ratio(candle)
            )

            # Weak doji-like candles should not be treated as a
            # strong breaker confirmation.
            if body_ratio < self.MIN_BODY_RATIO:
                continue

            if breaker_direction == "SELL":

                # Former bullish OB failed when price closed below
                # its protected lower boundary.
                if close <= zone_low:

                    if self._confirmed_directional_move(
                        candles,
                        index,
                        "SELL",
                        zone_low,
                        zone_high,
                    ):
                        return index

            else:

                # Former bearish OB failed when price closed above
                # its protected upper boundary.
                if close >= zone_high:

                    if self._confirmed_directional_move(
                        candles,
                        index,
                        "BUY",
                        zone_low,
                        zone_high,
                    ):
                        return index

        return None

    # ==============================================================
    # DIRECTIONAL CONFIRMATION
    # ==============================================================

    def _confirmed_directional_move(
        self,
        candles: Sequence[Dict[str, Any]],
        index: int,
        direction: str,
        zone_low: float,
        zone_high: float,
    ) -> bool:

        candle = candles[index]

        candle_range = self._range(
            candle
        )

        if candle_range <= 0:
            return False

        body_ratio = (
            self._body_ratio(candle)
        )

        if body_ratio < self.MIN_BODY_RATIO:
            return False

        if direction == "BUY":

            distance = (
                float(candle["close"])
                - zone_high
            )

        else:

            distance = (
                zone_low
                - float(candle["close"])
            )

        return (
            distance
            >= candle_range
            * 0.25
        )

    # ==============================================================
    # DISPLACEMENT
    # ==============================================================

    def _bullish_displacement(
        self,
        origin: Dict[str, Any],
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        origin_range = self._range(
            origin
        )

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

        distance = max(
            highest_close
            - float(origin["high"]),
            highest_high
            - float(origin["high"]),
        )

        return (
            distance
            >= origin_range
            * self.MIN_DISPLACEMENT_RATIO
        )

    def _bearish_displacement(
        self,
        origin: Dict[str, Any],
        future: Sequence[Dict[str, Any]],
    ) -> bool:

        origin_range = self._range(
            origin
        )

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

        distance = max(
            float(origin["low"])
            - lowest_close,
            float(origin["low"])
            - lowest_low,
        )

        return (
            distance
            >= origin_range
            * self.MIN_DISPLACEMENT_RATIO
        )

    def _break_displacement(
        self,
        candles: Sequence[Dict[str, Any]],
        origin_index: int,
        break_index: int,
        zone_high: float,
        zone_low: float,
        direction: str,
    ) -> float:

        if break_index < 0:
            return 0.0

        candle = candles[
            break_index
        ]

        if direction == "BUY":

            return max(
                0.0,
                float(candle["close"])
                - zone_high,
                float(candle["high"])
                - zone_high,
            )

        return max(
            0.0,
            zone_low
            - float(candle["close"]),
            zone_low
            - float(candle["low"]),
        )

    def _displacement_strength(
        self,
        candles: Sequence[Dict[str, Any]],
        origin_index: int,
        break_index: int,
        zone_high: float,
        zone_low: float,
        direction: str,
    ) -> float:

        origin = candles[
            origin_index
        ]

        origin_range = self._range(
            origin
        )

        if origin_range <= 0:
            return 0.0

        distance = self._break_displacement(
            candles=candles,
            origin_index=origin_index,
            break_index=break_index,
            zone_high=zone_high,
            zone_low=zone_low,
            direction=direction,
        )

        ratio = (
            distance
            / origin_range
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
    # STRUCTURAL RELATIONSHIP
    # ==============================================================

    @staticmethod
    def _structure_breaks(
        structure: Dict[str, Any],
        break_index: int,
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

            if event_index < break_index:
                continue

            event_direction = event.get(
                "direction"
            )

            if (
                direction == "BUY"
                and event_direction == "BUY"
            ):
                return True

            if (
                direction == "SELL"
                and event_direction == "SELL"
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

        if index < 0:
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
        body_ratio: float,
        displacement_strength: float,
        structure_break: bool,
        volume_strength: Optional[float],
    ) -> float:

        score = 0.0

        score += (
            min(
                max(
                    body_ratio,
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
                100.0,
            )
            * 0.50
        )

        if structure_break:
            score += 20.0

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

        return round(
            min(score, 100.0),
            2,
        )

    # ==============================================================
    # RETESTS
    # ==============================================================

    def _evaluate_retests(
        self,
        candles: Sequence[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
    ) -> None:

        for block in blocks:

            zone_high = float(
                block["zone"]["high"]
            )

            zone_low = float(
                block["zone"]["low"]
            )

            direction = block[
                "direction"
            ]

            created_index = int(
                block["created_index"]
            )

            retests: List[
                Dict[str, Any]
            ] = []

            for index in range(
                created_index + 1,
                len(candles),
            ):

                candle = candles[
                    index
                ]

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

                    held = (
                        close >= zone_low
                    )

                else:

                    rejection = (
                        close < zone_low
                    )

                    held = (
                        close <= zone_high
                    )

                retests.append(
                    {
                        "index": index,
                        "high": high,
                        "low": low,
                        "close": close,
                        "rejection": rejection,
                        "held": held,
                    }
                )

            block["retests"] = retests

    # ==============================================================
    # MITIGATION / INVALIDATION
    # ==============================================================

    def _evaluate_mitigation_and_invalidation(
        self,
        candles: Sequence[Dict[str, Any]],
        blocks: List[Dict[str, Any]],
    ) -> None:

        for block in blocks:

            start = int(
                block["created_index"]
            )

            zone_high = float(
                block["zone"]["high"]
            )

            zone_low = float(
                block["zone"]["low"]
            )

            direction = block[
                "direction"
            ]

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

                candle = candles[
                    index
                ]

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
                # Breaker invalidation is based on a CLOSE beyond
                # the protected opposite boundary.
                #
                # Wick penetration alone does not invalidate.
                # --------------------------------------------------

                if direction == "BUY":

                    if close < zone_low:

                        invalidated = True
                        invalidation_index = (
                            index
                        )
                        invalidation_price = (
                            close
                        )
                        break

                else:

                    if close > zone_high:

                        invalidated = True
                        invalidation_index = (
                            index
                        )
                        invalidation_price = (
                            close
                        )
                        break

            if invalidated:

                block["valid"] = False
                block["state"] = (
                    "INVALIDATED"
                )

                block["invalidation"] = {
                    "invalidated": True,
                    "index": (
                        invalidation_index
                    ),
                    "price": (
                        invalidation_price
                    ),
                    "reason": (
                        "closed beyond the "
                        "protected breaker "
                        "boundary"
                    ),
                }

            else:

                block["valid"] = True

                if touches == 0:

                    state = "FRESH"

                elif deepest_penetration >= 1.0:

                    state = (
                        "FULLY_MITIGATED"
                    )

                else:

                    state = (
                        "PARTIALLY_MITIGATED"
                    )

                block["state"] = state

            block["mitigation"] = {
                "touched": touches > 0,
                "touch_count": touches,
                "penetration_ratio": round(
                    deepest_penetration,
                    4,
                ),
                "state": (
                    block["state"]
                    if block["valid"]
                    else "INVALIDATED"
                ),
            }

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
            "component": "breaker_blocks",

            "candle_count": candle_count,

            "lookback": self.lookback,

            "displacement_lookahead": (
                self.displacement_lookahead
            ),

            "min_body_ratio": (
                self.MIN_BODY_RATIO
            ),

            "min_displacement_ratio": (
                self.MIN_DISPLACEMENT_RATIO
            ),

            "breaker_blocks": [],

            "bullish_breaker_blocks": [],
            "bearish_breaker_blocks": [],

            "valid_breaker_blocks": [],
            "fresh_breaker_blocks": [],
            "mitigated_breaker_blocks": [],
            "invalidated_breaker_blocks": [],

            "counts": {
                "total": 0,
                "bullish": 0,
                "bearish": 0,
                "valid": 0,
                "fresh": 0,
                "mitigated": 0,
                "invalidated": 0,
            },

            "last_breaker": None,
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_breaker_blocks(
    candles: Any,
    structure: Optional[
        Dict[str, Any]
    ] = None,
    order_blocks: Optional[Any] = None,
    volume: Optional[Any] = None,
    lookback: int = (
        BreakerBlocks.DEFAULT_LOOKBACK
    ),
    displacement_lookahead: int = (
        BreakerBlocks.DEFAULT_DISPLACEMENT_LOOKAHEAD
    ),
) -> Dict[str, Any]:

    analyzer = BreakerBlocks(
        lookback=lookback,
        displacement_lookahead=(
            displacement_lookahead
        ),
    )

    return analyzer.analyze(
        candles=candles,
        structure=structure,
        order_blocks=order_blocks,
        volume=volume,
    )


# ==================================================================
# COMPATIBILITY ALIASES
# ==================================================================

BreakerBlock = BreakerBlocks
