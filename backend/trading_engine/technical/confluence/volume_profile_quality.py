
"""
BALLY FLOW - Volume Profile Quality Analysis

STRICT TECHNICAL-ANALYSIS COMPONENT.

This module builds a price/volume distribution from OHLC candles and
evaluates the quality and location of the current market relative to
the resulting Volume Profile.

The module does NOT:
    - perform fundamental analysis
    - perform hybrid decision-making
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - make the final BUY / SELL / NO_TRADE decision

VOLUME PROFILE CONCEPTS
-----------------------

This implementation uses practical Volume Profile concepts:

    1. Point of Control (POC)
    2. Value Area
    3. Value Area High (VAH)
    4. Value Area Low (VAL)
    5. High Volume Nodes (HVN)
    6. Low Volume Nodes (LVN)
    7. Volume concentration
    8. Current price location
    9. Distance from POC
    10. Acceptance / rejection context
    11. Profile quality

IMPORTANT
---------

Volume Profile is a distribution of traded volume by PRICE, not merely
a conventional time-based volume indicator.

When true tick-by-price data is unavailable, this module estimates the
distribution from candle OHLC and volume. Volume is distributed across
the candle's traded price range rather than assigned blindly to the
candle close.

Supported volume fields:

    volume
    tick_volume

External volume can also be supplied through analyze(..., volume=...).

TECHNICAL ONLY
--------------

Every result contains:

    "technical_only": True
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple


class VolumeProfileQuality:
    """
    Technical Volume Profile builder and quality evaluator.
    """

    NAME = "BALLY FLOW Volume Profile Quality"

    DEFAULT_LOOKBACK = 50
    DEFAULT_BINS = 24
    DEFAULT_VALUE_AREA_PERCENT = 70.0

    MIN_CANDLE_RANGE = 0.0
    MIN_PROFILE_VOLUME = 0.0

    HVN_THRESHOLD = 1.50
    LVN_THRESHOLD = 0.50

    def __init__(
        self,
        lookback: int = DEFAULT_LOOKBACK,
        bins: int = DEFAULT_BINS,
        value_area_percent: float = DEFAULT_VALUE_AREA_PERCENT,
    ) -> None:

        if not isinstance(lookback, int):
            raise TypeError("lookback must be an integer")

        if lookback < 5:
            raise ValueError("lookback must be at least 5")

        if not isinstance(bins, int):
            raise TypeError("bins must be an integer")

        if bins < 5:
            raise ValueError("bins must be at least 5")

        if bins > 200:
            raise ValueError("bins must not exceed 200")

        if not isinstance(value_area_percent, (int, float)):
            raise TypeError(
                "value_area_percent must be numeric"
            )

        if not 50.0 <= float(value_area_percent) <= 100.0:
            raise ValueError(
                "value_area_percent must be between 50 and 100"
            )

        self.lookback = lookback
        self.bins = bins
        self.value_area_percent = float(value_area_percent)

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def analyze(
        self,
        candles: Any,
        volume: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Build and evaluate a Volume Profile.

        Parameters
        ----------
        candles:
            OHLC candle sequence ordered oldest -> newest.

        volume:
            Optional external volume sequence. When supplied, its length
            must match the candle sequence.

        Returns
        -------
        dict
            Standardized technical-only Volume Profile analysis.
        """

        normalized = self._normalize_candles(candles)

        if volume is not None:
            self._attach_external_volume(
                normalized,
                volume,
            )

        if len(normalized) < self.lookback:
            return self._insufficient_result(
                len(normalized)
            )

        profile_candles = normalized[
            -self.lookback:
        ]

        current_price = float(
            profile_candles[-1]["close"]
        )

        volume_available = any(
            self._extract_volume(candle) is not None
            for candle in profile_candles
        )

        if not volume_available:
            return self._no_volume_result(
                len(normalized),
                current_price,
            )

        profile = self._build_profile(
            profile_candles
        )

        if profile is None:
            return self._no_volume_result(
                len(normalized),
                current_price,
            )

        quality = self._calculate_profile_quality(
            profile
        )

        location = self._classify_price_location(
            current_price=current_price,
            profile=profile,
        )

        nodes = self._identify_nodes(
            profile
        )

        acceptance = self._evaluate_acceptance(
            profile_candles=profile_candles,
            profile=profile,
            current_price=current_price,
        )

        poc_distance = self._distance_from_poc(
            current_price,
            profile["poc"],
            profile["range_high"],
            profile["range_low"],
        )

        value_area_width = (
            profile["vah"]
            - profile["val"]
        )

        value_area_ratio = (
            value_area_width
            / profile["range_size"]
            if profile["range_size"] > 0
            else 0.0
        )

        return {
            "status": "READY",
            "technical_only": True,
            "component": "volume_profile_quality",

            "candle_count": len(normalized),
            "profile_candle_count": len(
                profile_candles
            ),

            "lookback": self.lookback,
            "bins": self.bins,
            "value_area_percent": (
                self.value_area_percent
            ),

            "volume_available": True,
            "volume_source": self._volume_source(
                profile_candles
            ),

            "current_price": current_price,

            "profile": {
                "range_high": profile["range_high"],
                "range_low": profile["range_low"],
                "range_size": profile["range_size"],

                "poc": profile["poc"],
                "vah": profile["vah"],
                "val": profile["val"],

                "total_volume": profile[
                    "total_volume"
                ],

                "value_area_volume": profile[
                    "value_area_volume"
                ],

                "value_area_ratio": round(
                    value_area_ratio,
                    4,
                ),
            },

            "price_location": location,

            "distance_from_poc": poc_distance,

            "nodes": nodes,

            "acceptance": acceptance,

            "quality": quality,

            "profile_quality_score": quality[
                "score"
            ],

            "high_volume_nodes": nodes[
                "high_volume_nodes"
            ],

            "low_volume_nodes": nodes[
                "low_volume_nodes"
            ],

            "poc": profile["poc"],
            "value_area_high": profile["vah"],
            "value_area_low": profile["val"],

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }

    # ==============================================================
    # NORMALIZATION
    # ==============================================================

    @staticmethod
    def _normalize_candles(
        candles: Any,
    ) -> List[Dict[str, Any]]:
        """
        Normalize dictionaries or OHLC objects.
        """

        if candles is None:
            raise ValueError(
                "candles are required"
            )

        if isinstance(candles, dict):
            candles = candles.get("candles")

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
        """
        Attach external volume to normalized candles.
        """

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
                numeric = float(value)
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    "volume contains non-numeric data"
                ) from exc

            if numeric < 0:
                raise ValueError(
                    "volume cannot be negative"
                )

            candle["volume"] = numeric

    # ==============================================================
    # VOLUME
    # ==============================================================

    @staticmethod
    def _extract_volume(
        candle: Dict[str, Any],
    ) -> Optional[float]:
        """
        Prefer real volume when available and fall back to tick volume.
        """

        for key in (
            "volume",
            "tick_volume",
        ):

            if key not in candle:
                continue

            try:
                value = float(
                    candle[key]
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if value < 0:
                continue

            return value

        return None

    @classmethod
    def _volume_source(
        cls,
        candles: Sequence[Dict[str, Any]],
    ) -> str:

        has_real = any(
            "volume" in candle
            for candle in candles
        )

        has_tick = any(
            "tick_volume" in candle
            for candle in candles
        )

        if has_real:
            return "volume"

        if has_tick:
            return "tick_volume"

        return "none"

    # ==============================================================
    # PROFILE CONSTRUCTION
    # ==============================================================

    def _build_profile(
        self,
        candles: Sequence[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Construct a volume-at-price distribution.

        Candle volume is distributed across the candle's price range.
        This is an approximation of true Volume Profile when
        tick-by-price data is unavailable.
        """

        range_low = min(
            float(candle["low"])
            for candle in candles
        )

        range_high = max(
            float(candle["high"])
            for candle in candles
        )

        range_size = (
            range_high - range_low
        )

        if range_size <= self.MIN_CANDLE_RANGE:
            return None

        bin_size = (
            range_size / self.bins
        )

        if bin_size <= 0:
            return None

        volumes = [
            0.0
            for _ in range(self.bins)
        ]

        total_volume = 0.0

        for candle in candles:

            candle_volume = (
                self._extract_volume(candle)
            )

            if candle_volume is None:
                continue

            if candle_volume <= 0:
                continue

            low = float(candle["low"])
            high = float(candle["high"])

            if high <= low:
                index = self._price_to_bin(
                    float(candle["close"]),
                    range_low,
                    range_high,
                    bin_size,
                )

                volumes[index] += candle_volume
                total_volume += candle_volume
                continue

            first_bin = self._price_to_bin(
                low,
                range_low,
                range_high,
                bin_size,
            )

            last_bin = self._price_to_bin(
                high,
                range_low,
                range_high,
                bin_size,
            )

            first_bin = max(
                0,
                min(
                    first_bin,
                    self.bins - 1,
                ),
            )

            last_bin = max(
                0,
                min(
                    last_bin,
                    self.bins - 1,
                ),
            )

            touched_bins = (
                last_bin - first_bin + 1
            )

            if touched_bins <= 0:
                continue

            allocated = (
                candle_volume
                / touched_bins
            )

            for bin_index in range(
                first_bin,
                last_bin + 1,
            ):
                volumes[bin_index] += (
                    allocated
                )

            total_volume += candle_volume

        if total_volume <= self.MIN_PROFILE_VOLUME:
            return None

        prices = [
            range_low
            + (
                index + 0.5
            ) * bin_size
            for index in range(self.bins)
        ]

        poc_index = max(
            range(self.bins),
            key=lambda i: volumes[i],
        )

        poc = prices[poc_index]

        value_area_low_index, value_area_high_index = (
            self._calculate_value_area(
                volumes,
                poc_index,
            )
        )

        val = (
            range_low
            + value_area_low_index
            * bin_size
        )

        vah = (
            range_low
            + (
                value_area_high_index + 1
            )
            * bin_size
        )

        value_area_volume = sum(
            volumes[
                value_area_low_index:
                value_area_high_index + 1
            ]
        )

        return {
            "range_low": range_low,
            "range_high": range_high,
            "range_size": range_size,

            "bin_size": bin_size,

            "volumes": volumes,
            "prices": prices,

            "poc_index": poc_index,
            "poc": poc,

            "val_index": (
                value_area_low_index
            ),
            "vah_index": (
                value_area_high_index
            ),

            "val": val,
            "vah": vah,

            "total_volume": total_volume,
            "value_area_volume": (
                value_area_volume
            ),
        }

    def _price_to_bin(
        self,
        price: float,
        range_low: float,
        range_high: float,
        bin_size: float,
    ) -> int:

        if price <= range_low:
            return 0

        if price >= range_high:
            return self.bins - 1

        index = int(
            (
                price - range_low
            )
            / bin_size
        )

        return max(
            0,
            min(
                index,
                self.bins - 1,
            ),
        )

    # ==============================================================
    # VALUE AREA
    # ==============================================================

    def _calculate_value_area(
        self,
        volumes: Sequence[float],
        poc_index: int,
    ) -> Tuple[int, int]:
        """
        Expand outward from POC until the configured percentage of
        total profile volume is captured.

        At every step, the higher-volume adjacent side is included
        first. This approximates the standard Value Area expansion
        methodology.
        """

        total_volume = sum(volumes)

        if total_volume <= 0:
            return (
                poc_index,
                poc_index,
            )

        target = (
            total_volume
            * self.value_area_percent
            / 100.0
        )

        accumulated = volumes[poc_index]

        low_index = poc_index
        high_index = poc_index

        while accumulated < target:

            left_index = (
                low_index - 1
            )

            right_index = (
                high_index + 1
            )

            left_volume = (
                volumes[left_index]
                if left_index >= 0
                else -1.0
            )

            right_volume = (
                volumes[right_index]
                if right_index < len(volumes)
                else -1.0
            )

            if (
                left_volume < 0
                and right_volume < 0
            ):
                break

            if left_volume >= right_volume:

                if left_index >= 0:
                    low_index = left_index
                    accumulated += (
                        left_volume
                    )

                elif right_index < len(volumes):
                    high_index = right_index
                    accumulated += (
                        right_volume
                    )

            else:

                if right_index < len(volumes):
                    high_index = right_index
                    accumulated += (
                        right_volume
                    )

                elif left_index >= 0:
                    low_index = left_index
                    accumulated += (
                        left_volume
                    )

        return (
            low_index,
            high_index,
        )

    # ==============================================================
    # NODE DETECTION
    # ==============================================================

    def _identify_nodes(
        self,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:

        volumes = profile["volumes"]
        prices = profile["prices"]

        average_volume = (
            sum(volumes)
            / len(volumes)
            if volumes
            else 0.0
        )

        if average_volume <= 0:
            return {
                "high_volume_nodes": [],
                "low_volume_nodes": [],
                "highest_volume": 0.0,
                "average_bin_volume": 0.0,
            }

        high_nodes: List[Dict[str, Any]] = []
        low_nodes: List[Dict[str, Any]] = []

        for index, value in enumerate(
            volumes
        ):

            ratio = (
                value / average_volume
            )

            node = {
                "index": index,
                "price": prices[index],
                "volume": round(
                    value,
                    8,
                ),
                "relative_volume": round(
                    ratio,
                    4,
                ),
            }

            if ratio >= self.HVN_THRESHOLD:
                high_nodes.append(node)

            elif ratio <= self.LVN_THRESHOLD:
                low_nodes.append(node)

        high_nodes.sort(
            key=lambda item: item["volume"],
            reverse=True,
        )

        low_nodes.sort(
            key=lambda item: item["volume"],
        )

        return {
            "high_volume_nodes": high_nodes,
            "low_volume_nodes": low_nodes,
            "highest_volume": max(volumes),
            "average_bin_volume": (
                average_volume
            ),
        }

    # ==============================================================
    # PRICE LOCATION
    # ==============================================================

    @staticmethod
    def _classify_price_location(
        current_price: float,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:

        val = float(profile["val"])
        vah = float(profile["vah"])
        poc = float(profile["poc"])

        if current_price < val:

            classification = "BELOW_VALUE"
            zone = "BELOW_VALUE_AREA"

        elif current_price > vah:

            classification = "ABOVE_VALUE"
            zone = "ABOVE_VALUE_AREA"

        else:

            classification = "INSIDE_VALUE"

            if current_price < poc:
                zone = "VALUE_BELOW_POC"

            elif current_price > poc:
                zone = "VALUE_ABOVE_POC"

            else:
                zone = "AT_POC"

        range_size = float(
            profile["range_size"]
        )

        if range_size > 0:

            ratio = (
                current_price
                - float(profile["range_low"])
            ) / range_size

        else:
            ratio = 0.0

        return {
            "classification": classification,
            "zone": zone,
            "ratio": round(
                max(
                    0.0,
                    min(ratio, 1.0),
                ),
                4,
            ),
            "percentage": round(
                max(
                    0.0,
                    min(ratio * 100.0, 100.0),
                ),
                2,
            ),
        }

    # ==============================================================
    # POC DISTANCE
    # ==============================================================

    @staticmethod
    def _distance_from_poc(
        current_price: float,
        poc: float,
        range_high: float,
        range_low: float,
    ) -> Dict[str, Any]:

        distance = (
            current_price - poc
        )

        range_size = (
            range_high - range_low
        )

        ratio = (
            abs(distance) / range_size
            if range_size > 0
            else 0.0
        )

        if distance > 0:
            side = "ABOVE_POC"

        elif distance < 0:
            side = "BELOW_POC"

        else:
            side = "AT_POC"

        return {
            "price": round(
                distance,
                8,
            ),
            "ratio": round(
                ratio,
                4,
            ),
            "percentage": round(
                ratio * 100.0,
                2,
            ),
            "side": side,
        }

    # ==============================================================
    # ACCEPTANCE / REJECTION
    # ==============================================================

    def _evaluate_acceptance(
        self,
        profile_candles: Sequence[Dict[str, Any]],
        profile: Dict[str, Any],
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Evaluate whether recent price action is accepting or rejecting
        the Value Area.

        This is contextual information, not a trading signal.
        """

        val = float(profile["val"])
        vah = float(profile["vah"])

        recent = profile_candles[
            max(
                0,
                len(profile_candles) - 5,
            ):
        ]

        inside = 0
        above = 0
        below = 0

        closes = []

        for candle in recent:

            close = float(
                candle["close"]
            )

            closes.append(close)

            if close < val:
                below += 1

            elif close > vah:
                above += 1

            else:
                inside += 1

        total = max(
            len(recent),
            1,
        )

        if inside / total >= 0.60:
            state = "VALUE_ACCEPTANCE"

        elif above / total >= 0.60:
            state = "ABOVE_VALUE_ACCEPTANCE"

        elif below / total >= 0.60:
            state = "BELOW_VALUE_ACCEPTANCE"

        elif current_price > vah:
            state = "ABOVE_VALUE_TEST"

        elif current_price < val:
            state = "BELOW_VALUE_TEST"

        else:
            state = "VALUE_TRANSITION"

        rejection = self._detect_value_rejection(
            recent,
            val,
            vah,
        )

        return {
            "state": state,
            "recent_candles": len(recent),
            "inside_value_count": inside,
            "above_value_count": above,
            "below_value_count": below,
            "inside_value_ratio": round(
                inside / total,
                4,
            ),
            "above_value_ratio": round(
                above / total,
                4,
            ),
            "below_value_ratio": round(
                below / total,
                4,
            ),
            "value_rejection": rejection,
        }

    @staticmethod
    def _detect_value_rejection(
        candles: Sequence[Dict[str, Any]],
        val: float,
        vah: float,
    ) -> Dict[str, Any]:

        bullish_rejection = False
        bearish_rejection = False

        for candle in candles:

            high = float(
                candle["high"]
            )

            low = float(
                candle["low"]
            )

            close = float(
                candle["close"]
            )

            if (
                low < val
                and close > val
            ):
                bullish_rejection = True

            if (
                high > vah
                and close < vah
            ):
                bearish_rejection = True

        if (
            bullish_rejection
            and bearish_rejection
        ):
            classification = (
                "TWO_SIDED_REJECTION"
            )

        elif bullish_rejection:
            classification = (
                "LOWER_VALUE_REJECTION"
            )

        elif bearish_rejection:
            classification = (
                "UPPER_VALUE_REJECTION"
            )

        else:
            classification = "NONE"

        return {
            "detected": (
                bullish_rejection
                or bearish_rejection
            ),
            "bullish": bullish_rejection,
            "bearish": bearish_rejection,
            "classification": classification,
        }

    # ==============================================================
    # PROFILE QUALITY
    # ==============================================================

    @staticmethod
    def _calculate_profile_quality(
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Estimate the quality of the constructed profile.

        This evaluates the mathematical quality of the distribution,
        not trade direction.
        """

        volumes = profile["volumes"]

        if not volumes:
            return {
                "score": 0.0,
                "classification": "INVALID",
                "concentration": 0.0,
                "distribution_coverage": 0.0,
            }

        total = sum(volumes)

        if total <= 0:
            return {
                "score": 0.0,
                "classification": "INVALID",
                "concentration": 0.0,
                "distribution_coverage": 0.0,
            }

        non_zero = sum(
            1
            for value in volumes
            if value > 0
        )

        coverage = (
            non_zero / len(volumes)
        )

        highest = max(volumes)

        concentration = (
            highest / total
        )

        # A profile with volume distributed across multiple bins is
        # generally more informative than one containing virtually
        # all volume in one price bin.
        coverage_score = min(
            coverage * 100.0,
            100.0,
        )

        concentration_score = min(
            concentration * 100.0,
            100.0,
        )

        score = (
            coverage_score * 0.60
            + concentration_score * 0.40
        )

        if score >= 70.0:
            classification = "HIGH"
        elif score >= 45.0:
            classification = "MODERATE"
        else:
            classification = "LOW"

        return {
            "score": round(
                min(score, 100.0),
                2,
            ),
            "classification": classification,
            "concentration": round(
                concentration,
                4,
            ),
            "distribution_coverage": round(
                coverage,
                4,
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
            "component": (
                "volume_profile_quality"
            ),

            "candle_count": candle_count,
            "profile_candle_count": 0,

            "lookback": self.lookback,
            "bins": self.bins,
            "value_area_percent": (
                self.value_area_percent
            ),

            "volume_available": False,
            "volume_source": "none",

            "current_price": None,

            "profile": None,
            "price_location": None,
            "distance_from_poc": None,

            "nodes": {
                "high_volume_nodes": [],
                "low_volume_nodes": [],
                "highest_volume": 0.0,
                "average_bin_volume": 0.0,
            },

            "acceptance": None,

            "quality": {
                "score": 0.0,
                "classification": "INSUFFICIENT_DATA",
                "concentration": 0.0,
                "distribution_coverage": 0.0,
            },

            "profile_quality_score": 0.0,

            "high_volume_nodes": [],
            "low_volume_nodes": [],

            "poc": None,
            "value_area_high": None,
            "value_area_low": None,

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }

    # ==============================================================
    # NO VOLUME
    # ==============================================================

    def _no_volume_result(
        self,
        candle_count: int,
        current_price: Optional[float],
    ) -> Dict[str, Any]:

        return {
            "status": "NO_VOLUME_DATA",
            "technical_only": True,
            "component": (
                "volume_profile_quality"
            ),

            "candle_count": candle_count,
            "profile_candle_count": min(
                candle_count,
                self.lookback,
            ),

            "lookback": self.lookback,
            "bins": self.bins,
            "value_area_percent": (
                self.value_area_percent
            ),

            "volume_available": False,
            "volume_source": "none",

            "current_price": current_price,

            "profile": None,
            "price_location": None,
            "distance_from_poc": None,

            "nodes": {
                "high_volume_nodes": [],
                "low_volume_nodes": [],
                "highest_volume": 0.0,
                "average_bin_volume": 0.0,
            },

            "acceptance": None,

            "quality": {
                "score": 0.0,
                "classification": "NO_VOLUME_DATA",
                "concentration": 0.0,
                "distribution_coverage": 0.0,
            },

            "profile_quality_score": 0.0,

            "high_volume_nodes": [],
            "low_volume_nodes": [],

            "poc": None,
            "value_area_high": None,
            "value_area_low": None,

            "structure_context": {
                "provided": False,
                "used": False,
            },
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_volume_profile_quality(
    candles: Any,
    volume: Optional[Any] = None,
    lookback: int = (
        VolumeProfileQuality.DEFAULT_LOOKBACK
    ),
    bins: int = (
        VolumeProfileQuality.DEFAULT_BINS
    ),
    value_area_percent: float = (
        VolumeProfileQuality.DEFAULT_VALUE_AREA_PERCENT
    ),
) -> Dict[str, Any]:

    analyzer = VolumeProfileQuality(
        lookback=lookback,
        bins=bins,
        value_area_percent=value_area_percent,
    )

    return analyzer.analyze(
        candles=candles,
        volume=volume,
    )


# ==================================================================
# COMPATIBILITY ALIAS
# ==================================================================

VolumeProfile = VolumeProfileQuality