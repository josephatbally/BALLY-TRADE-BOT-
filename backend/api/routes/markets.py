
"""
BALLY FLOW API - Market Routes
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.main import (
    run_market,
    run_all_markets,
)

from backend.trading_engine.scanner import scanner_info

from backend.trading_engine.engine import (
    analyze_live_market,
    analyze_markets,
)

from backend.trading_engine.hybrid.hybrid_engine import (
    analyze_hybrid_market,
)


router = APIRouter()


# =====================================================================
# MARKET DEFINITIONS
# =====================================================================

MARKETS = [
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
]

VALID_MODES = {
    "technical",
    "hybrid",
}

def compact_market_analysis(result: dict) -> dict:
    """Return a compact API-safe projection of an engine result."""
    projected = dict(result)

    timeframes = projected.get("technical_timeframes")
    if isinstance(timeframes, dict):
        compact_timeframes = {}

        for timeframe, timeframe_result in timeframes.items():
            if not isinstance(timeframe_result, dict):
                compact_timeframes[timeframe] = timeframe_result
                continue

            tf = dict(timeframe_result)
            analysis = tf.get("analysis")

            if isinstance(analysis, dict):
                analysis = dict(analysis)

                liquidity = analysis.get("liquidity")
                if isinstance(liquidity, dict):
                    liquidity = dict(liquidity)
                    sweeps = liquidity.get("sweeps")

                    if isinstance(sweeps, list):
                        liquidity["sweep_count"] = len(sweeps)
                        liquidity["sweeps"] = []

                    analysis["liquidity"] = liquidity

                confluence = analysis.get("technical_confluence")
                if isinstance(confluence, dict):
                    confluence = dict(confluence)

                    if isinstance(confluence.get("components"), dict):
                        confluence["components"] = {}

                    analysis["technical_confluence"] = confluence

                tf["analysis"] = analysis

            compact_timeframes[timeframe] = tf

        projected["technical_timeframes"] = compact_timeframes

    technical_analysis = projected.get("technical_analysis")
    if isinstance(technical_analysis, dict):
        technical_analysis = dict(technical_analysis)
        technical_analysis.pop("timeframes", None)
        projected["technical_analysis"] = technical_analysis

    structural_context = projected.get("structural_context")
    if isinstance(structural_context, dict):
        structural_context = dict(structural_context)
        structural_context.pop("timeframes", None)
        projected["structural_context"] = structural_context

    return projected

# =====================================================================
# MARKET LIST
# =====================================================================

@router.get("")
def get_markets():
    """
    Return the six agreed BALLY FLOW markets.
    """

    return {
        "status": "READY",
        "count": len(MARKETS),
        "markets": MARKETS,
    }


# =====================================================================
# SCANNER INFORMATION
# =====================================================================

@router.get("/scanner")
def get_scanner_status():
    """
    Return scanner capabilities and current scanner status.
    """

    return scanner_info()


# =====================================================================
# SINGLE MARKET SCAN
# =====================================================================

@router.post("/{symbol}/scan")
def scan_single_market(
    symbol: str,
    count: Optional[int] = Query(
        default=None,
        ge=1,
        le=1000,
    ),
):
    """
    Run a single-market market-data scan.

    This endpoint intentionally does NOT generate
    BUY / SELL / NO_TRADE decisions.
    """

    symbol = symbol.upper()

    if symbol not in MARKETS:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Unsupported market.",
                "market": symbol,
                "supported_markets": MARKETS,
            },
        )

    try:
        return run_market(
            market=symbol,
            count=count,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =====================================================================
# ALL MARKET SCAN
# =====================================================================

@router.post("/scan")
def scan_all_markets(
    count: Optional[int] = Query(
        default=None,
        ge=1,
        le=1000,
    ),
):
    """
    Run the complete six-market market-data scan.
    """

    try:
        return run_all_markets(
            count=count,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =====================================================================
# SINGLE MARKET ANALYSIS
# =====================================================================

@router.get("/{symbol}/analysis")
def analyze_single_market(
    symbol: str,
    mode: str = Query(
        default="technical",
    ),
):
    """
    Run the authoritative trading analysis engine.

    technical:
        Technical SMC + AI confidence pipeline.

    hybrid:
        Technical + Fundamental + Hybrid decision pipeline.

    This endpoint never sends an MT5 order.
    """

    symbol = symbol.upper()
    mode = mode.lower().strip()

    if symbol not in MARKETS:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Unsupported market.",
                "market": symbol,
                "supported_markets": MARKETS,
            },
        )

    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported trading mode.",
                "mode": mode,
                "supported_modes": sorted(VALID_MODES),
            },
        )

    try:
        if mode == "technical":
            result = analyze_live_market(symbol)

        else:
            result = analyze_hybrid_market(
                symbol=symbol,
            )

        return {
            "status": "READY",
            "mode": mode,
            "market": symbol,
            "analysis": compact_market_analysis(result),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Market analysis failed.",
                "market": symbol,
                "mode": mode,
                "error": str(exc),
            },
        ) from exc


# =====================================================================
# ALL MARKET ANALYSIS
# =====================================================================

@router.get("/analysis")
def analyze_all_markets(
    mode: str = Query(
        default="technical",
    ),
):
    """
    Run authoritative analysis for all six markets.

    The result remains analysis-only. No order is sent.
    """

    mode = mode.lower().strip()

    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported trading mode.",
                "mode": mode,
                "supported_modes": sorted(VALID_MODES),
            },
        )

    try:
        results = {}

        if mode == "technical":
            results = analyze_markets(
                markets=MARKETS,
            )

        else:
            for symbol in MARKETS:
                results[symbol] = analyze_hybrid_market(
                    symbol=symbol,
                )

        return {
            "status": "READY",
            "mode": mode,
            "market_count": len(MARKETS),
            "markets": MARKETS,
            "analysis": results,
            "execution": {
                "allowed": False,
                "order_send_allowed": False,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Multi-market analysis failed.",
                "mode": mode,
                "error": str(exc),
            },
        ) from exc
