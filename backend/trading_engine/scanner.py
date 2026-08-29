
"""
BALLY FLOW - Market Scanner
===========================

Authoritative six-market top-down market-data scanner.

RESPONSIBILITIES
----------------
The scanner ONLY:

    - scans the six configured BALLY FLOW markets;
    - retrieves H4 -> H1 -> M15 data for each market;
    - uses the broker-aware symbol resolver through symbol_data;
    - validates basic market-data availability;
    - preserves independent market results;
    - preserves independent timeframe results;
    - reports scan readiness;
    - provides standardized scanner output.

AGREED MARKETS
--------------
    XAUUSD
    EURUSD
    GBPUSD
    USDJPY
    XAGUSD
    NASDAQ

TOP-DOWN HIERARCHY
------------------
    H4 -> H1 -> M15

COMPLETE SCAN
-------------
    6 markets
    x
    3 timeframes
    =
    18 market-data streams

DEFAULT HISTORY
---------------
    H4  -> 300 candles
    H1  -> 500 candles
    M15 -> 1000 candles

IMPORTANT
---------
This module MUST NOT:

    - calculate indicators;
    - calculate SMC;
    - calculate market structure;
    - calculate liquidity;
    - calculate order blocks;
    - calculate FVG;
    - calculate confluence;
    - calculate AI confidence;
    - perform fundamental analysis;
    - create BUY decisions;
    - create SELL decisions;
    - create NO_TRADE decisions;
    - calculate risk;
    - calculate position size;
    - place MT5 orders;
    - execute trades.

Those responsibilities belong to downstream layers.

PIPELINE POSITION
-----------------
    MT5
      |
      v
    symbol_data.py
      |
      v
    scanner.py
      |
      +----> Technical Analysis
      |
      +----> Fundamental Analysis
      |
      +----> Hybrid Decision Pipeline

The scanner is a market-data acquisition boundary.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

from .market_data.symbol_data import (
    MARKETS,
    TOP_DOWN_TIMEFRAMES,
    DEFAULT_CANDLE_COUNT,
    get_top_down_data,
    initialize_mt5,
    mt5_initialized,
    normalize_market,
    supported_markets,
    supported_timeframes,
)


# =====================================================================
# CONSTANTS
# =====================================================================

SCANNER_NAME = "BALLY FLOW Market Scanner"

SCAN_STATUS_READY = "READY"
SCAN_STATUS_PARTIAL = "PARTIAL"
SCAN_STATUS_ERROR = "ERROR"

TIMEFRAME_ORDER: Tuple[str, ...] = (
    "H4",
    "H1",
    "M15",
)

MARKET_ORDER: Tuple[str, ...] = (
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
)

EXPECTED_MARKET_COUNT = 6
EXPECTED_TIMEFRAME_COUNT = 3
EXPECTED_STREAM_COUNT = 18


# =====================================================================
# VALIDATION
# =====================================================================

def _validate_count(
    count: Optional[int],
) -> Optional[int]:
    """
    Validate optional uniform candle count.

    None preserves the optimized per-timeframe policy in
    symbol_data.py:

        H4  -> 300
        H1  -> 500
        M15 -> 1000
    """

    if count is None:
        return None

    if isinstance(count, bool):
        raise TypeError(
            "count must be an integer or None"
        )

    if not isinstance(count, int):
        raise TypeError(
            "count must be an integer or None"
        )

    if count <= 0:
        raise ValueError(
            "count must be greater than zero"
        )

    return count


def _validate_timeframes(
    timeframes: Optional[Sequence[str]],
) -> Tuple[str, ...]:
    """
    Validate requested scanner timeframes.

    Only H4, H1 and M15 are permitted.
    """

    if timeframes is None:
        return TIMEFRAME_ORDER

    if isinstance(timeframes, str):
        requested = (timeframes,)
    else:
        requested = tuple(timeframes)

    normalized = []

    for timeframe in requested:

        if not isinstance(timeframe, str):
            raise TypeError(
                "each timeframe must be a string"
            )

        value = timeframe.strip().upper()

        if value not in TOP_DOWN_TIMEFRAMES:
            raise ValueError(
                f"unsupported scanner timeframe: {timeframe!r}. "
                f"Supported: {', '.join(TIMEFRAME_ORDER)}"
            )

        if value not in normalized:
            normalized.append(value)

    if not normalized:
        raise ValueError(
            "at least one timeframe is required"
        )

    # Always preserve authoritative top-down order.
    return tuple(
        timeframe
        for timeframe in TIMEFRAME_ORDER
        if timeframe in normalized
    )


def _validate_market_list() -> None:
    """
    Validate that the configured scanner market universe is
    exactly the BALLY FLOW six-market universe.

    This protects the scanner from accidental configuration drift.
    """

    configured = tuple(
        normalize_market(market)
        for market in MARKETS
    )

    expected = MARKET_ORDER

    if configured != expected:
        raise RuntimeError(
            "BALLY FLOW market configuration mismatch. "
            f"Expected {expected}, got {configured}"
        )


# =====================================================================
# TIMEFRAME READINESS
# =====================================================================

def _timeframe_is_ready(
    timeframe_result: Any,
) -> bool:
    """
    Determine whether one timeframe contains usable market data.

    This checks availability only.

    It does NOT evaluate market quality or direction.
    """

    if not isinstance(timeframe_result, dict):
        return False

    if timeframe_result.get("status") != SCAN_STATUS_READY:
        return False

    candles = timeframe_result.get("candles")

    if not isinstance(candles, list):
        return False

    if len(candles) == 0:
        return False

    return True


def _build_timeframe_readiness(
    data: Dict[str, Any],
    timeframes: Sequence[str],
) -> Dict[str, Any]:
    """
    Build standardized readiness information for one market.
    """

    source_timeframes = data.get(
        "timeframes",
        {},
    )

    if not isinstance(source_timeframes, dict):
        source_timeframes = {}

    timeframe_status: Dict[str, str] = {}
    candle_counts: Dict[str, int] = {}
    missing_timeframes = []

    for timeframe in timeframes:

        timeframe_data = source_timeframes.get(
            timeframe
        )

        if _timeframe_is_ready(
            timeframe_data
        ):

            timeframe_status[timeframe] = (
                SCAN_STATUS_READY
            )

            candle_counts[timeframe] = len(
                timeframe_data.get(
                    "candles",
                    [],
                )
            )

        else:

            timeframe_status[timeframe] = (
                SCAN_STATUS_ERROR
            )

            candle_counts[timeframe] = 0

            missing_timeframes.append(
                timeframe
            )

    ready_count = sum(
        1
        for status in timeframe_status.values()
        if status == SCAN_STATUS_READY
    )

    required_count = len(timeframes)

    if ready_count == required_count:

        status = SCAN_STATUS_READY

    elif ready_count > 0:

        status = SCAN_STATUS_PARTIAL

    else:

        status = SCAN_STATUS_ERROR

    return {
        "status": status,
        "required_timeframes": list(timeframes),
        "ready_timeframe_count": ready_count,
        "required_timeframe_count": required_count,
        "candle_counts": candle_counts,
        "timeframe_status": timeframe_status,
        "missing_timeframes": missing_timeframes,
    }


# =====================================================================
# SINGLE MARKET SCAN
# =====================================================================

def scan_market(
    market: str,
    count: Optional[int] = None,
    symbol: Optional[str] = None,
    timeframes: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Perform a complete top-down scan for one logical market.

    Default:

        H4 -> H1 -> M15

    The scanner returns raw standardized market data plus
    readiness information.

    No trading decision is generated.
    """

    logical_market = normalize_market(
        market
    )

    validated_count = _validate_count(
        count
    )

    requested_timeframes = _validate_timeframes(
        timeframes
    )

    try:

        data = get_top_down_data(
            market=logical_market,
            count=validated_count,
            symbol=symbol,
        )

        if not isinstance(data, dict):
            raise RuntimeError(
                "symbol_data returned an invalid "
                "top-down data object"
            )

        source_timeframes = data.get(
            "timeframes",
            {},
        )

        if not isinstance(source_timeframes, dict):
            source_timeframes = {}

        readiness = _build_timeframe_readiness(
            data=data,
            timeframes=requested_timeframes,
        )

        result: Dict[str, Any] = {
            "status": readiness["status"],
            "scanner": SCANNER_NAME,

            "market": logical_market,

            "broker_symbol": data.get(
                "broker_symbol",
                data.get("symbol"),
            ),

            "symbol": data.get(
                "symbol",
                data.get("broker_symbol"),
            ),

            "analysis_order": list(
                requested_timeframes
            ),

            "top_down": True,

            "market_data_only": True,

            "timeframe_count": len(
                requested_timeframes
            ),

            "ready_timeframe_count": readiness[
                "ready_timeframe_count"
            ],

            "data_ready": (
                readiness["status"]
                == SCAN_STATUS_READY
            ),

            "readiness": readiness,

            "timeframes": {},

            # Explicit downstream placeholders.
            "technical_analysis": None,
            "fundamental_analysis": None,
            "hybrid_analysis": None,
            "decision": None,
        }

        for timeframe in requested_timeframes:

            timeframe_data = source_timeframes.get(
                timeframe
            )

            if isinstance(
                timeframe_data,
                dict,
            ):

                result["timeframes"][
                    timeframe
                ] = timeframe_data

            else:

                result["timeframes"][
                    timeframe
                ] = {
                    "status": SCAN_STATUS_ERROR,
                    "timeframe": timeframe,
                    "requested_candle_count": (
                        validated_count
                    ),
                    "candle_count": 0,
                    "candles": [],
                    "latest_closed_candle": None,
                    "latest_candle_time": None,
                    "latest_closed_candle_time": None,
                }

        # Preserve upstream errors if present.
        upstream_errors = data.get(
            "errors"
        )

        if upstream_errors:
            result["errors"] = dict(
                upstream_errors
            )

        return result

    except Exception as exc:

        return {
            "status": SCAN_STATUS_ERROR,
            "scanner": SCANNER_NAME,

            "market": logical_market,

            "broker_symbol": symbol,
            "symbol": symbol,

            "analysis_order": list(
                requested_timeframes
            ),

            "top_down": True,
            "market_data_only": True,

            "timeframe_count": len(
                requested_timeframes
            ),

            "ready_timeframe_count": 0,

            "data_ready": False,

            "readiness": {
                "status": SCAN_STATUS_ERROR,
                "required_timeframes": list(
                    requested_timeframes
                ),
                "ready_timeframe_count": 0,
                "required_timeframe_count": len(
                    requested_timeframes
                ),
                "candle_counts": {
                    timeframe: 0
                    for timeframe in requested_timeframes
                },
                "timeframe_status": {
                    timeframe: SCAN_STATUS_ERROR
                    for timeframe in requested_timeframes
                },
                "missing_timeframes": list(
                    requested_timeframes
                ),
            },

            "timeframes": {},

            "technical_analysis": None,
            "fundamental_analysis": None,
            "hybrid_analysis": None,
            "decision": None,

            "error": str(exc),
        }


# =====================================================================
# SIX-MARKET TOP-DOWN SCAN
# =====================================================================

def scan_all_markets(
    count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Perform the complete BALLY FLOW six-market top-down scan.

    Markets:

        XAUUSD
        EURUSD
        GBPUSD
        USDJPY
        XAGUSD
        NASDAQ

    Each market receives:

        H4
        H1
        M15

    Therefore a complete scan contains:

        6 x 3 = 18 timeframe streams.

    Failure of one market does not stop the remaining markets.
    """

    _validate_market_list()

    validated_count = _validate_count(
        count
    )

    results: Dict[str, Dict[str, Any]] = {}

    for market in MARKET_ORDER:

        results[market] = scan_market(
            market=market,
            count=validated_count,
            timeframes=TIMEFRAME_ORDER,
        )

    ready_markets = [
        market
        for market in MARKET_ORDER
        if results[market].get("status")
        == SCAN_STATUS_READY
    ]

    partial_markets = [
        market
        for market in MARKET_ORDER
        if results[market].get("status")
        == SCAN_STATUS_PARTIAL
    ]

    failed_markets = [
        market
        for market in MARKET_ORDER
        if results[market].get("status")
        == SCAN_STATUS_ERROR
    ]

    total_ready_timeframes = sum(
        int(
            results[market].get(
                "ready_timeframe_count",
                0,
            )
        )
        for market in MARKET_ORDER
    )

    total_required_timeframes = (
        EXPECTED_STREAM_COUNT
    )

    if len(ready_markets) == EXPECTED_MARKET_COUNT:

        status = SCAN_STATUS_READY

    elif ready_markets or partial_markets:

        status = SCAN_STATUS_PARTIAL

    else:

        status = SCAN_STATUS_ERROR

    return {
        "status": status,

        "scanner": SCANNER_NAME,

        "top_down": True,

        "market_data_only": True,

        "analysis_order": list(
            TIMEFRAME_ORDER
        ),

        "markets": results,

        "market_count": EXPECTED_MARKET_COUNT,

        "expected_market_count": (
            EXPECTED_MARKET_COUNT
        ),

        "timeframes_per_market": (
            EXPECTED_TIMEFRAME_COUNT
        ),

        "expected_stream_count": (
            EXPECTED_STREAM_COUNT
        ),

        "ready_market_count": len(
            ready_markets
        ),

        "partial_market_count": len(
            partial_markets
        ),

        "failed_market_count": len(
            failed_markets
        ),

        "ready_timeframe_count": (
            total_ready_timeframes
        ),

        "required_timeframe_count": (
            total_required_timeframes
        ),

        "data_ready": (
            status == SCAN_STATUS_READY
        ),

        "ready_markets": ready_markets,

        "partial_markets": partial_markets,

        "failed_markets": failed_markets,

        # No decision is produced by scanner.
        "decision": None,
    }


# =====================================================================
# SCANNER READINESS
# =====================================================================

def scanner_ready() -> bool:
    """
    Return True when MT5 is initialized.

    This is only a market-data connection check.

    It does NOT authorize trading.
    """

    try:

        if not mt5_initialized():
            initialize_mt5()

        return mt5_initialized()

    except Exception:

        return False


# =====================================================================
# SCANNER MARKET METADATA
# =====================================================================

def scanner_markets() -> Tuple[str, ...]:
    """
    Return the authoritative six BALLY FLOW markets.
    """

    _validate_market_list()

    return MARKET_ORDER


def scanner_timeframes() -> Tuple[str, ...]:
    """
    Return the authoritative top-down timeframes.
    """

    return TIMEFRAME_ORDER


def scanner_stream_count() -> int:
    """
    Return the number of market/timeframe streams in a
    complete scanner cycle.

    6 markets x 3 timeframes = 18 streams.
    """

    return (
        len(MARKET_ORDER)
        * len(TIMEFRAME_ORDER)
    )


def scanner_info() -> Dict[str, Any]:
    """
    Return scanner configuration and readiness metadata.
    """

    _validate_market_list()

    return {
        "name": SCANNER_NAME,

        "status": (
            SCAN_STATUS_READY
            if scanner_ready()
            else SCAN_STATUS_ERROR
        ),

        "markets": list(
            MARKET_ORDER
        ),

        "market_count": len(
            MARKET_ORDER
        ),

        "timeframes": list(
            TIMEFRAME_ORDER
        ),

        "timeframes_per_market": len(
            TIMEFRAME_ORDER
        ),

        "analysis_order": list(
            TIMEFRAME_ORDER
        ),

        "top_down_hierarchy": (
            "H4 -> H1 -> M15"
        ),

        "stream_count": scanner_stream_count(),

        "default_candle_count": (
            DEFAULT_CANDLE_COUNT
        ),

        "technical_analysis": False,

        "fundamental_analysis": False,

        "hybrid_analysis": False,

        "trading_decision": False,

        "risk_management": False,

        "position_sizing": False,

        "execution": False,
    }


# =====================================================================
# CONVENIENCE API
# =====================================================================

def scan(
    market: Optional[str] = None,
    count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convenience scanner entry point.

    market supplied:
        scan one market top-down.

    market omitted:
        scan all six markets top-down.
    """

    if market is None:

        return scan_all_markets(
            count=count
        )

    return scan_market(
        market=market,
        count=count,
        timeframes=TIMEFRAME_ORDER,
    )


# =====================================================================
# PUBLIC EXPORTS
# =====================================================================

__all__ = [
    "SCANNER_NAME",

    "SCAN_STATUS_READY",
    "SCAN_STATUS_PARTIAL",
    "SCAN_STATUS_ERROR",

    "TIMEFRAME_ORDER",
    "MARKET_ORDER",

    "EXPECTED_MARKET_COUNT",
    "EXPECTED_TIMEFRAME_COUNT",
    "EXPECTED_STREAM_COUNT",

    "scan_market",
    "scan_all_markets",

    "scanner_ready",
    "scanner_markets",
    "scanner_timeframes",
    "scanner_stream_count",
    "scanner_info",

    "scan",
]

# =====================================================================
# MODULE EXECUTION
# =====================================================================

if __name__ == "__main__":

    print("=" * 70)
    print("BALLY FLOW - SIX MARKET TOP-DOWN SCANNER")
    print("=" * 70)

    try:

        info = scanner_info()

        print(f"STATUS: {info['status']}")
        print(f"MARKETS: {info['market_count']}")
        print(
            f"TIMEFRAMES: "
            f"{' -> '.join(info['timeframes'])}"
        )
        print(
            f"STREAMS: {info['stream_count']}"
        )
        print()

        result = scan_all_markets()

        print("=" * 70)
        print("SCAN RESULT")
        print("=" * 70)

        print(f"STATUS: {result['status']}")
        print(
            f"READY MARKETS: "
            f"{result['ready_market_count']}/"
            f"{result['expected_market_count']}"
        )
        print(
            f"READY TIMEFRAMES: "
            f"{result['ready_timeframe_count']}/"
            f"{result['required_timeframe_count']}"
        )

        print()

        for market in MARKET_ORDER:

            market_result = result["markets"][market]

            print(
                f"{market}: "
                f"{market_result['status']} "
                f"("
                f"{market_result['ready_timeframe_count']}/"
                f"{EXPECTED_TIMEFRAME_COUNT} timeframes"
                f")"
            )

            for timeframe in TIMEFRAME_ORDER:

                timeframe_result = (
                    market_result
                    .get("timeframes", {})
                    .get(timeframe, {})
                )

                print(
                    f"    {timeframe}: "
                    f"{timeframe_result.get('status', 'ERROR')} "
                    f"- "
                    f"{timeframe_result.get('candle_count', 0)} candles"
                )

        print()
        print("=" * 70)
        print("SCANNER COMPLETE")
        print("=" * 70)

    except Exception as exc:

        print("=" * 70)
        print("SCANNER ERROR")
        print("=" * 70)
        print(f"{type(exc).__name__}: {exc}")