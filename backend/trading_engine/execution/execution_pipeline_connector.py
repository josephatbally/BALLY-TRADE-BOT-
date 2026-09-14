"""
BALLY FLOW - Execution Pipeline Connector

This module connects the Executor output to the Live Executor.

PIPELINE FLOW
=============

Upstream (Risk Management, Position Check, Final Gate, Order Builder)
    ↓
Executor (validates & authorizes)
    ↓
Execution Pipeline Connector (THIS MODULE)
    ↓
Live Executor (MT5 communication)
    ↓
order_check() → order_send() → Broker
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from . import live_executor


# ======================================================================
# CONFIGURATION
# ======================================================================

NAME = "BALLY FLOW Execution Pipeline Connector"
VERSION = "1.0.0"


# ======================================================================
# PIPELINE ORCHESTRATION
# ======================================================================

def connect_executor_to_live_executor(
    executor_result: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Connect Executor output to Live Executor.
    
    This function:
    1. Validates executor authorization
    2. Extracts the authorized order
    3. Passes to Live Executor for MT5 execution
    4. Returns complete execution result
    
    Parameters
    ----------
    executor_result : dict
        Output from executor.execute() or execute_order()
    
    gate : dict, optional
        Final gate result (passed to live_executor)
    
    Returns
    -------
    dict
        Complete execution result from live_executor.execute_live_trade()
    """
    
    # ----------------------------------------------------------------
    # 1. Validate executor result
    # ----------------------------------------------------------------
    
    if not isinstance(executor_result, dict):
        return {
            "status": "BLOCKED",
            "reason": "executor_result must be a dictionary",
            "authorized": False,
            "live_executor": False,
        }
    
    authorized = executor_result.get("authorized", False)
    
    if not authorized:
        return {
            "status": "BLOCKED",
            "reason": executor_result.get(
                "reason",
                "executor did not authorize execution"
            ),
            "authorized": False,
            "live_executor": False,
            "executor_status": executor_result.get("status"),
        }
    
    live_executor_allowed = executor_result.get(
        "live_executor_allowed",
        False,
    )
    
    if not live_executor_allowed:
        return {
            "status": "BLOCKED",
            "reason": "live_executor_allowed is False",
            "authorized": True,
            "live_executor": False,
            "reason_detail": executor_result.get("reason"),
        }
    
    # ----------------------------------------------------------------
    # 2. Extract order
    # ----------------------------------------------------------------
    
    order = executor_result.get("order")
    
    if not isinstance(order, dict):
        return {
            "status": "BLOCKED",
            "reason": "executor order is invalid",
            "authorized": True,
            "live_executor": False,
        }
    
    # ----------------------------------------------------------------
    # 3. Pass to Live Executor
    # ----------------------------------------------------------------
    
    try:
        live_execution_result = live_executor.execute_live_trade(
            order=order,
            gate=gate,
        )
        
    except Exception as exc:
        return {
            "status": "FAILED",
            "reason": f"live_executor exception: {exc}",
            "authorized": True,
            "live_executor": False,
            "error": str(exc),
        }
    
    # ----------------------------------------------------------------
    # 4. Return complete result
    # ----------------------------------------------------------------
    
    return {
        "status": live_execution_result.get("status"),
        "authorized": True,
        "live_executor": True,
        "executor_result": executor_result,
        "live_executor_result": live_execution_result,
        "reason": (
            "trade executed"
            if live_execution_result.get("real_trade")
            else live_execution_result.get("reason")
        ),
        "real_trade": live_execution_result.get("real_trade", False),
        "executed": live_execution_result.get("executed", False),
    }


def execute_full_pipeline(
    executor_result: Dict[str, Any],
    gate: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience alias for connect_executor_to_live_executor().
    """
    return connect_executor_to_live_executor(
        executor_result=executor_result,
        gate=gate,
    )


# ======================================================================
# MODULE INFORMATION
# ======================================================================

def connector_info() -> Dict[str, Any]:
    """
    Return connector architecture information.
    """
    
    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",
        
        "pipeline_position": [
            "executor",
            "execution_pipeline_connector",
            "live_executor",
            "mt5.order_check",
            "mt5.order_send",
        ],
        
        "responsibilities": [
            "validate_executor_authorization",
            "extract_authorized_order",
            "validate_live_executor_flags",
            "delegate_to_live_executor",
            "return_complete_execution_result",
        ],
        
        "decision_generation": False,
        "decision_override": False,
        "technical_analysis": False,
        "fundamental_analysis": False,
        "hybrid_decision": False,
        "risk_management": False,
        "position_sizing": False,
        "mt5_order_check": False,
        "mt5_order_send": False,
        "order_placement": False,
        
        "bridges": [
            "executor",
            "live_executor",
        ],
    }


__all__ = [
    "connect_executor_to_live_executor",
    "execute_full_pipeline",
    "connector_info",
]


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":
    
    print("==============================================")
    print("BALLY FLOW EXECUTION PIPELINE CONNECTOR")
    print("==============================================")
    
    print("\nINFO:")
    print(connector_info())
    
    # Test with a mock executor result
    mock_executor_result = {
        "status": "READY",
        "executed": False,
        "authorized": True,
        "decision": "BUY",
        "order": {
            "symbol": "XAUUSD",
            "decision": "BUY",
            "order_type": "BUY",
            "volume": 0.01,
            "entry": 4700.0,
            "stop_loss": 4680.0,
            "take_profit": 4760.0,
            "magic_number": 20260817,
            "comment": "BALLY_TRADES_BOT",
        },
        "live_executor_allowed": True,
        "reason": "order validated and authorized",
    }
    
    mock_gate = {
        "gate": "PASS",
        "allowed": True,
    }
    
    print("\nTEST RESULT:")
    result = execute_full_pipeline(
        executor_result=mock_executor_result,
        gate=mock_gate,
    )
    
    print(result)
