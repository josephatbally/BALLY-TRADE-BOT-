
"""
BALLY FLOW - Executor

Execution authorization and validation layer.

PIPELINE
--------
Decision Engine
    ↓
Risk Management
    ↓
Position Check
    ↓
Final Gate
    ↓
Order Builder
    ↓
Executor
    ↓
Live Executor
    ↓
MT5 order_check
    ↓
MT5 order_send

RESPONSIBILITIES
----------------
- Consume an authorized order from order_builder.py
- Validate the order before live execution
- Preserve the upstream BUY/SELL/NO_TRADE decision
- Validate required order fields
- Validate price relationships
- Validate volume
- Preserve execution safety
- Delegate actual broker interaction to live_executor.py

This module MUST NOT:
- generate BUY/SELL decisions
- override an upstream decision
- perform technical analysis
- perform fundamental analysis
- perform hybrid analysis
- calculate position size
- manage trading risk
- directly call MT5 order_send
"""

from __future__ import annotations

from typing import Any, Dict, Optional


SUPPORTED_SIGNALS = ("BUY", "SELL", "NO_TRADE")

DEFAULT_MAGIC_NUMBER = 20260817
DEFAULT_COMMENT = "BALLY_TRADES_BOT"

# Safety defaults.
EXECUTION_ENABLED = True
LIVE_TRADING = True
ALLOW_ORDER_SEND = True
DRY_RUN = False


class Executor:
    """
    BALLY FLOW execution validation and delegation layer.

    The Executor does not make trading decisions.

    The decision contained in the authorized order is preserved
    exactly as supplied by the upstream Decision Engine.
    """

    def __init__(
        self,
        execution_enabled: bool = EXECUTION_ENABLED,
        live_trading: bool = LIVE_TRADING,
        allow_order_send: bool = ALLOW_ORDER_SEND,
        dry_run: bool = DRY_RUN,
    ) -> None:

        self.name = "BALLY FLOW Executor"
        self.version = "1.0.0"

        self.execution_enabled = bool(execution_enabled)
        self.live_trading = bool(live_trading)
        self.allow_order_send = bool(allow_order_send)
        self.dry_run = bool(dry_run)

    # ============================================================
    # INFORMATION
    # ============================================================

    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": "READY",
            "supported_signals": list(SUPPORTED_SIGNALS),
            "pipeline_position": [
                "decision_engine",
                "risk_management",
                "position_check",
                "final_gate",
                "order_builder",
                "executor",
                "live_executor",
                "mt5.order_check",
                "mt5.order_send",
            ],
            "responsibilities": [
                "consume_authorized_order",
                "validate_order",
                "validate_decision",
                "validate_price_relationship",
                "validate_volume",
                "preserve_execution_safety",
                "delegate_to_live_executor",
            ],
            "decision_generation": False,
            "decision_override": False,
            "technical_analysis": False,
            "fundamental_analysis": False,
            "hybrid_decision": False,
            "risk_management": False,
            "position_sizing": False,
            "direct_mt5_order_send": False,
            "mt5_order_check": False,
            "order_placement": False,
            "live_trading": self.live_trading,
            "execution_enabled": self.execution_enabled,
            "allow_order_send": self.allow_order_send,
            "dry_run": self.dry_run,
            "decision_authority": "upstream_decision_engine",
            "execution_authority": "executor",
            "broker_execution_authority": "live_executor",
        }

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def _validate_decision(decision: Any) -> Optional[str]:
        if not isinstance(decision, str):
            return "decision must be a string"

        if decision not in SUPPORTED_SIGNALS:
            return f"unsupported decision: {decision}"

        return None

    @staticmethod
    def _validate_order(order: Any) -> Optional[str]:

        if not isinstance(order, dict):
            return "order must be a dictionary"

        required = (
            "symbol",
            "decision",
            "order_type",
            "volume",
            "entry",
            "stop_loss",
            "take_profit",
        )

        for field in required:
            if field not in order:
                return f"missing required field: {field}"

        if not isinstance(order["symbol"], str) or not order["symbol"].strip():
            return "invalid symbol"

        decision_error = Executor._validate_decision(order["decision"])

        if decision_error:
            return decision_error

        if order["order_type"] not in ("BUY", "SELL"):
            return "invalid order_type"

        if order["decision"] in ("BUY", "SELL"):
            if order["order_type"] != order["decision"]:
                return "order_type does not match decision"

        try:
            volume = float(order["volume"])
        except (TypeError, ValueError):
            return "volume must be numeric"

        if volume <= 0:
            return "volume must be greater than zero"

        try:
            entry = float(order["entry"])
            stop_loss = float(order["stop_loss"])
            take_profit = float(order["take_profit"])
        except (TypeError, ValueError):
            return "entry, stop_loss and take_profit must be numeric"

        if entry <= 0 or stop_loss <= 0 or take_profit <= 0:
            return "prices must be greater than zero"

        return Executor._validate_price_relationship(
            order["decision"],
            entry,
            stop_loss,
            take_profit,
        )

    @staticmethod
    def _validate_price_relationship(
        decision: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
    ) -> Optional[str]:

        if decision == "BUY":

            if stop_loss >= entry:
                return "BUY stop_loss must be below entry"

            if take_profit <= entry:
                return "BUY take_profit must be above entry"

        elif decision == "SELL":

            if stop_loss <= entry:
                return "SELL stop_loss must be above entry"

            if take_profit >= entry:
                return "SELL take_profit must be below entry"

        return None

    # ============================================================
    # EXECUTION
    # ============================================================

    def execute(
        self,
        order: Dict[str, Any],
        *,
        gate: Optional[Dict[str, Any]] = None,
        risk: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        delegate: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate and authorize an order for downstream execution.

        Actual MT5 execution is NOT performed here.
        """

        # --------------------------------------------------------
        # Order validation
        # --------------------------------------------------------

        error = self._validate_order(order)

        if error:
            return {
                "status": "BLOCKED",
                "executed": False,
                "authorized": False,
                "reason": error,
                "decision": order.get("decision") if isinstance(order, dict) else None,
                "order": None,
                "live_executor_allowed": False,
                "mt5_order_check": False,
                "mt5_order_send": False,
            }

        decision = order["decision"]

        # --------------------------------------------------------
        # NO_TRADE can never reach broker execution.
        # --------------------------------------------------------

        if decision == "NO_TRADE":
            return {
                "status": "BLOCKED",
                "executed": False,
                "authorized": False,
                "reason": "NO_TRADE decision cannot be executed",
                "decision": decision,
                "order": None,
                "live_executor_allowed": False,
                "mt5_order_check": False,
                "mt5_order_send": False,
            }

        # --------------------------------------------------------
        # Final gate
        # --------------------------------------------------------

        if gate is not None:

            if not isinstance(gate, dict):
                return {
                    "status": "BLOCKED",
                    "executed": False,
                    "authorized": False,
                    "reason": "invalid final gate result",
                    "decision": decision,
                    "order": None,
                    "live_executor_allowed": False,
                    "mt5_order_check": False,
                    "mt5_order_send": False,
                }

            gate_allowed = gate.get(
                "allowed",
                gate.get("execution_allowed", False),
            )

            gate_status = gate.get("gate", gate.get("status"))

            if gate_allowed is not True and gate_status != "PASS":
                return {
                    "status": "BLOCKED",
                    "executed": False,
                    "authorized": False,
                    "reason": "final execution gate did not pass",
                    "decision": decision,
                    "order": None,
                    "live_executor_allowed": False,
                    "mt5_order_check": False,
                    "mt5_order_send": False,
                }

        # --------------------------------------------------------
        # Position authorization
        # --------------------------------------------------------

        if position is not None:

            if not isinstance(position, dict):
                return {
                    "status": "BLOCKED",
                    "executed": False,
                    "authorized": False,
                    "reason": "invalid position check result",
                    "decision": decision,
                    "order": None,
                    "live_executor_allowed": False,
                    "mt5_order_check": False,
                    "mt5_order_send": False,
                }

            if position.get("allowed") is False:
                return {
                    "status": "BLOCKED",
                    "executed": False,
                    "authorized": False,
                    "reason": position.get(
                        "reason",
                        "position check rejected execution",
                    ),
                    "decision": decision,
                    "order": None,
                    "live_executor_allowed": False,
                    "mt5_order_check": False,
                    "mt5_order_send": False,
                }

        # --------------------------------------------------------
        # Preserve order exactly.
        # --------------------------------------------------------

        normalized_order = dict(order)

        normalized_order.setdefault(
            "magic_number",
            DEFAULT_MAGIC_NUMBER,
        )

        normalized_order.setdefault(
            "comment",
            DEFAULT_COMMENT,
        )

        # --------------------------------------------------------
        # Safety barrier
        #
        # Executor never directly sends to MT5.
        # --------------------------------------------------------

        live_executor_allowed = bool(
            delegate
            and self.execution_enabled
            and self.live_trading
            and self.allow_order_send
            and not self.dry_run
        )

        return {
            "status": "READY",
            "executed": False,
            "authorized": True,
            "decision": decision,
            "order": normalized_order,
            "reason": (
                "order validated and authorized for downstream "
                "live executor"
                if live_executor_allowed
                else
                "order validated; live execution remains disabled"
            ),
            "execution_enabled": self.execution_enabled,
            "live_trading": self.live_trading,
            "allow_order_send": self.allow_order_send,
            "dry_run": self.dry_run,
            "live_executor_allowed": live_executor_allowed,
            "mt5_order_check": False,
            "mt5_order_send": False,
        }


# ================================================================
# SINGLETON / CONVENIENCE API
# ================================================================

_default_executor = Executor()


def executor_info() -> Dict[str, Any]:
    """Return Executor capability and safety information."""
    return _default_executor.info()


def execute_order(
    order: Dict[str, Any],
    *,
    gate: Optional[Dict[str, Any]] = None,
    risk: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None,
    delegate: bool = False,
) -> Dict[str, Any]:
    """
    Convenience API for execution validation.
    """

    return _default_executor.execute(
        order,
        gate=gate,
        risk=risk,
        position=position,
        delegate=delegate,
    )


__all__ = [
    "Executor",
    "SUPPORTED_SIGNALS",
    "DEFAULT_MAGIC_NUMBER",
    "DEFAULT_COMMENT",
    "EXECUTION_ENABLED",
    "LIVE_TRADING",
    "ALLOW_ORDER_SEND",
    "DRY_RUN",
    "executor_info",
    "execute_order",
]
