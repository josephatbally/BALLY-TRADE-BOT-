"""
BALLY FLOW - AI Pattern Memory

Pattern-memory layer for the AI system.

RESPONSIBILITIES
----------------
This module:

    - stores standardized historical trade-pattern outcomes
    - creates compact pattern signatures
    - retrieves similar historical patterns
    - calculates historical success statistics
    - provides historical evidence to downstream AI layers
    - remains independent from execution and risk management

This module MUST NOT:

    - make the final BUY / SELL / NO_TRADE decision
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size
    - override Technical Engine
    - override Hybrid Engine
    - perform fundamental analysis

DECISION AUTHORITY
------------------
    Pattern Memory -> supporting AI evidence
    AI Confidence -> confidence aggregation
    Hybrid Engine / Decision Engine -> trading decision
"""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any, Dict, List, Optional, Sequence, Tuple


class PatternMemory:
    """
    Stores and retrieves historical pattern outcomes.

    Memory is intentionally kept in-process.

    Persistent database/storage can be connected later without
    changing the public API of this module.
    """

    VERSION = "1.0.0"

    SUPPORTED_TIMEFRAMES = (
        "H4",
        "H1",
        "M15",
    )

    MAX_MEMORY_RECORDS = 5000

    def __init__(self, max_records: int = MAX_MEMORY_RECORDS) -> None:
        self.name = "BALLY FLOW AI Pattern Memory"

        try:
            max_records = int(max_records)
        except (TypeError, ValueError):
            max_records = self.MAX_MEMORY_RECORDS

        self.max_records = max(
            1,
            min(max_records, self.MAX_MEMORY_RECORDS),
        )

        self._memory: List[Dict[str, Any]] = []

    # ==============================================================
    # PUBLIC INFORMATION
    # ==============================================================

    def info(self) -> Dict[str, Any]:
        """Return module information."""

        return {
            "name": self.name,
            "version": self.VERSION,
            "status": "READY",
            "memory_records": len(self._memory),
            "max_memory_records": self.max_records,
            "supported_timeframes": list(self.SUPPORTED_TIMEFRAMES),
            "outputs": [
                "pattern_signature",
                "similar_patterns",
                "historical_win_rate",
                "historical_sample_size",
                "historical_bias",
                "pattern_strength",
            ],
            "decision_authority": "downstream_ai_decision_layers",
            "technical_analysis": True,
            "fundamental_analysis": False,
            "hybrid_decision": False,
            "risk_management": False,
            "execution": False,
            "order_placement": False,
        }

    # ==============================================================
    # PATTERN SIGNATURE
    # ==============================================================

    def create_signature(
        self,
        technical_analysis: Optional[Dict[str, Any]] = None,
        market_profile: Optional[Dict[str, Any]] = None,
        timeframe: Optional[str] = None,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a compact standardized pattern signature.

        The signature intentionally uses high-level characteristics
        rather than storing the entire technical-analysis payload.
        """

        technical_analysis = (
            technical_analysis
            if isinstance(technical_analysis, dict)
            else {}
        )

        market_profile = (
            market_profile
            if isinstance(market_profile, dict)
            else {}
        )

        tf = self._normalize_timeframe(timeframe)

        structure = self._extract_component(
            technical_analysis,
            "market_structure",
        )

        liquidity = self._extract_component(
            technical_analysis,
            "liquidity",
        )

        order_blocks = self._extract_component(
            technical_analysis,
            "order_blocks",
        )

        fvg = self._extract_component(
            technical_analysis,
            "fvg",
        )

        premium_discount = self._extract_component(
            technical_analysis,
            "premium_discount",
        )

        supply_demand = self._extract_component(
            technical_analysis,
            "supply_demand",
        )

        volume_profile = self._extract_component(
            technical_analysis,
            "volume_profile",
        )

        trend = self._extract_direction(
            market_profile.get("trend"),
            structure.get("bias"),
        )

        momentum = self._extract_direction(
            market_profile.get("momentum"),
        )

        volatility = self._extract_regime(
            market_profile.get("volatility"),
        )

        market_regime = self._normalize_text(
            market_profile.get("market_regime")
        )

        price_location = self._normalize_text(
            market_profile.get("price_location", {}).get("position")
            if isinstance(market_profile.get("price_location"), dict)
            else None
        )

        structure_bias = self._normalize_text(
            structure.get("bias")
        )

        bos_count = self._count_events(
            structure.get("bos")
        )

        choch_count = self._count_events(
            structure.get("choch")
        )

        liquidity_sweeps = self._count_events(
            liquidity.get("sweeps")
        )

        valid_order_blocks = self._extract_nested_count(
            order_blocks,
            "valid_order_blocks",
        )

        valid_fvgs = self._extract_nested_count(
            fvg,
            "valid_fvgs",
        )

        valid_supply_demand = self._extract_nested_count(
            supply_demand,
            "valid_zones",
        )

        profile_quality = self._safe_float(
            volume_profile.get("profile_quality_score")
        )

        premium = bool(premium_discount.get("premium", False))
        discount = bool(premium_discount.get("discount", False))

        signature = {
            "symbol": self._normalize_symbol(symbol),
            "timeframe": tf,
            "trend": trend,
            "momentum": momentum,
            "volatility": volatility,
            "market_regime": market_regime or "UNKNOWN",
            "price_location": price_location or "UNKNOWN",
            "structure_bias": structure_bias or "UNKNOWN",
            "bos_count": bos_count,
            "choch_count": choch_count,
            "liquidity_sweeps": liquidity_sweeps,
            "valid_order_blocks": valid_order_blocks,
            "valid_fvgs": valid_fvgs,
            "valid_supply_demand": valid_supply_demand,
            "volume_profile_quality": (
                round(profile_quality, 2)
                if profile_quality is not None
                else None
            ),
            "premium": premium,
            "discount": discount,
        }

        return signature

    # ==============================================================
    # STORE PATTERN
    # ==============================================================

    def remember(
        self,
        pattern: Optional[Dict[str, Any]] = None,
        outcome: Optional[str] = None,
        pnl: Optional[float] = None,
        signal: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Store a historical pattern outcome.

        outcome:
            WIN, LOSS, BREAKEVEN, or UNKNOWN

        signal:
            BUY, SELL, NO_TRADE, or UNKNOWN

        This records history only. It does not influence execution
        directly.
        """

        if not isinstance(pattern, dict):
            raise TypeError("pattern must be a dictionary")

        normalized_outcome = self._normalize_outcome(outcome)
        normalized_signal = self._normalize_signal(signal)

        pnl_value = self._safe_float(pnl)

        record = {
            "pattern": dict(pattern),
            "outcome": normalized_outcome,
            "signal": normalized_signal,
            "pnl": pnl_value,
            "metadata": (
                dict(metadata)
                if isinstance(metadata, dict)
                else {}
            ),
        }

        self._memory.append(record)

        if len(self._memory) > self.max_records:
            excess = len(self._memory) - self.max_records
            del self._memory[:excess]

        return {
            "status": "RECORDED",
            "memory_size": len(self._memory),
            "record": record,
        }

    # ==============================================================
    # SIMILARITY
    # ==============================================================

    def similarity(
        self,
        pattern_a: Dict[str, Any],
        pattern_b: Dict[str, Any],
    ) -> float:
        """
        Calculate similarity between two pattern signatures.

        Returns 0.0 to 100.0.
        """

        if not isinstance(pattern_a, dict):
            return 0.0

        if not isinstance(pattern_b, dict):
            return 0.0

        fields = (
            "timeframe",
            "trend",
            "momentum",
            "volatility",
            "market_regime",
            "price_location",
            "structure_bias",
            "bos_count",
            "choch_count",
            "liquidity_sweeps",
            "valid_order_blocks",
            "valid_fvgs",
            "valid_supply_demand",
            "volume_profile_quality",
            "premium",
            "discount",
        )

        weights = {
            "timeframe": 1.5,
            "trend": 2.0,
            "momentum": 1.5,
            "volatility": 1.0,
            "market_regime": 1.5,
            "price_location": 1.5,
            "structure_bias": 2.0,
            "bos_count": 1.0,
            "choch_count": 1.0,
            "liquidity_sweeps": 1.0,
            "valid_order_blocks": 1.0,
            "valid_fvgs": 1.0,
            "valid_supply_demand": 1.0,
            "volume_profile_quality": 1.0,
            "premium": 0.5,
            "discount": 0.5,
        }

        total_weight = 0.0
        matched_weight = 0.0

        for field in fields:
            weight = weights.get(field, 1.0)

            if field not in pattern_a or field not in pattern_b:
                continue

            a = pattern_a.get(field)
            b = pattern_b.get(field)

            total_weight += weight

            if self._field_similarity(field, a, b):
                matched_weight += weight

        if total_weight <= 0:
            return 0.0

        return round(
            (matched_weight / total_weight) * 100.0,
            2,
        )

    # ==============================================================
    # FIND SIMILAR
    # ==============================================================

    def find_similar(
        self,
        pattern: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        minimum_similarity: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Find historically similar patterns.
        """

        if not isinstance(pattern, dict):
            raise TypeError("pattern must be a dictionary")

        try:
            limit = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit = 10

        threshold = self._clamp(
            self._safe_float(minimum_similarity, 60.0),
            0.0,
            100.0,
        )

        matches: List[Dict[str, Any]] = []

        for record in self._memory:
            historical_pattern = record.get("pattern", {})

            score = self.similarity(
                pattern,
                historical_pattern,
            )

            if score < threshold:
                continue

            matches.append(
                {
                    "similarity": score,
                    "outcome": record.get(
                        "outcome",
                        "UNKNOWN",
                    ),
                    "signal": record.get(
                        "signal",
                        "UNKNOWN",
                    ),
                    "pnl": record.get("pnl"),
                    "pattern": historical_pattern,
                    "metadata": record.get(
                        "metadata",
                        {},
                    ),
                }
            )

        matches.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        matches = matches[:limit]

        return {
            "status": "READY",
            "query_pattern": pattern,
            "match_count": len(matches),
            "matches": matches,
        }

    # ==============================================================
    # HISTORICAL STATISTICS
    # ==============================================================

    def statistics(
        self,
        matches: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate historical outcome statistics.

        If matches are supplied, statistics are calculated only
        from those matches. Otherwise the complete memory is used.
        """

        records = (
            list(matches)
            if matches is not None
            else list(self._memory)
        )

        outcomes = Counter(
            self._normalize_outcome(
                record.get("outcome")
            )
            for record in records
            if isinstance(record, dict)
        )

        wins = outcomes.get("WIN", 0)
        losses = outcomes.get("LOSS", 0)
        breakeven = outcomes.get("BREAKEVEN", 0)

        resolved = wins + losses + breakeven

        if resolved > 0:
            win_rate = (
                wins / resolved
            ) * 100.0
        else:
            win_rate = 0.0

        if wins > losses:
            bias = "POSITIVE"
        elif losses > wins:
            bias = "NEGATIVE"
        else:
            bias = "NEUTRAL"

        if resolved >= 20:
            strength = "STRONG"
        elif resolved >= 10:
            strength = "MODERATE"
        elif resolved >= 3:
            strength = "WEAK"
        else:
            strength = "INSUFFICIENT"

        return {
            "status": "READY",
            "sample_size": len(records),
            "resolved_sample_size": resolved,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "unknown": outcomes.get("UNKNOWN", 0),
            "win_rate": round(win_rate, 2),
            "historical_bias": bias,
            "pattern_strength": strength,
        }

    # ==============================================================
    # PATTERN ANALYSIS
    # ==============================================================

    def analyze_pattern(
        self,
        pattern: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        minimum_similarity: float = 60.0,
    ) -> Dict[str, Any]:
        """
        Complete pattern-memory analysis.

        This is the primary downstream API.
        """

        if not isinstance(pattern, dict):
            raise TypeError("pattern must be a dictionary")

        similar = self.find_similar(
            pattern=pattern,
            limit=limit,
            minimum_similarity=minimum_similarity,
        )

        statistics = self.statistics(
            matches=similar["matches"],
        )

        return {
            "status": "READY",
            "pattern": pattern,
            "similar_patterns": similar["matches"],
            "similar_pattern_count": similar["match_count"],
            "historical_win_rate": statistics["win_rate"],
            "historical_sample_size": statistics[
                "resolved_sample_size"
            ],
            "historical_bias": statistics[
                "historical_bias"
            ],
            "pattern_strength": statistics[
                "pattern_strength"
            ],
            "statistics": statistics,
            "decision": None,
            "decision_authority": (
                "downstream_ai_decision_layers"
            ),
        }

    # ==============================================================
    # MEMORY MANAGEMENT
    # ==============================================================

    def clear(self) -> Dict[str, Any]:
        """Clear in-memory historical patterns."""

        previous_size = len(self._memory)
        self._memory.clear()

        return {
            "status": "CLEARED",
            "previous_memory_size": previous_size,
            "memory_size": 0,
        }

    def size(self) -> int:
        """Return current memory size."""

        return len(self._memory)

    # ==============================================================
    # INTERNAL HELPERS
    # ==============================================================

    @staticmethod
    def _extract_component(
        technical_analysis: Dict[str, Any],
        name: str,
    ) -> Dict[str, Any]:

        value = technical_analysis.get(name)

        return value if isinstance(value, dict) else {}

    @staticmethod
    def _normalize_symbol(
        symbol: Optional[str],
    ) -> str:

        if not isinstance(symbol, str):
            return "UNKNOWN"

        value = symbol.strip().upper()

        return value or "UNKNOWN"

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: Optional[str],
    ) -> str:

        if not isinstance(timeframe, str):
            return "UNKNOWN"

        value = timeframe.strip().upper()

        if value in cls.SUPPORTED_TIMEFRAMES:
            return value

        return "UNKNOWN"

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip().upper()

        return str(value).strip().upper()

    @classmethod
    def _extract_direction(
        cls,
        *values: Any,
    ) -> str:

        for value in values:
            if isinstance(value, dict):
                value = value.get("direction")

            text = cls._normalize_text(value)

            if text:
                return text

        return "UNKNOWN"

    @classmethod
    def _extract_regime(
        cls,
        value: Any,
    ) -> str:

        if isinstance(value, dict):
            value = value.get("regime")

        text = cls._normalize_text(value)

        return text or "UNKNOWN"

    @staticmethod
    def _count_events(
        value: Any,
    ) -> int:

        if isinstance(value, (list, tuple)):
            return len(value)

        if isinstance(value, dict):
            for key in (
                "count",
                "total",
                "events",
            ):
                candidate = value.get(key)

                if isinstance(candidate, (list, tuple)):
                    return len(candidate)

                try:
                    if candidate is not None:
                        return max(0, int(candidate))
                except (TypeError, ValueError):
                    pass

        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _extract_nested_count(
        cls,
        component: Dict[str, Any],
        key: str,
    ) -> int:

        if not isinstance(component, dict):
            return 0

        return cls._count_events(
            component.get(key)
        )

    @staticmethod
    def _safe_float(
        value: Any,
        default: Optional[float] = None,
    ) -> Optional[float]:

        try:
            result = float(value)

            if not isfinite(result):
                return default

            return result

        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(maximum, value),
        )

    @staticmethod
    def _normalize_signal(
        signal: Optional[str],
    ) -> str:

        if not isinstance(signal, str):
            return "UNKNOWN"

        value = signal.strip().upper()

        if value in {
            "BUY",
            "SELL",
            "NO_TRADE",
        }:
            return value

        return "UNKNOWN"

    @staticmethod
    def _normalize_outcome(
        outcome: Optional[str],
    ) -> str:

        if not isinstance(outcome, str):
            return "UNKNOWN"

        value = outcome.strip().upper()

        if value in {
            "WIN",
            "LOSS",
            "BREAKEVEN",
            "UNKNOWN",
        }:
            return value

        return "UNKNOWN"

    def _field_similarity(
        self,
        field: str,
        a: Any,
        b: Any,
    ) -> bool:

        if a is None or b is None:
            return False

        if field in {
            "bos_count",
            "choch_count",
            "liquidity_sweeps",
            "valid_order_blocks",
            "valid_fvgs",
            "valid_supply_demand",
        }:
            try:
                a_value = float(a)
                b_value = float(b)

                return abs(a_value - b_value) <= 1.0

            except (TypeError, ValueError):
                return False

        if field == "volume_profile_quality":
            try:
                a_value = float(a)
                b_value = float(b)

                return abs(a_value - b_value) <= 15.0

            except (TypeError, ValueError):
                return False

        return str(a).strip().upper() == str(
            b
        ).strip().upper()


# ==================================================================
# MODULE-LEVEL API
# ==================================================================

_PATTERN_MEMORY = PatternMemory()


def pattern_memory_info() -> Dict[str, Any]:
    """Return Pattern Memory information."""

    return _PATTERN_MEMORY.info()


def create_pattern_signature(
    technical_analysis: Optional[Dict[str, Any]] = None,
    market_profile: Optional[Dict[str, Any]] = None,
    timeframe: Optional[str] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized pattern signature."""

    return _PATTERN_MEMORY.create_signature(
        technical_analysis=technical_analysis,
        market_profile=market_profile,
        timeframe=timeframe,
        symbol=symbol,
    )


def remember_pattern(
    pattern: Dict[str, Any],
    outcome: Optional[str] = None,
    pnl: Optional[float] = None,
    signal: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Store a historical pattern."""

    return _PATTERN_MEMORY.remember(
        pattern=pattern,
        outcome=outcome,
        pnl=pnl,
        signal=signal,
        metadata=metadata,
    )


def find_similar_patterns(
    pattern: Dict[str, Any],
    limit: int = 10,
    minimum_similarity: float = 60.0,
) -> Dict[str, Any]:
    """Find similar historical patterns."""

    return _PATTERN_MEMORY.find_similar(
        pattern=pattern,
        limit=limit,
        minimum_similarity=minimum_similarity,
    )


def analyze_pattern_memory(
    pattern: Dict[str, Any],
    limit: int = 20,
    minimum_similarity: float = 60.0,
) -> Dict[str, Any]:
    """Analyze a pattern against historical memory."""

    return _PATTERN_MEMORY.analyze_pattern(
        pattern=pattern,
        limit=limit,
        minimum_similarity=minimum_similarity,
    )


def pattern_memory_statistics() -> Dict[str, Any]:
    """Return complete memory statistics."""

    return _PATTERN_MEMORY.statistics()


def clear_pattern_memory() -> Dict[str, Any]:
    """Clear the in-memory pattern database."""

    return _PATTERN_MEMORY.clear()


__all__ = [
    "PatternMemory",
    "pattern_memory_info",
    "create_pattern_signature",
    "remember_pattern",
    "find_similar_patterns",
    "analyze_pattern_memory",
    "pattern_memory_statistics",
    "clear_pattern_memory",
]