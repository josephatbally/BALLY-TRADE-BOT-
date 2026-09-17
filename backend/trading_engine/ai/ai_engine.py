"""
BALLY FLOW - AI Orchestration & Continuous Market Learning Engine

Orchestrates pattern memory, adaptive learning, market profiling, and trade evaluation.
Persists structural market observations and trade outcomes across all pairs to SQLite,
enabling the AI to learn how each symbol moves over time and continuously refine strategy confidence.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.database import get_db_connection
from backend.trading_engine.ai.adaptive_learning import AdaptiveLearning
from backend.trading_engine.ai.confidence import calculate_ai_confidence
from backend.trading_engine.ai.market_profile import analyze_market_profile
from backend.trading_engine.ai.pattern_memory import PatternMemory
from backend.trading_engine.ai.trade_evaluator import classify_outcome, evaluate_trade

logger = logging.getLogger("bally_flow.ai_engine")


class AIEngine:
    """
    Central AI engine responsible for:
      - Continuous multi-pair market structural analysis
      - Pattern recognition and signature memory
      - Adaptive win-rate and regime scoring
      - SQLite-backed durable knowledge persistence
      - Real-time AI confidence synthesis
    """

    def __init__(self) -> None:
        self.pattern_memory = PatternMemory(max_records=1000)
        self.adaptive_learning = AdaptiveLearning(max_records=1000)
        self._load_persisted_knowledge()

    def _load_persisted_knowledge(self) -> None:
        """Hydrates AI memory from SQLite on startup."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Load pattern knowledge
            cursor.execute(
                """
                SELECT symbol, timeframe, regime, signature_hash, setup_type,
                       direction, win_count, loss_count, total_pnl, avg_confidence
                FROM ai_pattern_knowledge
                LIMIT 500
                """
            )
            rows = cursor.fetchall()
            for r in rows:
                sig = {
                    "symbol": r["symbol"],
                    "timeframe": r["timeframe"],
                    "regime": r["regime"],
                    "signature_hash": r["signature_hash"],
                    "setup_type": r["setup_type"],
                    "direction": r["direction"],
                }
                total = r["win_count"] + r["loss_count"]
                outcome = "WIN" if r["win_count"] >= r["loss_count"] else "LOSS"
                if total > 0:
                    self.pattern_memory.remember(
                        signature=sig,
                        outcome=outcome,
                        return_pct=r["total_pnl"] / max(total, 1),
                        quality=r["avg_confidence"],
                        symbol=r["symbol"],
                        timeframe=r["timeframe"],
                    )

            conn.close()
            logger.info("AIEngine loaded persisted structural memory from SQLite.")
        except Exception as exc:
            logger.warning("Could not hydrate AI memory from SQLite: %s", exc)

    def study_market(
        self,
        symbol: str,
        timeframe: str,
        candles: Sequence[Any],
        technical_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Studies market candles for a pair, detects the structural regime,
        queries pattern memory, and produces adaptive learning weights.
        """
        symbol_clean = str(symbol).strip().upper()
        tf_clean = str(timeframe).strip().upper()

        # 1. Market Profile & Structural Regime Analysis
        try:
            profile = analyze_market_profile(
                symbol=symbol_clean,
                timeframe=tf_clean,
                candles=candles,
            )
        except Exception:
            profile = {
                "regime": "BALANCED_RANGE",
                "trend": {"strength": 0.5, "direction": "NEUTRAL"},
                "volatility": {"regime": "NORMAL"},
                "momentum": {"direction": "NEUTRAL"},
            }

        regime = profile.get("regime", "BALANCED_RANGE")

        # 2. Extract or build pattern signature
        signature = self.pattern_memory.create_signature(
            technical=technical_analysis or {},
            market_profile=profile,
            symbol=symbol_clean,
            timeframe=tf_clean,
        )

        # 3. Retrieve similar historical setups
        similar_stats = self.pattern_memory.statistics(
            symbol=symbol_clean,
            timeframe=tf_clean,
        )

        # 4. Adaptive learning performance for symbol
        adaptive_score = self.adaptive_learning.learning_score(
            symbol=symbol_clean,
            timeframe=tf_clean,
        )

        # 5. Calculate dynamic adaptive confidence multiplier
        # High historical win rates on this pair boost confidence; choppy/failing regimes adjust downwards
        sample_count = similar_stats.get("sample_count", 0)
        win_rate = similar_stats.get("win_rate", 0.5)

        if sample_count >= 5:
            if win_rate > 0.65:
                multiplier = 1.05 + min((win_rate - 0.65) * 0.5, 0.15)
            elif win_rate < 0.40:
                multiplier = max(0.85, 1.0 - (0.40 - win_rate) * 0.5)
            else:
                multiplier = 1.0
        else:
            multiplier = 1.0

        # Persist observation metrics to SQLite
        self._record_symbol_scan(symbol_clean, regime, profile, multiplier)

        return {
            "symbol": symbol_clean,
            "timeframe": tf_clean,
            "regime": regime,
            "profile": profile,
            "signature": signature,
            "similar_stats": similar_stats,
            "adaptive_score": adaptive_score,
            "multiplier": round(multiplier, 2),
            "win_rate": round(win_rate * 100, 1) if sample_count > 0 else None,
            "samples_learned": sample_count,
        }

    def _record_symbol_scan(
        self, symbol: str, regime: str, profile: Dict[str, Any], multiplier: float
    ) -> None:
        """Updates continuous market scan records in SQLite."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ai_symbol_learning (
                    symbol, total_scans, market_regime, volatility_score,
                    trend_strength, adaptive_multiplier, updated_at
                ) VALUES (?, 1, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(symbol) DO UPDATE SET
                    total_scans = total_scans + 1,
                    market_regime = excluded.market_regime,
                    volatility_score = excluded.volatility_score,
                    trend_strength = excluded.trend_strength,
                    adaptive_multiplier = excluded.adaptive_multiplier,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    symbol,
                    str(regime),
                    float(profile.get("volatility", {}).get("atr_pct", 0.0) or 0.0),
                    float(profile.get("trend", {}).get("strength", 0.5) or 0.5),
                    float(multiplier),
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.debug("Scan telemetry update failed: %s", exc)

    def record_trade_outcome(
        self,
        symbol: str,
        timeframe: str,
        signal: str,
        outcome: str,
        entry_price: float,
        exit_price: float,
        pnl: float,
        quality: float = 75.0,
        regime: str = "TRENDING",
    ) -> Dict[str, Any]:
        """
        Records the real-world outcome of a closed trade into AI memory,
        updating adaptive scores and persisting the lesson to SQLite.
        """
        symbol_clean = str(symbol).strip().upper()
        tf_clean = str(timeframe).strip().upper()
        sig_clean = str(signal).strip().upper()
        outcome_clean = "WIN" if pnl > 0 or "WIN" in str(outcome).upper() else "LOSS"

        # 1. Update in-memory adaptive learning
        self.adaptive_learning.record_outcome(
            symbol=symbol_clean,
            timeframe=tf_clean,
            signal=sig_clean,
            outcome=outcome_clean,
            pnl=pnl,
            quality=quality,
        )

        # 2. Update SQLite
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            is_win = 1 if outcome_clean == "WIN" else 0
            is_loss = 1 if outcome_clean == "LOSS" else 0

            # Update symbol learning table
            cursor.execute(
                """
                INSERT INTO ai_symbol_learning (
                    symbol, total_scans, total_trades, wins, losses, win_rate, updated_at
                ) VALUES (?, 1, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(symbol) DO UPDATE SET
                    total_trades = total_trades + 1,
                    wins = wins + excluded.wins,
                    losses = losses + excluded.losses,
                    win_rate = ROUND(CAST(wins + excluded.wins AS REAL) / (total_trades + 1) * 100.0, 1),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    symbol_clean,
                    is_win,
                    is_loss,
                    100.0 if is_win else 0.0,
                ),
            )

            # Update pattern knowledge table
            cursor.execute(
                """
                INSERT INTO ai_pattern_knowledge (
                    symbol, timeframe, regime, signature_hash, setup_type,
                    direction, win_count, loss_count, total_pnl, avg_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol_clean,
                    tf_clean,
                    regime,
                    f"{symbol_clean}_{tf_clean}_{regime}_{sig_clean}",
                    "SMC_CONFLUENCE",
                    sig_clean,
                    is_win,
                    is_loss,
                    float(pnl),
                    float(quality),
                ),
            )

            conn.commit()
            conn.close()
            logger.info(
                "AIEngine learned from trade outcome on %s: %s (P&L: $%.2f)",
                symbol_clean,
                outcome_clean,
                pnl,
            )
        except Exception as exc:
            logger.warning("Failed to persist trade outcome to SQLite: %s", exc)

        return {
            "status": "RECORDED",
            "symbol": symbol_clean,
            "outcome": outcome_clean,
            "pnl": pnl,
            "total_learned": self.adaptive_learning.size(),
        }

    def get_learning_telemetry(self) -> Dict[str, Any]:
        """Provides full AI learning telemetry for the dashboard and flow."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_symbol_learning ORDER BY symbol ASC")
            rows = cursor.fetchall()
            symbol_data = [dict(r) for r in rows]
            conn.close()
        except Exception:
            symbol_data = []

        return {
            "ai_status": "ACTIVE_LEARNING",
            "patterns_in_memory": self.pattern_memory.size(),
            "outcomes_learned": self.adaptive_learning.size(),
            "symbols": symbol_data,
        }


# Global singleton instance
ai_engine = AIEngine()
