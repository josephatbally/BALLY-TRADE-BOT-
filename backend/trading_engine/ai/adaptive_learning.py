"""
BALLY FLOW - AI Adaptive Learning

Adaptive learning layer for BALLY FLOW.

RESPONSIBILITIES
----------------
This module:

    - learns from completed trade outcomes
    - tracks signal performance
    - tracks pattern performance
    - calculates adaptive performance scores
    - detects improving/degrading performance
    - provides learning evidence to downstream AI layers
    - remains independent from execution and risk management

This module MUST NOT:

    - place MT5 orders
    - execute trades
    - manage risk
    - calculate position size
    - override Technical Engine
    - override Hybrid Engine
    - make the authoritative BUY / SELL / NO_TRADE decision
    - disable trading by itself

ARCHITECTURE
------------
    Historical Outcomes
           |
           v
    Adaptive Learning
           |
           +--> Signal Performance
           +--> Pattern Performance
           +--> Market Performance
           +--> Recent Performance
           |
           v
    AI Evidence
           |
           v
    AI Confidence / Decision Engine

Decision authority remains downstream.
"""

from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any, Dict, Iterable, List, Optional


class AdaptiveLearning:
    """
    BALLY FLOW adaptive-learning engine.

    The engine keeps lightweight in-memory learning statistics.

    Persistent storage can be connected later without changing
    the public API.
    """

    VERSION = "1.0.0"

    SUPPORTED_MARKETS = (
        "XAUUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "XAGUSD",
        "NASDAQ",
    )

    SUPPORTED_TIMEFRAMES = (
        "H4",
        "H1",
        "M15",
    )

    MAX_RECORDS = 5000

    def __init__(
        self,
        max_records: int = MAX_RECORDS,
    ) -> None:

        self.name = "BALLY FLOW AI Adaptive Learning"

        try:
            max_records = int(max_records)
        except (TypeError, ValueError):
            max_records = self.MAX_RECORDS

        self.max_records = max(
            1,
            min(max_records, self.MAX_RECORDS),
        )

        self._records: List[Dict[str, Any]] = []

    # ==============================================================
    # INFORMATION
    # ==============================================================

    def info(self) -> Dict[str, Any]:
        """
        Return adaptive-learning module information.
        """

        return {
            "name": self.name,
            "version": self.VERSION,
            "status": "READY",
            "record_count": len(self._records),
            "max_records": self.max_records,
            "supported_markets": list(
                self.SUPPORTED_MARKETS
            ),
            "supported_timeframes": list(
                self.SUPPORTED_TIMEFRAMES
            ),
            "outputs": [
                "learning_score",
                "performance_score",
                "signal_performance",
                "market_performance",
                "pattern_performance",
                "recent_performance",
                "learning_bias",
            ],
            "decision_authority": (
                "downstream_ai_decision_layers"
            ),
            "technical_analysis": True,
            "fundamental_analysis": False,
            "hybrid_decision": False,
            "risk_management": False,
            "execution": False,
            "order_placement": False,
        }

    # ==============================================================
    # RECORD OUTCOME
    # ==============================================================

    def record_outcome(
        self,
        signal: Optional[str] = None,
        outcome: Optional[str] = None,
        pnl: Optional[float] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        pattern_signature: Optional[
            Dict[str, Any]
        ] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record the result of a completed trading opportunity.

        This function records history only.

        It does not change:
            - trading mode
            - risk settings
            - execution permissions
            - final decision
        """

        normalized_signal = self._normalize_signal(
            signal
        )

        normalized_outcome = self._normalize_outcome(
            outcome
        )

        normalized_symbol = self._normalize_symbol(
            symbol
        )

        normalized_timeframe = self._normalize_timeframe(
            timeframe
        )

        pnl_value = self._safe_float(pnl)

        confidence_value = self._safe_float(
            confidence
        )

        record = {
            "signal": normalized_signal,
            "outcome": normalized_outcome,
            "pnl": pnl_value,
            "symbol": normalized_symbol,
            "timeframe": normalized_timeframe,
            "pattern_signature": (
                dict(pattern_signature)
                if isinstance(pattern_signature, dict)
                else {}
            ),
            "confidence": confidence_value,
            "metadata": (
                dict(metadata)
                if isinstance(metadata, dict)
                else {}
            ),
        }

        self._records.append(record)

        if len(self._records) > self.max_records:
            excess = (
                len(self._records)
                - self.max_records
            )

            del self._records[:excess]

        return {
            "status": "RECORDED",
            "record_count": len(self._records),
            "record": record,
        }

    # ==============================================================
    # OUTCOME SCORE
    # ==============================================================

    @staticmethod
    def _outcome_score(
        outcome: str,
    ) -> float:
        """
        Convert an outcome to a learning score.

        WIN       = +1.0
        BREAKEVEN =  0.0
        LOSS      = -1.0
        UNKNOWN   =  0.0
        """

        outcome = str(outcome).upper()

        if outcome == "WIN":
            return 1.0

        if outcome == "LOSS":
            return -1.0

        return 0.0

    # ==============================================================
    # PERFORMANCE
    # ==============================================================

    def calculate_performance(
        self,
        records: Optional[
            Iterable[Dict[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Calculate aggregate learning performance.
        """

        source = (
            list(records)
            if records is not None
            else list(self._records)
        )

        wins = 0
        losses = 0
        breakeven = 0
        unknown = 0

        pnl_total = 0.0

        for record in source:

            if not isinstance(record, dict):
                continue

            outcome = self._normalize_outcome(
                record.get("outcome")
            )

            if outcome == "WIN":
                wins += 1

            elif outcome == "LOSS":
                losses += 1

            elif outcome == "BREAKEVEN":
                breakeven += 1

            else:
                unknown += 1

            pnl = self._safe_float(
                record.get("pnl")
            )

            if pnl is not None:
                pnl_total += pnl

        resolved = (
            wins
            + losses
            + breakeven
        )

        if resolved:
            win_rate = (
                wins / resolved
            ) * 100.0
        else:
            win_rate = 0.0

        if resolved:
            performance_score = (
                (
                    wins
                    - losses
                )
                / resolved
            ) * 100.0
        else:
            performance_score = 0.0

        performance_score = self._clamp(
            performance_score,
            -100.0,
            100.0,
        )

        if performance_score >= 25.0:
            bias = "POSITIVE"

        elif performance_score <= -25.0:
            bias = "NEGATIVE"

        else:
            bias = "NEUTRAL"

        return {
            "status": "READY",
            "sample_size": len(source),
            "resolved_sample_size": resolved,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "unknown": unknown,
            "win_rate": round(
                win_rate,
                2,
            ),
            "performance_score": round(
                performance_score,
                2,
            ),
            "pnl_total": round(
                pnl_total,
                2,
            ),
            "learning_bias": bias,
        }

    # ==============================================================
    # SIGNAL PERFORMANCE
    # ==============================================================

    def signal_performance(
        self,
        signal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate performance for a specific signal.

        Example:
            BUY
            SELL
        """

        normalized_signal = (
            self._normalize_signal(signal)
        )

        records = [
            record
            for record in self._records
            if record.get("signal")
            == normalized_signal
        ]

        performance = self.calculate_performance(
            records
        )

        return {
            "status": "READY",
            "signal": normalized_signal,
            **performance,
        }

    # ==============================================================
    # MARKET PERFORMANCE
    # ==============================================================

    def market_performance(
        self,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate historical performance for a market.
        """

        normalized_symbol = (
            self._normalize_symbol(symbol)
        )

        records = [
            record
            for record in self._records
            if record.get("symbol")
            == normalized_symbol
        ]

        performance = self.calculate_performance(
            records
        )

        return {
            "status": "READY",
            "symbol": normalized_symbol,
            **performance,
        }

    # ==============================================================
    # TIMEFRAME PERFORMANCE
    # ==============================================================

    def timeframe_performance(
        self,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate historical performance for a timeframe.
        """

        normalized_timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        records = [
            record
            for record in self._records
            if record.get("timeframe")
            == normalized_timeframe
        ]

        performance = self.calculate_performance(
            records
        )

        return {
            "status": "READY",
            "timeframe": normalized_timeframe,
            **performance,
        }

    # ==============================================================
    # PATTERN PERFORMANCE
    # ==============================================================

    def pattern_performance(
        self,
        pattern_signature: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Calculate performance for records having a matching
        pattern signature.

        Exact signature fields are compared.
        """

        if not isinstance(
            pattern_signature,
            dict,
        ):
            pattern_signature = {}

        matches: List[
            Dict[str, Any]
        ] = []

        for record in self._records:

            historical = record.get(
                "pattern_signature"
            )

            if not isinstance(
                historical,
                dict,
            ):
                continue

            if self._pattern_matches(
                pattern_signature,
                historical,
            ):
                matches.append(record)

        performance = self.calculate_performance(
            matches
        )

        return {
            "status": "READY",
            "pattern_match_count": len(matches),
            "pattern_performance": performance,
        }

    # ==============================================================
    # RECENT PERFORMANCE
    # ==============================================================

    def recent_performance(
        self,
        lookback: int = 20,
    ) -> Dict[str, Any]:
        """
        Calculate performance using only the most recent
        learning records.
        """

        try:
            lookback = int(lookback)
        except (TypeError, ValueError):
            lookback = 20

        lookback = max(
            1,
            min(
                lookback,
                self.max_records,
            ),
        )

        records = self._records[-lookback:]

        performance = self.calculate_performance(
            records
        )

        return {
            "status": "READY",
            "lookback": lookback,
            **performance,
        }

    # ==============================================================
    # LEARNING SCORE
    # ==============================================================

    def learning_score(
        self,
        signal: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        pattern_signature: Optional[
            Dict[str, Any]
        ] = None,
        recent_lookback: int = 20,
    ) -> Dict[str, Any]:
        """
        Produce a standardized adaptive-learning score.

        The score is supporting evidence only.

        It does NOT become the trading decision.
        """

        overall = self.calculate_performance()

        signal_result = (
            self.signal_performance(signal)
            if signal is not None
            else {
                "performance_score": 0.0,
                "sample_size": 0,
                "win_rate": 0.0,
            }
        )

        market_result = (
            self.market_performance(symbol)
            if symbol is not None
            else {
                "performance_score": 0.0,
                "sample_size": 0,
                "win_rate": 0.0,
            }
        )

        timeframe_result = (
            self.timeframe_performance(
                timeframe
            )
            if timeframe is not None
            else {
                "performance_score": 0.0,
                "sample_size": 0,
                "win_rate": 0.0,
            }
        )

        pattern_result = (
            self.pattern_performance(
                pattern_signature
            )
            if isinstance(
                pattern_signature,
                dict,
            )
            else {
                "pattern_match_count": 0,
                "pattern_performance": {
                    "performance_score": 0.0,
                    "sample_size": 0,
                    "win_rate": 0.0,
                },
            }
        )

        pattern_performance = pattern_result.get(
            "pattern_performance",
            {},
        )

        recent = self.recent_performance(
            recent_lookback
        )

        # ----------------------------------------------------------
        # Only use components with meaningful samples.
        # ----------------------------------------------------------

        components = []

        if signal_result.get(
            "sample_size",
            0,
        ) > 0:
            components.append(
                (
                    signal_result[
                        "performance_score"
                    ],
                    0.30,
                )
            )

        if market_result.get(
            "sample_size",
            0,
        ) > 0:
            components.append(
                (
                    market_result[
                        "performance_score"
                    ],
                    0.20,
                )
            )

        if timeframe_result.get(
            "sample_size",
            0,
        ) > 0:
            components.append(
                (
                    timeframe_result[
                        "performance_score"
                    ],
                    0.10,
                )
            )

        if pattern_performance.get(
            "sample_size",
            0,
        ) > 0:
            components.append(
                (
                    pattern_performance[
                        "performance_score"
                    ],
                    0.25,
                )
            )

        if recent.get(
            "sample_size",
            0,
        ) > 0:
            components.append(
                (
                    recent[
                        "performance_score"
                    ],
                    0.15,
                )
            )

        if components:

            weight_total = sum(
                weight
                for _, weight in components
            )

            score = sum(
                value * weight
                for value, weight in components
            ) / weight_total

        else:
            score = 0.0

        score = self._clamp(
            score,
            -100.0,
            100.0,
        )

        # Convert -100..100 into 0..100.
        normalized_score = (
            score + 100.0
        ) / 2.0

        if score >= 25.0:
            learning_bias = "POSITIVE"

        elif score <= -25.0:
            learning_bias = "NEGATIVE"

        else:
            learning_bias = "NEUTRAL"

        return {
            "status": "READY",
            "learning_score": round(
                normalized_score,
                2,
            ),
            "raw_learning_score": round(
                score,
                2,
            ),
            "learning_bias": learning_bias,
            "overall_performance": overall,
            "signal_performance": signal_result,
            "market_performance": market_result,
            "timeframe_performance": timeframe_result,
            "pattern_performance": pattern_result,
            "recent_performance": recent,
            "sample_size": len(self._records),
            "decision": None,
            "decision_authority": (
                "downstream_ai_decision_layers"
            ),
        }

    # ==============================================================
    # FULL ANALYSIS
    # ==============================================================

    def analyze(
        self,
        signal: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        pattern_signature: Optional[
            Dict[str, Any]
        ] = None,
        recent_lookback: int = 20,
    ) -> Dict[str, Any]:
        """
        Primary adaptive-learning API.
        """

        result = self.learning_score(
            signal=signal,
            symbol=symbol,
            timeframe=timeframe,
            pattern_signature=pattern_signature,
            recent_lookback=recent_lookback,
        )

        return {
            "status": "READY",
            "learning": result,
            "decision": None,
            "execution_allowed": False,
            "risk_management": False,
            "decision_authority": (
                "downstream_ai_decision_layers"
            ),
        }

    # ==============================================================
    # MEMORY MANAGEMENT
    # ==============================================================

    def clear(self) -> Dict[str, Any]:
        """
        Clear all adaptive-learning records.
        """

        previous_size = len(
            self._records
        )

        self._records.clear()

        return {
            "status": "CLEARED",
            "previous_record_count": previous_size,
            "record_count": 0,
        }

    def size(self) -> int:
        """
        Return number of learning records.
        """

        return len(self._records)

    # ==============================================================
    # INTERNAL HELPERS
    # ==============================================================

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

        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    @staticmethod
    def _normalize_signal(
        signal: Optional[str],
    ) -> str:

        if not isinstance(
            signal,
            str,
        ):
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

        if not isinstance(
            outcome,
            str,
        ):
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

    @staticmethod
    def _normalize_symbol(
        symbol: Optional[str],
    ) -> str:

        if not isinstance(
            symbol,
            str,
        ):
            return "UNKNOWN"

        value = symbol.strip().upper()

        return value or "UNKNOWN"

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: Optional[str],
    ) -> str:

        if not isinstance(
            timeframe,
            str,
        ):
            return "UNKNOWN"

        value = timeframe.strip().upper()

        if value in cls.SUPPORTED_TIMEFRAMES:
            return value

        return "UNKNOWN"

    @staticmethod
    def _pattern_matches(
        requested: Dict[str, Any],
        historical: Dict[str, Any],
    ) -> bool:
        """
        Compare only fields supplied by the requested signature.
        """

        if not requested:
            return False

        for key, value in requested.items():

            if key not in historical:
                return False

            historical_value = historical.get(
                key
            )

            if isinstance(
                value,
                (int, float),
            ) and isinstance(
                historical_value,
                (int, float),
            ):

                try:
                    if abs(
                        float(value)
                        - float(historical_value)
                    ) > 1.0:
                        return False

                except (
                    TypeError,
                    ValueError,
                ):
                    return False

            else:

                if str(value).strip().upper() != str(
                    historical_value
                ).strip().upper():
                    return False

        return True


# ==================================================================
# MODULE-LEVEL SINGLETON
# ==================================================================

_ADAPTIVE_LEARNING = AdaptiveLearning()


# ==================================================================
# PUBLIC API
# ==================================================================

def adaptive_learning_info() -> Dict[str, Any]:
    """
    Return adaptive-learning information.
    """

    return _ADAPTIVE_LEARNING.info()


def record_learning_outcome(
    signal: Optional[str] = None,
    outcome: Optional[str] = None,
    pnl: Optional[float] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    pattern_signature: Optional[
        Dict[str, Any]
    ] = None,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Record a completed outcome.
    """

    return _ADAPTIVE_LEARNING.record_outcome(
        signal=signal,
        outcome=outcome,
        pnl=pnl,
        symbol=symbol,
        timeframe=timeframe,
        pattern_signature=pattern_signature,
        confidence=confidence,
        metadata=metadata,
    )


def calculate_learning_score(
    signal: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    pattern_signature: Optional[
        Dict[str, Any]
    ] = None,
    recent_lookback: int = 20,
) -> Dict[str, Any]:
    """
    Calculate adaptive-learning evidence.
    """

    return _ADAPTIVE_LEARNING.learning_score(
        signal=signal,
        symbol=symbol,
        timeframe=timeframe,
        pattern_signature=pattern_signature,
        recent_lookback=recent_lookback,
    )


def analyze_adaptive_learning(
    signal: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    pattern_signature: Optional[
        Dict[str, Any]
    ] = None,
    recent_lookback: int = 20,
) -> Dict[str, Any]:
    """
    Run complete adaptive-learning analysis.
    """

    return _ADAPTIVE_LEARNING.analyze(
        signal=signal,
        symbol=symbol,
        timeframe=timeframe,
        pattern_signature=pattern_signature,
        recent_lookback=recent_lookback,
    )


def adaptive_learning_performance() -> Dict[str, Any]:
    """
    Return overall learning performance.
    """

    return _ADAPTIVE_LEARNING.calculate_performance()


def adaptive_learning_signal_performance(
    signal: str,
) -> Dict[str, Any]:
    """
    Return performance for BUY or SELL.
    """

    return _ADAPTIVE_LEARNING.signal_performance(
        signal
    )


def adaptive_learning_market_performance(
    symbol: str,
) -> Dict[str, Any]:
    """
    Return performance for a market.
    """

    return _ADAPTIVE_LEARNING.market_performance(
        symbol
    )


def adaptive_learning_recent_performance(
    lookback: int = 20,
) -> Dict[str, Any]:
    """
    Return recent learning performance.
    """

    return _ADAPTIVE_LEARNING.recent_performance(
        lookback
    )


def clear_adaptive_learning() -> Dict[str, Any]:
    """
    Clear adaptive-learning memory.
    """

    return _ADAPTIVE_LEARNING.clear()


__all__ = [
    "AdaptiveLearning",
    "adaptive_learning_info",
    "record_learning_outcome",
    "calculate_learning_score",
    "analyze_adaptive_learning",
    "adaptive_learning_performance",
    "adaptive_learning_signal_performance",
    "adaptive_learning_market_performance",
    "adaptive_learning_recent_performance",
    "clear_adaptive_learning",
]