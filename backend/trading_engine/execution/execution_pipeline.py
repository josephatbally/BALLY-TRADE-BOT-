"""
BALLY FLOW - Execution Pipeline
================================

AUTHORITATIVE ORCHESTRATION LAYER

Pipeline:

    TRADE PLAN
        ↓
    RISK MANAGER
        ↓
    RISK EXECUTION BRIDGE
        ↓
    POSITION CHECK
        ↓
    FINAL GATE
        ↓
    ORDER BUILDER
        ↓
    EXECUTOR
        ↓
    LIVE EXECUTOR
        ↓
    MT5

IMPORTANT
---------
This module coordinates existing modules.

It does NOT:

- generate BUY / SELL decisions
- perform technical analysis
- perform fundamental analysis
- calculate independent risk
- calculate independent position size
- create independent SL/TP
- override Risk Manager
- bypass Risk Execution Bridge
- bypass Position Check
- bypass Final Gate
- call MT5 order_send directly

Only live_executor.py owns MT5 order_check/order_send.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


NAME = "BALLY FLOW Execution Pipeline"
VERSION = "2.0.0"

SUPPORTED_SIGNALS = (
    "BUY",
    "SELL",
    "NO_TRADE",
)

MINIMUM_RR = 1.0
MAXIMUM_RR = 3.0


# ======================================================================
# BASIC HELPERS
# ======================================================================

def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, str):
        value = value.strip().lower()

        if value in {"true", "1", "yes", "pass", "ready", "allowed"}:
            return True

        if value in {"false", "0", "no", "block", "blocked"}:
            return False

    return bool(value)


def _safe_signal(value: Any) -> str:
    return str(value or "").upper().strip()


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _failure(
    status: str,
    reason: str,
    **extra: Any,
) -> Dict[str, Any]:

    result = {
        "status": status,
        "execution_allowed": False,
        "reason": reason,
    }

    result.update(extra)

    return result


def _get_first(
    source: Optional[Dict[str, Any]],
    *keys: str,
) -> Any:

    if not isinstance(source, dict):
        return None

    for key in keys:

        if key in source and source[key] is not None:
            return source[key]

    return None


# ======================================================================
# MODULE LOADING
# ======================================================================

def _load_symbol(
    module_name: str,
    function_name: str,
):
    """
    Dynamically load a pipeline component.

    Dynamic imports prevent unnecessary hard failures during
    isolated module testing.
    """

    import importlib

    module = importlib.import_module(module_name)

    function = getattr(module, function_name)

    return function


# ======================================================================
# TRADE PLAN → RISK MANAGER
# ======================================================================
def _run_risk_manager(
    trade_plan: Dict[str, Any],
    risk_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send the standardized Trade Plan into Risk Manager.

    Risk Manager remains authoritative for:

    - drawdown
    - SL
    - TP
    - RR
    - position sizing
    - margin
    - final risk authorization

    IMPORTANT INTEGRATION CONTRACT
    -------------------------------
    Structural levels required by the Take Profit Engine are exposed
    directly at the top level of the market_context passed to
    risk_manager.evaluate_risk().

    The original nested structural_context is also preserved so that
    downstream modules can continue to access the canonical context
    without breaking existing APIs.
    """

    # ==============================================================
    # 1. BASIC TRADE PLAN VALIDATION
    # ==============================================================

    if not isinstance(trade_plan, dict):
        return _failure(
            "BLOCKED",
            "trade_plan must be a dictionary",
        )

    context = (
        risk_context
        if isinstance(risk_context, dict)
        else {}
    )

    # ==============================================================
    # 2. EXTRACT DECISION
    # ==============================================================

    signal = _safe_signal(
        _get_first(
            trade_plan,
            "decision",
            "signal",
        )
    )

    if signal not in {"BUY", "SELL"}:
        return _failure(
            "BLOCKED",
            "trade plan does not contain an executable BUY/SELL decision",
            decision=signal,
        )

    # ==============================================================
    # 3. EXTRACT SYMBOL
    # ==============================================================

    symbol = _get_first(
        trade_plan,
        "symbol",
    )

    if not isinstance(symbol, str) or not symbol.strip():
        return _failure(
            "BLOCKED",
            "trade plan symbol is missing",
        )

    symbol = symbol.strip()

    # ==============================================================
    # 4. EXTRACT ENTRY
    # ==============================================================

    entry = _safe_float(
        _get_first(
            trade_plan,
            "entry",
            "entry_price",
        )
    )

    if entry is None or entry <= 0:
        return _failure(
            "BLOCKED",
            "trade plan entry is invalid",
        )

    # ==============================================================
    # 5. ACCOUNT INFORMATION
    # ==============================================================

    account_balance = _safe_float(
        _get_first(
            context,
            "account_balance",
            "balance",
        )
    )

    account_equity = _safe_float(
        _get_first(
            context,
            "account_equity",
            "equity",
        )
    )

    if account_balance is None:
        return _failure(
            "BLOCKED",
            "account balance is required by risk management",
        )

    if account_equity is None:
        return _failure(
            "BLOCKED",
            "account equity is required by risk management",
        )

    starting_balance = _safe_float(
        _get_first(
            context,
            "starting_balance",
        )
    )

    if starting_balance is None:
        starting_balance = account_balance

    starting_day_balance = _safe_float(
        _get_first(
            context,
            "starting_day_balance",
        )
    )

    if starting_day_balance is None:
        starting_day_balance = account_balance

    # ==============================================================
    # 6. RISK CONFIGURATION
    # ==============================================================

    base_risk_percent = _safe_float(
        _get_first(
            context,
            "base_risk_percent",
            "risk_percent",
        )
    )

    if base_risk_percent is None:
        base_risk_percent = 1.0

    preferred_lot = _get_first(
        context,
        "preferred_lot",
    )

    opportunity_score = _safe_float(
        _get_first(
            trade_plan,
            "opportunity_score",
            "opportunity_quality",
        )
    )

    if opportunity_score is None:
        opportunity_score = 0.0

    max_drawdown_percent = _safe_float(
        _get_first(
            context,
            "max_drawdown_percent",
        )
    )

    if max_drawdown_percent is None:
        max_drawdown_percent = 20.0

    max_daily_loss_percent = _safe_float(
        _get_first(
            context,
            "max_daily_loss_percent",
        )
    )

    if max_daily_loss_percent is None:
        max_daily_loss_percent = 5.0

    margin_safety_buffer_percent = _safe_float(
        _get_first(
            context,
            "margin_safety_buffer_percent",
        )
    )

    if margin_safety_buffer_percent is None:
        margin_safety_buffer_percent = 10.0

    # ==============================================================
    # 7. MARKET CONTEXT
    # ==============================================================

    raw_market_context = (
        trade_plan.get("market_context")
        or trade_plan.get("market_conditions")
        or {}
    )

    if not isinstance(raw_market_context, dict):
        raw_market_context = {}

    # ==============================================================
    # 8. STRUCTURAL CONTEXT
    # ==============================================================

    raw_structural_context = (
        trade_plan.get("structural_context")
        or trade_plan.get("structure")
        or {}
    )

    if not isinstance(raw_structural_context, dict):
        raw_structural_context = {}

    # ==============================================================
    # 9. BUILD RISK-MANAGER CONTEXT
    # ==============================================================
    #
    # THIS IS THE IMPORTANT REPAIR.
    #
    # The Take Profit Engine searches directly for keys such as:
    #
    #   liquidity_pool_high
    #   liquidity_high
    #   previous_high
    #   swing_high
    #   order_block_high
    #   supply_high
    #   target_high
    #
    # and for SELL:
    #
    #   liquidity_pool_low
    #   liquidity_low
    #   previous_low
    #   swing_low
    #   order_block_low
    #   demand_low
    #   target_low
    #
    # Therefore structural_context cannot remain only under:
    #
    #   context["structural_context"]
    #
    # It must also be exposed at the top level.
    #
    # Preserve the original nested context as well.

    risk_market_context = {}

    # --------------------------------------------------------------
    # First preserve ordinary market context.
    # --------------------------------------------------------------

    risk_market_context.update(
        raw_market_context
    )

    # --------------------------------------------------------------
    # Then expose structural levels directly.
    #
    # Structural context is deliberately applied after ordinary
    # market context so explicitly supplied structural values remain
    # authoritative for structural SL/TP calculations.
    # --------------------------------------------------------------

    risk_market_context.update(
        raw_structural_context
    )

    # --------------------------------------------------------------
    # Preserve structured/nested representations for compatibility.
    # --------------------------------------------------------------

    risk_market_context["market_context"] = (
        raw_market_context
    )

    risk_market_context["structural_context"] = (
        raw_structural_context
    )

    risk_market_context["trade_plan"] = trade_plan

    # ==============================================================
    # 10. SYMBOL INFORMATION
    # ==============================================================

        # --------------------------------------------------------------
    # Broker symbol specification
    # --------------------------------------------------------------
    #
    # Risk Manager / Position Sizing requires the live broker
    # specification for the symbol:
    #
    #   - volume_min
    #   - volume_max
    #   - volume_step
    #   - trade_contract_size
    #   - point
    #   - digits
    #
    # Prefer explicitly supplied symbol_info, but if it is absent,
    # obtain it from the existing centralized MT5 market-data layer.
    #
    # Do NOT fabricate broker specifications.
    # Fail closed if MT5 cannot provide them.
    # --------------------------------------------------------------

    symbol_info = _get_first(
        context,
        "symbol_info",
    )

    if symbol_info is None:

        try:

            get_symbol_info = _load_symbol(
                "backend.trading_engine.market_data.mt5_connection",
                "get_symbol_info",
            )

            symbol_info = get_symbol_info(
                symbol.strip()
            )

        except Exception as exc:

            return _failure(
                "BLOCKED",
                f"unable to obtain broker symbol specification: {exc}",
                symbol_info_required=True,
                symbol=symbol.strip(),
            )

    if symbol_info is None:

        return _failure(
            "BLOCKED",
            f"broker symbol specification unavailable: {symbol.strip()}",
            symbol_info_required=True,
            symbol=symbol.strip(),
        )
    # ==============================================================
    # 11. LOAD AUTHORITATIVE RISK MANAGER
    # ==============================================================

    try:

        evaluate_risk = _load_symbol(
            "backend.trading_engine.risk.risk_manager",
            "evaluate_risk",
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"risk manager loading failed: {exc}",
            risk_manager_exception=True,
        )

    # ==============================================================
    # 12. CALL AUTHORITATIVE RISK MANAGER
    # ==============================================================

    try:

        risk_result = evaluate_risk(
            signal=signal,
            symbol=symbol,
            entry=entry,

            market_context=risk_market_context,

            account_balance=account_balance,
            account_equity=account_equity,

            base_risk_percent=base_risk_percent,

            preferred_lot=preferred_lot,

            opportunity_score=opportunity_score,

            starting_balance=starting_balance,
            starting_day_balance=starting_day_balance,

            max_drawdown_percent=max_drawdown_percent,
            max_daily_loss_percent=max_daily_loss_percent,

            margin_safety_buffer_percent=(
                margin_safety_buffer_percent
            ),

            symbol_info=symbol_info,
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"risk manager execution failed: {exc}",
            risk_manager_exception=True,
        )

    # ==============================================================
    # 13. VALIDATE RISK-MANAGER OUTPUT
    # ==============================================================

    if not isinstance(risk_result, dict):

        return _failure(
            "BLOCKED",
            "risk manager returned invalid output",
        )

    # ==============================================================
    # 14. RISK AUTHORIZATION
    # ==============================================================

    risk_authorized = _safe_bool(
        risk_result.get("risk_authorized"),
        False,
    )

    if not risk_authorized:

        return {
            "status": "BLOCKED",
            "execution_allowed": False,

            "risk_authorized": False,

            "decision": signal,
            "symbol": symbol,

            "reason": risk_result.get(
                "reason",
                "risk manager did not authorize trade",
            ),

            "risk_result": risk_result,
        }

    # ==============================================================
    # 15. RISK AUTHORIZED
    # ==============================================================

    return {
        "status": "READY",

        "execution_allowed": True,

        "risk_authorized": True,

        "decision": signal,

        "symbol": symbol,

        "risk_result": risk_result,
    }

# ======================================================================
# RISK MANAGER → RISK EXECUTION BRIDGE
# ======================================================================

def _run_risk_bridge(
    signal: str,
    risk_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Pass Risk Manager authorization through the Risk Execution Bridge.
    """

    try:

        authorize_for_execution = _load_symbol(
            "backend.trading_engine.risk.risk_execution_bridge",
            "authorize_for_execution",
        )

        bridge_result = authorize_for_execution(
            signal,
            risk_result,
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"risk execution bridge failed: {exc}",
            bridge_exception=True,
        )

    if not isinstance(bridge_result, dict):
        return _failure(
            "BLOCKED",
            "risk execution bridge returned invalid output",
        )

    if not _safe_bool(
        bridge_result.get("execution_allowed"),
        False,
    ):
        return {
            "status": "BLOCKED",
            "execution_allowed": False,
            "reason": bridge_result.get(
                "reason",
                "risk execution bridge did not authorize execution",
            ),
            "bridge_result": bridge_result,
        }

    return {
        "status": "READY",
        "execution_allowed": True,
        "bridge_result": bridge_result,
    }


# ======================================================================
# POSITION CHECK
# ======================================================================

def _run_position_check(
    execution_order: Dict[str, Any],
    position_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Consume the already-computed position check when supplied.

    The pipeline never invents position authorization.
    """

    if isinstance(position_result, dict):

        allowed = _safe_bool(
            position_result.get(
                "position_allowed",
                position_result.get(
                    "allowed",
                    position_result.get("authorized"),
                ),
            ),
            False,
        )

        if not allowed:

            return _failure(
                "BLOCKED",
                position_result.get(
                    "reason",
                    "position check blocked execution",
                ),
                position_result=position_result,
            )

        return {
            "status": "READY",
            "position_allowed": True,
            "position_result": position_result,
        }

    # --------------------------------------------------------------
    # If no precomputed result exists, use PositionCheck.
    # --------------------------------------------------------------

    symbol = execution_order.get("symbol")
    signal = execution_order.get("decision")

    positions = []

    try:

        import MetaTrader5 as mt5

        mt5_positions = mt5.positions_get()

        if mt5_positions is not None:
            positions = list(mt5_positions)

    except Exception:
        positions = []

    try:

        check_function = _load_symbol(
            "backend.trading_engine.execution.position_check",
            "position_allowed",
        )

        allowed = check_function(
            symbol,
            signal,
            positions,
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"position check failed: {exc}",
        )

    if not _safe_bool(allowed, False):

        return _failure(
            "BLOCKED",
            "existing position or position policy blocked execution",
        )

    return {
        "status": "READY",
        "position_allowed": True,
        "position_result": {
            "allowed": True,
        },
    }


# ======================================================================
# FINAL GATE
# ======================================================================

def _run_final_gate(
    trade_plan: Dict[str, Any],
    risk_result: Dict[str, Any],
    position_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Final authorization before order construction.
    """

    decision = _safe_signal(
        _get_first(
            trade_plan,
            "decision",
            "signal",
        )
    )

    # --------------------------------------------------------------
    # Prefer existing Final Gate implementation.
    # --------------------------------------------------------------

    try:

        evaluate_final_gate = _load_symbol(
            "backend.trading_engine.execution.final_gate",
            "evaluate_final_gate",
        )

        result = evaluate_final_gate(
            decision=decision,
            risk=risk_result,
            position=position_result,
            trade_plan=trade_plan,
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"final gate failed: {exc}",
        )

    if not isinstance(result, dict):
        return _failure(
            "BLOCKED",
            "final gate returned invalid output",
        )

    passed = (
        result.get("gate") == "PASS"
        and result.get("allowed") is True
    )

    if not passed:

        return {
            "status": "BLOCKED",
            "execution_allowed": False,
            "reason": result.get(
                "reason",
                "final execution gate blocked trade",
            ),
            "gate_result": result,
        }

    return {
        "status": "READY",
        "execution_allowed": True,
        "gate_result": result,
    }


# ======================================================================
# ORDER BUILDER
# ======================================================================

def _run_order_builder(
    final_gate_result: Dict[str, Any],
    trade_plan: Dict[str, Any],
    symbol_info: Any = None,
) -> Dict[str, Any]:
    """
    Build standardized order only after Final Gate PASS.

    Order Builder owns order specification.
    """

    gate_result = final_gate_result.get(
        "gate_result",
        final_gate_result,
    )

    decision = _safe_signal(
        _get_first(
            trade_plan,
            "decision",
            "signal",
        )
    )

    risk_result = trade_plan.get(
        "_risk_result"
    )

    # --------------------------------------------------------------
    # Risk data should already be attached by execute_pipeline().
    # --------------------------------------------------------------

    if risk_result is None:
        return _failure(
            "BLOCKED",
            "risk result missing before order builder",
        )

    try:

        build_order = _load_symbol(
            "backend.trading_engine.execution.order_builder",
            "build_order",
        )

        order = build_order(
            decision,
            risk_result.get(
                "trade_plan",
                risk_result,
            ),
            gate_result,
        )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"order builder failed: {exc}",
        )

    if not isinstance(order, dict):
        return _failure(
            "BLOCKED",
            "order builder returned invalid output",
        )

    # --------------------------------------------------------------
    # Broker symbol information is carried forward but never used
    # here to override risk constraints.
    # --------------------------------------------------------------

    if symbol_info is not None:
        order["_symbol_info"] = symbol_info

    return {
        "status": "READY",
        "execution_allowed": True,
        "order": order,
    }


# ======================================================================
# EXECUTOR
# ======================================================================

def _run_executor(
    approved_order: Dict[str, Any],
    gate_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send approved order to Executor.

    Executor decides whether it can forward to Live Executor.
    """

    try:

        execute_order = _load_symbol(
            "backend.trading_engine.execution.executor",
            "execute_order",
        )

        result = execute_order(
            approved_order,
            gate=gate_result,
            delegate=True,
        )

    except TypeError:

        # Compatibility with Executor implementations that accept
        # the gate as an optional argument.
        try:

            result = execute_order(
                approved_order,
                gate=gate_result,
            )

        except Exception as exc:

            return _failure(
                "BLOCKED",
                f"executor failed: {exc}",
            )

    except Exception as exc:

        return _failure(
            "BLOCKED",
            f"executor failed: {exc}",
        )

    if not isinstance(result, dict):
        return _failure(
            "BLOCKED",
            "executor returned invalid output",
        )

    return {
        "status": result.get(
            "status",
            "READY",
        ),
        "execution_allowed": _safe_bool(
            result.get(
                "authorized",
                result.get(
                    "execution_allowed",
                    False,
                ),
            ),
            False,
        ),
        "executor_result": result,
    }


# ======================================================================
# COMPLETE RISK → EXECUTION PIPELINE
# ======================================================================

def execute_pipeline(
    trade_plan: Dict[str, Any],
    symbol_info: Any = None,
    margin_result: Optional[Dict[str, Any]] = None,
    position_result: Optional[Dict[str, Any]] = None,
    execute_live: bool = False,
    max_spread_points: Optional[float] = None,
    max_price_deviation_points: Optional[float] = None,
    reject_existing_position: bool = True,
    risk_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Complete BALLY FLOW execution orchestration.

    Authoritative sequence:

        Trade Plan
            ↓
        Risk Manager
            ↓
        Risk Execution Bridge
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
        MT5

    The execute_live parameter is passed downstream only.
    It does not independently authorize live trading.
    """

    # ==============================================================
    # 1. TRADE PLAN VALIDATION
    # ==============================================================

    if not isinstance(trade_plan, dict):

        return _failure(
            "BLOCKED",
            "trade_plan must be a dictionary",
        )

    decision = _safe_signal(
        _get_first(
            trade_plan,
            "decision",
            "signal",
        )
    )

    if decision not in SUPPORTED_SIGNALS:

        return _failure(
            "BLOCKED",
            "invalid trade-plan decision",
            decision=decision,
        )

    if decision == "NO_TRADE":

        return _failure(
            "BLOCKED",
            "NO_TRADE cannot enter risk or execution pipeline",
            decision=decision,
        )

    # ==============================================================
    # 2. RISK MANAGER
    # ==============================================================

    risk_stage = _run_risk_manager(
        trade_plan=trade_plan,
        risk_context=risk_context,
    )

    if not risk_stage.get("execution_allowed"):

        return {
            "status": "BLOCKED",
            "stage": "risk_manager",
            "decision": decision,
            "risk": risk_stage,
        }

    risk_result = risk_stage["risk_result"]

    # ==============================================================
    # 3. RISK EXECUTION BRIDGE
    # ==============================================================

    bridge_stage = _run_risk_bridge(
        signal=decision,
        risk_result=risk_result,
    )

    if not bridge_stage.get("execution_allowed"):

        return {
            "status": "BLOCKED",
            "stage": "risk_execution_bridge",
            "decision": decision,
            "risk": risk_result,
            "bridge": bridge_stage,
        }

    bridge_result = bridge_stage["bridge_result"]

    # ==============================================================
    # 4. EXTRACT EXECUTION ORDER
    # ==============================================================

    execution_order = bridge_result.get(
        "execution_order"
    )

    if not isinstance(execution_order, dict):

        return _failure(
            "BLOCKED",
            "risk execution bridge did not produce execution_order",
            stage="risk_execution_bridge",
            risk=risk_result,
            bridge=bridge_result,
        )

    # ==============================================================
    # 5. PRESERVE RISK OUTPUT FOR ORDER BUILDER
    # ==============================================================

    order_trade_plan = dict(trade_plan)

    order_trade_plan["_risk_result"] = risk_result

    # ==============================================================
    # 6. POSITION CHECK
    # ==============================================================

    if reject_existing_position:

        position_stage = _run_position_check(
            execution_order=execution_order,
            position_result=position_result,
        )

        if not position_stage.get("position_allowed"):

            return {
                "status": "BLOCKED",
                "stage": "position_check",
                "decision": decision,
                "risk": risk_result,
                "bridge": bridge_result,
                "position": position_stage,
            }

    else:

        position_stage = {
            "status": "READY",
            "position_allowed": True,
            "position_result": {
                "allowed": True,
                "policy_disabled": True,
            },
        }

    # ==============================================================
    # 7. FINAL GATE
    # ==============================================================

    final_gate_stage = _run_final_gate(
        trade_plan=order_trade_plan,
        risk_result=risk_result,
        position_result=position_stage.get(
            "position_result",
            position_stage,
        ),
    )

    if not final_gate_stage.get("execution_allowed"):

        return {
            "status": "BLOCKED",
            "stage": "final_gate",
            "decision": decision,
            "risk": risk_result,
            "bridge": bridge_result,
            "position": position_stage,
            "final_gate": final_gate_stage,
        }

    # ==============================================================
    # 8. ORDER BUILDER
    # ==============================================================

    builder_stage = _run_order_builder(
        final_gate_result=final_gate_stage,
        trade_plan=order_trade_plan,
        symbol_info=symbol_info,
    )

    if not builder_stage.get("execution_allowed"):

        return {
            "status": "BLOCKED",
            "stage": "order_builder",
            "decision": decision,
            "risk": risk_result,
            "bridge": bridge_result,
            "position": position_stage,
            "final_gate": final_gate_stage,
            "order_builder": builder_stage,
        }

    approved_order = builder_stage["order"]

    # ==============================================================
    # 9. EXECUTOR
    # ==============================================================

    executor_stage = _run_executor(
        approved_order=approved_order,
        gate_result=final_gate_stage.get(
            "gate_result",
            final_gate_stage,
        ),
    )

    # ==============================================================
    # 10. FINAL PIPELINE RESULT
    # ==============================================================

    return {
        "status": executor_stage.get(
            "status",
            "READY",
        ),

        "pipeline": "BALLY_FLOW_EXECUTION_PIPELINE",

        "decision": decision,

        "execution_allowed": executor_stage.get(
            "execution_allowed",
            False,
        ),

        "live_requested": bool(execute_live),

        "risk": risk_result,

        "risk_execution_bridge": bridge_result,

        "position_check": position_stage,

        "final_gate": final_gate_stage,

        "order_builder": builder_stage,

        "order": approved_order,

        "executor": executor_stage,

        "execution_stages": [
            "trade_plan",
            "risk_manager",
            "risk_execution_bridge",
            "position_check",
            "final_gate",
            "order_builder",
            "executor",
            "live_executor",
            "mt5.order_check",
            "mt5.order_send",
        ],
    }


# ======================================================================
# HIGH-LEVEL TRADE PIPELINE
# ======================================================================

def execute_trade_pipeline(
    trade_plan: Dict[str, Any],
    *,
    symbol_info: Any = None,
    risk_context: Optional[Dict[str, Any]] = None,
    position_result: Optional[Dict[str, Any]] = None,
    execute_live: bool = False,
    reject_existing_position: bool = True,
) -> Dict[str, Any]:
    """
    High-level public API.

    Example:

        execute_trade_pipeline(
            trade_plan,
            risk_context={
                "account_balance": ...,
                "account_equity": ...,
                "starting_balance": ...,
                "starting_day_balance": ...,
                "symbol_info": ...,
                "base_risk_percent": 1.0,
                "preferred_lot": None,
            },
        )
    """

    return execute_pipeline(
        trade_plan=trade_plan,
        symbol_info=symbol_info,
        position_result=position_result,
        execute_live=execute_live,
        reject_existing_position=reject_existing_position,
        risk_context=risk_context,
    )


# ======================================================================
# INFORMATION API
# ======================================================================

def execution_pipeline_info() -> Dict[str, Any]:
    """
    Return authoritative execution pipeline architecture.
    """

    return {
        "name": NAME,
        "version": VERSION,
        "status": "READY",

        "signals": list(SUPPORTED_SIGNALS),

        "pipeline": [
            "trade_plan",
            "risk_manager",
            "risk_execution_bridge",
            "position_check",
            "final_gate",
            "order_builder",
            "executor",
            "live_executor",
            "mt5.order_check",
            "mt5.order_send",
        ],

        "risk_layer": [
            "drawdown",
            "stop_loss",
            "take_profit",
            "position_sizing",
            "margin",
            "risk_manager",
        ],

        "minimum_rr": MINIMUM_RR,
        "maximum_rr": MAXIMUM_RR,

        "decision_authority": "upstream_decision_engine",

        "risk_authority": "risk_manager.py",

        "bridge_authority": "risk_execution_bridge.py",

        "final_gate_required": True,

        "order_builder_required": True,

        "order_check_owner": "live_executor.py",

        "order_send_owner": "live_executor.py",

        "direct_mt5_order_send": False,

        "decision_generation": False,

        "decision_override": False,

        "technical_analysis": False,

        "fundamental_analysis": False,

        "hybrid_decision": False,

        "independent_risk_calculation": False,

        "independent_position_sizing": False,

        "independent_sl_calculation": False,

        "independent_tp_calculation": False,

        "risk_management": True,

        "execution": True,

        "live_execution_authority": "live_executor.py",
    }


def execution_status() -> Dict[str, Any]:
    """
    Compact execution status.
    """

    return {
        "status": "READY",
        "pipeline_ready": True,
        "risk_manager_required": True,
        "risk_execution_bridge_required": True,
        "position_check_required": True,
        "final_gate_required": True,
        "order_builder_required": True,
        "executor_required": True,
        "live_executor_required": True,
        "mt5_order_check_owner": "live_executor.py",
        "mt5_order_send_owner": "live_executor.py",
        "maximum_rr": MAXIMUM_RR,
    }


# ======================================================================
# SELF TEST
# ======================================================================

if __name__ == "__main__":

    print("==============================================")
    print("BALLY FLOW EXECUTION PIPELINE")
    print("==============================================")

    print("\nPIPELINE INFO:")
    print(execution_pipeline_info())

    print("\nSTATUS:")
    print(execution_status())