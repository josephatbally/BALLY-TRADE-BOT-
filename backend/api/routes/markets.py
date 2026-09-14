
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


# =====================================================================
# LIVE QUOTES & SPARKLINE ENDPOINT
# =====================================================================
@router.get("/quotes")
def get_market_quotes() -> dict:
    """
    Return real-time prices, 24h change %, and sparkline points for the 6 core markets.
    """
    import MetaTrader5 as mt5
    from backend.trading_engine.market_data.mt5_connection import get_mt5_connection

    conn = get_mt5_connection()
    quotes = []

    for sym in MARKETS:
        price = 0.0
        change_pct = 0.0
        direction = "BULLISH"
        points = []

        try:
            actual = conn.resolve_symbol(sym) or sym
            tick = mt5.symbol_info_tick(actual)
            if tick is not None:
                price = float(tick.bid if tick.bid > 0 else tick.ask)

            # Get recent 12 closes (M15) for TradingView sparkline
            rates = mt5.copy_rates_from_pos(actual, mt5.TIMEFRAME_M15, 0, 12)
            if rates is not None and len(rates) > 0:
                closes = [float(r['close']) for r in rates]
                first_close = closes[0]
                last_close = closes[-1]
                if price == 0.0:
                    price = last_close
                if first_close > 0:
                    change_pct = round(((last_close - first_close) / first_close) * 100.0, 2)
                direction = "BULLISH" if change_pct >= 0 else "BEARISH"

                # Normalize closes into a 10-60 coordinate scale for sparkline
                min_c = min(closes)
                max_c = max(closes)
                spread = max_c - min_c if max_c > min_c else 1.0
                points = [round(((c - min_c) / spread) * 45 + 10, 1) for c in closes]
            else:
                points = [30, 32, 31, 35, 34, 38, 36, 42, 40, 45, 43, 48]
        except Exception:
            points = [30, 32, 31, 35, 34, 38, 36, 42, 40, 45, 43, 48]

        # Format price with appropriate decimals
        if "JPY" in sym:
            fmt_price = f"{price:.3f}" if price > 0 else "—"
        elif "XAU" in sym or "XAG" in sym or "NAS" in sym:
            fmt_price = f"{price:.2f}" if price > 0 else "—"
        else:
            fmt_price = f"{price:.5f}" if price > 0 else "—"

        change_str = f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%"

        quotes.append({
            "symbol": sym,
            "price": fmt_price,
            "raw_price": price,
            "change": change_str,
            "change_pct": change_pct,
            "direction": direction,
            "points": points,
        })

    return {"status": "READY", "quotes": quotes}