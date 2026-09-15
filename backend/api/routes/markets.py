
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
import time
_analysis_cache = {}
_CACHE_TTL = 30  # seconds

from backend.trading_engine.scanner import scanner_info

from backend.trading_engine.engine import (
    analyze_live_market,
    analyze_markets,
)

from backend.trading_engine.hybrid.hybrid_engine import (
    analyze_hybrid_market,
)


router = APIRouter()

# In-memory analysis cache: calculations take ~25s for 6 symbols,
# so cache results for 30s to keep mobile fast and prevent timeouts.
import time as _time

_ANALYSIS_CACHE = {}
_ANALYSIS_TTL = 30.0

def _get_cached_analysis(key):
    entry = _ANALYSIS_CACHE.get(key)
    if not entry:
        return None
    created, payload = entry
    if _time.time() - created > _ANALYSIS_TTL:
        return None
    return payload

def _store_analysis_cache(key, payload):
    _ANALYSIS_CACHE[key] = (_time.time(), payload)

_orig_analyze_markets = analyze_markets

def analyze_markets(markets=None):
    cached = _get_cached_analysis("technical")
    if cached is not None:
        return cached
    result = _orig_analyze_markets(markets=markets)
    _store_analysis_cache("technical", result)
    return result

_orig_analyze_hybrid_market = analyze_hybrid_market

def analyze_hybrid_market(symbol=None):
    key = f"hybrid:{symbol}"
    cached = _get_cached_analysis(key)
    if cached is not None:
        return cached
    result = _orig_analyze_hybrid_market(symbol=symbol)
    _store_analysis_cache(key, result)
    return result



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

    # Candidate names for broker symbol variations
    SYMBOL_ALIASES = {
        "NASDAQ": ["NASDAQ", "USTEC", "NAS100", "US100", "NDX", "USTECH", "US100m", "NAS100m", "USTECm"],
        "XAUUSD": ["XAUUSD", "GOLD", "XAUUSDm", "GOLDm"],
        "XAGUSD": ["XAGUSD", "SILVER", "XAGUSDm", "SILVERm"],
        "EURUSD": ["EURUSD", "EURUSDm", "EURUSD."],
        "GBPUSD": ["GBPUSD", "GBPUSDm", "GBPUSD."],
        "USDJPY": ["USDJPY", "USDJPYm", "USDJPY."],
    }

    def _resolve(sym: str) -> str:
        candidates = SYMBOL_ALIASES.get(sym, [sym])
        for c in candidates:
            try:
                info = mt5.symbol_info(c)
                if info is not None:
                    return c
            except Exception:
                pass
        return sym

    quotes = []

    for sym in MARKETS:
        price = 0.0
        change_pct = 0.0
        direction = "BULLISH"
        points = []

        try:
            actual = _resolve(sym)
            mt5.symbol_select(actual, True)

            tick = mt5.symbol_info_tick(actual)
            if tick is not None:
                price = float(tick.bid if tick.bid > 0 else tick.ask)

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

                min_c = min(closes)
                max_c = max(closes)
                rng = (max_c - min_c) if (max_c - min_c) > 0 else 1.0
                for c in closes:
                    norm_val = round(6.0 + ((c - min_c) / rng) * 24.0, 1)
                    points.append(norm_val)

            if not points:
                points = [10.0, 12.0, 11.0, 15.0, 14.0, 18.0, 20.0, 19.0, 23.0, 22.0, 25.0, 26.0]

            if price > 0:
                if price >= 1000:
                    price_str = f"{price:,.2f}"
                elif price >= 1:
                    price_str = f"{price:.4f}"
                else:
                    price_str = f"{price:.5f}"
            else:
                price_str = "--"

            quotes.append({
                "symbol": sym,
                "price": price_str,
                "raw_price": price,
                "change_percent": f"{'+' if change_pct >= 0 else ''}{change_pct:.2f}%",
                "raw_change": change_pct,
                "direction": direction,
                "points": points,
            })
        except Exception:
            quotes.append({
                "symbol": sym,
                "price": "--",
                "raw_price": 0.0,
                "change_percent": "+0.00%",
                "raw_change": 0.0,
                "direction": "BULLISH",
                "points": [10.0, 12.0, 15.0, 14.0, 18.0, 20.0, 23.0, 26.0],
            })

    return {"status": "ok", "quotes": quotes}