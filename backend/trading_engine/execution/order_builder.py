"""
BALLY FLOW - Order Builder

Converts an already-authorized trade plan into a standardized
execution order specification.

ARCHITECTURE
------------

Decision Engine
      |
      v
Risk Management
      |
      v
Position Check
      |
      v
Final Gate
      |
      v
Order Builder          <-- THIS MODULE
      |
      v
Executor
      |
      v
Live Executor
      |
      +--> MT5 order_check
      |
      +--> MT5 order_send


RESPONSIBILITIES
----------------
This module:

    - accepts an upstream BUY / SELL decision
    - requires Final Gate authorization
    - validates required trade-plan fields
    - normalizes order information
    - creates a standardized order specification
    - prepares data for the downstream Executor


This module MUST NOT:

    - generate BUY / SELL / NO_TRADE
    - override the upstream decision
    - perform technical analysis
    - perform fundamental analysis
    - perform hybrid analysis
    - calculate risk
    - calculate position size
    - change SL
    - change TP
    - call MT5
    - call mt5.order_check()
    - call mt5.order_send()
    - execute an order


DECISION AUTHORITY
------------------
The Decision Engine remains authoritative.

EXECUTION AUTHORITY
-------------------
The downstream Execution Pipeline / Executor remains responsible
for actual execution.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


BUY = "BUY"
SELL = "SELL"
NO_TRADE = "NO_TRADE"

VALID_SIGNALS = {
    BUY,
    SELL,
}


class OrderBuilder:
    """
    Builds a standardized order specification from an already
    authorized trade plan.

    No market decision is created here.
    """

    VERSION = "1.0.0"

    def __init__(self) -> None:
        self.name = "BALLY FLOW Order Builder"

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def build(
        self,
        decision: Any,
        trade_plan: Optional[Dict[str, Any]],
        final_gate: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build a standardized execution order.

        Parameters
        ----------
        decision:
            Authoritative upstream BUY or SELL decision.

        trade_plan:
            Existing trade plan produced upstream.

        final_gate:
            Result returned by final_gate.py.

        Returns
        -------
        dict
            Standardized order-builder result.
        """

        normalized_decision = self._extract_decision(decision)

        # ----------------------------------------------------------
        # Decision must already exist.
        # ----------------------------------------------------------

        if normalized_decision is None:
            return self._blocked(
                None,
                "missing_or_invalid_upstream_decision",
            )

        # ----------------------------------------------------------
        # NO_TRADE can never become an executable order.
        # ----------------------------------------------------------

        if normalized_decision == NO_TRADE:
            return self._blocked(
                normalized_decision,
                "NO_TRADE_cannot_be_built_into_order",
            )

        # ----------------------------------------------------------
        # Final Gate is mandatory.
        # ----------------------------------------------------------

        gate_result = self._validate_final_gate(final_gate)

        if not gate_result["passed"]:
            return self._blocked(
                normalized_decision,
                gate_result["reason"],
            )

        # ----------------------------------------------------------
        # Trade plan is mandatory.
        # ----------------------------------------------------------

        plan_result = self._validate_trade_plan(trade_plan)

        if not plan_result["passed"]:
            return self._blocked(
                normalized_decision,
                plan_result["reason"],
            )

        plan = trade_plan

        # ----------------------------------------------------------
        # Extract standardized fields.
        # ----------------------------------------------------------

        symbol = self._first_value(
            plan,
            "symbol",
            "broker_symbol",
            "instrument",
        )

        entry = self._first_value(
            plan,
            "entry",
            "entry_price",
            "price",
        )

        stop_loss = self._first_value(
            plan,
            "stop_loss",
            "sl",
            "stop",
        )

        take_profit = self._first_value(
            plan,
            "take_profit",
            "tp",
            "target",
        )

        volume = self._first_value(
            plan,
            "volume",
            "lot",
            "lots",
            "lot_size",
        )

        # ----------------------------------------------------------
        # Symbol is required.
        # ----------------------------------------------------------

        if not isinstance(symbol, str) or not symbol.strip():
            return self._blocked(
                normalized_decision,
                "trade_plan_missing_symbol",
            )

        symbol = symbol.strip()

        # ----------------------------------------------------------
        # Entry is required.
        # ----------------------------------------------------------

        if not self._valid_number(entry):
            return self._blocked(
                normalized_decision,
                "trade_plan_missing_or_invalid_entry",
            )

        # ----------------------------------------------------------
        # Stop loss is required.
        # ----------------------------------------------------------

        if not self._valid_number(stop_loss):
            return self._blocked(
                normalized_decision,
                "trade_plan_missing_or_invalid_stop_loss",
            )

        # ----------------------------------------------------------
        # Take profit is required.
        # ----------------------------------------------------------

        if not self._valid_number(take_profit):
            return self._blocked(
                normalized_decision,
                "trade_plan_missing_or_invalid_take_profit",
            )

        # ----------------------------------------------------------
        # Volume / lot size is required.
        #
        # IMPORTANT:
        # This module does NOT calculate the lot size.
        # It only consumes the value supplied by Risk Management.
        # ----------------------------------------------------------

        if not self._valid_number(volume):
            return self._blocked(
                normalized_decision,
                "trade_plan_missing_or_invalid_volume",
            )

        # ----------------------------------------------------------
        # Validate directional price relationships.
        #
        # This does not modify prices.
        # ----------------------------------------------------------

        price_validation = self._validate_price_relationship(
            normalized_decision,
            float(entry),
            float(stop_loss),
            float(take_profit),
        )

        if not price_validation["passed"]:
            return self._blocked(
                normalized_decision,
                price_validation["reason"],
            )

        # ----------------------------------------------------------
        # Optional execution metadata.
        # ----------------------------------------------------------

        order_type = self._order_type(normalized_decision)

        magic_number = self._first_value(
            plan,
            "magic_number",
            "magic",
        )

        comment = self._first_value(
            plan,
            "comment",
        )

        deviation = self._first_value(
            plan,
            "deviation",
            "max_deviation",
        )

        filling_mode = self._first_value(
            plan,
            "filling_mode",
        )

        # ----------------------------------------------------------
        # Standardized order specification.
        # ----------------------------------------------------------

        order = {
            "symbol": symbol,
            "decision": normalized_decision,
            "order_type": order_type,

            "volume": float(volume),

            "entry": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),

            "magic_number": magic_number,
            "comment": comment,
            "deviation": deviation,
            "filling_mode": filling_mode,
        }

        # ----------------------------------------------------------
        # Final result.
        # ----------------------------------------------------------

        return {
            "status": "READY",
            "built": True,

            "decision": normalized_decision,
            "decision_preserved": True,

            "symbol": symbol,

            "order": order,

            "source": {
                "decision_engine": True,
                "risk_management": True,
                "position_check": True,
                "final_gate": True,
            },

            "validation": {
                "decision": True,
                "final_gate": True,
                "trade_plan": True,
                "price_relationship": True,
                "volume_present": True,
            },

            "executor_allowed": True,

            # Explicitly false because this module does not execute.
            "execution_performed": False,
            "mt5_order_check": False,
            "mt5_order_send": False,

            "decision_authority": "upstream_decision_engine",
            "execution_authority": "downstream_execution_pipeline",

            "reason": "order_specification_built_successfully",
        }

    # ==============================================================
    # DECISION
    # ==============================================================

    @staticmethod
    def _extract_decision(decision: Any) -> Optional[str]:
        """
        Extract an existing decision.

        Never creates a new decision.
        """

        if isinstance(decision, str):
            value = decision.strip().upper()

        elif isinstance(decision, dict):
            value = (
                decision.get("decision")
                or decision.get("signal")
                or decision.get("hybrid_signal")
                or decision.get("technical_signal")
            )

            if not isinstance(value, str):
                return None

            value = value.strip().upper()

        else:
            return None

        if value == NO_TRADE:
            return NO_TRADE

        if value not in VALID_SIGNALS:
            return None

        return value

    # ==============================================================
    # FINAL GATE
    # ==============================================================

    @staticmethod
    def _validate_final_gate(
        final_gate: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Require explicit Final Gate authorization.
        """

        if not isinstance(final_gate, dict):
            return {
                "passed": False,
                "reason": "final_gate_result_missing_or_invalid",
            }

        gate = str(
            final_gate.get("gate", "")
        ).strip().upper()

        allowed = final_gate.get("allowed")

        execution_allowed = final_gate.get(
            "execution_allowed"
        )

        if gate != "PASS":
            return {
                "passed": False,
                "reason": "final_gate_not_passed",
            }

        if allowed is not True:
            return {
                "passed": False,
                "reason": "final_gate_allowed_flag_not_confirmed",
            }

        if execution_allowed is not True:
            return {
                "passed": False,
                "reason": "final_gate_execution_authorization_not_confirmed",
            }

        return {
            "passed": True,
            "reason": "final_gate_authorized",
        }

    # ==============================================================
    # TRADE PLAN
    # ==============================================================

    @staticmethod
    def _validate_trade_plan(
        trade_plan: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not isinstance(trade_plan, dict):
            return {
                "passed": False,
                "reason": "trade_plan_missing_or_invalid",
            }

        if not trade_plan:
            return {
                "passed": False,
                "reason": "trade_plan_empty",
            }

        return {
            "passed": True,
            "reason": "trade_plan_present",
        }

    # ==============================================================
    # PRICE RELATIONSHIP
    # ==============================================================

    @staticmethod
    def _validate_price_relationship(
        decision: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
    ) -> Dict[str, Any]:
        """
        Validate basic directional price relationships.

        BUY:
            SL < Entry < TP

        SELL:
            TP < Entry < SL

        Prices are never modified.
        """

        if decision == BUY:

            if not stop_loss < entry:
                return {
                    "passed": False,
                    "reason": "BUY_stop_loss_must_be_below_entry",
                }

            if not take_profit > entry:
                return {
                    "passed": False,
                    "reason": "BUY_take_profit_must_be_above_entry",
                }

        elif decision == SELL:

            if not stop_loss > entry:
                return {
                    "passed": False,
                    "reason": "SELL_stop_loss_must_be_above_entry",
                }

            if not take_profit < entry:
                return {
                    "passed": False,
                    "reason": "SELL_take_profit_must_be_below_entry",
                }

        else:
            return {
                "passed": False,
                "reason": "unsupported_order_direction",
            }

        return {
            "passed": True,
            "reason": "price_relationship_valid",
        }

    # ==============================================================
    # ORDER TYPE
    # ==============================================================

    @staticmethod
    def _order_type(decision: str) -> str:

        if decision == BUY:
            return "BUY"

        if decision == SELL:
            return "SELL"

        raise ValueError(
            "OrderBuilder cannot create an order type for "
            f"{decision!r}"
        )

    # ==============================================================
    # VALUE HELPERS
    # ==============================================================

    @staticmethod
    def _first_value(
        data: Dict[str, Any],
        *keys: str,
    ) -> Any:

        for key in keys:
            if key in data and data[key] is not None:
                return data[key]

        return None

    @staticmethod
    def _valid_number(value: Any) -> bool:

        if isinstance(value, bool):
            return False

        try:
            number = float(value)
        except (TypeError, ValueError):
            return False

        return number > 0

    # ==============================================================
    # BLOCKED RESULT
    # ==============================================================

    @staticmethod
    def _blocked(
        decision: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "status": "BLOCKED",
            "built": False,

            "decision": decision,
            "decision_preserved": True,

            "order": None,

            "executor_allowed": False,
            "execution_performed": False,

            "mt5_order_check": False,
            "mt5_order_send": False,

            "reason": reason,

            "decision_authority": "upstream_decision_engine",
            "execution_authority": "downstream_execution_pipeline",
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def build_order(
    decision: Any,
    trade_plan: Optional[Dict[str, Any]],
    final_gate: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Convenience API for building an execution order.
    """

    builder = OrderBuilder()

    return builder.build(
        decision=decision,
        trade_plan=trade_plan,
        final_gate=final_gate,
    )


# ==================================================================
# MODULE INFORMATION
# ==================================================================

def order_builder_info() -> Dict[str, Any]:
    """
    Return standardized Order Builder architecture information.
    """

    return {
        "name": "BALLY FLOW Order Builder",
        "version": "1.0.0",
        "status": "READY",

        "supported_signals": [
            BUY,
            SELL,
            NO_TRADE,
        ],

        "pipeline_position": [
            "decision_engine",
            "risk_management",
            "position_check",
            "final_gate",
            "order_builder",
            "executor",
            "live_executor",
        ],

        "responsibilities": [
            "consume_authorized_decision",
            "consume_risk_managed_trade_plan",
            "require_final_gate_pass",
            "validate_trade_plan",
            "validate_price_relationship",
            "standardize_order_specification",
        ],

        "decision_generation": False,
        "decision_override": False,

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,

        "risk_management": False,
        "position_sizing": False,

        "final_gate_required": True,

        "executor_output": True,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "order_placement": False,
        "execution": False,

        "decision_authority": "upstream_decision_engine",
        "execution_authority": "downstream_execution_pipeline",
    }


__all__ = [
    "BUY",
    "SELL",
    "NO_TRADE",
    "VALID_SIGNALS",
    "OrderBuilder",
    "build_order",
    "order_builder_info",
]