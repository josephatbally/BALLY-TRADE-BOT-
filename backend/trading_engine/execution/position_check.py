
"""
BALLY FLOW - Position Check

Execution-safety layer responsible for determining whether an existing
position conflicts with a proposed trade.

RESPONSIBILITIES
----------------
This module:

    - checks existing MT5 positions for a symbol
    - identifies BUY / SELL exposure
    - detects same-direction and opposite-direction positions
    - supports the execution pipeline
    - provides a standardized position-check result

This module MUST NOT:

    - generate BUY / SELL signals
    - perform technical analysis
    - perform fundamental analysis
    - perform hybrid analysis
    - calculate position size
    - modify account risk settings
    - place MT5 orders
    - call mt5.order_send()
    - override the upstream Decision Engine

POSITION CHECK FLOW
-------------------

    Upstream Decision
           |
           v
    Proposed Trade
           |
           v
    Position Check
       /        \
      /          \
 Existing       No Existing
 Position       Position
    |               |
    v               v
 Conflict?       ALLOW
    |
    +--> YES -> REJECT
    |
    +--> NO  -> ALLOW

The final gate remains responsible for the complete execution
authorization decision.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


BUY = "BUY"
SELL = "SELL"
NO_TRADE = "NO_TRADE"

SUPPORTED_SIGNALS = (BUY, SELL, NO_TRADE)


class PositionCheck:
    """
    Broker-position inspection layer.

    The class is intentionally independent from signal generation and
    order placement.
    """

    NAME = "BALLY FLOW Position Check"
    VERSION = "1.0.0"

    def __init__(self, reject_existing_position: bool = True) -> None:
        self.reject_existing_position = bool(reject_existing_position)

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def check(
        self,
        symbol: str,
        signal: str,
        positions: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Check whether existing positions conflict with a proposed trade.

        Parameters
        ----------
        symbol:
            Trading symbol, for example XAUUSD.

        signal:
            Proposed BUY, SELL, or NO_TRADE signal.

        positions:
            Optional MT5 position collection.

            If supplied, it is inspected directly.

            If omitted, the method attempts to query MT5 safely.
            Failure to access MT5 does NOT create a false assumption
            that there are no positions.

        Returns
        -------
        dict
            Standardized position-check result.
        """

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        symbol = symbol.strip()

        if not symbol:
            raise ValueError("symbol is required")

        if not isinstance(signal, str):
            raise TypeError("signal must be a string")

        signal = signal.strip().upper()

        if signal not in SUPPORTED_SIGNALS:
            raise ValueError(
                f"unsupported signal: {signal}. "
                f"Expected one of {SUPPORTED_SIGNALS}"
            )

        # ----------------------------------------------------------
        # NO_TRADE never needs a position conflict check.
        # ----------------------------------------------------------

        if signal == NO_TRADE:
            return self._result(
                symbol=symbol,
                signal=signal,
                status="READY",
                allowed=False,
                conflict=False,
                reason="NO_TRADE signal cannot be executed",
                position_count=0,
                matching_positions=0,
                opposite_positions=0,
                positions_available=True,
            )

        # ----------------------------------------------------------
        # Obtain positions.
        # ----------------------------------------------------------

        if positions is None:
            positions, retrieval_error = self._get_mt5_positions(symbol)

            if retrieval_error is not None:
                return self._result(
                    symbol=symbol,
                    signal=signal,
                    status="ERROR",
                    allowed=False,
                    conflict=True,
                    reason="Unable to verify existing positions",
                    position_count=0,
                    matching_positions=0,
                    opposite_positions=0,
                    positions_available=False,
                    error=retrieval_error,
                )

        else:
            retrieval_error = None

        # ----------------------------------------------------------
        # Normalize position collection.
        # ----------------------------------------------------------

        normalized_positions = self._normalize_positions(
            symbol=symbol,
            positions=positions,
        )

        position_count = len(normalized_positions)

        matching_positions = [
            p
            for p in normalized_positions
            if p["direction"] == signal
        ]

        opposite_signal = SELL if signal == BUY else BUY

        opposite_positions = [
            p
            for p in normalized_positions
            if p["direction"] == opposite_signal
        ]

        # ----------------------------------------------------------
        # Existing-position policy.
        # ----------------------------------------------------------

        if self.reject_existing_position and position_count > 0:
            return self._result(
                symbol=symbol,
                signal=signal,
                status="READY",
                allowed=False,
                conflict=True,
                reason="Existing position detected",
                position_count=position_count,
                matching_positions=len(matching_positions),
                opposite_positions=len(opposite_positions),
                positions_available=True,
                existing_positions=normalized_positions,
            )

        # ----------------------------------------------------------
        # No existing position.
        # ----------------------------------------------------------

        return self._result(
            symbol=symbol,
            signal=signal,
            status="READY",
            allowed=True,
            conflict=False,
            reason="No conflicting existing position",
            position_count=position_count,
            matching_positions=len(matching_positions),
            opposite_positions=len(opposite_positions),
            positions_available=True,
            existing_positions=normalized_positions,
        )

    # ==============================================================
    # CONVENIENCE METHODS
    # ==============================================================

    def has_existing_position(
        self,
        symbol: str,
        positions: Optional[Any] = None,
    ) -> bool:
        """
        Return True when at least one position exists for symbol.
        """

        result = self.check(
            symbol=symbol,
            signal=NO_TRADE,
            positions=positions,
        )

        return result["position_count"] > 0

    def is_allowed(
        self,
        symbol: str,
        signal: str,
        positions: Optional[Any] = None,
    ) -> bool:
        """
        Return only the position-check permission.
        """

        return bool(
            self.check(
                symbol=symbol,
                signal=signal,
                positions=positions,
            )["allowed"]
        )

    # ==============================================================
    # MT5 ACCESS
    # ==============================================================

    @staticmethod
    def _get_mt5_positions(
        symbol: str,
    ) -> tuple[Any, Optional[str]]:
        """
        Safely retrieve MT5 positions.

        No order is created or modified here.
        """

        try:
            import MetaTrader5 as mt5
        except ImportError as exc:
            return None, f"MetaTrader5 unavailable: {exc}"

        try:
            result = mt5.positions_get(symbol=symbol)

            if result is None:
                error = mt5.last_error()

                return None, (
                    "MT5 positions_get returned None: "
                    f"{error}"
                )

            return result, None

        except Exception as exc:
            return None, f"MT5 position retrieval failed: {exc}"

    # ==============================================================
    # NORMALIZATION
    # ==============================================================

    @classmethod
    def _normalize_positions(
        cls,
        symbol: str,
        positions: Any,
    ) -> list[Dict[str, Any]]:
        """
        Convert MT5 position objects or dictionary-like positions
        into a stable internal representation.
        """

        if positions is None:
            return []

        try:
            position_list = list(positions)
        except TypeError:
            position_list = [positions]

        normalized: list[Dict[str, Any]] = []

        for position in position_list:
            position_symbol = cls._read_value(
                position,
                "symbol",
            )

            # ------------------------------------------------------
            # Ignore positions belonging to other symbols.
            # ------------------------------------------------------

            if position_symbol is not None:
                if str(position_symbol).upper() != symbol.upper():
                    continue

            raw_type = cls._read_value(
                position,
                "type",
            )

            direction = cls._normalize_direction(
                raw_type,
            )

            volume = cls._read_value(
                position,
                "volume",
            )

            ticket = cls._read_value(
                position,
                "ticket",
            )

            price_open = cls._read_value(
                position,
                "price_open",
            )

            profit = cls._read_value(
                position,
                "profit",
            )

            normalized.append(
                {
                    "symbol": (
                        str(position_symbol)
                        if position_symbol is not None
                        else symbol
                    ),
                    "direction": direction,
                    "type": raw_type,
                    "volume": volume,
                    "ticket": ticket,
                    "price_open": price_open,
                    "profit": profit,
                }
            )

        return normalized

    @staticmethod
    def _read_value(
        position: Any,
        key: str,
    ) -> Any:
        """
        Read a field from either a dictionary or an object.
        """

        if isinstance(position, dict):
            return position.get(key)

        return getattr(position, key, None)

    @staticmethod
    def _normalize_direction(
        raw_type: Any,
    ) -> str:
        """
        Normalize MT5 position type into BUY / SELL / UNKNOWN.
        """

        if isinstance(raw_type, str):
            value = raw_type.strip().upper()

            if value in {"BUY", "LONG", "POSITION_TYPE_BUY"}:
                return BUY

            if value in {"SELL", "SHORT", "POSITION_TYPE_SELL"}:
                return SELL

        # MT5:
        # POSITION_TYPE_BUY  = 0
        # POSITION_TYPE_SELL = 1

        if raw_type == 0:
            return BUY

        if raw_type == 1:
            return SELL

        return "UNKNOWN"

    # ==============================================================
    # RESULT BUILDER
    # ==============================================================

    @classmethod
    def _result(
        cls,
        *,
        symbol: str,
        signal: str,
        status: str,
        allowed: bool,
        conflict: bool,
        reason: str,
        position_count: int,
        matching_positions: int,
        opposite_positions: int,
        positions_available: bool,
        existing_positions: Optional[list[Dict[str, Any]]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Produce the standardized position-check result.
        """

        result: Dict[str, Any] = {
            "status": status,
            "component": "position_check",
            "symbol": symbol,
            "signal": signal,
            "allowed": bool(allowed),
            "conflict": bool(conflict),
            "reason": reason,
            "position_count": int(position_count),
            "matching_positions": int(matching_positions),
            "opposite_positions": int(opposite_positions),
            "positions_available": bool(positions_available),
            "existing_positions": existing_positions or [],
            "decision": None,
            "decision_authority": "upstream_decision_engine",
            "execution_authority": "downstream_execution_pipeline",
        }

        if error is not None:
            result["error"] = error

        return result


# ==================================================================
# MODULE-LEVEL CONVENIENCE API
# ==================================================================

_DEFAULT_POSITION_CHECK = PositionCheck(
    reject_existing_position=True,
)


def check_position(
    symbol: str,
    signal: str,
    positions: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Module-level position-check API.
    """

    return _DEFAULT_POSITION_CHECK.check(
        symbol=symbol,
        signal=signal,
        positions=positions,
    )


def has_existing_position(
    symbol: str,
    positions: Optional[Any] = None,
) -> bool:
    """
    Module-level existing-position check.
    """

    return _DEFAULT_POSITION_CHECK.has_existing_position(
        symbol=symbol,
        positions=positions,
    )


def position_allowed(
    symbol: str,
    signal: str,
    positions: Optional[Any] = None,
) -> bool:
    """
    Module-level permission check.
    """

    return _DEFAULT_POSITION_CHECK.is_allowed(
        symbol=symbol,
        signal=signal,
        positions=positions,
    )


def position_check_info() -> Dict[str, Any]:
    """
    Public module information API.
    """

    return {
        "name": "BALLY FLOW Position Check",
        "version": "1.0.0",
        "status": "READY",
        "supported_signals": [
            BUY,
            SELL,
            NO_TRADE,
        ],
        "responsibilities": [
            "existing_position_detection",
            "same_direction_detection",
            "opposite_direction_detection",
            "execution_conflict_detection",
        ],
        "reject_existing_position": True,
        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "decision_generation": False,
        "risk_management": False,
        "position_sizing": False,
        "order_builder": False,
        "mt5_order_check": False,
        "mt5_order_send": False,
        "decision_authority": "upstream_decision_engine",
        "execution_authority": "downstream_execution_pipeline",
    }


__all__ = [
    "BUY",
    "SELL",
    "NO_TRADE",
    "PositionCheck",
    "check_position",
    "has_existing_position",
    "position_allowed",
    "position_check_info",
]

def position_check_info() -> dict:
    return {
        "name": "BALLY FLOW Position Check",
        "version": "1.0.0",
        "status": "READY",
        "supported_signals": [
            "BUY",
            "SELL",
            "NO_TRADE",
        ],
        "responsibilities": [
            "existing_position_detection",
            "same_direction_detection",
            "opposite_direction_detection",
            "execution_conflict_detection",
        ],
        "reject_existing_position": True,
        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "decision_generation": False,
        "risk_management": False,
        "position_sizing": False,
        "order_builder": False,
        "mt5_order_check": False,
        "mt5_order_send": False,
        "decision_authority": "upstream_decision_engine",
        "execution_authority": "downstream_execution_pipeline",
    }