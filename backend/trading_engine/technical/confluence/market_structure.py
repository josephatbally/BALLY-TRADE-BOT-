
"""
BALLY FLOW - Market Structure Analysis
======================================

Strict technical-analysis component.

This module is responsible ONLY for identifying market structure.

It does NOT:
    - perform fundamental analysis
    - perform hybrid decision-making
    - execute trades
    - place MT5 orders
    - calculate position size
    - manage risk
    - generate trade plans

Market structure concepts supported:
    - Confirmed swing highs
    - Confirmed swing lows
    - Higher High (HH)
    - Higher Low (HL)
    - Lower High (LH)
    - Lower Low (LL)
    - Equal High (EQH)
    - Equal Low (EQL)
    - Bullish BOS
    - Bearish BOS
    - Bullish CHoCH
    - Bearish CHoCH

Important implementation rules:
    1. Candles must be ordered oldest -> newest.
    2. Swing points require candles on both sides.
    3. Structure breaks are confirmed by candle CLOSE.
    4. A wick through a level is not a confirmed break.
    5. Structure is processed chronologically.
    6. BOS represents continuation of established structure.
    7. CHoCH represents a confirmed break against established structure.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class MarketStructure:
    """
    Technical market-structure analyzer for BALLY FLOW.

    The analyzer works from OHLC candle data and produces structural
    information without making trading decisions.

    Default swing lookback:
        2 candles on each side.

    Example:

        MarketStructure().analyze(candles)

    Public result contains:

        status
        technical_only
        component
        candle_count
        lookback
        bias
        current_structure
        swing_highs
        swing_lows
        classifications
        bos
        choch
        last_event
    """

    NAME = "BALLY FLOW Market Structure"

    DEFAULT_LOOKBACK = 2

    # Small tolerance for floating-point equality.
    PRICE_EPSILON = 1e-10

    def __init__(self, lookback: int = DEFAULT_LOOKBACK) -> None:
        if not isinstance(lookback, int):
            raise TypeError("lookback must be an integer")

        if lookback < 1:
            raise ValueError("lookback must be greater than zero")

        self.lookback = lookback

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze(
        self,
        candles: Any,
    ) -> Dict[str, Any]:
        """
        Analyze market structure from OHLC candles.

        Candles must be ordered:

            oldest -> newest

        Supported candle forms:

            {
                "open": 123.0,
                "high": 125.0,
                "low": 121.0,
                "close": 124.0,
            }

        or objects exposing:

            .open
            .high
            .low
            .close
        """

        normalized = self._normalize_candles(candles)

        minimum_candles = self.lookback * 2 + 3

        if len(normalized) < minimum_candles:
            return self._insufficient_result(len(normalized))

        swings = self._detect_swings(normalized)

        classifications = self._classify_swings(swings)

        bias = self._determine_bias(classifications)

        break_events = self._detect_structure_breaks(
            normalized,
            swings,
            classifications,
        )

        # A confirmed structural event can update the effective bias.
        final_bias = self._determine_final_bias(
            classifications=classifications,
            break_events=break_events,
            initial_bias=bias,
        )

        current_structure = self._current_structure(
            classifications
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "market_structure",
            "candle_count": len(normalized),
            "lookback": self.lookback,
            "bias": final_bias,
            "initial_bias": bias,
            "current_structure": current_structure,
            "swing_highs": swings["highs"],
            "swing_lows": swings["lows"],
            "classifications": classifications,
            "bos": break_events["bos"],
            "choch": break_events["choch"],
            "last_event": break_events["last_event"],
        }

    # ==================================================================
    # CANDLE NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize_candles(
        candles: Any,
    ) -> List[Dict[str, float]]:
        """
        Normalize supported candle representations into dictionaries.
        """

        if candles is None:
            raise ValueError("candles are required")

        # Allow:
        #
        # {
        #     "candles": [...]
        # }
        #
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

        normalized: List[Dict[str, float]] = []

        for index, candle in enumerate(sequence):
            normalized.append(
                MarketStructure._extract_ohlc(
                    candle,
                    index,
                )
            )

        return normalized

    @staticmethod
    def _extract_ohlc(
        candle: Any,
        index: int,
    ) -> Dict[str, float]:
        """
        Extract and validate OHLC values.
        """

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

        else:
            try:
                open_price = getattr(candle, "open")
                high = getattr(candle, "high")
                low = getattr(candle, "low")
                close = getattr(candle, "close")
            except AttributeError as exc:
                raise ValueError(
                    f"candle {index} does not expose OHLC fields"
                ) from exc

        try:
            values = {
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
            }
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"candle {index} contains non-numeric OHLC data"
            ) from exc

        if values["high"] < values["low"]:
            raise ValueError(
                f"candle {index} has high below low"
            )

        return values

    # ==================================================================
    # SWING DETECTION
    # ==================================================================

    def _detect_swings(
        self,
        candles: Sequence[Dict[str, float]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect confirmed swing highs and lows.

        A swing is confirmed only when the required number of candles
        exists on both sides.

        Swing high:

            current high > left highs
            current high >= right highs

        Swing low:

            current low < left lows
            current low <= right lows

        This asymmetric equality handling prevents excessive duplicate
        swings while still allowing equal-level liquidity structures.
        """

        highs: List[Dict[str, Any]] = []
        lows: List[Dict[str, Any]] = []

        n = len(candles)
        lb = self.lookback

        for index in range(lb, n - lb):
            current = candles[index]

            left = candles[index - lb:index]

            right = candles[
                index + 1:index + lb + 1
            ]

            left_highs = [
                candle["high"]
                for candle in left
            ]

            right_highs = [
                candle["high"]
                for candle in right
            ]

            left_lows = [
                candle["low"]
                for candle in left
            ]

            right_lows = [
                candle["low"]
                for candle in right
            ]

            current_high = current["high"]
            current_low = current["low"]

            is_swing_high = (
                current_high > max(left_highs)
                and current_high >= max(right_highs)
            )

            is_swing_low = (
                current_low < min(left_lows)
                and current_low <= min(right_lows)
            )

            if is_swing_high:
                highs.append(
                    {
                        "index": index,
                        "price": current_high,
                        "type": "swing_high",
                    }
                )

            if is_swing_low:
                lows.append(
                    {
                        "index": index,
                        "price": current_low,
                        "type": "swing_low",
                    }
                )

        return {
            "highs": highs,
            "lows": lows,
        }

    # ==================================================================
    # STRUCTURAL CLASSIFICATION
    # ==================================================================

    @classmethod
    def _prices_equal(
        cls,
        first: float,
        second: float,
    ) -> bool:
        """
        Floating-point safe equality check.
        """

        return abs(first - second) <= cls.PRICE_EPSILON

    @classmethod
    def _classify_swings(
        cls,
        swings: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Classify swing points chronologically.

        Highs are compared only with previous highs.

        Lows are compared only with previous lows.

        High labels:
            H
            HH
            LH
            EQH

        Low labels:
            L
            HL
            LL
            EQL
        """

        classifications: List[Dict[str, Any]] = []

        previous_high: Optional[float] = None
        previous_low: Optional[float] = None

        combined = [
            {
                **item,
                "side": "high",
            }
            for item in swings["highs"]
        ]

        combined.extend(
            {
                **item,
                "side": "low",
            }
            for item in swings["lows"]
        )

        combined.sort(
            key=lambda item: item["index"]
        )

        for item in combined:
            price = float(item["price"])

            if item["side"] == "high":

                if previous_high is None:
                    label = "H"

                elif cls._prices_equal(
                    price,
                    previous_high,
                ):
                    label = "EQH"

                elif price > previous_high:
                    label = "HH"

                else:
                    label = "LH"

                previous_high = price

            else:

                if previous_low is None:
                    label = "L"

                elif cls._prices_equal(
                    price,
                    previous_low,
                ):
                    label = "EQL"

                elif price > previous_low:
                    label = "HL"

                else:
                    label = "LL"

                previous_low = price

            classifications.append(
                {
                    "index": item["index"],
                    "price": price,
                    "side": item["side"],
                    "label": label,
                }
            )

        return classifications

    # ==================================================================
    # STRUCTURAL BIAS
    # ==================================================================

    @staticmethod
    def _determine_bias(
        classifications: Sequence[Dict[str, Any]],
    ) -> str:
        """
        Determine structural bias from confirmed swing classifications.

        HH + HL -> bullish pressure
        LH + LL -> bearish pressure

        If neither side has structural dominance:

            RANGE
        """

        bullish_score = 0
        bearish_score = 0

        for item in classifications:
            label = item["label"]

            if label in ("HH", "HL"):
                bullish_score += 1

            elif label in ("LH", "LL"):
                bearish_score += 1

        if bullish_score > bearish_score:
            return "BULLISH"

        if bearish_score > bullish_score:
            return "BEARISH"

        return "RANGE"

    # ==================================================================
    # BOS / CHoCH
    # ==================================================================

    def _detect_structure_breaks(
        self,
        candles: Sequence[Dict[str, float]],
        swings: Dict[str, List[Dict[str, Any]]],
        classifications: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Detect confirmed BOS and CHoCH chronologically.

        Critical rules:

            - Only candle CLOSE confirms a break.
            - A wick does not confirm a break.
            - A level can only be broken after its swing exists.
            - Levels are processed in chronological order.
            - Bullish continuation = bullish BOS.
            - Bearish continuation = bearish BOS.
            - Opposite-direction structural break = CHoCH.

        The active structural bias evolves as confirmed breaks occur.
        """

        bos: List[Dict[str, Any]] = []
        choch: List[Dict[str, Any]] = []

        high_swings = list(swings["highs"])
        low_swings = list(swings["lows"])

        # ------------------------------------------------------------------
        # Build chronological swing stream.
        # ------------------------------------------------------------------

        swing_stream: List[Dict[str, Any]] = []

        for swing in high_swings:
            swing_stream.append(
                {
                    **swing,
                    "side": "high",
                }
            )

        for swing in low_swings:
            swing_stream.append(
                {
                    **swing,
                    "side": "low",
                }
            )

        swing_stream.sort(
            key=lambda item: item["index"]
        )

        if not swing_stream:
            return {
                "bos": [],
                "choch": [],
                "last_event": None,
            }

        # ------------------------------------------------------------------
        # Initial structural direction.
        # ------------------------------------------------------------------

        current_bias = self._initial_direction(
            classifications
        )

        active_high: Optional[Dict[str, Any]] = None
        active_low: Optional[Dict[str, Any]] = None

        # Index used to introduce swings only once they become known.
        swing_cursor = 0

        # Prevent the same level from generating multiple events.
        broken_high_indices: set[int] = set()
        broken_low_indices: set[int] = set()

        # ------------------------------------------------------------------
        # Process every CLOSED candle chronologically.
        # ------------------------------------------------------------------

        for candle_index, candle in enumerate(candles):

            # --------------------------------------------------------------
            # Add all confirmed swings that are available by this point.
            # --------------------------------------------------------------

            while (
                swing_cursor < len(swing_stream)
                and swing_stream[swing_cursor]["index"]
                <= candle_index
            ):
                swing = swing_stream[swing_cursor]

                if swing["side"] == "high":
                    active_high = swing

                else:
                    active_low = swing

                swing_cursor += 1

            close = candle["close"]

            # --------------------------------------------------------------
            # Bullish break of active structural high.
            # --------------------------------------------------------------

            if (
                active_high is not None
                and candle_index > active_high["index"]
                and active_high["index"]
                not in broken_high_indices
                and close > active_high["price"]
            ):
                event_type = self._classify_break(
                    direction="BUY",
                    current_bias=current_bias,
                )

                event = self._build_break_event(
                    index=candle_index,
                    price=close,
                    broken_level=active_high["price"],
                    direction="BUY",
                    event_type=event_type,
                    broken_swing=active_high,
                )

                if event_type == "BOS":
                    bos.append(event)
                else:
                    choch.append(event)

                broken_high_indices.add(
                    active_high["index"]
                )

                current_bias = "BULLISH"

                # Once broken, this high is no longer an active
                # unbroken resistance level.
                active_high = None

            # --------------------------------------------------------------
            # Bearish break of active structural low.
            # --------------------------------------------------------------

            if (
                active_low is not None
                and candle_index > active_low["index"]
                and active_low["index"]
                not in broken_low_indices
                and close < active_low["price"]
            ):
                event_type = self._classify_break(
                    direction="SELL",
                    current_bias=current_bias,
                )

                event = self._build_break_event(
                    index=candle_index,
                    price=close,
                    broken_level=active_low["price"],
                    direction="SELL",
                    event_type=event_type,
                    broken_swing=active_low,
                )

                if event_type == "BOS":
                    bos.append(event)
                else:
                    choch.append(event)

                broken_low_indices.add(
                    active_low["index"]
                )

                current_bias = "BEARISH"

                active_low = None

        all_events = [
            {
                **event,
                "event_type": "BOS",
            }
            for event in bos
        ]

        all_events.extend(
            {
                **event,
                "event_type": "CHoCH",
            }
            for event in choch
        )

        all_events.sort(
            key=lambda event: event["index"]
        )

        return {
            "bos": bos,
            "choch": choch,
            "last_event": (
                all_events[-1]
                if all_events
                else None
            ),
        }

    # ==================================================================
    # BREAK HELPERS
    # ==================================================================

    @staticmethod
    def _initial_direction(
        classifications: Sequence[Dict[str, Any]],
    ) -> str:
        """
        Establish the first meaningful structural direction.

        The first directional pair is preferred over simply counting
        every historical classification.
        """

        last_high_label: Optional[str] = None
        last_low_label: Optional[str] = None

        for item in classifications:
            label = item["label"]

            if item["side"] == "high":
                last_high_label = label

            else:
                last_low_label = label

            if (
                last_high_label in ("HH",)
                and last_low_label in ("HL",)
            ):
                return "BULLISH"

            if (
                last_high_label in ("LH",)
                and last_low_label in ("LL",)
            ):
                return "BEARISH"

        # Fallback to broad structural scoring.
        bullish = 0
        bearish = 0

        for item in classifications:
            if item["label"] in ("HH", "HL"):
                bullish += 1

            elif item["label"] in ("LH", "LL"):
                bearish += 1

        if bullish > bearish:
            return "BULLISH"

        if bearish > bullish:
            return "BEARISH"

        return "RANGE"

    @staticmethod
    def _classify_break(
        direction: str,
        current_bias: str,
    ) -> str:
        """
        Determine whether a confirmed break is BOS or CHoCH.
        """

        if direction == "BUY":

            if current_bias == "BULLISH":
                return "BOS"

            return "CHoCH"

        if direction == "SELL":

            if current_bias == "BEARISH":
                return "BOS"

            return "CHoCH"

        raise ValueError(
            f"unsupported break direction: {direction}"
        )

    @staticmethod
    def _build_break_event(
        index: int,
        price: float,
        broken_level: float,
        direction: str,
        event_type: str,
        broken_swing: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build standardized BOS/CHoCH event.
        """

        return {
            "index": index,
            "price": price,
            "broken_level": broken_level,
            "direction": direction,
            "type": event_type,
            "broken_swing_index": broken_swing["index"],
            "broken_swing_type": broken_swing["type"],
        }

    # ==================================================================
    # FINAL BIAS
    # ==================================================================

    @staticmethod
    def _determine_final_bias(
        classifications: Sequence[Dict[str, Any]],
        break_events: Dict[str, Any],
        initial_bias: str,
    ) -> str:
        """
        Determine final structural bias.

        A confirmed CHoCH/BOS is allowed to update the current
        directional state.

        This remains structural information only; it is NOT a trade
        decision.
        """

        bias = initial_bias

        events = [
            *break_events.get("bos", []),
            *break_events.get("choch", []),
        ]

        events.sort(
            key=lambda event: event["index"]
        )

        for event in events:

            if event["direction"] == "BUY":
                bias = "BULLISH"

            elif event["direction"] == "SELL":
                bias = "BEARISH"

        return bias

    # ==================================================================
    # CURRENT STRUCTURE
    # ==================================================================

    @staticmethod
    def _current_structure(
        classifications: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Return the latest and previous structural highs/lows.
        """

        highs = [
            item
            for item in classifications
            if item["side"] == "high"
        ]

        lows = [
            item
            for item in classifications
            if item["side"] == "low"
        ]

        return {
            "last_high": (
                highs[-1]
                if highs
                else None
            ),
            "previous_high": (
                highs[-2]
                if len(highs) >= 2
                else None
            ),
            "last_low": (
                lows[-1]
                if lows
                else None
            ),
            "previous_low": (
                lows[-2]
                if len(lows) >= 2
                else None
            ),
        }

    # ==================================================================
    # INSUFFICIENT DATA
    # ==================================================================

    def _insufficient_result(
        self,
        candle_count: int,
    ) -> Dict[str, Any]:
        """
        Safe result when insufficient candles exist.
        """

        return {
            "status": "INSUFFICIENT_DATA",
            "technical_only": True,
            "component": "market_structure",
            "candle_count": candle_count,
            "lookback": self.lookback,
            "bias": "UNKNOWN",
            "initial_bias": "UNKNOWN",
            "current_structure": {
                "last_high": None,
                "previous_high": None,
                "last_low": None,
                "previous_low": None,
            },
            "swing_highs": [],
            "swing_lows": [],
            "classifications": [],
            "bos": [],
            "choch": [],
            "last_event": None,
        }


# ======================================================================
# CONVENIENCE API
# ======================================================================

def analyze_market_structure(
    candles: Any,
    lookback: int = MarketStructure.DEFAULT_LOOKBACK,
) -> Dict[str, Any]:
    """
    Convenience entry point for Market Structure analysis.
    """

    analyzer = MarketStructure(
        lookback=lookback
    )

    return analyzer.analyze(candles)
