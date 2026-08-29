"""
BALLY FLOW - MetaTrader 5 Connection & Broker Symbol Discovery

Production-oriented MT5 connection layer.

Responsibilities
----------------
- Initialize and verify the MT5 terminal.
- Maintain a shared MT5 connection.
- Discover broker-provided symbols dynamically.
- Resolve BALLY FLOW logical instruments to actual broker symbols.
- Validate symbol metadata before market-data use.
- Select symbols in Market Watch.
- Provide connection and symbol diagnostics.
- Cleanly shut down the MT5 connection.

Logical instruments
-------------------
    XAUUSD
    EURUSD
    GBPUSD
    USDJPY
    XAGUSD
    NASDAQ

IMPORTANT
---------
BALLY FLOW does NOT assume that a broker uses a particular symbol name.

Examples:
    XAUUSD -> XAUUSD
    XAUUSD -> XAUUSDm
    XAUUSD -> GOLD
    NASDAQ -> NAS100
    NASDAQ -> USTEC
    NASDAQ -> US100

The actual mapping is discovered from the connected MT5 terminal.

This module does NOT:
- generate trading signals
- perform technical analysis
- perform fundamental analysis
- calculate risk
- calculate position size
- place orders
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import MetaTrader5 as mt5


# ==================================================================
# LOGICAL MARKET DEFINITIONS
# ==================================================================

LOGICAL_MARKETS = (
    "XAUUSD",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAGUSD",
    "NASDAQ",
)


# ==================================================================
# SYMBOL MATCHING PROFILES
# ==================================================================

# These are NOT broker symbol names.
#
# They are semantic identifiers used to discover the correct
# instrument from the broker's available MT5 symbols.

SYMBOL_PROFILES: Dict[str, Dict[str, Any]] = {
    "XAUUSD": {
        "base": "XAU",
        "profit": "USD",
        "keywords": (
            "XAUUSD",
            "GOLD",
        ),
        "exclude": (
            "MINI",
            "MICRO",
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
        ),
    },
    "XAGUSD": {
        "base": "XAG",
        "profit": "USD",
        "keywords": (
            "XAGUSD",
            "SILVER",
        ),
        "exclude": (
            "MINI",
            "MICRO",
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
        ),
    },
    "EURUSD": {
        "base": "EUR",
        "profit": "USD",
        "keywords": (
            "EURUSD",
        ),
        "exclude": (
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
        ),
    },
    "GBPUSD": {
        "base": "GBP",
        "profit": "USD",
        "keywords": (
            "GBPUSD",
        ),
        "exclude": (
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
        ),
    },
    "USDJPY": {
        "base": "USD",
        "profit": "JPY",
        "keywords": (
            "USDJPY",
        ),
        "exclude": (
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
        ),
    },
    "NASDAQ": {
        "base": None,
        "profit": None,
        "keywords": (
            "NASDAQ",
            "NAS100",
            "USTEC",
            "US100",
            "US TECH",
            "USTECH",
        ),
        "exclude": (
            "FUT",
            "FUTURE",
            "OPTION",
            "CALL",
            "PUT",
            "MINI",
            "MICRO",
        ),
    },
}


# ==================================================================
# DATA CLASS
# ==================================================================

@dataclass
class BrokerSymbol:
    """
    Standardized broker-symbol metadata.

    This is deliberately independent of MT5's raw namedtuple.
    """

    logical_symbol: str
    broker_symbol: str

    visible: bool
    selected: bool

    trade_mode: Optional[int]
    digits: Optional[int]
    point: Optional[float]

    trade_tick_size: Optional[float]
    trade_tick_value: Optional[float]

    volume_min: Optional[float]
    volume_max: Optional[float]
    volume_step: Optional[float]

    bid: Optional[float]
    ask: Optional[float]
    spread: Optional[int]

    currency_base: Optional[str]
    currency_profit: Optional[str]
    currency_margin: Optional[str]

    description: Optional[str]
    path: Optional[str]

    match_score: float


# ==================================================================
# MAIN CONNECTION CLASS
# ==================================================================

class MT5Connection:
    """
    Central MT5 connection and broker-symbol discovery manager.
    """

    def __init__(
        self,
        logical_markets: Sequence[str] = LOGICAL_MARKETS,
    ) -> None:

        self.logical_markets = tuple(
            self._clean_logical_symbol(symbol)
            for symbol in logical_markets
        )

        self.initialized = False

        # Logical -> broker symbol cache.
        self._symbol_cache: Dict[str, str] = {}

        # Logical -> diagnostic metadata.
        self._metadata_cache: Dict[
            str,
            BrokerSymbol,
        ] = {}

    # ==============================================================
    # NORMALIZATION
    # ==============================================================

    @staticmethod
    def _clean_logical_symbol(
        symbol: str,
    ) -> str:

        if not isinstance(symbol, str):
            raise TypeError(
                "symbol must be a string"
            )

        cleaned = symbol.strip().upper()

        if not cleaned:
            raise ValueError(
                "symbol cannot be empty"
            )

        return cleaned

    @staticmethod
    def _normalize_name(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        text = str(value).upper().strip()

        # Remove separators commonly used by brokers.
        text = re.sub(
            r"[\s._:/\\\-]+",
            "",
            text,
        )

        return text

    # ==============================================================
    # INITIALIZATION
    # ==============================================================

    def initialize(
        self,
        *,
        path: Optional[str] = None,
        login: Optional[int] = None,
        password: Optional[str] = None,
        server: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """
        Initialize the MT5 terminal connection.

        When no parameters are supplied, the currently logged-in
        MT5 terminal is used.
        """

        kwargs: Dict[str, Any] = {}

        if path is not None:
            kwargs["path"] = path

        if login is not None:
            kwargs["login"] = int(login)

        if password is not None:
            kwargs["password"] = password

        if server is not None:
            kwargs["server"] = server

        if timeout is not None:
            kwargs["timeout"] = int(timeout)

        try:

            if kwargs:
                result = mt5.initialize(**kwargs)
            else:
                result = mt5.initialize()

        except Exception:

            self.initialized = False

            return False

        self.initialized = bool(result)

        if not self.initialized:
            return False

        # Clear stale mappings after every fresh initialization.
        self._symbol_cache.clear()
        self._metadata_cache.clear()

        return self.is_connected()

    # ==============================================================
    # CONNECTION STATUS
    # ==============================================================

    def is_connected(self) -> bool:

        if not self.initialized:
            return False

        try:
            terminal = mt5.terminal_info()
        except Exception:
            return False

        return terminal is not None

    def status(self) -> Dict[str, Any]:

        terminal = None
        account = None

        if self.is_connected():

            try:
                terminal = mt5.terminal_info()
            except Exception:
                terminal = None

            try:
                account = mt5.account_info()
            except Exception:
                account = None

        return {
            "initialized": self.initialized,
            "connected": terminal is not None,
            "last_error": mt5.last_error(),
            "terminal": terminal,
            "account": account,
            "cached_symbols": dict(
                self._symbol_cache
            ),
        }

    def terminal_info(self) -> Any:

        if not self.is_connected():
            raise RuntimeError(
                "MT5 terminal is not connected"
            )

        return mt5.terminal_info()

    def account_info(self) -> Any:

        if not self.is_connected():
            raise RuntimeError(
                "MT5 terminal is not connected"
            )

        return mt5.account_info()

    # ==============================================================
    # MT5 SYMBOL COLLECTION
    # ==============================================================

    def _get_all_symbols(self) -> List[Any]:

        if not self.is_connected():
            raise RuntimeError(
                "MT5 terminal is not connected"
            )

        try:
            symbols = mt5.symbols_get()
        except Exception as exc:
            raise RuntimeError(
                "Unable to retrieve MT5 symbol list"
            ) from exc

        if symbols is None:
            return []

        return list(symbols)

    # ==============================================================
    # SYMBOL METADATA HELPERS
    # ==============================================================

    @staticmethod
    def _get_attr(
        info: Any,
        name: str,
        default: Any = None,
    ) -> Any:

        try:
            return getattr(
                info,
                name,
                default,
            )
        except Exception:
            return default

    @classmethod
    def _to_optional_float(
        cls,
        value: Any,
    ) -> Optional[float]:

        if value is None:
            return None

        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    @classmethod
    def _to_optional_int(
        cls,
        value: Any,
    ) -> Optional[int]:

        if value is None:
            return None

        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

    # ==============================================================
    # CURRENCY / SEMANTIC MATCHING
    # ==============================================================

    def _currency_match_score(
        self,
        logical_symbol: str,
        info: Any,
    ) -> float:

        profile = SYMBOL_PROFILES.get(
            logical_symbol
        )

        if profile is None:
            return 0.0

        score = 0.0

        base = self._normalize_name(
            self._get_attr(
                info,
                "currency_base",
            )
        )

        profit = self._normalize_name(
            self._get_attr(
                info,
                "currency_profit",
            )
        )

        margin = self._normalize_name(
            self._get_attr(
                info,
                "currency_margin",
            )
        )

        expected_base = self._normalize_name(
            profile.get("base")
        )

        expected_profit = self._normalize_name(
            profile.get("profit")
        )

        if expected_base:

            if base == expected_base:
                score += 25.0

        if expected_profit:

            if profit == expected_profit:
                score += 25.0

        # Margin currency can provide supporting evidence.
        if expected_profit:

            if margin == expected_profit:
                score += 5.0

        return score

    def _name_match_score(
        self,
        logical_symbol: str,
        broker_name: str,
    ) -> float:

        profile = SYMBOL_PROFILES.get(
            logical_symbol
        )

        if profile is None:
            return 0.0

        normalized_name = self._normalize_name(
            broker_name
        )

        if not normalized_name:
            return 0.0

        for excluded in profile.get(
            "exclude",
            (),
        ):

            excluded_normalized = (
                self._normalize_name(excluded)
            )

            if (
                excluded_normalized
                and excluded_normalized in normalized_name
            ):
                return -1000.0

        score = 0.0

        for keyword in profile.get(
            "keywords",
            (),
        ):

            normalized_keyword = (
                self._normalize_name(keyword)
            )

            if not normalized_keyword:
                continue

            if normalized_name == normalized_keyword:

                score = max(
                    score,
                    100.0,
                )

            elif normalized_name.startswith(
                normalized_keyword
            ):

                score = max(
                    score,
                    85.0,
                )

            elif normalized_keyword in normalized_name:

                score = max(
                    score,
                    70.0,
                )

        return score

    # ==============================================================
    # SYMBOL QUALITY SCORE
    # ==============================================================

    def _score_symbol(
        self,
        logical_symbol: str,
        info: Any,
    ) -> float:

        broker_name = self._get_attr(
            info,
            "name",
            "",
        )

        score = self._name_match_score(
            logical_symbol,
            broker_name,
        )

        if score < 0:
            return score

        score += self._currency_match_score(
            logical_symbol,
            info,
        )

        visible = bool(
            self._get_attr(
                info,
                "visible",
                False,
            )
        )

        if visible:
            score += 10.0

        # Symbols with usable market prices are preferred.
        bid = self._to_optional_float(
            self._get_attr(
                info,
                "bid",
            )
        )

        ask = self._to_optional_float(
            self._get_attr(
                info,
                "ask",
            )
        )

        if (
            bid is not None
            and bid > 0
        ):
            score += 5.0

        if (
            ask is not None
            and ask > 0
        ):
            score += 5.0

        # A valid point value is useful evidence that this is a
        # normal tradable/quotable instrument.
        point = self._to_optional_float(
            self._get_attr(
                info,
                "point",
            )
        )

        if (
            point is not None
            and point > 0
        ):
            score += 5.0

        return score

    # ==============================================================
    # SYMBOL VALIDATION
    # ==============================================================

    def _validate_symbol_info(
        self,
        logical_symbol: str,
        info: Any,
    ) -> Tuple[bool, List[str]]:

        errors: List[str] = []

        if info is None:
            errors.append(
                "symbol_info is unavailable"
            )
            return False, errors

        name = self._get_attr(
            info,
            "name",
        )

        if not name:
            errors.append(
                "broker symbol has no name"
            )

        point = self._to_optional_float(
            self._get_attr(
                info,
                "point",
            )
        )

        if point is None or point <= 0:
            errors.append(
                "invalid symbol point"
            )

        digits = self._to_optional_int(
            self._get_attr(
                info,
                "digits",
            )
        )

        if digits is None or digits < 0:
            errors.append(
                "invalid symbol digits"
            )

        volume_min = self._to_optional_float(
            self._get_attr(
                info,
                "volume_min",
            )
        )

        volume_max = self._to_optional_float(
            self._get_attr(
                info,
                "volume_max",
            )
        )

        volume_step = self._to_optional_float(
            self._get_attr(
                info,
                "volume_step",
            )
        )

        if (
            volume_min is not None
            and volume_min <= 0
        ):
            errors.append(
                "invalid volume_min"
            )

        if (
            volume_max is not None
            and volume_max <= 0
        ):
            errors.append(
                "invalid volume_max"
            )

        if (
            volume_step is not None
            and volume_step <= 0
        ):
            errors.append(
                "invalid volume_step"
            )

        if (
            volume_min is not None
            and volume_max is not None
            and volume_max < volume_min
        ):
            errors.append(
                "volume_max is below volume_min"
            )

        # Logical market must be known to BALLY FLOW.
        if logical_symbol not in SYMBOL_PROFILES:
            errors.append(
                "unsupported logical market"
            )

        return (
            len(errors) == 0,
            errors,
        )

    # ==============================================================
    # BROKER SYMBOL METADATA
    # ==============================================================

    def _build_metadata(
        self,
        logical_symbol: str,
        info: Any,
        score: float,
    ) -> BrokerSymbol:

        return BrokerSymbol(
            logical_symbol=logical_symbol,
            broker_symbol=str(
                self._get_attr(
                    info,
                    "name",
                    "",
                )
            ),

            visible=bool(
                self._get_attr(
                    info,
                    "visible",
                    False,
                )
            ),

            selected=bool(
                self._get_attr(
                    info,
                    "select",
                    False,
                )
            ),

            trade_mode=self._to_optional_int(
                self._get_attr(
                    info,
                    "trade_mode",
                )
            ),

            digits=self._to_optional_int(
                self._get_attr(
                    info,
                    "digits",
                )
            ),

            point=self._to_optional_float(
                self._get_attr(
                    info,
                    "point",
                )
            ),

            trade_tick_size=(
                self._to_optional_float(
                    self._get_attr(
                        info,
                        "trade_tick_size",
                    )
                )
            ),

            trade_tick_value=(
                self._to_optional_float(
                    self._get_attr(
                        info,
                        "trade_tick_value",
                    )
                )
            ),

            volume_min=self._to_optional_float(
                self._get_attr(
                    info,
                    "volume_min",
                )
            ),

            volume_max=self._to_optional_float(
                self._get_attr(
                    info,
                    "volume_max",
                )
            ),

            volume_step=self._to_optional_float(
                self._get_attr(
                    info,
                    "volume_step",
                )
            ),

            bid=self._to_optional_float(
                self._get_attr(
                    info,
                    "bid",
                )
            ),

            ask=self._to_optional_float(
                self._get_attr(
                    info,
                    "ask",
                )
            ),

            spread=self._to_optional_int(
                self._get_attr(
                    info,
                    "spread",
                )
            ),

            currency_base=self._get_attr(
                info,
                "currency_base",
            ),

            currency_profit=self._get_attr(
                info,
                "currency_profit",
            ),

            currency_margin=self._get_attr(
                info,
                "currency_margin",
            ),

            description=self._get_attr(
                info,
                "description",
            ),

            path=self._get_attr(
                info,
                "path",
            ),

            match_score=round(
                float(score),
                2,
            ),
        )

    # ==============================================================
    # DISCOVERY
    # ==============================================================

    def discover_symbols(
        self,
        logical_symbol: Optional[str] = None,
        *,
        minimum_score: float = 60.0,
    ) -> Dict[str, Any]:

        if not self.is_connected():
            raise RuntimeError(
                "MT5 terminal is not connected"
            )

        if logical_symbol is not None:

            logical_symbol = (
                self._clean_logical_symbol(
                    logical_symbol
                )
            )

            requested = (
                logical_symbol,
            )

        else:
            requested = self.logical_markets

        all_symbols = self._get_all_symbols()

        results: Dict[str, Any] = {}

        for logical in requested:

            candidates: List[
                Tuple[float, Any]
            ] = []

            for info in all_symbols:

                score = self._score_symbol(
                    logical,
                    info,
                )

                if score < minimum_score:
                    continue

                candidates.append(
                    (
                        score,
                        info,
                    )
                )

            candidates.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            candidate_metadata = []

            for score, info in candidates[:10]:

                candidate_metadata.append(
                    self._build_metadata(
                        logical,
                        info,
                        score,
                    )
                )

            results[logical] = candidate_metadata

        return results

    # ==============================================================
    # RESOLVE
    # ==============================================================

    def resolve_symbol(
        self,
        symbol: str,
        *,
        minimum_score: float = 60.0,
        refresh: bool = False,
    ) -> Optional[str]:

        logical = self._clean_logical_symbol(
            symbol
        )

        if (
            not refresh
            and logical in self._symbol_cache
        ):

            cached = self._symbol_cache[
                logical
            ]

            info = mt5.symbol_info(
                cached
            )

            if info is not None:

                valid, _ = (
                    self._validate_symbol_info(
                        logical,
                        info,
                    )
                )

                if valid:
                    return cached

            self._symbol_cache.pop(
                logical,
                None,
            )

            self._metadata_cache.pop(
                logical,
                None,
            )

        discovered = self.discover_symbols(
            logical_symbol=logical,
            minimum_score=minimum_score,
        )

        candidates = discovered.get(
            logical,
            [],
        )

        if not candidates:
            return None

        best = candidates[0]

        broker_symbol = (
            best.broker_symbol
        )

        try:
            selected = mt5.symbol_select(
                broker_symbol,
                True,
            )
        except Exception:
            selected = False

        if not selected:
            # Selecting the symbol is required for reliable
            # downstream market-data access.
            return None

        info = mt5.symbol_info(
            broker_symbol
        )

        valid, errors = (
            self._validate_symbol_info(
                logical,
                info,
            )
        )

        if not valid:
            raise RuntimeError(
                f"Resolved MT5 symbol failed validation "
                f"for {logical}: {errors}"
            )

        metadata = self._build_metadata(
            logical,
            info,
            best.match_score,
        )

        self._symbol_cache[
            logical
        ] = broker_symbol

        self._metadata_cache[
            logical
        ] = metadata

        return broker_symbol

    # ==============================================================
    # ENSURE SYMBOL
    # ==============================================================

    def ensure_symbol(
        self,
        symbol: str,
    ) -> str:

        logical = self._clean_logical_symbol(
            symbol
        )

        actual = self.resolve_symbol(
            logical
        )

        if actual is None:

            raise ValueError(
                f"Unable to resolve broker symbol "
                f"for logical market: {logical}"
            )

        try:
            selected = mt5.symbol_select(
                actual,
                True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Unable to select broker symbol: "
                f"{actual}"
            ) from exc

        if not selected:
            raise RuntimeError(
                f"MT5 rejected symbol selection: "
                f"{actual}"
            )

        return actual

    # ==============================================================
    # SYMBOL INFO
    # ==============================================================

    def symbol_info(
        self,
        symbol: str,
    ) -> Any:

        actual = self.ensure_symbol(
            symbol
        )

        info = mt5.symbol_info(
            actual
        )

        if info is None:
            raise RuntimeError(
                f"Unable to retrieve symbol information: "
                f"{actual}"
            )

        return info

    def broker_symbol_metadata(
        self,
        symbol: str,
        *,
        refresh: bool = False,
    ) -> BrokerSymbol:

        logical = self._clean_logical_symbol(
            symbol
        )

        actual = self.resolve_symbol(
            logical,
            refresh=refresh,
        )

        if actual is None:
            raise ValueError(
                f"Unable to resolve broker symbol "
                f"for {logical}"
            )

        metadata = self._metadata_cache.get(
            logical
        )

        if metadata is not None:
            return metadata

        info = mt5.symbol_info(
            actual
        )

        if info is None:
            raise RuntimeError(
                f"Unable to retrieve symbol information: "
                f"{actual}"
            )

        metadata = self._build_metadata(
            logical,
            info,
            self._score_symbol(
                logical,
                info,
            ),
        )

        self._metadata_cache[
            logical
        ] = metadata

        return metadata

    # ==============================================================
    # TICK
    # ==============================================================

    def symbol_tick(
        self,
        symbol: str,
    ) -> Any:

        actual = self.ensure_symbol(
            symbol
        )

        tick = mt5.symbol_info_tick(
            actual
        )

        if tick is None:
            raise RuntimeError(
                f"No current tick available for "
                f"broker symbol: {actual}"
            )

        return tick

    # ==============================================================
    # DISCOVER ALL AGREED MARKETS
    # ==============================================================

    def discover_all_markets(
        self,
    ) -> Dict[str, Any]:

        result: Dict[str, Any] = {}

        for logical in self.logical_markets:

            try:

                actual = self.resolve_symbol(
                    logical,
                    refresh=True,
                )

                metadata = (
                    self.broker_symbol_metadata(
                        logical
                    )
                    if actual is not None
                    else None
                )

                result[logical] = {
                    "status": (
                        "READY"
                        if actual is not None
                        else "NOT_FOUND"
                    ),
                    "logical_symbol": logical,
                    "broker_symbol": actual,
                    "metadata": (
                        asdict(metadata)
                        if metadata is not None
                        else None
                    ),
                }

            except Exception as exc:

                result[logical] = {
                    "status": "ERROR",
                    "logical_symbol": logical,
                    "broker_symbol": None,
                    "metadata": None,
                    "error": str(exc),
                }

        return result

    # ==============================================================
    # LAST ERROR
    # ==============================================================

    @staticmethod
    def last_error() -> Any:
        return mt5.last_error()

    # ==============================================================
    # SHUTDOWN
    # ==============================================================

    def shutdown(self) -> None:

        try:
            mt5.shutdown()
        finally:

            self.initialized = False

            self._symbol_cache.clear()
            self._metadata_cache.clear()


# ==================================================================
# SHARED CONNECTION
# ==================================================================

_connection = MT5Connection()


# ==================================================================
# MODULE-LEVEL API
# ==================================================================

def initialize_mt5(
    *,
    path: Optional[str] = None,
    login: Optional[int] = None,
    password: Optional[str] = None,
    server: Optional[str] = None,
    timeout: Optional[int] = None,
) -> bool:

    return _connection.initialize(
        path=path,
        login=login,
        password=password,
        server=server,
        timeout=timeout,
    )


def is_mt5_connected() -> bool:
    return _connection.is_connected()


def mt5_status() -> Dict[str, Any]:
    return _connection.status()


def resolve_symbol(
    symbol: str,
    *,
    minimum_score: float = 60.0,
    refresh: bool = False,
) -> Optional[str]:

    return _connection.resolve_symbol(
        symbol,
        minimum_score=minimum_score,
        refresh=refresh,
    )


def ensure_symbol(
    symbol: str,
) -> str:

    return _connection.ensure_symbol(
        symbol
    )


def get_symbol_info(
    symbol: str,
) -> Any:

    return _connection.symbol_info(
        symbol
    )


def get_symbol_tick(
    symbol: str,
) -> Any:

    return _connection.symbol_tick(
        symbol
    )


def get_broker_symbol_metadata(
    symbol: str,
    *,
    refresh: bool = False,
) -> BrokerSymbol:

    return _connection.broker_symbol_metadata(
        symbol,
        refresh=refresh,
    )


def discover_market_symbols() -> Dict[str, Any]:

    return _connection.discover_all_markets()


def shutdown_mt5() -> None:

    _connection.shutdown()


__all__ = [
    "LOGICAL_MARKETS",
    "SYMBOL_PROFILES",
    "BrokerSymbol",
    "MT5Connection",
    "initialize_mt5",
    "is_mt5_connected",
    "mt5_status",
    "resolve_symbol",
    "ensure_symbol",
    "get_symbol_info",
    "get_symbol_tick",
    "get_broker_symbol_metadata",
    "discover_market_symbols",
    "shutdown_mt5",
]