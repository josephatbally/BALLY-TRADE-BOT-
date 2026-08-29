"""
BALLY FLOW - Final Execution Gate

Final safety authorization layer immediately before order construction.

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
Order Builder
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
This module verifies that an already-authorized trade is permitted
to continue into order construction.

This module MUST NOT:

    - generate BUY / SELL / NO_TRADE
    - perform technical analysis
    - perform fundamental analysis
    - perform hybrid analysis
    - calculate position size
    - change stop loss
    - change take profit
    - build an MT5 order
    - call mt5.order_check()
    - call mt5.order_send()
    - execute trades

The upstream Decision Engine remains authoritative for direction.

The Final Gate only answers:

    "Is this already-decided trade allowed to proceed?"

Possible gate results:

    PASS
    BLOCK
"""


from __future__ import annotations

from typing import Any, Dict, Optional


BUY = "BUY"
SELL = "SELL"
NO_TRADE = "NO_TRADE"

VALID_SIGNALS = {
    BUY,
    SELL,
    NO_TRADE,
}


class FinalGate:
    """
    Final execution authorization gate.

    The gate consumes upstream information and performs safety checks.
    It never creates or changes the trading decision.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        require_decision: bool = True,
        require_risk_approval: bool = True,
        require_position_clear: bool = True,
    ) -> None:

        self.name = "BALLY FLOW Final Execution Gate"

        self.require_decision = bool(require_decision)
        self.require_risk_approval = bool(require_risk_approval)
        self.require_position_clear = bool(require_position_clear)

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def evaluate(
        self,
        decision: Any,
        risk: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, Any]] = None,
        trade_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate whether an already-decided trade may proceed.

        Parameters
        ----------
        decision:
            Authoritative upstream trading decision.

        risk:
            Result from the risk-management layer.

        position:
            Result from position_check.py.

        trade_plan:
            Existing trade plan supplied by an upstream layer.

        Returns
        -------
        dict
            Standardized final-gate result.

        Important
        ---------
        The decision is never changed by this function.
        """

        normalized_decision = self._extract_decision(decision)

        checks = []

        # ----------------------------------------------------------
        # 1. Decision validity
        # ----------------------------------------------------------

        decision_check = self._check_decision(normalized_decision)
        checks.append(decision_check)

        if not decision_check["passed"]:
            return self._blocked_result(
                normalized_decision,
                checks,
                decision_check["reason"],
            )

        # ----------------------------------------------------------
        # NO_TRADE can never enter execution.
        # ----------------------------------------------------------

        if normalized_decision == NO_TRADE:
            return self._blocked_result(
                normalized_decision,
                checks,
                "upstream_decision_is_NO_TRADE",
            )

        # ----------------------------------------------------------
        # 2. Risk authorization
        # ----------------------------------------------------------

        if self.require_risk_approval:
            risk_check = self._check_risk(risk)
            checks.append(risk_check)

            if not risk_check["passed"]:
                return self._blocked_result(
                    normalized_decision,
                    checks,
                    risk_check["reason"],
                )
        else:
            checks.append(
                self._passed_check(
                    "risk_authorization",
                    "risk_check_not_required",
                )
            )

        # ----------------------------------------------------------
        # 3. Position authorization
        # ----------------------------------------------------------

        if self.require_position_clear:
            position_check = self._check_position(position)
            checks.append(position_check)

            if not position_check["passed"]:
                return self._blocked_result(
                    normalized_decision,
                    checks,
                    position_check["reason"],
                )
        else:
            checks.append(
                self._passed_check(
                    "position_check",
                    "position_check_not_required",
                )
            )

        # ----------------------------------------------------------
        # 4. Trade-plan validation
        # ----------------------------------------------------------

        trade_plan_check = self._check_trade_plan(trade_plan)
        checks.append(trade_plan_check)

        if not trade_plan_check["passed"]:
            return self._blocked_result(
                normalized_decision,
                checks,
                trade_plan_check["reason"],
            )

        # ----------------------------------------------------------
        # ALL GATES PASSED
        # ----------------------------------------------------------

        return {
            "status": "READY",
            "gate": "PASS",
            "allowed": True,
            "execution_allowed": True,

            # Preserve the authoritative upstream decision.
            "decision": normalized_decision,
            "decision_preserved": True,

            "checks": checks,
            "check_count": len(checks),
            "passed_check_count": sum(
                1 for check in checks if check["passed"]
            ),
            "failed_check_count": sum(
                1 for check in checks if not check["passed"]
            ),

            "reason": "all_final_execution_checks_passed",

            # Explicit architecture boundaries.
            "decision_authority": "upstream_decision_engine",
            "execution_authority": "downstream_execution_pipeline",

            "order_builder_allowed": True,
            "executor_allowed": True,

            # This module never performs these operations.
            "mt5_order_check": False,
            "mt5_order_send": False,
        }

    # ==============================================================
    # DECISION CHECK
    # ==============================================================

    @staticmethod
    def _extract_decision(decision: Any) -> Optional[str]:
        """
        Extract an existing decision without creating one.
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

        if value not in VALID_SIGNALS:
            return None

        return value

    @staticmethod
    def _check_decision(
        decision: Optional[str],
    ) -> Dict[str, Any]:

        if decision is None:
            return {
                "name": "decision",
                "passed": False,
                "reason": "missing_or_invalid_upstream_decision",
            }

        return {
            "name": "decision",
            "passed": True,
            "reason": "valid_upstream_decision",
            "value": decision,
        }

    # ==============================================================
    # RISK CHECK
    # ==============================================================

    @staticmethod
    def _check_risk(
        risk: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if risk is None:
            return {
                "name": "risk_authorization",
                "passed": False,
                "reason": "risk_result_missing",
            }

        if not isinstance(risk, dict):
            return {
                "name": "risk_authorization",
                "passed": False,
                "reason": "risk_result_invalid",
            }

        # Accept common authorization field names.
        approved = risk.get("approved")

        if approved is None:
            approved = risk.get("risk_approved")

        if approved is None:
            approved = risk.get("trade_allowed")

        if approved is None:
            approved = risk.get("allowed")

        if approved is not True:
            return {
                "name": "risk_authorization",
                "passed": False,
                "reason": "risk_authorization_not_confirmed",
            }

        return {
            "name": "risk_authorization",
            "passed": True,
            "reason": "risk_authorization_confirmed",
        }

    # ==============================================================
    # POSITION CHECK
    # ==============================================================

    @staticmethod
    def _check_position(
        position: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if position is None:
            return {
                "name": "position_check",
                "passed": False,
                "reason": "position_check_result_missing",
            }

        if not isinstance(position, dict):
            return {
                "name": "position_check",
                "passed": False,
                "reason": "position_check_result_invalid",
            }

        # Position-check implementations may expose one of several
        # explicit authorization fields.

        allowed = position.get("allowed")

        if allowed is None:
            allowed = position.get("position_allowed")

        if allowed is None:
            allowed = position.get("execution_allowed")

        if allowed is False:
            return {
                "name": "position_check",
                "passed": False,
                "reason": "existing_position_or_execution_conflict",
            }

        if allowed is not True:
            return {
                "name": "position_check",
                "passed": False,
                "reason": "position_authorization_not_confirmed",
            }

        return {
            "name": "position_check",
            "passed": True,
            "reason": "position_clear",
        }

    # ==============================================================
    # TRADE PLAN CHECK
    # ==============================================================

    @staticmethod
    def _check_trade_plan(
        trade_plan: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if trade_plan is None:
            return {
                "name": "trade_plan",
                "passed": False,
                "reason": "trade_plan_missing",
            }

        if not isinstance(trade_plan, dict):
            return {
                "name": "trade_plan",
                "passed": False,
                "reason": "trade_plan_invalid",
            }

        # A trade plan must contain enough information for the next
        # order-building layer to operate. We do not build or modify
        # the plan here.

        if not trade_plan:
            return {
                "name": "trade_plan",
                "passed": False,
                "reason": "trade_plan_empty",
            }

        return {
            "name": "trade_plan",
            "passed": True,
            "reason": "trade_plan_present",
        }

    # ==============================================================
    # RESULT HELPERS
    # ==============================================================

    @staticmethod
    def _passed_check(
        name: str,
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "name": name,
            "passed": True,
            "reason": reason,
        }

    @staticmethod
    def _blocked_result(
        decision: Optional[str],
        checks: list[Dict[str, Any]],
        reason: str,
    ) -> Dict[str, Any]:

        return {
            "status": "BLOCKED",
            "gate": "BLOCK",
            "allowed": False,
            "execution_allowed": False,

            # Never replace the upstream decision with NO_TRADE.
            "decision": decision,
            "decision_preserved": True,

            "checks": checks,
            "check_count": len(checks),
            "passed_check_count": sum(
                1 for check in checks if check["passed"]
            ),
            "failed_check_count": sum(
                1 for check in checks if not check["passed"]
            ),

            "reason": reason,

            "decision_authority": "upstream_decision_engine",
            "execution_authority": "downstream_execution_pipeline",

            "order_builder_allowed": False,
            "executor_allowed": False,

            "mt5_order_check": False,
            "mt5_order_send": False,
        }


# ==================================================================
# CONVENIENCE API
# ==================================================================

def evaluate_final_gate(
    decision: Any,
    risk: Optional[Dict[str, Any]] = None,
    position: Optional[Dict[str, Any]] = None,
    trade_plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience entry point for final execution authorization.
    """

    gate = FinalGate()

    return gate.evaluate(
        decision=decision,
        risk=risk,
        position=position,
        trade_plan=trade_plan,
    )


# ==================================================================
# MODULE INFORMATION
# ==================================================================

def final_gate_info() -> Dict[str, Any]:
    """
    Return execution-layer architecture information.
    """

    return {
        "name": "BALLY FLOW Final Execution Gate",
        "version": "1.0.0",
        "status": "READY",

        "signals": [
            BUY,
            SELL,
            NO_TRADE,
        ],

        "gate_results": [
            "PASS",
            "BLOCK",
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
            "decision_validation",
            "risk_authorization_validation",
            "position_authorization_validation",
            "trade_plan_validation",
            "final_execution_authorization",
        ],

        "decision_authority": "upstream_decision_engine",

        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "position_check": True,
        "order_building": False,
        "execution": False,
        "order_placement": False,

        "order_builder_allowed_after_pass": True,
        "executor_allowed_after_pass": True,

        "mt5_order_check": False,
        "mt5_order_send": False,

        "decision_generation": False,
        "decision_override": False,
        "decision_conversion": False,
    }


__all__ = [
    "BUY",
    "SELL",
    "NO_TRADE",
    "VALID_SIGNALS",
    "FinalGate",
    "evaluate_final_gate",
    "final_gate_info",
]

def final_gate_info() -> dict:
    return {
        "name": "BALLY FLOW Final Execution Gate",
        "version": "1.0.0",
        "status": "READY",
        "signals": [
            "BUY",
            "SELL",
            "NO_TRADE",
        ],
        "gate_results": [
            "PASS",
            "BLOCK",
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
            "decision_validation",
            "risk_authorization_validation",
            "position_authorization_validation",
            "trade_plan_validation",
            "final_execution_authorization",
        ],
        "decision_authority": "upstream_decision_engine",
        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "position_check": True,
        "order_building": False,
        "execution": False,
        "order_placement": False,
        "order_builder_allowed_after_pass": True,
        "executor_allowed_after_pass": True,
        "mt5_order_check": False,
        "mt5_order_send": False,
        "decision_generation": False,
        "decision_override": False,
        "decision_conversion": False,
    }