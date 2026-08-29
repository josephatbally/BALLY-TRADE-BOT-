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

The Decision Engine is intentionally not called here yet.

The application currently provides:

    MT5 -> Market Data -> Scanner -> Application

The Decision Engine will be connected after its implementation
and validation.
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

    @property
    def running(self) -> bool:
        """
        Return whether the application is running.
        """

        return self._running

    # -----------------------------------------------------------------
    # MODE
    # -----------------------------------------------------------------

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
        """

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
            "technical_enabled": self.is_technical(),
            "hybrid_enabled": self.is_hybrid(),
            "scanner": scanner_info(),
        }

    # -----------------------------------------------------------------
    # SINGLE MARKET
    # -----------------------------------------------------------------

    def scan_market(
        self,
        market: str,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Scan one market.

        This method currently performs market-data scanning only.

        Decision creation will be added through the Decision Engine
        after that layer is implemented.
        """

        if not self._running:
            self.start()

        kwargs: Dict[str, Any] = {}

        if count is not None:
            kwargs["count"] = count

        result = scan_market(
            market,
            **kwargs,
        )

        return {
            "status": "READY",
            "application": APP_NAME,
            "version": APP_VERSION,
            "mode": self.mode.value,
            "market": market,
            "scan": result,
            "decision": None,
        }

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