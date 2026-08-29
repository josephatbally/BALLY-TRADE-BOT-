"""
BALLY FLOW - Technical Premium / Discount Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module identifies the current price location inside a valid
dealing range and classifies that location as:

    PREMIUM
    DISCOUNT
    EQUILIBRIUM

The module does NOT:
    - perform fundamental analysis
    - generate the final BUY / SELL / NO_TRADE decision
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size

REAL-WORLD PREMIUM / DISCOUNT LOGIC
-----------------------------------

Premium / Discount is evaluated relative to a meaningful dealing
range rather than an arbitrary fixed price.

For a dealing range:

    range_high = meaningful swing high
    range_low  = meaningful swing low

The equilibrium is:

    equilibrium = (range_high + range_low) / 2

Price above equilibrium:
    PREMIUM

Price below equilibrium:
    DISCOUNT

Price at equilibrium:
    EQUILIBRIUM

The complete range is retained because the range boundaries are
important when evaluating liquidity, structure, Order Blocks and FVGs.

ZONE LOCATION
-------------

The default classification uses:

    DISCOUNT:
        0% -> 50%

    EQUILIBRIUM:
        approximately 50%

    PREMIUM:
        50% -> 100%

The module also exposes normalized position within the range:

    0.0  = range low
    0.5  = equilibrium
    1.0  = range high

TECHNICAL ONLY
--------------

Every successful result contains:

    "technical_only": True

This module provides context to the Confluence / Decision Engine.
It does not independently authorize a trade.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


class PremiumDiscount:
    """
    Technical Premium / Discount dealing-range analyzer.
    """

    NAME = "BALLY FLOW Premium Discount"

    DEFAULT_LOOKBACK = 20

    # Small tolerance around 50% used to classify equilibrium.
    DEFAULT_EQUILIBRIUM_TOLERANCE = 0.02

    # A dealing range must have meaningful price width.
    DEFAULT_MIN_RANGE_RATIO = 0.0001

    def __init__(
        self,
        lookback: int = DEFAULT_LOOKBACK,
        equilibrium_tolerance: float = DEFAULT_EQUILIBRIUM_TOLERANCE,
        min_range_ratio: float = DEFAULT_MIN_RANGE_RATIO,
    ) -> None:

        if not isinstance(lookback, int):
            raise TypeError("lookback must be an integer")

        if lookback < 2:
            raise ValueError("lookback must be at least 2")

        if not isinstance(
            equilibrium_tolerance,
            (int, float),
        ):
            raise TypeError(
                "equilibrium_tolerance must be numeric"
            )

        if not 0.0 <= float(equilibrium_tolerance) < 0.5:
            raise ValueError(
                "equilibrium_tolerance must be between 0 and 0.5"
            )

        if not isinstance(
            min_range_ratio,
            (int, float),
        ):
            raise TypeError(
                "min_range_ratio must be numeric"
            )

        if float(min_range_ratio) < 0.0:
            raise ValueError(
                "min_range_ratio must be greater than or equal to zero"
            )

        self.lookback = lookback
        self.equilibrium_tolerance = float(
            equilibrium_tolerance
        )
        self.min_range_ratio = float(
            min_range_ratio
        )

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def analyze(
        self,
        candles: Any,
        structure: Optional[Dict[str, Any]] = None,
        current_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze Premium / Discount from candle data.

        Parameters
        ----------
        candles:
            OHLC candle sequence ordered oldest -> newest.

        structure:
            Optional market-structure result. When available, meaningful
            swing highs/lows may be used to construct the dealing range.

        current_price:
            Optional current market price. If omitted, the latest candle
            close is used.

        Returns
        -------
        dict
            Standardized technical-only Premium / Discount analysis.
        """

        normalized = self._normalize_candles(candles)

        minimum = max(
            self.lookback,
            2,
        )

        if len(normalized) < minimum:
            return self._insufficient_result(
                len(normalized)
            )

        structure_data = structure or {}

        price = self._resolve_current_price(
            normalized,
            current_price,
        )

        dealing_range = self._build_dealing_range(
            normalized,
            structure_data,
        )

        if dealing_range is None:
            return self._invalid_range_result(
                candle_count=len(normalized),
                current_price=price,
            )

        range_low = dealing_range["low"]
        range_high = dealing_range["high"]
        range_size = dealing_range["size"]

        equilibrium = (
            range_low + range_high
        ) / 2.0

        position_ratio = (
            price - range_low
        ) / range_size

        position_ratio = max(
            0.0,
            min(position_ratio, 1.0),
        )

        classification = self._classify_position(
            position_ratio
        )

        zone = self._zone_name(
            position_ratio
        )

        distance_from_equilibrium = (
            price - equilibrium
        )

        distance_ratio = (
            abs(distance_from_equilibrium)
            / range_size
        )

        dealing_range_result = {
            "high": range_high,
            "low": range_low,
            "size": range_size,
            "equilibrium": equilibrium,
            "source": dealing_range["source"],
            "high_index": dealing_range["high_index"],
            "low_index": dealing_range["low_index"],
        }

        return {
            "status": "READY",
            "technical_only": True,
            "component": "premium_discount",
            "candle_count": len(normalized),

            "lookback": self.lookback,

            "equilibrium_tolerance": (
                self.equilibrium_tolerance
            ),

            "current_price": price,

            "dealing_range": dealing_range_result,

            "range_high": range_high,
            "range_low": range_low,

            "equilibrium": equilibrium,

            "position": {
                "ratio": round(
                    position_ratio,
                    6,
                ),
                "percentage": round(
                    position_ratio * 100.0,
                    2,
                ),
                "classification": classification,
                "zone": zone,
            },

            "premium": {
                "active": classification == "PREMIUM",
                "low": equilibrium,
                "high": range_high,
                "percentage_start": 50.0,
                "percentage_end": 100.0,
            },

            "discount": {
                "active": classification == "DISCOUNT",
                "low": range_low,
                "high": equilibrium,
                "percentage_start": 0.0,
                "percentage_end": 50.0,
            },

            "equilibrium_zone": {
                "active": classification == "EQUILIBRIUM",
                "price": equilibrium,
                "tolerance": (
                    self.equilibrium_tolerance
                ),
            },

            "distance_from_equilibrium": {
                "price": round(
                    distance_from_equilibrium,
                    10,
                ),
                "ratio": round(
                    distance_ratio,
                    6,
                ),
                "percentage": round(
                    distance_ratio * 100.0,
                    2,
                ),
            },

            "structure_context": {
                "provided": bool(structure_data),
                "used": dealing_range["source"]
                == "market_structure",
            },
        }

    # ==============================================================
    # CURRENT PRICE
    # ==============================================================

    @staticmethod
    def _resolve_current_price(
        candles: Sequence[Dict[str, Any]],
        current_price: Optional[float],
    ) -> float:

        if current_price is not None:

            try:
                price = float(current_price)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "current_price must be numeric"
                ) from exc

            if price <= 0:
                raise ValueError(
                    "current_price must be greater than zero"
                )

            return price

        return float(
            candles[-1]["close"]
        )

    # ==============================================================
    # DEALING RANGE
    # ==============================================================

    def _build_dealing_range(
        self,
        candles: Sequence[Dict[str, Any]],
        structure: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:

        structured_range = (
            self._range_from_structure(
                structure,
                candles,
            )
        )

        if structured_range is not None:
            return structured_range

        window = candles[
            -self.lookback:
        ]

        if not window:
            return None

        high_index = max(
            range(
                len(candles)
                - len(window),
                len(candles),
            ),
            key=lambda index: float(
                candles[index]["high"]
            ),
        )

        low_index = min(
            range(
                len(candles)
                - len(window),
                len(candles),
            ),
            key=lambda index: float(
                candles[index]["low"]
            ),
        )

        range_high = float(
            candles[high_index]["high"]
        )

        range_low = float(
            candles[low_index]["low"]
        )

        range_size = (
            range_high - range_low
        )

        if not self._valid_range(
            range_high,
            range_low,
            candles[-1]["close"],
        ):
            return None

        return {
            "high": range_high,
            "low": range_low,
            "size": range_size,
            "high_index": high_index,
            "low_index": low_index,
            "source": "lookback_range",
        }

    # ==============================================================
    # STRUCTURE RANGE
    # ==============================================================

    def _range_from_structure(
        self,
        structure: Dict[str, Any],
        candles: Sequence[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:

        if not isinstance(
            structure,
            dict,
        ):
            return None

        swing_highs = (
            structure.get("swing_highs")
        )

        swing_lows = (
            structure.get("swing_lows")
        )

        if not isinstance(
            swing_highs,
            list,
        ):
            swing_highs = []

        if not isinstance(
            swing_lows,
            list,
        ):
            swing_lows = []

        high_candidate = (
            self._latest_valid_structure_point(
                swing_highs,
                "high",
            )
        )

        low_candidate = (
            self._latest_valid_structure_point(
                swing_lows,
                "low",
            )
        )

        if (
            high_candidate is None
            or low_candidate is None
        ):
            return None

        range_high = high_candidate["price"]
        range_low = low_candidate["price"]

        high_index = high_candidate["index"]
        low_index = low_candidate["index"]

        if range_high <= range_low:
            return None

        range_size = (
            range_high - range_low
        )

        latest_close = float(
            candles[-1]["close"]
        )

        if not self._valid_range(
            range_high,
            range_low,
            latest_close,
        ):
            return None

        return {
            "high": range_high,
            "low": range_low,
            "size": range_size,
            "high_index": high_index,
            "low_index": low_index,
            "source": "market_structure",
        }

    @staticmethod
    def _latest_valid_structure_point(
        points: List[Any],
        price_key: str,
    ) -> Optional[Dict[str, Any]]:

        valid: List[Dict[str, Any]] = []

        for point in points:

            if not isinstance(
                point,
                dict,
            ):
                continue

            price = (
                point.get(price_key)
            )

            if price is None:
                price = point.get(
                    "price"
                )

            if price is None:
                price = point.get(
                    "value"
                )

            if price is None:
                continue

            try:
                price_value = float(price)
            except (TypeError, ValueError):
                continue

            index = point.get(
                "index"
            )

            if not isinstance(
                index,
                int,
            ):
                index = -1

            valid.append(
                {
                    "price": price_value,
                    "index": index,
                }
            )

        if not valid:
            return None

        return max(
            valid,
            key=lambda item: item["index"],
        )

    # ==============================================================
    # CLASSIFICATION
    # ==============================================================

    def _classify_position(
        self,
        position_ratio: float,
    ) -> str:

        tolerance = (
            self.equilibrium_tolerance
        )

        lower = 0.5 - tolerance
        upper = 0.5 + tolerance

        if position_ratio < lower:
            return "DISCOUNT"

        if position_ratio > upper:
            return "PREMIUM"

        return "EQUILIBRIUM"

    @staticmethod
    def _zone_name(
        position_ratio: float,
    ) -> str:

        if position_ratio < 0.5:
            return "DISCOUNT"

        if position_ratio > 0.5:
            return "PREMIUM"

        return "EQUILIBRIUM"

    # ==============================================================
    # RANGE VALIDATION
    # ==============================================================

    def _valid_range(
        self,
        range_high: float,
        range_low: float,
        reference_price: float,
    ) -> bool:

        if range_high <= range_low:
            return False

        range_size = (
            range_high - range_low
        )

        if range_size <= 0:
            return False

        reference = max(
            abs(float(reference_price)),
            1.0,
        )

        minimum_size = (
            reference
            * self.min_range_ratio
        )

        return range_size >= minimum_size

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

        if isinstance(
            candles,
            dict,
        ):
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

        normalized: List[
            Dict[str, Any]
        ] = []

        for index, candle in enumerate(
            sequence
        ):

            if isinstance(
                candle,
                dict,
            ):

                try:
                    open_price = candle[
                        "open"
                    ]
                    high = candle[
                        "high"
                    ]
                    low = candle[
                        "low"
                    ]
                    close = candle[
                        "close"
                    ]
                except KeyError as exc:
                    raise ValueError(
                        f"candle {index} is missing OHLC field: {exc}"
                    ) from exc

                item: Dict[str, Any] = {
                    "open": float(
                        open_price
                    ),
                    "high": float(
                        high
                    ),
                    "low": float(
                        low
                    ),
                    "close": float(
                        close
                    ),
                }

                for key in (
                    "volume",
                    "tick_volume",
                    "time",
                    "timestamp",
                ):
                    if key in candle:
                        item[key] = candle[
                            key
                        ]

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
                        f"candle {index} does not expose OHLC fields"
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
            "component": "premium_discount",
            "candle_count": candle_count,
            "lookback": self.lookback,
            "equilibrium_tolerance": (
                self.equilibrium_tolerance
            ),

            "current_price": None,

            "dealing_range": None,

            "range_high": None,
            "range_low": None,
            "equilibrium": None,

            "position": {
                "ratio": None,
                "percentage": None,
                "classification": None,
                "zone": None,
            },

            "premium": {
                "active": False,
                "low": None,
                "high": None,
                "percentage_start": 50.0,
                "percentage_end": 100.0,
            },

            "discount": {
                "active": False,
                "low": None,
                "high": None,
                "percentage_start": 0.0,
                "percentage_end": 50.0,
            },

            "equilibrium_zone": {
                "active": False,
                "price": None,
                "tolerance": (
                    self.equilibrium_tolerance
                ),
            },

            "distance_from_equilibrium": {
                "price": None,
                "ratio": None,
                "percentage": None,
            },

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }

    # ==============================================================
    # INVALID RANGE
    # ==============================================================

    @staticmethod
    def _invalid_range_result(
        candle_count: int,
        current_price: float,
    ) -> Dict[str, Any]:

        return {
            "status": "INVALID_RANGE",
            "technical_only": True,
            "component": "premium_discount",
            "candle_count": candle_count,

            "current_price": current_price,

            "dealing_range": None,

            "range_high": None,
            "range_low": None,
            "equilibrium": None,

            "position": {
                "ratio": None,
                "percentage": None,
                "classification": None,
                "zone": None,
            },

            "premium": {
                "active": False,
                "low": None,
                "high": None,
                "percentage_start": 50.0,
                "percentage_end": 100.0,
            },

            "discount": {
                "active": False,
                "low": None,
                "high": None,
                "percentage_start": 0.0,
                "percentage_end": 50.0,
            },

            "equilibrium_zone": {
                "active": False,
                "price": None,
                "tolerance": None,
            },

            "distance_from_equilibrium": {
                "price": None,
                "ratio": None,
                "percentage": None,
            },

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_premium_discount(
    candles: Any,
    structure: Optional[Dict[str, Any]] = None,
    current_price: Optional[float] = None,
    lookback: int = PremiumDiscount.DEFAULT_LOOKBACK,
    equilibrium_tolerance: float = (
        PremiumDiscount.DEFAULT_EQUILIBRIUM_TOLERANCE
    ),
    min_range_ratio: float = (
        PremiumDiscount.DEFAULT_MIN_RANGE_RATIO
    ),
) -> Dict[str, Any]:

    analyzer = PremiumDiscount(
        lookback=lookback,
        equilibrium_tolerance=(
            equilibrium_tolerance
        ),
        min_range_ratio=min_range_ratio,
    )

    return analyzer.analyze(
        candles=candles,
        structure=structure,
        current_price=current_price,
    )


# ==================================================================
# COMPATIBILITY ALIAS
# ==================================================================

PremiumDiscountAnalysis = PremiumDiscount