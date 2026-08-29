"""
BALLY FLOW - Market Data / Candles

Canonical market-candle data provider for BALLY FLOW.

RESPONSIBILITIES
----------------
This module is responsible for:

    - MT5 candle retrieval
    - timeframe normalization
    - OHLC/OHLCV normalization
    - chronological ordering
    - candle validation
    - data sufficiency checks
    - market availability checks
    - freshness checks
    - standardized candle-data responses

This module MUST NOT:

    - generate BUY / SELL signals
    - make trading decisions
    - perform technical confluence
    - perform fundamental analysis
    - calculate position size
    - manage risk
    - place MT5 orders
    - execute trades

CANONICAL DATA FLOW
-------------------

    MT5
      |
      v
    candles.py
      |
      v
    normalized candles
      |
      +--> Technical Engine
      |
      +--> Fundamental / Hybrid infrastructure
      |
      +--> Market Analytics
      |
      +--> other consumers

CANDLE FORMAT
-------------

Each normalized candle has:

    {
        "time": ...,
        "timestamp": ...,
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float,
        "tick_volume": float
    }

Candles are always ordered:

    oldest -> newest

IMPORTANT
---------

The module is designed to work safely when MetaTrader5 is unavailable
or when the market is closed. It does not silently manufacture data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_CANDLE_COUNT = 200

MINIMUM_CANDLE_COUNT = 1

# Maximum acceptable age of the newest candle, expressed as a multiple
# of the timeframe duration. A value of 3 means the newest candle may
# reasonably be up to approximately three timeframe periods old.
DEFAULT_FRESHNESS_MULTIPLIER = 3.0

# Common timeframe aliases.
TIMEFRAME_ALIASES = {
    "M1": "M1",
    "1M": "M1",
    "MIN1": "M1",
    "MINUTE1": "M1",

    "M2": "M2",
    "2M": "M2",

    "M3": "M3",
    "3M": "M3",

    "M4": "M4",
    "4M": "M4",

    "M5": "M5",
    "5M": "M5",

    "M6": "M6",
    "6M": "M6",

    "M10": "M10",
    "10M": "M10",

    "M12": "M12",
    "12M": "M12",

    "M15": "M15",
    "15M": "M15",

    "M20": "M20",
    "20M": "M20",

    "M30": "M30",
    "30M": "M30",

    "H1": "H1",
    "1H": "H1",
    "60M": "H1",

    "H2": "H2",
    "2H": "H2",

    "H3": "H3",
    "3H": "H3",

    "H4": "H4",
    "4H": "H4",

    "H6": "H6",
    "6H": "H6",

    "H8": "H8",
    "8H": "H8",

    "H12": "H12",
    "12H": "H12",

    "D1": "D1",
    "1D": "D1",

    "W1": "W1",
    "1W": "W1",

    "MN1": "MN1",
    "MN": "MN1",
    "MONTHLY": "MN1",
}


TIMEFRAME_SECONDS = {
    "M1": 60,
    "M2": 120,
    "M3": 180,
    "M4": 240,
    "M5": 300,
    "M6": 360,
    "M10": 600,
    "M12": 720,
    "M15": 900,
    "M20": 1200,
    "M30": 1800,

    "H1": 3600,
    "H2": 7200,
    "H3": 10800,
    "H4": 14400,
    "H6": 21600,
    "H8": 28800,
    "H12": 43200,

    "D1": 86400,
    "W1": 604800,

    # Approximation used only for freshness calculations.
    "MN1": 2592000,
}


# ============================================================================
# TIMEFRAME HELPERS
# ============================================================================

def normalize_timeframe(timeframe: Any) -> str:
    """
    Normalize a timeframe identifier.

    Examples
    --------
    M15 -> M15
    m15 -> M15
    15m -> M15
    H1  -> H1

    Raises
    ------
    ValueError
        If the timeframe is unsupported.
    """

    if timeframe is None:
        raise ValueError("timeframe is required")

    if not isinstance(timeframe, str):
        raise TypeError("timeframe must be a string")

    value = timeframe.strip().upper()

    if not value:
        raise ValueError("timeframe cannot be empty")

    normalized = TIMEFRAME_ALIASES.get(value)

    if normalized is None:
        raise ValueError(
            f"unsupported timeframe: {timeframe}"
        )

    return normalized


def timeframe_to_mt5(timeframe: str) -> Any:
    """
    Convert normalized timeframe into the corresponding MT5 constant.
    """

    normalized = normalize_timeframe(timeframe)

    if mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is not available"
        )

    attribute_name = f"TIMEFRAME_{normalized}"

    value = getattr(
        mt5,
        attribute_name,
        None,
    )

    if value is None:
        raise ValueError(
            f"MT5 does not provide timeframe: {normalized}"
        )

    return value


def timeframe_seconds(timeframe: Any) -> int:
    """
    Return approximate timeframe duration in seconds.
    """

    normalized = normalize_timeframe(timeframe)

    return TIMEFRAME_SECONDS[normalized]


# ============================================================================
# GENERIC VALUE HELPERS
# ============================================================================

def _to_float(
    value: Any,
    field_name: str,
) -> float:
    """
    Convert a numeric field safely to float.
    """

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{field_name} must be numeric"
        ) from exc

    if result != result:
        raise ValueError(
            f"{field_name} cannot be NaN"
        )

    if result in {
        float("inf"),
        float("-inf"),
    }:
        raise ValueError(
            f"{field_name} must be finite"
        )

    return result


def _get_field(
    candle: Any,
    field: str,
    default: Any = None,
) -> Any:
    """
    Read a field from either a dictionary-like candle or an object.
    """

    if isinstance(candle, dict):
        return candle.get(field, default)

    return getattr(
        candle,
        field,
        default,
    )


def _extract_timestamp(
    candle: Any,
) -> Optional[float]:
    """
    Extract a candle timestamp.

    Supports:

        time
        timestamp

    and datetime values.
    """

    value = _get_field(
        candle,
        "time",
        None,
    )

    if value is None:
        value = _get_field(
            candle,
            "timestamp",
            None,
        )

    if value is None:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value.timestamp()

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ============================================================================
# CANDLE VALIDATION
# ============================================================================

def validate_candle(
    candle: Dict[str, Any],
    index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize one candle.

    Required fields:

        open
        high
        low
        close

    Optional fields:

        volume
        tick_volume
        time
        timestamp
    """

    if not isinstance(candle, dict):
        raise TypeError(
            "candle must be a dictionary"
        )

    prefix = (
        f"candle {index}"
        if index is not None
        else "candle"
    )

    required = (
        "open",
        "high",
        "low",
        "close",
    )

    values: Dict[str, float] = {}

    for field in required:

        if field not in candle:
            raise ValueError(
                f"{prefix} is missing OHLC field: {field}"
            )

        values[field] = _to_float(
            candle[field],
            field,
        )

    open_price = values["open"]
    high = values["high"]
    low = values["low"]
    close = values["close"]

    if high < low:
        raise ValueError(
            f"{prefix} has high below low"
        )

    if high < open_price:
        raise ValueError(
            f"{prefix} has high below open"
        )

    if high < close:
        raise ValueError(
            f"{prefix} has high below close"
        )

    if low > open_price:
        raise ValueError(
            f"{prefix} has low above open"
        )

    if low > close:
        raise ValueError(
            f"{prefix} has low above close"
        )

    normalized: Dict[str, Any] = {
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
    }

    if "volume" in candle:

        volume = _to_float(
            candle["volume"],
            "volume",
        )

        if volume < 0:
            raise ValueError(
                f"{prefix} volume cannot be negative"
            )

        normalized["volume"] = volume

    if "tick_volume" in candle:

        tick_volume = _to_float(
            candle["tick_volume"],
            "tick_volume",
        )

        if tick_volume < 0:
            raise ValueError(
                f"{prefix} tick_volume cannot be negative"
            )

        normalized["tick_volume"] = tick_volume

    if "time" in candle:
        normalized["time"] = candle["time"]

    if "timestamp" in candle:
        normalized["timestamp"] = candle["timestamp"]

    return normalized


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_candles(
    candles: Any,
    sort_oldest_first: bool = True,
    validate: bool = True,
) -> List[Dict[str, Any]]:
    """
    Normalize arbitrary candle input into standard dictionaries.

    Supported inputs:

        list[dict]
        tuple[dict]
        MT5 namedtuple records
        dictionary containing "candles"

    Candles are returned oldest -> newest by default.
    """

    if candles is None:
        raise ValueError("candles are required")

    if isinstance(candles, dict):

        if "candles" in candles:
            candles = candles["candles"]

        else:
            candles = [candles]

    try:
        sequence = list(candles)
    except TypeError as exc:
        raise TypeError(
            "candles must be an iterable"
        ) from exc

    normalized: List[Dict[str, Any]] = []

    for index, candle in enumerate(sequence):

        item: Dict[str, Any] = {}

        for field in (
            "open",
            "high",
            "low",
            "close",
            "volume",
            "tick_volume",
            "time",
            "timestamp",
        ):

            value = _get_field(
                candle,
                field,
                None,
            )

            if value is not None:
                item[field] = value

        # Some MT5 records expose tick_volume but not volume.
        # We preserve both rather than silently confusing them.
        if validate:
            item = validate_candle(
                item,
                index=index,
            )
        else:
            for field in (
                "open",
                "high",
                "low",
                "close",
            ):
                if field in item:
                    item[field] = _to_float(
                        item[field],
                        field,
                    )

        normalized.append(item)

    if sort_oldest_first:

        timestamps = [
            _extract_timestamp(candle)
            for candle in normalized
        ]

        if all(
            timestamp is not None
            for timestamp in timestamps
        ):

            normalized = [
                candle
                for _, candle in sorted(
                    zip(
                        timestamps,
                        normalized,
                    ),
                    key=lambda pair: pair[0],
                )
            ]

    return normalized


# ============================================================================
# MT5 INITIALIZATION
# ============================================================================

def ensure_mt5_connection() -> Dict[str, Any]:
    """
    Ensure that the MT5 Python API is initialized.

    Returns standardized connection information.
    """

    if mt5 is None:
        return {
            "connected": False,
            "available": False,
            "reason": (
                "MetaTrader5 package is not installed"
            ),
            "terminal": None,
        }

    try:
        initialized = mt5.initialize()
    except Exception as exc:
        return {
            "connected": False,
            "available": True,
            "reason": str(exc),
            "terminal": None,
        }

    if not initialized:

        error = None

        try:
            error = mt5.last_error()
        except Exception:
            error = None

        return {
            "connected": False,
            "available": True,
            "reason": (
                f"MT5 initialization failed: {error}"
            ),
            "terminal": None,
        }

    terminal = None

    try:
        terminal = mt5.terminal_info()
    except Exception:
        terminal = None

    return {
        "connected": True,
        "available": True,
        "reason": None,
        "terminal": terminal,
    }


# ============================================================================
# SYMBOL VALIDATION
# ============================================================================

def ensure_symbol(
    symbol: str,
) -> Dict[str, Any]:
    """
    Ensure that an MT5 symbol exists and is selected.
    """

    if not isinstance(symbol, str):
        raise TypeError(
            "symbol must be a string"
        )

    symbol = symbol.strip()

    if not symbol:
        raise ValueError(
            "symbol cannot be empty"
        )

    connection = ensure_mt5_connection()

    if not connection["connected"]:
        return {
            "available": False,
            "symbol": symbol,
            "reason": connection["reason"],
            "info": None,
        }

    try:
        selected = mt5.symbol_select(
            symbol,
            True,
        )
    except Exception as exc:
        return {
            "available": False,
            "symbol": symbol,
            "reason": str(exc),
            "info": None,
        }

    if not selected:
        return {
            "available": False,
            "symbol": symbol,
            "reason": (
                "symbol could not be selected"
            ),
            "info": None,
        }

    try:
        info = mt5.symbol_info(symbol)
    except Exception as exc:
        return {
            "available": False,
            "symbol": symbol,
            "reason": str(exc),
            "info": None,
        }

    if info is None:
        return {
            "available": False,
            "symbol": symbol,
            "reason": "symbol information unavailable",
            "info": None,
        }

    return {
        "available": True,
        "symbol": symbol,
        "reason": None,
        "info": info,
    }


# ============================================================================
# MARKET AVAILABILITY
# ============================================================================

def is_weekend(
    now: Optional[datetime] = None,
) -> bool:
    """
    Return True for Saturday/Sunday in UTC.

    This is a broad availability safeguard. Individual instruments
    can have different trading schedules, so callers should still use
    actual MT5 market information when available.
    """

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    return now.weekday() >= 5


def market_availability(
    symbol: str,
) -> Dict[str, Any]:
    """
    Determine broad market availability for a symbol.
    """

    now = datetime.now(
        timezone.utc
    )

    weekend = is_weekend(now)

    if weekend:
        return {
            "available": False,
            "market_open": False,
            "weekend": True,
            "reason": "market_weekend",
            "timestamp": now.timestamp(),
        }

    if mt5 is None:
        return {
            "available": False,
            "market_open": False,
            "weekend": False,
            "reason": "MetaTrader5 unavailable",
            "timestamp": now.timestamp(),
        }

    try:
        tick = mt5.symbol_info_tick(
            symbol
        )
    except Exception as exc:
        return {
            "available": False,
            "market_open": False,
            "weekend": False,
            "reason": str(exc),
            "timestamp": now.timestamp(),
        }

    if tick is None:
        return {
            "available": False,
            "market_open": False,
            "weekend": False,
            "reason": "no tick available",
            "timestamp": now.timestamp(),
        }

    bid = getattr(
        tick,
        "bid",
        0.0,
    )

    ask = getattr(
        tick,
        "ask",
        0.0,
    )

    has_price = (
        bid is not None
        and ask is not None
        and float(bid) > 0
        and float(ask) > 0
    )

    return {
        "available": bool(has_price),
        "market_open": bool(has_price),
        "weekend": False,
        "reason": None
        if has_price
        else "no valid bid/ask",
        "bid": (
            float(bid)
            if bid is not None
            else None
        ),
        "ask": (
            float(ask)
            if ask is not None
            else None
        ),
        "timestamp": now.timestamp(),
    }


# ============================================================================
# FRESHNESS
# ============================================================================

def candle_age_seconds(
    candle: Dict[str, Any],
    now: Optional[datetime] = None,
) -> Optional[float]:
    """
    Return age of a candle in seconds.

    Returns None if the candle contains no usable timestamp.
    """

    timestamp = _extract_timestamp(
        candle
    )

    if timestamp is None:
        return None

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    age = (
        now.timestamp()
        - timestamp
    )

    return max(
        age,
        0.0,
    )


def validate_freshness(
    candles: Sequence[Dict[str, Any]],
    timeframe: str,
    multiplier: float = DEFAULT_FRESHNESS_MULTIPLIER,
) -> Dict[str, Any]:
    """
    Evaluate freshness of the newest candle.

    A candle is considered stale when its age exceeds:

        timeframe duration * multiplier

    Missing timestamps do not automatically invalidate candle data.
    Instead, freshness becomes UNKNOWN.
    """

    if multiplier <= 0:
        raise ValueError(
            "freshness multiplier must be greater than zero"
        )

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    if not candles:
        return {
            "fresh": False,
            "known": False,
            "reason": "no candles",
            "age_seconds": None,
            "maximum_age_seconds": None,
        }

    newest = candles[-1]

    age = candle_age_seconds(
        newest
    )

    maximum_age = (
        timeframe_seconds(
            normalized_timeframe
        )
        * multiplier
    )

    if age is None:
        return {
            "fresh": True,
            "known": False,
            "reason": "timestamp unavailable",
            "age_seconds": None,
            "maximum_age_seconds": maximum_age,
        }

    fresh = age <= maximum_age

    return {
        "fresh": fresh,
        "known": True,
        "reason": (
            None
            if fresh
            else "newest candle is stale"
        ),
        "age_seconds": round(
            age,
            3,
        ),
        "maximum_age_seconds": maximum_age,
    }


# ============================================================================
# MT5 RETRIEVAL
# ============================================================================

def fetch_mt5_candles(
    symbol: str,
    timeframe: Any = "M15",
    count: int = DEFAULT_CANDLE_COUNT,
    start_pos: int = 0,
) -> List[Dict[str, Any]]:
    """
    Fetch candles directly from MT5.

    Candles are returned oldest -> newest.

    The returned data is normalized into ordinary dictionaries.
    """

    if not isinstance(count, int):
        raise TypeError(
            "count must be an integer"
        )

    if count < MINIMUM_CANDLE_COUNT:
        raise ValueError(
            "count must be greater than zero"
        )

    if not isinstance(start_pos, int):
        raise TypeError(
            "start_pos must be an integer"
        )

    if start_pos < 0:
        raise ValueError(
            "start_pos cannot be negative"
        )

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    connection = ensure_mt5_connection()

    if not connection["connected"]:
        raise RuntimeError(
            connection["reason"]
        )

    symbol_result = ensure_symbol(
        symbol
    )

    if not symbol_result["available"]:
        raise RuntimeError(
            symbol_result["reason"]
        )

    mt5_timeframe = timeframe_to_mt5(
        normalized_timeframe
    )

    try:
        rates = mt5.copy_rates_from_pos(
            symbol,
            mt5_timeframe,
            start_pos,
            count,
        )
    except Exception as exc:
        raise RuntimeError(
            f"MT5 candle retrieval failed: {exc}"
        ) from exc

    if rates is None:
        error = None

        try:
            error = mt5.last_error()
        except Exception:
            error = None

        raise RuntimeError(
            f"MT5 returned no candle data: {error}"
        )

    try:
        sequence = list(rates)
    except TypeError as exc:
        raise RuntimeError(
            "MT5 candle data is not iterable"
        ) from exc

    if not sequence:
        return []

    candles: List[Dict[str, Any]] = []

    for index, rate in enumerate(sequence):

        item = {
            "time": _get_field(
                rate,
                "time",
                None,
            ),
            "open": _get_field(
                rate,
                "open",
                None,
            ),
            "high": _get_field(
                rate,
                "high",
                None,
            ),
            "low": _get_field(
                rate,
                "low",
                None,
            ),
            "close": _get_field(
                rate,
                "close",
                None,
            ),
            "tick_volume": _get_field(
                rate,
                "tick_volume",
                None,
            ),
            "volume": _get_field(
                rate,
                "real_volume",
                None,
            ),
        }

        # Some brokers/data feeds may provide zero real volume.
        # Keep tick_volume as the useful fallback without destroying
        # the original real_volume field.
        if item["volume"] is None:
            item["volume"] = item["tick_volume"]

        normalized = validate_candle(
            item,
            index=index,
        )

        timestamp = _extract_timestamp(
            normalized
        )

        if timestamp is not None:
            normalized["timestamp"] = timestamp

        candles.append(
            normalized
        )

    return normalize_candles(
        candles,
        sort_oldest_first=True,
        validate=True,
    )


# ============================================================================
# STANDARDIZED DATA RESULT
# ============================================================================

def build_candle_result(
    symbol: str,
    timeframe: str,
    candles: Sequence[Dict[str, Any]],
    requested_count: int,
    freshness_multiplier: float = DEFAULT_FRESHNESS_MULTIPLIER,
) -> Dict[str, Any]:
    """
    Build the canonical standardized candle result.
    """

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    normalized = normalize_candles(
        candles,
        sort_oldest_first=True,
        validate=True,
    )

    freshness = validate_freshness(
        normalized,
        normalized_timeframe,
        multiplier=freshness_multiplier,
    )

    newest = (
        normalized[-1]
        if normalized
        else None
    )

    oldest = (
        normalized[0]
        if normalized
        else None
    )

    return {
        "status": (
            "READY"
            if normalized
            else "NO_DATA"
        ),
        "market_data": True,
        "component": "candles",

        "symbol": symbol,
        "timeframe": normalized_timeframe,

        "requested_count": requested_count,
        "candle_count": len(normalized),

        "candles": normalized,

        "oldest_candle": oldest,
        "newest_candle": newest,

        "freshness": freshness,

        "sufficient_data": (
            len(normalized)
            >= requested_count
        ),

        "technical_only": True,
    }


# ============================================================================
# PUBLIC API
# ============================================================================

def get_candles(
    symbol: str,
    timeframe: Any = "M15",
    count: int = DEFAULT_CANDLE_COUNT,
    start_pos: int = 0,
    freshness_multiplier: float = DEFAULT_FRESHNESS_MULTIPLIER,
    require_fresh: bool = False,
    require_full_count: bool = False,
) -> Dict[str, Any]:
    """
    Canonical candle retrieval API.

    Parameters
    ----------
    symbol:
        MT5 trading symbol, e.g. XAUUSD.

    timeframe:
        M1, M5, M15, H1, H4, etc.

    count:
        Number of candles requested.

    start_pos:
        MT5 starting position.

    freshness_multiplier:
        Maximum candle age expressed as a multiple of timeframe duration.

    require_fresh:
        If True, stale data results in status DATA_STALE.

    require_full_count:
        If True, fewer candles than requested results in
        INSUFFICIENT_DATA.

    Returns
    -------
    dict
        Standardized market-data response.
    """

    if not isinstance(count, int):
        raise TypeError(
            "count must be an integer"
        )

    if count < MINIMUM_CANDLE_COUNT:
        raise ValueError(
            "count must be greater than zero"
        )

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    # Broad weekend protection.
    availability = market_availability(
        symbol
    )

    if not availability["available"]:

        # We still attempt data retrieval when MT5 can provide
        # historical candles. This is important because technical
        # analysis can legitimately inspect historical data while
        # the market is closed.
        if (
            availability.get("reason")
            == "market_weekend"
        ):
            pass

        elif mt5 is None:
            return {
                "status": "UNAVAILABLE",
                "market_data": True,
                "component": "candles",
                "technical_only": True,
                "symbol": symbol,
                "timeframe": normalized_timeframe,
                "requested_count": count,
                "candle_count": 0,
                "candles": [],
                "oldest_candle": None,
                "newest_candle": None,
                "freshness": {
                    "fresh": False,
                    "known": False,
                    "reason": availability["reason"],
                    "age_seconds": None,
                    "maximum_age_seconds": None,
                },
                "sufficient_data": False,
                "market_availability": availability,
            }

    try:
        candles = fetch_mt5_candles(
            symbol=symbol,
            timeframe=normalized_timeframe,
            count=count,
            start_pos=start_pos,
        )

    except Exception as exc:

        return {
            "status": "ERROR",
            "market_data": True,
            "component": "candles",
            "technical_only": True,
            "symbol": symbol,
            "timeframe": normalized_timeframe,
            "requested_count": count,
            "candle_count": 0,
            "candles": [],
            "oldest_candle": None,
            "newest_candle": None,
            "freshness": {
                "fresh": False,
                "known": False,
                "reason": str(exc),
                "age_seconds": None,
                "maximum_age_seconds": None,
            },
            "sufficient_data": False,
            "market_availability": availability,
            "error": str(exc),
        }

    result = build_candle_result(
        symbol=symbol,
        timeframe=normalized_timeframe,
        candles=candles,
        requested_count=count,
        freshness_multiplier=freshness_multiplier,
    )

    result["market_availability"] = availability

    if require_full_count:

        if len(candles) < count:
            result["status"] = (
                "INSUFFICIENT_DATA"
            )

    elif not candles:
        result["status"] = "NO_DATA"

    if require_fresh:

        if result["freshness"]["known"]:

            if not result["freshness"]["fresh"]:
                result["status"] = "DATA_STALE"

    return result


def get_candle_data(
    symbol: str,
    timeframe: Any = "M15",
    count: int = DEFAULT_CANDLE_COUNT,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility alias for get_candles().
    """

    return get_candles(
        symbol=symbol,
        timeframe=timeframe,
        count=count,
        **kwargs,
    )


def fetch_candles(
    symbol: str,
    timeframe: Any = "M15",
    count: int = DEFAULT_CANDLE_COUNT,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Compatibility alias for get_candles().
    """

    return get_candles(
        symbol=symbol,
        timeframe=timeframe,
        count=count,
        **kwargs,
    )


# ============================================================================
# DIRECT CANDLE-ONLY API
# ============================================================================

def get_normalized_candles(
    symbol: str,
    timeframe: Any = "M15",
    count: int = DEFAULT_CANDLE_COUNT,
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """
    Convenience API returning only the normalized candle list.

    Raises RuntimeError when candle retrieval fails.
    """

    result = get_candles(
        symbol=symbol,
        timeframe=timeframe,
        count=count,
        **kwargs,
    )

    if result["status"] in {
        "ERROR",
        "UNAVAILABLE",
    }:

        raise RuntimeError(
            result.get(
                "error",
                result.get(
                    "freshness",
                    {},
                ).get(
                    "reason",
                    "candle retrieval failed",
                ),
            )
        )

    return result["candles"]


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    "DEFAULT_CANDLE_COUNT",
    "MINIMUM_CANDLE_COUNT",
    "DEFAULT_FRESHNESS_MULTIPLIER",
    "TIMEFRAME_ALIASES",
    "TIMEFRAME_SECONDS",

    "normalize_timeframe",
    "timeframe_to_mt5",
    "timeframe_seconds",

    "validate_candle",
    "normalize_candles",

    "ensure_mt5_connection",
    "ensure_symbol",

    "is_weekend",
    "market_availability",

    "candle_age_seconds",
    "validate_freshness",

    "fetch_mt5_candles",
    "build_candle_result",

    "get_candles",
    "get_candle_data",
    "fetch_candles",
    "get_normalized_candles",
]