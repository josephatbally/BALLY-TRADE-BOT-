"""
BALLY FLOW - Symbol Market Data

Broker-aware market-data acquisition and symbol normalization layer.

RESPONSIBILITIES
----------------
This module:

    - Defines the agreed BALLY FLOW markets.
    - Defines H4 / H1 / M15 top-down timeframes.
    - Resolves logical markets to broker-specific MT5 symbols.
    - Handles broker prefixes, suffixes and common aliases.
    - Selects symbols in MT5.
    - Retrieves OHLCV data from MetaTrader 5.
    - Correctly handles MT5 / NumPy structured rate records.
    - Converts rates into standardized candle dictionaries.
    - Removes duplicate candles.
    - Sorts candles oldest -> newest.
    - Validates OHLC and timestamps.
    - Provides H4 / H1 / M15 top-down market snapshots.
    - Provides all-market acquisition with per-market isolation.
    - Identifies the latest closed candle.

This module MUST NOT:

    - perform technical analysis
    - calculate SMC
    - calculate confluence
    - make BUY / SELL / NO_TRADE decisions
    - perform fundamental analysis
    - calculate risk
    - calculate position size
    - execute trades
    - place MT5 orders


TOP-DOWN ANALYSIS
-----------------

BALLY FLOW uses:

    H4 -> H1 -> M15


AGREED MARKETS
--------------

    XAUUSD
    EURUSD
    GBPUSD
    USDJPY
    XAGUSD
    NASDAQ

Logical market names are independent from broker symbol names.

Examples:

    XAUUSD -> XAUUSD
    XAUUSD -> XAUUSDm
    XAUUSD -> XAUUSD.a

    XAGUSD -> SILVER
    XAGUSD -> XAGUSDm

    NASDAQ -> USTEC
    NASDAQ -> NAS100
    NASDAQ -> US100

The strategy should always use the logical market.

This module resolves the actual broker symbol.


CANDLE FORMAT
-------------

Standardized candles:

    {
        "time": ...,
        "open": ...,
        "high": ...,
        "low": ...,
        "close": ...,
        "volume": ...
    }

Newest candle is last.


IMPORTANT MT5 BEHAVIOR
----------------------

MT5 copy_rates_from_pos(..., 0, count) normally includes the
currently forming candle.

The market-data layer does NOT silently delete it from the returned
historical collection because callers may need it.

Use latest_closed_candle() when confirmed closed-candle data is required.
"""


from __future__ import annotations

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)
import math
import time as time_module


# =====================================================================
# OPTIONAL MT5 IMPORT
# =====================================================================

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None


# =====================================================================
# CONSTANTS
# =====================================================================

MARKETS: Tuple[str, ...] = (
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
)

TIMEFRAMES: Tuple[str, ...] = (
    "H4",
    "H1",
    "M15",
)

TOP_DOWN_TIMEFRAMES: Tuple[str, ...] = (
    "H4",
    "H1",
    "M15",
)

DEFAULT_CANDLE_COUNT = 300

TOP_DOWN_CANDLE_COUNTS: Dict[str, int] = {
    "H4": 300,
    "H1": 500,
    "M15": 1000,
}
MIN_CANDLE_COUNT = 10
MAX_CANDLE_COUNT = 5000

# =====================================================================
# TIMEFRAME MAPPING
# =====================================================================

TIMEFRAME_SECONDS: Dict[str, int] = {
    "M1": 60,
    "M5": 300,
    "M15": 900,
    "M30": 1800,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
    "W1": 604800,
    "MN1": 2592000,
}


TIMEFRAME_MAP: Dict[str, Any] = {}

if mt5 is not None:

    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }


# =====================================================================
# BROKER SYMBOL ALIASES
# =====================================================================

SYMBOL_ALIASES: Dict[str, Tuple[str, ...]] = {

    "XAUUSD": (
        "XAUUSD",
        "GOLD",
        "XAUUSDm",
        "XAUUSD.a",
        "XAUUSD.",
        "GOLDm",
        "GOLD.a",
    ),

    "EURUSD": (
        "EURUSD",
        "EURUSDm",
        "EURUSD.a",
        "EURUSD.",
    ),

    "GBPUSD": (
        "GBPUSD",
        "GBPUSDm",
        "GBPUSD.a",
        "GBPUSD.",
    ),

    "USDJPY": (
        "USDJPY",
        "USDJPYm",
        "USDJPY.a",
        "USDJPY.",
    ),

    "XAGUSD": (
        "XAGUSD",
        "SILVER",
        "XAGUSDm",
        "XAGUSD.a",
        "XAGUSD.",
        "SILVERm",
        "SILVER.a",
    ),

    "NASDAQ": (
        "NASDAQ",
        "NAS100",
        "USTEC",
        "US100",
        "NASDAQ100",
        "NAS100m",
        "NAS100.a",
        "USTECm",
        "USTEC.a",
        "US100m",
        "US100.a",
    ),
}


# =====================================================================
# VALIDATION CONSTANTS
# =====================================================================

REQUIRED_CANDLE_FIELDS = (
    "open",
    "high",
    "low",
    "close",
)


# =====================================================================
# GENERAL HELPERS
# =====================================================================

def _is_finite_number(value: Any) -> bool:
    """
    Return True if value can safely be interpreted as finite float.
    """

    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to finite float.
    """

    try:
        result = float(value)

        if not math.isfinite(result):
            return None

        return result

    except (TypeError, ValueError, OverflowError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    """
    Safely convert a value to integer.
    """

    try:
        return int(value)

    except (TypeError, ValueError, OverflowError):
        return None


# =====================================================================
# MARKET VALIDATION
# =====================================================================

def _validate_market(market: str) -> str:
    """
    Validate and normalize a logical BALLY FLOW market.
    """

    if not isinstance(market, str):
        raise TypeError("market must be a string")

    normalized = market.strip().upper()

    if not normalized:
        raise ValueError("market is required")

    if normalized in MARKETS:
        return normalized

    for logical, aliases in SYMBOL_ALIASES.items():

        alias_set = {
            alias.upper()
            for alias in aliases
        }

        if normalized in alias_set:
            return logical

    raise ValueError(
        f"unsupported market: {market!r}. "
        f"Supported markets: {', '.join(MARKETS)}"
    )


# =====================================================================
# TIMEFRAME VALIDATION
# =====================================================================

def _validate_timeframe(timeframe: str) -> str:
    """
    Validate and normalize timeframe.
    """

    if not isinstance(timeframe, str):
        raise TypeError("timeframe must be a string")

    normalized = timeframe.strip().upper()

    if normalized not in TIMEFRAME_SECONDS:
        raise ValueError(
            f"unsupported timeframe: {timeframe!r}"
        )

    return normalized


def _validate_count(count: int) -> int:
    """
    Validate requested candle count.

    BALLY FLOW allows flexible history requests while protecting
    the MT5 data layer from unreasonable requests.
    """

    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("count must be an integer")

    if count < MIN_CANDLE_COUNT:
        raise ValueError(
            f"count must be at least {MIN_CANDLE_COUNT}"
        )

    if count > MAX_CANDLE_COUNT:
        raise ValueError(
            f"count cannot exceed {MAX_CANDLE_COUNT}"
        )

    return count

def top_down_candle_count(timeframe: str) -> int:
    """
    Return the recommended historical candle depth for a
    BALLY FLOW top-down timeframe.

    H4  -> 300
    H1  -> 500
    M15 -> 1000
    """

    normalized = normalize_timeframe(timeframe)

    if normalized not in TOP_DOWN_CANDLE_COUNTS:
        raise ValueError(
            f"{normalized} is not a BALLY FLOW top-down timeframe"
        )

    return TOP_DOWN_CANDLE_COUNTS[normalized]

# =====================================================================
# TIMEFRAME HELPERS
# =====================================================================

def normalize_timeframe(timeframe: str) -> str:
    """
    Normalize timeframe.

    Examples:

        m15 -> M15
        h1  -> H1
        h4  -> H4
    """

    return _validate_timeframe(timeframe)


def timeframe_seconds(timeframe: str) -> int:
    """
    Return timeframe duration in seconds.
    """

    normalized = normalize_timeframe(timeframe)

    return TIMEFRAME_SECONDS[normalized]


def mt5_timeframe(timeframe: str) -> Any:
    """
    Return MT5 timeframe constant.
    """

    normalized = normalize_timeframe(timeframe)

    if mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    if normalized not in TIMEFRAME_MAP:
        raise RuntimeError(
            f"MT5 timeframe is unavailable: {normalized}"
        )

    return TIMEFRAME_MAP[normalized]


# =====================================================================
# MARKET HELPERS
# =====================================================================

def normalize_market(market: str) -> str:
    """
    Normalize logical market.

    Examples:

        GOLD   -> XAUUSD
        SILVER -> XAGUSD
        NAS100 -> NASDAQ
        USTEC  -> NASDAQ
    """

    return _validate_market(market)


def symbol_aliases(market: str) -> Tuple[str, ...]:
    """
    Return known aliases for a logical market.
    """

    logical = normalize_market(market)

    return SYMBOL_ALIASES[logical]


# =====================================================================
# MT5 AVAILABILITY
# =====================================================================

def mt5_available() -> bool:
    """
    Return whether MetaTrader5 Python package is available.
    """

    return mt5 is not None


def mt5_initialized() -> bool:
    """
    Return whether an MT5 terminal session is initialized.
    """

    if mt5 is None:
        return False

    try:

        terminal_info = mt5.terminal_info()

        return terminal_info is not None

    except Exception:
        return False


def initialize_mt5() -> bool:
    """
    Initialize MT5.

    Existing initialized sessions are reused.
    """

    if mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    if mt5_initialized():
        return True

    result = mt5.initialize()

    if not result:

        error = mt5.last_error()

        raise RuntimeError(
            f"MT5 initialization failed: {error}"
        )

    return True


def shutdown_mt5() -> None:
    """
    Shut down MT5 Python connection.

    Does NOT close positions or modify trades.
    """

    if mt5 is None:
        return

    try:
        mt5.shutdown()

    except Exception:
        pass


# =====================================================================
# MT5 SYMBOL ENUMERATION
# =====================================================================

def _get_mt5_symbols() -> List[Any]:
    """
    Safely retrieve symbols known by the broker terminal.
    """

    if mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    initialize_mt5()

    try:

        symbols = mt5.symbols_get()

    except Exception as exc:

        raise RuntimeError(
            f"failed to retrieve MT5 symbols: {exc}"
        ) from exc

    if symbols is None:
        return []

    try:
        return list(symbols)

    except TypeError:
        return []


def _symbol_name(item: Any) -> Optional[str]:
    """
    Extract symbol name from:

        string
        MT5 SymbolInfo
        compatible object
        dictionary
    """

    if isinstance(item, str):

        name = item.strip()

        return name or None

    if isinstance(item, dict):

        value = item.get("name")

        if value is None:
            return None

        name = str(value).strip()

        return name or None

    value = getattr(item, "name", None)

    if value is None:
        return None

    name = str(value).strip()

    return name or None


# =====================================================================
# SYMBOL MATCHING
# =====================================================================

def _normalized_symbol_name(name: str) -> str:
    """
    Normalize broker symbol for comparison.

    Keeps alphanumeric characters only and uppercases them.
    """

    return "".join(
        character
        for character in str(name).upper()
        if character.isalnum()
    )


def _symbol_match_score(
    logical: str,
    candidate: str,
) -> int:
    """
    Score a broker symbol candidate.

    Higher score = stronger match.

    Exact known aliases receive highest priority.
    """

    candidate_upper = candidate.upper()

    aliases = symbol_aliases(logical)

    alias_upper = {
        alias.upper()
        for alias in aliases
    }

    if candidate_upper in alias_upper:
        return 10000

    normalized_candidate = _normalized_symbol_name(
        candidate
    )

    normalized_aliases = [
        _normalized_symbol_name(alias)
        for alias in aliases
    ]

    # ---------------------------------------------------------------
    # Exact normalized alias
    # ---------------------------------------------------------------

    if normalized_candidate in normalized_aliases:
        return 9000

    # ---------------------------------------------------------------
    # Common broker prefix/suffix
    # ---------------------------------------------------------------

    for alias in normalized_aliases:

        if not alias:
            continue

        if (
            normalized_candidate.startswith(alias)
            or
            normalized_candidate.endswith(alias)
        ):

            extra = len(
                normalized_candidate
            ) - len(alias)

            # Prefer the candidate with the smallest
            # broker-added prefix/suffix.
            return 8000 - min(extra, 1000)

    # ---------------------------------------------------------------
    # Logical market containment
    # ---------------------------------------------------------------

    normalized_logical = _normalized_symbol_name(
        logical
    )

    if (
        normalized_logical
        and normalized_logical in normalized_candidate
    ):
        return 5000

    # ---------------------------------------------------------------
    # Special NASDAQ aliases
    # ---------------------------------------------------------------

    if logical == "NASDAQ":

        index_aliases = (
            "NASDAQ",
            "NAS100",
            "USTEC",
            "US100",
            "NASDAQ100",
        )

        for alias in index_aliases:

            normalized_alias = _normalized_symbol_name(
                alias
            )

            if normalized_alias in normalized_candidate:

                return 7000

    return 0


def resolve_symbol(
    market: str,
    symbols: Optional[Sequence[Any]] = None,
) -> Optional[str]:
    """
    Resolve logical BALLY FLOW market to actual broker symbol.

    Resolution strategy:

        1. Exact known broker alias.
        2. Normalized exact alias.
        3. Prefix/suffix broker variant.
        4. NASDAQ alias.
        5. Logical market containment.

    The highest-quality candidate is selected.
    """

    logical = normalize_market(market)

    if symbols is None:
        symbols = _get_mt5_symbols()

    candidates: List[Tuple[int, str]] = []

    for item in symbols:

        name = _symbol_name(item)

        if not name:
            continue

        score = _symbol_match_score(
            logical,
            name,
        )

        if score > 0:
            candidates.append(
                (score, name)
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item[0],
            len(item[1]),
            item[1].upper(),
        )
    )

    return candidates[0][1]


def discover_market_symbols() -> Dict[str, Dict[str, Any]]:
    """
    Discover broker symbols for every agreed logical market.

    Returns a per-market result without silently failing the
    entire discovery operation.
    """

    initialize_mt5()

    available_symbols = _get_mt5_symbols()

    results: Dict[str, Dict[str, Any]] = {}

    for market in MARKETS:

        resolved = resolve_symbol(
            market,
            symbols=available_symbols,
        )

        if resolved is None:

            results[market] = {
                "status": "NOT_FOUND",
                "market": market,
                "broker_symbol": None,
                "aliases": list(
                    symbol_aliases(market)
                ),
            }

            continue

        info = None

        try:
            info = mt5.symbol_info(
                resolved
            )
        except Exception:
            info = None

        results[market] = {
            "status": "READY",
            "market": market,
            "broker_symbol": resolved,
            "aliases": list(
                symbol_aliases(market)
            ),
            "symbol_info_available": (
                info is not None
            ),
        }

    return results


# =====================================================================
# SYMBOL SELECTION
# =====================================================================

def select_symbol(
    market: str,
    symbol: Optional[str] = None,
) -> str:
    """
    Resolve and select a broker symbol in MT5.

    Explicit symbol is preferred.

    Returns actual broker symbol.
    """

    if mt5 is None:
        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    logical = normalize_market(market)

    initialize_mt5()

    # ---------------------------------------------------------------
    # Explicit broker symbol
    # ---------------------------------------------------------------

    if symbol is not None:

        selected = str(symbol).strip()

        if not selected:
            raise ValueError(
                "symbol cannot be empty"
            )

        info = mt5.symbol_info(
            selected
        )

        if info is None:
            raise ValueError(
                f"MT5 symbol not found: {selected}"
            )

        selected_result = mt5.symbol_select(
            selected,
            True,
        )

        if not selected_result:

            error = mt5.last_error()

            raise RuntimeError(
                f"failed to select symbol "
                f"{selected}: {error}"
            )

        return selected

    # ---------------------------------------------------------------
    # Automatic broker resolution
    # ---------------------------------------------------------------

    resolved = resolve_symbol(
        logical
    )

    if resolved is None:

        raise ValueError(
            f"unable to resolve MT5 symbol for "
            f"{logical}. Known aliases: "
            f"{', '.join(symbol_aliases(logical))}"
        )

    info = mt5.symbol_info(
        resolved
    )

    if info is None:

        raise RuntimeError(
            f"MT5 returned no symbol information "
            f"for resolved symbol: {resolved}"
        )

    selected_result = mt5.symbol_select(
        resolved,
        True,
    )

    if not selected_result:

        error = mt5.last_error()

        raise RuntimeError(
            f"failed to select MT5 symbol "
            f"{resolved}: {error}"
        )

    return resolved


# =====================================================================
# RATE FIELD EXTRACTION
# =====================================================================

def _extract_rate_field(
    rate: Any,
    field: str,
) -> Any:
    """
    Extract a rate field robustly.

    Supports:

        - dict
        - MT5 namedtuple
        - NumPy structured scalar / numpy.void
        - objects exposing attributes
        - objects supporting [] access

    IMPORTANT:
    MT5 copy_rates_* commonly returns NumPy structured arrays.
    Iterating such an array produces NumPy structured records,
    where field access is performed with rate["open"] rather than
    getattr(rate, "open").

    This function therefore tries mapping/index access first,
    then attribute access.
    """

    if rate is None:
        return None

    # ---------------------------------------------------------------
    # Dictionary / mapping-like access
    # ---------------------------------------------------------------

    if isinstance(rate, dict):

        return rate.get(field)

    # ---------------------------------------------------------------
    # Structured NumPy record / tuple-like field access
    # ---------------------------------------------------------------

    try:

        return rate[field]

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ):
        pass

    # ---------------------------------------------------------------
    # Attribute access
    # ---------------------------------------------------------------

    try:

        return getattr(rate, field)

    except AttributeError:
        return None


# =====================================================================
# SINGLE RATE NORMALIZATION
# =====================================================================

def normalize_rate(
    rate: Any,
) -> Dict[str, Any]:
    """
    Convert one MT5 rate into standardized candle dictionary.
    """

    if rate is None:
        raise ValueError(
            "rate is required"
        )

    item: Dict[str, Any] = {}

    # ---------------------------------------------------------------
    # Required OHLC
    # ---------------------------------------------------------------

    for field in REQUIRED_CANDLE_FIELDS:

        value = _extract_rate_field(
            rate,
            field,
        )

        if value is None:

            raise ValueError(
                f"rate is missing required field: {field}"
            )

        numeric = _safe_float(value)

        if numeric is None:

            raise ValueError(
                f"rate field {field} is not numeric"
            )

        item[field] = numeric

    # ---------------------------------------------------------------
    # OHLC integrity
    # ---------------------------------------------------------------

    high = item["high"]
    low = item["low"]
    open_price = item["open"]
    close = item["close"]

    if high < low:

        raise ValueError(
            "rate has high below low"
        )

    if high < open_price:

        raise ValueError(
            "rate has high below open"
        )

    if high < close:

        raise ValueError(
            "rate has high below close"
        )

    if low > open_price:

        raise ValueError(
            "rate has low above open"
        )

    if low > close:

        raise ValueError(
            "rate has low above close"
        )

    # ---------------------------------------------------------------
    # Time
    # ---------------------------------------------------------------

    timestamp = _extract_rate_field(
        rate,
        "time",
    )

    if timestamp is not None:

        timestamp_int = _safe_int(
            timestamp
        )

        if timestamp_int is not None:
            item["time"] = timestamp_int

    # ---------------------------------------------------------------
    # Real volume
    # ---------------------------------------------------------------

    real_volume = _extract_rate_field(
        rate,
        "real_volume",
    )

    real_value = _safe_float(
        real_volume
    )

    if (
        real_value is not None
        and real_value > 0
    ):

        item["volume"] = real_value
        item["volume_source"] = "real_volume"

    # ---------------------------------------------------------------
    # Standard volume field
    # ---------------------------------------------------------------

    if "volume" not in item:

        direct_volume = _extract_rate_field(
            rate,
            "volume",
        )

        volume_value = _safe_float(
            direct_volume
        )

        if volume_value is not None:

            item["volume"] = volume_value
            item["volume_source"] = "volume"

    # ---------------------------------------------------------------
    # MT5 tick volume
    # ---------------------------------------------------------------

    if "volume" not in item:

        tick_volume = _extract_rate_field(
            rate,
            "tick_volume",
        )

        tick_value = _safe_float(
            tick_volume
        )

        if tick_value is not None:

            item["volume"] = tick_value
            item["volume_source"] = "tick_volume"

    return item


# =====================================================================
# RATE NORMALIZATION
# =====================================================================

def normalize_rates(
    rates: Any,
) -> List[Dict[str, Any]]:
    """
    Convert MT5 rates to standardized candles.

    Output:

        oldest -> newest

    Duplicate timestamps are removed.
    """

    if rates is None:
        return []

    try:

        sequence = list(rates)

    except TypeError as exc:

        raise TypeError(
            "rates must be iterable"
        ) from exc

    candles: List[Dict[str, Any]] = []

    for index, rate in enumerate(sequence):

        try:

            candle = normalize_rate(
                rate
            )

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"invalid rate at index {index}: {exc}"
            ) from exc

        candles.append(candle)

    # ---------------------------------------------------------------
    # Chronological ordering
    # ---------------------------------------------------------------

    if candles and all(
        "time" in candle
        for candle in candles
    ):

        candles.sort(
            key=lambda candle: candle["time"]
        )

    # ---------------------------------------------------------------
    # Remove duplicate timestamps.
    #
    # Keep the LAST occurrence because it is generally the most
    # complete representation if duplicated records exist.
    # ---------------------------------------------------------------

    if candles and all(
        "time" in candle
        for candle in candles
    ):

        deduplicated: Dict[int, Dict[str, Any]] = {}

        for candle in candles:

            deduplicated[
                int(candle["time"])
            ] = candle

        candles = [
            deduplicated[timestamp]
            for timestamp in sorted(
                deduplicated
            )
        ]

    return candles


# =====================================================================
# CANDLE VALIDATION
# =====================================================================

def validate_candles(
    candles: Sequence[Dict[str, Any]],
    minimum: int = MIN_CANDLE_COUNT,
) -> bool:
    """
    Validate standardized candles.

    Returns True when valid and minimum length is satisfied.
    """

    if isinstance(candles, (str, bytes)):
        raise TypeError(
            "candles must be a sequence"
        )

    if not isinstance(candles, Sequence):
        raise TypeError(
            "candles must be a sequence"
        )

    if not isinstance(minimum, int):
        raise TypeError(
            "minimum must be an integer"
        )

    if minimum < 0:
        raise ValueError(
            "minimum cannot be negative"
        )

    if len(candles) < minimum:
        return False

    previous_time: Optional[int] = None

    for index, candle in enumerate(candles):

        if not isinstance(candle, dict):

            raise ValueError(
                f"candle {index} must be a dictionary"
            )

        # -----------------------------------------------------------
        # Required OHLC
        # -----------------------------------------------------------

        for field in REQUIRED_CANDLE_FIELDS:

            if field not in candle:

                raise ValueError(
                    f"candle {index} missing field: {field}"
                )

            if not _is_finite_number(
                candle[field]
            ):

                raise ValueError(
                    f"candle {index} has invalid {field}"
                )

        open_price = float(
            candle["open"]
        )

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        close = float(
            candle["close"]
        )

        # -----------------------------------------------------------
        # OHLC relationship
        # -----------------------------------------------------------

        if high < low:

            raise ValueError(
                f"candle {index} has high below low"
            )

        if high < open_price or high < close:

            raise ValueError(
                f"candle {index} has invalid high"
            )

        if low > open_price or low > close:

            raise ValueError(
                f"candle {index} has invalid low"
            )

        # -----------------------------------------------------------
        # Timestamp
        # -----------------------------------------------------------

        if "time" in candle:

            timestamp = _safe_int(
                candle["time"]
            )

            if timestamp is None:

                raise ValueError(
                    f"candle {index} has invalid time"
                )

            if (
                previous_time is not None
                and timestamp < previous_time
            ):

                raise ValueError(
                    "candles must be ordered "
                    "oldest to newest"
                )

            if (
                previous_time is not None
                and timestamp == previous_time
            ):

                raise ValueError(
                    "candles contain duplicate timestamps"
                )

            previous_time = timestamp

        # -----------------------------------------------------------
        # Volume
        # -----------------------------------------------------------

        if "volume" in candle:

            volume = _safe_float(
                candle["volume"]
            )

            if volume is None:

                raise ValueError(
                    f"candle {index} has invalid volume"
                )

            if volume < 0:

                raise ValueError(
                    f"candle {index} has negative volume"
                )

    return True


# =====================================================================
# MT5 RATE RETRIEVAL
# =====================================================================

def get_rates(
    market: str,
    timeframe: str,
    count: int = DEFAULT_CANDLE_COUNT,
    symbol: Optional[str] = None,
    start_pos: int = 0,
) -> List[Dict[str, Any]]:
    """
    Retrieve standardized candles from MT5.

    Parameters
    ----------
    market:
        Logical BALLY FLOW market.

    timeframe:
        MT5 timeframe.

    count:
        Number of candles.

    symbol:
        Optional explicit broker symbol.

    start_pos:
        MT5 starting position.

    Returns
    -------
    list
        Standardized candles ordered oldest -> newest.
    """

    if mt5 is None:

        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    logical_market = normalize_market(
        market
    )

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    candle_count = _validate_count(
        count
    )

    if isinstance(start_pos, bool):
        raise TypeError(
            "start_pos must be an integer"
        )

    if not isinstance(start_pos, int):
        raise TypeError(
            "start_pos must be an integer"
        )

    if start_pos < 0:

        raise ValueError(
            "start_pos cannot be negative"
        )

    initialize_mt5()

    actual_symbol = select_symbol(
        market=logical_market,
        symbol=symbol,
    )

    timeframe_constant = mt5_timeframe(
        normalized_timeframe
    )

    # ---------------------------------------------------------------
    # MT5 retrieval
    # ---------------------------------------------------------------

    try:

        rates = mt5.copy_rates_from_pos(
            actual_symbol,
            timeframe_constant,
            start_pos,
            candle_count,
        )

    except Exception as exc:

        raise RuntimeError(
            f"MT5 candle retrieval failed for "
            f"{actual_symbol} "
            f"{normalized_timeframe}: {exc}"
        ) from exc

    if rates is None:

        error = mt5.last_error()

        raise RuntimeError(
            f"failed to retrieve candles for "
            f"{actual_symbol} "
            f"{normalized_timeframe}: {error}"
        )

    candles = normalize_rates(
        rates
    )

    if not candles:

        error = mt5.last_error()

        raise RuntimeError(
            f"no candle data returned for "
            f"{actual_symbol} "
            f"{normalized_timeframe}: {error}"
        )

    validate_candles(
        candles,
        minimum=1,
    )

    return candles


# =====================================================================
# TOP-DOWN DATA
# =====================================================================

def get_top_down_data(
    market: str,
    count: Optional[int] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve authoritative BALLY FLOW top-down market data.

    Analysis hierarchy:

        H4 -> H1 -> M15

    If count is supplied, the same count is used for all
    timeframes.

    If count is None, BALLY FLOW uses its optimized historical
    depth:

        H4  -> 300 candles
        H1  -> 500 candles
        M15 -> 1000 candles

    This function performs market-data acquisition only.
    It does not perform technical analysis or trading decisions.
    """

    logical_market = normalize_market(market)

    if count is not None:
        candle_count = _validate_count(count)
    else:
        candle_count = None

    actual_symbol: Optional[str] = None

    initialize_mt5()

    actual_symbol = select_symbol(
        market=logical_market,
        symbol=symbol,
    )

    result: Dict[str, Any] = {
        "status": "READY",
        "market": logical_market,
        "broker_symbol": actual_symbol,
        "symbol": actual_symbol,
        "analysis_order": [
            "H4",
            "H1",
            "M15",
        ],
        "timeframes": {},
    }

    failures: Dict[str, str] = {}

    for timeframe in TOP_DOWN_TIMEFRAMES:

        requested_count = (
            candle_count
            if candle_count is not None
            else top_down_candle_count(timeframe)
        )

        try:

            candles = get_rates(
                market=logical_market,
                timeframe=timeframe,
                count=requested_count,
                symbol=actual_symbol,
            )

            closed_candle = latest_closed_candle(
                candles,
                timeframe,
            )

            result["timeframes"][timeframe] = {
                "status": "READY",
                "timeframe": timeframe,
                "requested_candle_count": requested_count,
                "candle_count": len(candles),
                "candles": candles,
                "latest_closed_candle": closed_candle,
                "latest_candle_time": (
                    candles[-1].get("time")
                    if candles
                    else None
                ),
                "latest_closed_candle_time": (
                    closed_candle.get("time")
                    if closed_candle
                    else None
                ),
            }

        except Exception as exc:

            failures[timeframe] = str(exc)

            result["timeframes"][timeframe] = {
                "status": "ERROR",
                "timeframe": timeframe,
                "requested_candle_count": requested_count,
                "candle_count": 0,
                "candles": [],
                "latest_closed_candle": None,
                "latest_candle_time": None,
                "latest_closed_candle_time": None,
                "error": str(exc),
            }

    successful = sum(
        1
        for timeframe in TOP_DOWN_TIMEFRAMES
        if result["timeframes"][timeframe]["status"] == "READY"
    )

    if successful == len(TOP_DOWN_TIMEFRAMES):
        result["status"] = "READY"

    elif successful > 0:
        result["status"] = "PARTIAL"

    else:
        result["status"] = "ERROR"

    result["successful_timeframe_count"] = successful
    result["timeframe_count"] = len(TOP_DOWN_TIMEFRAMES)

    if failures:
        result["errors"] = failures

    return result

def get_market_snapshot(
    market: str,
    count: Optional[int] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return the BALLY FLOW H4/H1/M15 market snapshot.
    """

    return get_top_down_data(
        market=market,
        count=count,
        symbol=symbol,
    )
# =====================================================================
# ALL MARKETS
# =====================================================================
def get_all_markets_data(
    count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieve H4/H1/M15 data for every BALLY FLOW market.

    By default, each timeframe uses its own optimized history:

        H4  -> 300
        H1  -> 500
        M15 -> 1000

    If count is supplied, that count is used for every timeframe.
    """

    if count is not None:
        candle_count = _validate_count(count)
    else:
        candle_count = None

    results: Dict[str, Any] = {}

    for market in MARKETS:

        try:

            results[market] = get_top_down_data(
                market=market,
                count=candle_count,
            )

        except Exception as exc:

            results[market] = {
                "status": "ERROR",
                "market": market,
                "broker_symbol": None,
                "symbol": None,
                "analysis_order": list(
                    TOP_DOWN_TIMEFRAMES
                ),
                "timeframes": {},
                "error": str(exc),
            }

    successful = sum(
        1
        for value in results.values()
        if value.get("status") == "READY"
    )

    return {
        "status": (
            "READY"
            if successful == len(MARKETS)
            else "PARTIAL"
            if successful > 0
            else "ERROR"
        ),
        "market_count": len(MARKETS),
        "successful_market_count": successful,
        "candle_policy": (
            "per_timeframe"
            if candle_count is None
            else "uniform"
        ),
        "markets": results,
    }


# =====================================================================
# LATEST CLOSED CANDLE
# =====================================================================

def latest_closed_candle(
    candles: Sequence[Dict[str, Any]],
    timeframe: str,
    now: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return latest fully closed candle.

    MT5 candle timestamps represent candle opening time.

    A candle is considered closed when:

        candle_open_time + timeframe_seconds <= now

    If a candle has no timestamp, it cannot be proven closed.
    """

    if not candles:
        return None

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    current_time = (
        int(now)
        if now is not None
        else int(time_module.time())
    )

    duration = timeframe_seconds(
        normalized_timeframe
    )

    # Ensure chronological order without mutating caller data.
    ordered = list(candles)

    ordered_with_time = [
        candle
        for candle in ordered
        if isinstance(candle, dict)
        and candle.get("time") is not None
    ]

    if ordered_with_time:

        ordered_with_time.sort(
            key=lambda candle: int(
                candle["time"]
            )
        )

    candidates: List[
        Dict[str, Any]
    ] = []

    for candle in ordered_with_time:

        timestamp = _safe_int(
            candle.get("time")
        )

        if timestamp is None:
            continue

        if timestamp + duration <= current_time:

            candidates.append(candle)

    if not candidates:
        return None

    return candidates[-1]


# =====================================================================
# CANDLE AGE
# =====================================================================

def candle_age_seconds(
    candle: Dict[str, Any],
    now: Optional[int] = None,
) -> Optional[int]:
    """
    Return candle age in seconds.
    """

    if not isinstance(candle, dict):

        raise TypeError(
            "candle must be a dictionary"
        )

    timestamp = candle.get(
        "time"
    )

    if timestamp is None:
        return None

    timestamp_int = _safe_int(
        timestamp
    )

    if timestamp_int is None:
        return None

    current_time = (
        int(now)
        if now is not None
        else int(time_module.time())
    )

    return max(
        0,
        current_time - timestamp_int,
    )


# =====================================================================
# MARKET DATA FRESHNESS
# =====================================================================

def is_candle_closed(
    candle: Dict[str, Any],
    timeframe: str,
    now: Optional[int] = None,
) -> bool:
    """
    Return True when a candle has fully closed.
    """

    if not isinstance(candle, dict):

        raise TypeError(
            "candle must be a dictionary"
        )

    timestamp = _safe_int(
        candle.get("time")
    )

    if timestamp is None:
        return False

    current_time = (
        int(now)
        if now is not None
        else int(time_module.time())
    )

    duration = timeframe_seconds(
        timeframe
    )

    return (
        timestamp + duration
        <= current_time
    )


def data_is_fresh(
    candles: Sequence[Dict[str, Any]],
    timeframe: str,
    max_age_multiplier: float = 2.0,
    now: Optional[int] = None,
) -> bool:
    """
    Determine whether the latest candle is reasonably fresh.

    max_age_multiplier defines the allowed candle age relative to
    timeframe duration.

    Example:

        H1 with multiplier 2.0
        -> latest candle should not be older than ~2 hours.
    """

    if not candles:
        return False

    if not _is_finite_number(
        max_age_multiplier
    ):

        raise ValueError(
            "max_age_multiplier must be numeric"
        )

    multiplier = float(
        max_age_multiplier
    )

    if multiplier <= 0:
        raise ValueError(
            "max_age_multiplier must be greater than zero"
        )

    latest = candles[-1]

    age = candle_age_seconds(
        latest,
        now=now,
    )

    if age is None:
        return False

    allowed_age = (
        timeframe_seconds(timeframe)
        * multiplier
    )

    return age <= allowed_age


# =====================================================================
# MARKET LIST
# =====================================================================

def supported_markets() -> Tuple[str, ...]:
    """
    Return immutable agreed market list.
    """

    return MARKETS


def supported_timeframes() -> Tuple[str, ...]:
    """
    Return supported top-down timeframes.
    """

    return TOP_DOWN_TIMEFRAMES


# =====================================================================
# CONVENIENCE MARKET DATA API
# =====================================================================

def get_market_data(
    market: str,
    timeframe: str,
    count: int = DEFAULT_CANDLE_COUNT,
) -> Dict[str, Any]:
    """
    Convenience API for one market/timeframe.
    """

    logical_market = normalize_market(
        market
    )

    normalized_timeframe = normalize_timeframe(
        timeframe
    )

    candles = get_rates(
        market=logical_market,
        timeframe=normalized_timeframe,
        count=count,
    )

    latest = (
        candles[-1]
        if candles
        else None
    )

    closed = latest_closed_candle(
        candles,
        normalized_timeframe,
    )

    return {
        "status": "READY",
        "market": logical_market,
        "symbol": resolve_symbol(
            logical_market
        ),
        "timeframe": normalized_timeframe,
        "candle_count": len(candles),
        "candles": candles,
        "latest_candle": latest,
        "latest_closed_candle": closed,
    }


# =====================================================================
# TOP-DOWN VALIDATION
# =====================================================================

def validate_top_down_data(
    data: Dict[str, Any],
    minimum: int = MIN_CANDLE_COUNT,
) -> bool:
    """
    Validate a top-down market snapshot.

    Requires H4, H1 and M15 to contain valid candle collections.
    """

    if not isinstance(data, dict):

        raise TypeError(
            "data must be a dictionary"
        )

    if data.get("market") is None:

        raise ValueError(
            "top-down data is missing market"
        )

    normalize_market(
        data["market"]
    )

    timeframes = data.get(
        "timeframes"
    )

    if not isinstance(
        timeframes,
        dict,
    ):

        raise ValueError(
            "top-down data is missing timeframes"
        )

    for timeframe in TOP_DOWN_TIMEFRAMES:

        timeframe_data = timeframes.get(
            timeframe
        )

        if not isinstance(
            timeframe_data,
            dict,
        ):

            return False

        if timeframe_data.get(
            "status"
        ) != "READY":

            return False

        candles = timeframe_data.get(
            "candles"
        )

        if not isinstance(
            candles,
            Sequence,
        ):

            return False

        if not validate_candles(
            candles,
            minimum=minimum,
        ):

            return False

    return True


# =====================================================================
# BROKER SYMBOL SUMMARY
# =====================================================================

def get_symbol_info(
    market: str,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return broker-aware symbol metadata.

    This is informational only.

    It does not place or modify orders.
    """

    if mt5 is None:

        raise RuntimeError(
            "MetaTrader5 package is not installed"
        )

    logical_market = normalize_market(
        market
    )

    actual_symbol = select_symbol(
        market=logical_market,
        symbol=symbol,
    )

    info = mt5.symbol_info(
        actual_symbol
    )

    if info is None:

        error = mt5.last_error()

        raise RuntimeError(
            f"unable to retrieve symbol information "
            f"for {actual_symbol}: {error}"
        )

    return {
        "status": "READY",
        "market": logical_market,
        "broker_symbol": actual_symbol,
        "name": getattr(
            info,
            "name",
            actual_symbol,
        ),
        "description": getattr(
            info,
            "description",
            None,
        ),
        "currency_base": getattr(
            info,
            "currency_base",
            None,
        ),
        "currency_profit": getattr(
            info,
            "currency_profit",
            None,
        ),
        "digits": getattr(
            info,
            "digits",
            None,
        ),
        "point": getattr(
            info,
            "point",
            None,
        ),
        "trade_mode": getattr(
            info,
            "trade_mode",
            None,
        ),
        "visible": getattr(
            info,
            "visible",
            None,
        ),
        "volume_min": getattr(
            info,
            "volume_min",
            None,
        ),
        "volume_max": getattr(
            info,
            "volume_max",
            None,
        ),
        "volume_step": getattr(
            info,
            "volume_step",
            None,
        ),
    }


# =====================================================================
# MODULE EXPORTS
# =====================================================================

__all__ = [
    "MARKETS",
    "TIMEFRAMES",
    "TOP_DOWN_TIMEFRAMES",
    "DEFAULT_CANDLE_COUNT",
    "MIN_CANDLE_COUNT",
    "SYMBOL_ALIASES",
    "TIMEFRAME_SECONDS",
    "TIMEFRAME_MAP",

    "normalize_market",
    "normalize_timeframe",
    "timeframe_seconds",
    "mt5_timeframe",

    "symbol_aliases",
    "resolve_symbol",
    "discover_market_symbols",

    "mt5_available",
    "mt5_initialized",
    "initialize_mt5",
    "shutdown_mt5",

    "select_symbol",
    "get_symbol_info",

    "normalize_rate",
    "normalize_rates",
    "validate_candles",

    "get_rates",
    "get_top_down_data",
    "get_market_snapshot",
    "get_all_markets_data",
    "get_market_data",

    "latest_closed_candle",
    "candle_age_seconds",
    "is_candle_closed",
    "data_is_fresh",

    "validate_top_down_data",

    "supported_markets",
    "supported_timeframes",
]