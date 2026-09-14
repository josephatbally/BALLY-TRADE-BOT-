"""
BALLY FLOW - Application Entry Point

RESPONSIBILITIES
----------------
main.py is the top-level application orchestrator.

It is responsible for:

    - starting BALLY FLOW
    - validating the operating mode
    - exposing the two-mode architecture
    - coordinating market scanning
    - providing application status
    - providing single-market and all-market scan interfaces
    - keeping application-level orchestration separate from trading logic

SUPPORTED MODES
---------------

BALLY FLOW has exactly TWO trading modes:

    TECHNICAL
    HYBRID

These modes are mutually exclusive.

TECHNICAL
---------
Technical mode uses:

    H4 -> H1 -> M15
    Market Data
    Market Analytics
    Technical Engine
    Technical Confluence
    Decision Engine
    Risk Management
    Execution

Technical decisions ARE executable.

HYBRID
------
Hybrid mode is a separate pipeline.

It will combine:

    Technical Analysis
    +
    Fundamental Analysis

and then pass the resulting decision downstream.

IMPORTANT
---------

main.py MUST NOT:

    - calculate technical indicators
    - calculate SMC
    - calculate confluence
    - create BUY / SELL decisions
    - calculate position size
    - calculate risk
    - place MT5 orders

Those responsibilities belong to their dedicated layers.

CURRENT BUILD STAGE
-------------------

The Decision Engine is connected through the application
orchestration boundary.

The application coordinates:

    MT5
      |
      v
    Market Data
      |
      v
    Scanner
      |
      v
    Technical / Hybrid Analysis
      |
      v
    Decision Engine
      |
      v
    Trade Plan
      |
      v
    Risk Management
      |
      v
    Execution Pipeline

main.py does not implement any of those subsystem decisions
or calculations itself.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


from backend.trading_engine.scanner import (
    scan_market,
    scan_all_markets,
    scanner_info,
)
from backend.trading_engine.modes.mode_controller import (
    ModeController,
    TradingMode,
)
from backend.trading_engine.market_data.mt5_connection import (
    initialize_mt5,
    is_mt5_connected,
    get_symbol_tick,
    get_account_info,
    mt5_status,
)
from backend.trading_engine.engine import (
    analyze_live_market,
)
from backend.trading_engine.hybrid.hybrid_engine import (
    analyze_hybrid_market,
)
from backend.trading_engine.trade_plan import (
    create_trade_plan,
)
from backend.trading_engine.execution.execution_pipeline import (
    execute_pipeline,
)

try:
    from backend import trading_config
except ImportError:
    import trading_config


# =====================================================================
# APPLICATION VERSION
# =====================================================================

APP_NAME = "BALLY FLOW"

APP_VERSION = "1.0.0"


# =====================================================================
# APPLICATION
# =====================================================================

class BallyFlowApplication:
    """
    Top-level BALLY FLOW application orchestrator.

    This class does not perform trading decisions.

    It coordinates the already separated subsystems.
    """

    def __init__(
        self,
        mode: TradingMode = TradingMode.TECHNICAL,
    ) -> None:

        self._mode_controller = ModeController(
            mode=mode
        )

        self._running = False

    # -----------------------------------------------------------------
    # APPLICATION STATE
    # -----------------------------------------------------------------

    @property
    def mode(self) -> TradingMode:
        """
        Return the currently selected trading mode.
        """

        return self._mode_controller.mode

        self._mode_controller = ModeController(
            mode=mode
        )

        self._running = False
        self._auto_trading_enabled: bool = getattr(trading_config, "AUTO_TRADING_ENABLED", False)

    @property
    def running(self) -> bool:
        """
        Return whether the application is running.
        """

        return self._running

    @property
    def auto_trading_enabled(self) -> bool:
        """
        Return whether automatic live order execution is enabled.
        """
        return self._auto_trading_enabled

    def set_auto_trading(self, enabled: bool) -> bool:
        """
        Enable or disable live MT5 order execution.
        """
        self._auto_trading_enabled = bool(enabled)
        return self._auto_trading_enabled

    # -----------------------------------------------------------------
    # MODE
    # -----------------------------------------------------------------

    @property
    def auto_trading_enabled(self) -> bool:
        """Return whether automatic live order execution is enabled."""
        return self._auto_trading_enabled

    def set_auto_trading(self, enabled: bool) -> bool:
        """Enable or disable live MT5 order execution."""
        self._auto_trading_enabled = bool(enabled)
        return self._auto_trading_enabled

    def set_mode(
        self,
        mode: TradingMode,
    ) -> TradingMode:
        """
        Change the active trading mode.

        Only the two approved modes are accepted:

            TECHNICAL
            HYBRID

        ModeController enforces the actual validation.
        """

        return self._mode_controller.set_mode(
            mode
        )

    def is_technical(self) -> bool:
        """
        Return True when Technical mode is active.
        """

        return self._mode_controller.is_technical()

    def is_hybrid(self) -> bool:
        """
        Return True when Hybrid mode is active.
        """

        return self._mode_controller.is_hybrid()

    # -----------------------------------------------------------------
    # START / STOP
    # -----------------------------------------------------------------

    def start(self) -> Dict[str, Any]:
        """
        Start the BALLY FLOW application.

        Starting the application does not automatically execute
        trades.

        MT5 is initialized through the shared MT5 connection.
        """

        if not is_mt5_connected():
            initialize_mt5()

        self._running = True

        return self.status()

    def stop(self) -> Dict[str, Any]:
        """
        Stop the application orchestration layer.

        This does not close positions and does not send MT5 orders.
        """

        self._running = False

        return self.status()

    # -----------------------------------------------------------------
    # STATUS
    # -----------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """
        Return application status.
        """

        return {
            "status": "READY" if self._running else "STOPPED",
            "application": APP_NAME,
            "version": APP_VERSION,
            "running": self._running,
            "mode": self.mode.value,
            "auto_trading_enabled": self._auto_trading_enabled,
            "technical_enabled": self.is_technical(),
            "hybrid_enabled": self.is_hybrid(),
            "scanner": scanner_info(),
        }
    def status(self) -> Dict[str, Any]:
        return {
            "application": APP_NAME,
            "version": APP_VERSION,
            "running": self.running,
            "mode": self.mode.value,
            "auto_trading_enabled": self._auto_trading_enabled,  # Add this line
            "mt5": mt5_status(),
        }

    # -----------------------------------------------------------------
    # SINGLE MARKET
    # -----------------------------------------------------------------

    def _build_upstream_trade_plan(
        self,
        market: str,
        decision: str,
        analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the upstream Trade Plan after an authoritative
        BUY/SELL decision has been produced.

        This method does NOT calculate:

            - stop loss
            - take profit
            - risk
            - position size
            - execution authorization

        Those responsibilities remain downstream.

        The entry price is obtained from the authoritative MT5
        tick source:

            BUY  -> Ask
            SELL -> Bid
        """

        signal = str(
            decision or ""
        ).strip().upper()

        if signal not in ("BUY", "SELL"):
            raise ValueError(
                f"Cannot build a trade plan for decision: {signal!r}"
            )

        tick = get_symbol_tick(
            market
        )

        if tick is None:
            raise RuntimeError(
                f"No live MT5 tick available for {market}."
            )

        bid = getattr(
            tick,
            "bid",
            None,
        )

        ask = getattr(
            tick,
            "ask",
            None,
        )

        try:
            bid = float(bid)
            ask = float(ask)
        except (TypeError, ValueError):
            raise RuntimeError(
                f"Invalid live MT5 bid/ask for {market}: "
                f"bid={bid!r}, ask={ask!r}"
            )

        if bid <= 0 or ask <= 0:
            raise RuntimeError(
                f"Invalid live MT5 bid/ask for {market}: "
                f"bid={bid}, ask={ask}"
            )

        entry = (
            ask
            if signal == "BUY"
            else bid
        )

        market_context = analysis.get(
            "market_context"
        )

        if not isinstance(
            market_context,
            dict,
        ):
            market_context = analysis.get(
                "market_conditions"
            )

        if not isinstance(
            market_context,
            dict,
        ):
            market_context = {}

        structural_context = analysis.get(
            "structural_context"
        )

        if not isinstance(
            structural_context,
            dict,
        ):
            structural_context = analysis.get(
                "structure"
            )

        if not isinstance(
            structural_context,
            dict,
        ):
            structural_context = analysis.get(
                "technical_analysis"
            )

        if not isinstance(
            structural_context,
            dict,
        ):
            structural_context = {}

        opportunity_score = analysis.get(
            "opportunity_score"
        )

        if opportunity_score is None:
            opportunity_score = analysis.get(
                "enhanced_quality_score"
            )

        if opportunity_score is None:
            opportunity_score = analysis.get(
                "core_confluence_score"
            )

        trade_plan = create_trade_plan(
            decision=signal,
            symbol=market,
            entry=entry,
            market_context=market_context,
            structural_context=structural_context,
            opportunity_score=opportunity_score,
            timeframe="M15",
            metadata={
                "application": APP_NAME,
                "mode": self.mode.value,
                "source": "decision_engine",
                "decision": signal,
                "bid": bid,
                "ask": ask,
            },
        )

        if not isinstance(
            trade_plan,
            dict,
        ):
            raise RuntimeError(
                "Trade Plan builder returned an invalid object."
            )

        if trade_plan.get("valid") is not True:
            raise RuntimeError(
                "Trade Plan validation failed."
            )

        if str(
            trade_plan.get("decision", "")
        ).upper() != signal:
            raise RuntimeError(
                "Trade Plan decision does not match "
                "the authoritative Decision Engine decision."
            )

        return trade_plan

    def _get_risk_context(self):
        """
        Build dynamic account context for downstream risk management.

        Account information comes from the shared MT5 connection layer.
        This method does not calculate risk, position size, SL, TP, or
        execution permissions.
        """

        try:
            account = get_account_info()
        except Exception as exc:
            return {
                "status": "BLOCKED",
                "account_available": False,
                "reason": f"MT5 account information unavailable: {exc}",
            }

        if account is None:
            return {
                "status": "BLOCKED",
                "account_available": False,
                "reason": "MT5 account information unavailable",
            }

        balance = getattr(account, "balance", None)
        equity = getattr(account, "equity", None)
        margin_free = getattr(account, "margin_free", None)

        try:
            balance = float(balance)
        except (TypeError, ValueError):
            balance = None

        try:
            equity = float(equity)
        except (TypeError, ValueError):
            equity = None

        try:
            margin_free = float(margin_free)
        except (TypeError, ValueError):
            margin_free = None

        if balance is None or balance <= 0:
            return {
                "status": "BLOCKED",
                "account_available": False,
                "reason": "MT5 account balance is unavailable or invalid",
            }

        if equity is None or equity <= 0:
            return {
                "status": "BLOCKED",
                "account_available": False,
                "reason": "MT5 account equity is unavailable or invalid",
            }

        return {
            "status": "READY",
            "account_available": True,
            "account_balance": balance,
            "account_equity": equity,
            "margin_free": margin_free,
        }

    def _run_pipeline(
        self,
        market: str,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run one BALLY FLOW market through the application pipeline.

        Scanner
            -> Technical / Hybrid Analysis
            -> Decision Engine
            -> Trade Plan
            -> Risk
            -> Execution Pipeline

        Live order submission remains disabled here.
        """

        if not self._running:
            self.start()

        logical_market = str(
            market
        ).strip().upper()

        # -----------------------------------------------------------
        # Scanner readiness boundary.
        # -----------------------------------------------------------

        scan_kwargs: Dict[str, Any] = {}

        if count is not None:
            scan_kwargs["count"] = count

        scan_result = scan_market(
            logical_market,
            **scan_kwargs,
        )

        if not isinstance(
            scan_result,
            dict,
        ):
            raise RuntimeError(
                "Scanner returned an invalid result."
            )

        if scan_result.get("status") not in (
            "READY",
            "PARTIAL",
        ):
            return {
                "status": "NO_TRADE",
                "application": APP_NAME,
                "version": APP_VERSION,
                "mode": self.mode.value,
                "market": logical_market,
                "scan": scan_result,
                "decision": "NO_TRADE",
                "signal": "NO_TRADE",
                "reason": "Market scanner is not ready.",
                "trade_plan": None,
                "execution": None,
            }

        # -----------------------------------------------------------
        # TECHNICAL MODE
        # -----------------------------------------------------------

        if self.is_technical():

            analysis = analyze_live_market(
                logical_market
            )

            if not isinstance(
                analysis,
                dict,
            ):
                raise RuntimeError(
                    "Technical Engine returned an invalid result."
                )

            decision = str(
                analysis.get(
                    "decision",
                    analysis.get(
                        "signal",
                        "NO_TRADE",
                    ),
                )
                or "NO_TRADE"
            ).strip().upper()

            if decision not in (
                "BUY",
                "SELL",
            ):
                return {
                    "status": "NO_TRADE",
                    "application": APP_NAME,
                    "version": APP_VERSION,
                    "mode": self.mode.value,
                    "market": logical_market,
                    "scan": scan_result,
                    "analysis": analysis,
                    "decision": "NO_TRADE",
                    "signal": decision,
                    "reason": analysis.get(
                        "reason",
                        analysis.get(
                            "rejection_reason",
                            "Decision Engine returned NO_TRADE.",
                        ),
                    ),
                    "trade_plan": None,
                    "execution": None,
                }

            trade_plan = self._build_upstream_trade_plan(
                market=logical_market,
                decision=decision,
                analysis=analysis,
            )

            risk_context = self._get_risk_context()
            execution = execute_pipeline(
                trade_plan=trade_plan,
                risk_context=risk_context,
                execute_live=self._auto_trading_enabled,
            )


            return {
                "status": (
                    "READY"
                    if isinstance(execution, dict)
                    else "ERROR"
                ),
                "application": APP_NAME,
                "version": APP_VERSION,
                "mode": self.mode.value,
                "market": logical_market,
                "scan": scan_result,
                "analysis": analysis,
                "decision": decision,
                "signal": decision,
                "trade_plan": trade_plan,
                "execution": execution,
            }

        # -----------------------------------------------------------
        # HYBRID MODE
        # -----------------------------------------------------------

        if self.is_hybrid():

            technical_result = analyze_live_market(
                logical_market
            )

            if not isinstance(
                technical_result,
                dict,
            ):
                raise RuntimeError(
                    "Technical Engine returned an invalid result."
                )

            hybrid_result = analyze_hybrid_market(
                symbol=logical_market,
                technical_result=technical_result,
            )

            if not isinstance(
                hybrid_result,
                dict,
            ):
                raise RuntimeError(
                    "Hybrid Engine returned an invalid result."
                )

            decision = str(
                hybrid_result.get(
                    "hybrid_signal",
                    hybrid_result.get(
                        "decision",
                        hybrid_result.get(
                            "signal",
                            "NO_TRADE",
                        ),
                    ),
                )
                or "NO_TRADE"
            ).strip().upper()

            if decision not in (
                "BUY",
                "SELL",
            ):
                return {
                    "status": "NO_TRADE",
                    "application": APP_NAME,
                    "version": APP_VERSION,
                    "mode": self.mode.value,
                    "market": logical_market,
                    "scan": scan_result,
                    "technical_analysis": technical_result,
                    "analysis": hybrid_result,
                    "decision": "NO_TRADE",
                    "signal": decision,
                    "reason": hybrid_result.get(
                        "reason",
                        "Hybrid Engine returned NO_TRADE.",
                    ),
                    "trade_plan": None,
                    "execution": None,
                }

            # Hybrid-specific fields remain authoritative in the
            # hybrid result. Technical analysis is retained as the
            # structural context required downstream.
            plan_context: Dict[str, Any] = dict(
                hybrid_result
            )

            plan_context["technical_analysis"] = (
                technical_result.get(
                    "technical_analysis",
                    technical_result,
                )
            )

            if "enhanced_quality_score" not in plan_context:
                plan_context["enhanced_quality_score"] = (
                    technical_result.get(
                        "enhanced_quality_score"
                    )
                )

            if "core_confluence_score" not in plan_context:
                plan_context["core_confluence_score"] = (
                    technical_result.get(
                        "core_confluence_score"
                    )
                )

            trade_plan = self._build_upstream_trade_plan(
                market=logical_market,
                decision=decision,
                analysis=plan_context,
            )

            risk_context = self._get_risk_context()

            execution = execute_pipeline(
                trade_plan=trade_plan,
                risk_context=risk_context,
                execute_live=self._auto_trading_enabled,
            )

            return {
                "status": (
                    "READY"
                    if isinstance(execution, dict)
                    else "ERROR"
                ),
                "application": APP_NAME,
                "version": APP_VERSION,
                "mode": self.mode.value,
                "market": logical_market,
                "scan": scan_result,
                "technical_analysis": technical_result,
                "analysis": hybrid_result,
                "decision": decision,
                "signal": decision,
                "trade_plan": trade_plan,
                "execution": execution,
            }

        raise RuntimeError(
            f"Unsupported BALLY FLOW mode: {self.mode.value}"
        )

    def scan_market(
        self,
        market: str,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run one market through the complete BALLY FLOW
        application pipeline.
        """

        return self._run_pipeline(
            market=market,
            count=count,
        )

    # -----------------------------------------------------------------
    # ALL MARKETS
    # -----------------------------------------------------------------

    def scan_all_markets(
        self,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Scan all agreed BALLY FLOW markets.

        Agreed markets:

            XAUUSD
            EURUSD
            GBPUSD
            USDJPY
            XAGUSD
            NASDAQ
        """

        if not self._running:
            self.start()

        kwargs: Dict[str, Any] = {}

        if count is not None:
            kwargs["count"] = count

        result = scan_all_markets(
            **kwargs,
        )

        return {
            "status": "READY",
            "application": APP_NAME,
            "version": APP_VERSION,
            "mode": self.mode.value,
            "scan": result,
            "decisions": None,
        }


# =====================================================================
# DEFAULT APPLICATION INSTANCE
# =====================================================================

app = BallyFlowApplication(
    mode=TradingMode.TECHNICAL
)


# =====================================================================
# PUBLIC APPLICATION API
# =====================================================================

def start(
    mode: TradingMode = TradingMode.TECHNICAL,
) -> Dict[str, Any]:
    """
    Start the default BALLY FLOW application.

    The requested mode must be either:

        TradingMode.TECHNICAL
        TradingMode.HYBRID
    """

    app.set_mode(mode)

    return app.start()


def stop() -> Dict[str, Any]:
    """
    Stop the default application.
    """

    return app.stop()


def status() -> Dict[str, Any]:
    """
    Return default application status.
    """

    return app.status()


def set_mode(
    mode: TradingMode,
) -> TradingMode:
    """
    Set the default application's trading mode.
    """

    return app.set_mode(mode)


def run_market(
    market: str,
    count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run a single-market scan using the default application.
    """

    return app.scan_market(
        market=market,
        count=count,
    )


def run_all_markets(
    count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run the complete agreed market scan.
    """

    return app.scan_all_markets(
        count=count,
    )


# =====================================================================
# CLI ENTRY POINT
# =====================================================================

def main() -> None:
    """
    Command-line application entry point.
    """

    result = start(
        mode=TradingMode.TECHNICAL
    )

    print("=" * 70)
    print(f"{APP_NAME} v{APP_VERSION}")
    print("=" * 70)

    print(
        "STATUS:",
        result["status"],
    )

    print(
        "MODE:",
        result["mode"],
    )

    print(
        "TECHNICAL ENABLED:",
        result["technical_enabled"],
    )

    print(
        "HYBRID ENABLED:",
        result["hybrid_enabled"],
    )

    print("=" * 70)


# =====================================================================
# MODULE EXECUTION
# =====================================================================

if __name__ == "__main__":
    main()

