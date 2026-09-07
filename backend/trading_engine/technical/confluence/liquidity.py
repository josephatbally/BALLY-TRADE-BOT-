"""
BALLY FLOW - Technical Liquidity Analysis

TECHNICAL MODE ONLY.

Detects:
- Buy-side liquidity
- Sell-side liquidity
- Equal highs
- Equal lows
- Previous day high/low
- Previous week high/low
- Asian session high/low
- London session high/low
- New York session high/low
- Liquidity sweeps

This module does NOT:
- perform fundamental analysis
- make hybrid decisions
- execute trades
- manage risk
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional


class Liquidity:
    """
    Technical liquidity analyzer.

    Session windows are UTC:

        Asian      00:00 - 08:00
        London     08:00 - 13:00
        New York   13:00 - 22:00
    """

    NAME = "BALLY FLOW Technical Liquidity"

    DEFAULT_TOLERANCE = 0.0005

    ASIAN_START = time(0, 0)
    ASIAN_END = time(8, 0)

    LONDON_START = time(8, 0)
    LONDON_END = time(13, 0)

    NEW_YORK_START = time(13, 0)
    NEW_YORK_END = time(22, 0)

    def __init__(
        self,
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> None:

        if not isinstance(tolerance, (int, float)):
            raise TypeError("tolerance must be numeric")

        if tolerance < 0:
            raise ValueError("tolerance cannot be negative")

        self.tolerance = float(tolerance)

    # ============================================================
    # PUBLIC API
    # ============================================================

    def analyze(
        self,
        candles: Any,
    ) -> Dict[str, Any]:

        normalized = self._normalize_candles(candles)

        if len(normalized) < 3:
            return self._insufficient_result(len(normalized))

        equal_highs = self._find_equal_highs(normalized)
        equal_lows = self._find_equal_lows(normalized)

        previous_day = self._previous_day_levels(normalized)
        previous_week = self._previous_week_levels(normalized)

        sessions = self._session_liquidity(normalized)

        buy_side = self._build_buy_side_liquidity(
            equal_highs,
            previous_day,
            previous_week,
            sessions,
        )

        sell_side = self._build_sell_side_liquidity(
            equal_lows,
            previous_day,
            previous_week,
            sessions,
        )

        sweeps = self._detect_sweeps(
            normalized,
            buy_side,
            sell_side,
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "liquidity",
            "candle_count": len(normalized),

            "buy_side_liquidity": buy_side,
            "sell_side_liquidity": sell_side,

            "equal_highs": equal_highs,
            "equal_lows": equal_lows,

            "previous_day": previous_day,
            "previous_week": previous_week,

            "sessions": sessions,

            "sweeps": sweeps,
            "last_sweep": sweeps[-1] if sweeps else None,
        }

    # ============================================================
    # CANDLE NORMALIZATION
    # ============================================================

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
            raise TypeError("candles must be iterable") from exc

        result: List[Dict[str, Any]] = []

        for index, candle in enumerate(sequence):

            if isinstance(candle, dict):

                try:
                    open_price = float(candle["open"])
                    high = float(candle["high"])
                    low = float(candle["low"])
                    close = float(candle["close"])
                except KeyError as exc:
                    raise ValueError(
                        f"candle {index} missing OHLC field: {exc}"
                    ) from exc

                timestamp = candle.get("time")

                if timestamp is None:
                    timestamp = candle.get("timestamp")

            else:

                try:
                    open_price = float(getattr(candle, "open"))
                    high = float(getattr(candle, "high"))
                    low = float(getattr(candle, "low"))
                    close = float(getattr(candle, "close"))
                except AttributeError as exc:
                    raise ValueError(
                        f"candle {index} does not expose OHLC fields"
                    ) from exc

                timestamp = getattr(candle, "time", None)

                if timestamp is None:
                    timestamp = getattr(
                        candle,
                        "timestamp",
                        None,
                    )

            if high < low:
                raise ValueError(
                    f"candle {index} has high below low"
                )

            result.append(
                {
                    "index": index,
                    "time": Liquidity._normalize_time(timestamp),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                }
            )

        return result

    @staticmethod
    def _normalize_time(
        value: Any,
    ) -> Optional[datetime]:

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):

            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
            except ValueError:
                return None

        return None

    # ============================================================
    # EQUAL HIGHS
    # ============================================================

    def _find_equal_highs(
        self,
        candles: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        results: List[Dict[str, Any]] = []

        for i in range(len(candles)):

            for j in range(i + 1, len(candles)):

                first = candles[i]["high"]
                second = candles[j]["high"]

                if self._approximately_equal(first, second):

                    results.append(
                        {
                            "type": "equal_high",
                            "side": "buy_side",
                            "price": round(
                                (first + second) / 2,
                                10,
                            ),
                            "first_index": i,
                            "second_index": j,
                        }
                    )

        return results

    # ============================================================
    # EQUAL LOWS
    # ============================================================

    def _find_equal_lows(
        self,
        candles: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        results: List[Dict[str, Any]] = []

        for i in range(len(candles)):

            for j in range(i + 1, len(candles)):

                first = candles[i]["low"]
                second = candles[j]["low"]

                if self._approximately_equal(first, second):

                    results.append(
                        {
                            "type": "equal_low",
                            "side": "sell_side",
                            "price": round(
                                (first + second) / 2,
                                10,
                            ),
                            "first_index": i,
                            "second_index": j,
                        }
                    )

        return results

    # ============================================================
    # PREVIOUS DAY
    # ============================================================

    @staticmethod
    def _previous_day_levels(
        candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        grouped: Dict[Any, List[Dict[str, Any]]] = {}

        for candle in candles:

            timestamp = candle["time"]

            if timestamp is None:
                continue

            day = timestamp.date()

            grouped.setdefault(day, []).append(candle)

        days = sorted(grouped.keys())

        if len(days) < 2:

            return {
                "high": None,
                "low": None,
                "available": False,
            }

        previous_day = days[-2]
        values = grouped[previous_day]

        return {
            "high": max(c["high"] for c in values),
            "low": min(c["low"] for c in values),
            "date": str(previous_day),
            "available": True,
        }

    # ============================================================
    # PREVIOUS WEEK
    # ============================================================

    @staticmethod
    def _previous_week_levels(
        candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        grouped: Dict[Any, List[Dict[str, Any]]] = {}

        for candle in candles:

            timestamp = candle["time"]

            if timestamp is None:
                continue

            iso = timestamp.isocalendar()

            key = (
                iso.year,
                iso.week,
            )

            grouped.setdefault(key, []).append(candle)

        weeks = sorted(grouped.keys())

        if len(weeks) < 2:

            return {
                "high": None,
                "low": None,
                "available": False,
            }

        previous_week = weeks[-2]
        values = grouped[previous_week]

        return {
            "high": max(c["high"] for c in values),
            "low": min(c["low"] for c in values),
            "year": previous_week[0],
            "week": previous_week[1],
            "available": True,
        }

    # ============================================================
    # SESSION LIQUIDITY
    # ============================================================

    def _session_liquidity(
        self,
        candles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        sessions = {
            "asian": self._empty_session(),
            "london": self._empty_session(),
            "new_york": self._empty_session(),
        }

        for candle in candles:

            timestamp = candle["time"]

            if timestamp is None:
                continue

            session_name = self._get_session(
                timestamp.time()
            )

            if session_name is None:
                continue

            session = sessions[session_name]

            session["candle_count"] += 1

            if (
                session["high"] is None
                or candle["high"] > session["high"]
            ):
                session["high"] = candle["high"]

            if (
                session["low"] is None
                or candle["low"] < session["low"]
            ):
                session["low"] = candle["low"]

        return sessions

    @staticmethod
    def _empty_session() -> Dict[str, Any]:

        return {
            "high": None,
            "low": None,
            "candle_count": 0,
        }

    @classmethod
    def _get_session(
        cls,
        current_time: time,
    ) -> Optional[str]:

        if (
            cls.ASIAN_START
            <= current_time
            < cls.ASIAN_END
        ):
            return "asian"

        if (
            cls.LONDON_START
            <= current_time
            < cls.LONDON_END
        ):
            return "london"

        if (
            cls.NEW_YORK_START
            <= current_time
            < cls.NEW_YORK_END
        ):
            return "new_york"

        return None

    # ============================================================
    # BUY-SIDE LIQUIDITY
    # ============================================================

    @staticmethod
    def _build_buy_side_liquidity(
        equal_highs: List[Dict[str, Any]],
        previous_day: Dict[str, Any],
        previous_week: Dict[str, Any],
        sessions: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        levels: List[Dict[str, Any]] = []

        for item in equal_highs:
            levels.append(item)

        if previous_day.get("available"):

            levels.append(
                {
                    "type": "previous_day_high",
                    "side": "buy_side",
                    "price": previous_day["high"],
                }
            )

        if previous_week.get("available"):

            levels.append(
                {
                    "type": "previous_week_high",
                    "side": "buy_side",
                    "price": previous_week["high"],
                }
            )

        for name, data in sessions.items():

            if data["high"] is not None:

                levels.append(
                    {
                        "type": f"{name}_high",
                        "side": "buy_side",
                        "price": data["high"],
                    }
                )

        return levels

    # ============================================================
    # SELL-SIDE LIQUIDITY
    # ============================================================

    @staticmethod
    def _build_sell_side_liquidity(
        equal_lows: List[Dict[str, Any]],
        previous_day: Dict[str, Any],
        previous_week: Dict[str, Any],
        sessions: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        levels: List[Dict[str, Any]] = []

        for item in equal_lows:
            levels.append(item)

        if previous_day.get("available"):

            levels.append(
                {
                    "type": "previous_day_low",
                    "side": "sell_side",
                    "price": previous_day["low"],
                }
            )

        if previous_week.get("available"):

            levels.append(
                {
                    "type": "previous_week_low",
                    "side": "sell_side",
                    "price": previous_week["low"],
                }
            )

        for name, data in sessions.items():

            if data["low"] is not None:

                levels.append(
                    {
                        "type": f"{name}_low",
                        "side": "sell_side",
                        "price": data["low"],
                    }
                )

        return levels

    # ============================================================
    # LIQUIDITY SWEEPS
    # ============================================================

    @staticmethod
    def _detect_sweeps(
        candles: List[Dict[str, Any]],
        buy_levels: List[Dict[str, Any]],
        sell_levels: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        sweeps: List[Dict[str, Any]] = []

        # Index liquidity levels by price so each candle only examines
        # levels inside its actual sweep interval instead of scanning
        # every liquidity level.
        from bisect import bisect_left, bisect_right

        buy_normalized = [
            (float(level["price"]), level["type"], position)
            for position, level in enumerate(buy_levels)
        ]

        sell_normalized = [
            (float(level["price"]), level["type"], position)
            for position, level in enumerate(sell_levels)
        ]

        buy_sorted = sorted(
            buy_normalized,
            key=lambda item: item[0],
        )

        sell_sorted = sorted(
            sell_normalized,
            key=lambda item: item[0],
        )

        buy_prices = [
            item[0]
            for item in buy_sorted
        ]

        sell_prices = [
            item[0]
            for item in sell_sorted
        ]

        append_sweep = sweeps.append

        for candle in candles:

            candle_index = candle["index"]
            candle_high = candle["high"]
            candle_low = candle["low"]
            candle_close = candle["close"]

            # --------------------------------------------------------
            # BUY-SIDE SWEEP
            # Original condition:
            #     candle_high > price
            #     candle_close < price
            #
            # Therefore:
            #     candle_close < price < candle_high
            # --------------------------------------------------------

            buy_start = bisect_right(
                buy_prices,
                candle_close,
            )

            buy_end = bisect_left(
                buy_prices,
                candle_high,
            )

            if buy_start < buy_end:

                candidates = buy_sorted[buy_start:buy_end]

                # The original implementation scans buy_levels in
                # their original order. Restore that exact ordering.
                candidates.sort(
                    key=lambda item: item[2]
                )

                for price, liquidity_type, _ in candidates:

                    append_sweep(
                        {
                            "index": candle_index,
                            "price": candle_close,
                            "liquidity_level": price,
                            "liquidity_type": liquidity_type,
                            "side": "buy_side",
                            "direction": "SELL",
                            "type": "LIQUIDITY_SWEEP",
                        }
                    )

            # --------------------------------------------------------
            # SELL-SIDE SWEEP
            # Original condition:
            #     candle_low < price
            #     candle_close > price
            #
            # Therefore:
            #     candle_low < price < candle_close
            # --------------------------------------------------------

            sell_start = bisect_right(
                sell_prices,
                candle_low,
            )

            sell_end = bisect_left(
                sell_prices,
                candle_close,
            )

            if sell_start < sell_end:

                candidates = sell_sorted[sell_start:sell_end]

                # Restore the original sell_levels ordering.
                candidates.sort(
                    key=lambda item: item[2]
                )

                for price, liquidity_type, _ in candidates:

                    append_sweep(
                        {
                            "index": candle_index,
                            "price": candle_close,
                            "liquidity_level": price,
                            "liquidity_type": liquidity_type,
                            "side": "sell_side",
                            "direction": "BUY",
                            "type": "LIQUIDITY_SWEEP",
                        }
                    )

        # Preserve the original final ordering.
        return sweeps

    # ============================================================
    # HELPERS
    # ============================================================

    def _approximately_equal(
        self,
        first: float,
        second: float,
    ) -> bool:

        difference = abs(first - second)

        reference = max(
            abs(first),
            abs(second),
            1.0,
        )

        return (
            difference / reference
            <= self.tolerance
        )

    # ============================================================
    # SAFE EMPTY RESULT
    # ============================================================

    def _insufficient_result(
        self,
        candle_count: int,
    ) -> Dict[str, Any]:

        return {
            "status": "INSUFFICIENT_DATA",
            "technical_only": True,
            "component": "liquidity",
            "candle_count": candle_count,

            "buy_side_liquidity": [],
            "sell_side_liquidity": [],

            "equal_highs": [],
            "equal_lows": [],

            "previous_day": {
                "high": None,
                "low": None,
                "available": False,
            },

            "previous_week": {
                "high": None,
                "low": None,
                "available": False,
            },

            "sessions": {
                "asian": self._empty_session(),
                "london": self._empty_session(),
                "new_york": self._empty_session(),
            },

            "sweeps": [],
            "last_sweep": None,
        }


def analyze_liquidity(
    candles: Any,
    tolerance: float = Liquidity.DEFAULT_TOLERANCE,
) -> Dict[str, Any]:

    analyzer = Liquidity(
        tolerance=tolerance
    )

    return analyzer.analyze(candles)
