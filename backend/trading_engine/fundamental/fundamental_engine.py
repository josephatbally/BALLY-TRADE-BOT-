"""
BALLY FLOW - Fundamental Engine

Authoritative fundamental-analysis entry point.

Responsibilities
----------------
    Economic calendar
        +
    News
        |
        v
    News analysis
        |
        v
    Fundamental score
        |
        v
    Standardized fundamental result

This module MUST NOT:

    - perform technical analysis
    - perform SMC analysis
    - perform hybrid decision-making
    - manage risk
    - calculate lot size
    - execute trades
    - place MT5 orders
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from backend.trading_engine.fundamental.economic_calendar import (
    get_events,
)

from backend.trading_engine.fundamental.news import (
    get_news,
)

from backend.trading_engine.fundamental.news_analyzer import (
    analyze_news,
)

from backend.trading_engine.fundamental.fundamental_score import (
    calculate_fundamental_score,
)


class FundamentalEngine:
    """
    Central fundamental-analysis engine.

    The result is consumed by the Hybrid Engine.
    """

    MODE = "fundamental"

    def __init__(self) -> None:
        self.name = "BALLY FLOW Fundamental Engine"

    def analyze(
        self,
        symbol: str,
        provider: Any = None,
    ) -> Dict[str, Any]:

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("symbol is required")

        # ----------------------------------------------------------
        # 1. ECONOMIC CALENDAR
        # ----------------------------------------------------------

        calendar = get_events(
            symbol=symbol,
            provider=provider,
        )

        # ----------------------------------------------------------
        # 2. NEWS
        # ----------------------------------------------------------

        news = get_news(
            symbol=symbol,
            provider=provider,
        )

        # ----------------------------------------------------------
        # 3. NEWS ANALYSIS
        # ----------------------------------------------------------

        news_analysis = analyze_news(
            news_result=news,
        )

        # ----------------------------------------------------------
        # 4. FUNDAMENTAL SCORE
        # ----------------------------------------------------------

        score = calculate_fundamental_score(
            news_analysis=news_analysis,
            calendar_analysis=calendar,
        )

        # ----------------------------------------------------------
        # 5. STANDARDIZED RESULT
        # ----------------------------------------------------------

        result = {
            "success": True,
            "status": "READY",
            "mode": self.MODE,
            "symbol": symbol,

            "analysis_timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            # ------------------------------------------------------
            # AUTHORITATIVE FUNDAMENTAL VALUES
            # ------------------------------------------------------

            "signal": score["signal"],
            "confidence": score["confidence"],
            "quality": score["quality"],

            "market_bias": score["market_bias"],
            "market_score": score["market_score"],

            "risk": score["risk"],

            "trade_allowed": score["trade_allowed"],

            "high_impact_risk": score[
                "high_impact_risk"
            ],

            "high_impact_count": score[
                "high_impact_count"
            ],

            "conflict": score["conflict"],
            "conflict_reason": score[
                "conflict_reason"
            ],

            # ------------------------------------------------------
            # TRADE PERMISSION
            # ------------------------------------------------------

            "trade_permission_reason": (
                "Fundamental conditions support directional "
                "analysis with no active high-impact event."
                if score["trade_allowed"]
                else
                "Fundamental conditions do not currently "
                "permit trading."
            ),

            # ------------------------------------------------------
            # COMPONENT RESULTS
            # ------------------------------------------------------

            "economic_calendar": calendar,

            "news": news,

            "news_analysis": news_analysis,

            "fundamental_score": score,

            # ------------------------------------------------------
            # ARCHITECTURAL SAFETY
            # ------------------------------------------------------

            "technical_analysis": False,

            "hybrid_analysis": False,

            "execution_ready": False,

            "execution_allowed": False,

            "order_send_allowed": False,

            "execution_sent": False,

            "live_execution": False,

            "dry_run": True,

            "decision": None,

            "decision_authority": "hybrid_or_decision_engine",
        }

        return result


# ==================================================================
# CONVENIENCE API
# ==================================================================


def run_fundamental_engine(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:

    engine = FundamentalEngine()

    return engine.analyze(
        symbol=symbol,
        provider=provider,
    )


def analyze_fundamental_market(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:

    return run_fundamental_engine(
        symbol=symbol,
        provider=provider,
    )


def fundamental_engine_info() -> Dict[str, Any]:

    return {
        "name": "BALLY FLOW Fundamental Engine",
        "status": "READY",
        "mode": "fundamental",
        "components": [
            "economic_calendar",
            "news",
            "news_analyzer",
            "fundamental_score",
        ],
        "technical_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "execution": False,
        "order_placement": False,
        "live_execution": False,
    }


if __name__ == "__main__":
    print(fundamental_engine_info())
