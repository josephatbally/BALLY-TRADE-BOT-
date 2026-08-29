
"""
BALLY FLOW - Mode Controller

Central routing and authorization layer for BALLY FLOW.

RESPONSIBILITIES
----------------
The Mode Controller:

    - manages the active trading mode
    - validates supported modes
    - identifies which analysis pipeline is enabled
    - routes market data to the appropriate pipeline
    - provides standardized mode metadata
    - prevents accidental execution of disabled pipelines

SUPPORTED MODES
---------------
    TECHNICAL
    HYBRID

ARCHITECTURE
------------

TECHNICAL MODE

    Scanner
       |
       v
    Market Analytics
       |
       v
    Technical Engine
       |
       v
    Decision Engine
       |
       v
    Risk
       |
       v
    Execution


HYBRID MODE

    Scanner
       |
       v
    Market Analytics
       |
       +------------------+
       |                  |
       v                  v
    Technical         Fundamental
       |                  |
       +--------+---------+
                |
                v
          Hybrid Engine
                |
                v
           AI / Confidence
                |
                v
          Decision Engine
                |
                v
               Risk
                |
                v
            Execution


IMPORTANT
---------
This module MUST NOT:

    - analyze candles
    - calculate technical indicators
    - perform SMC analysis
    - perform fundamental analysis
    - calculate AI confidence
    - make BUY / SELL decisions
    - calculate position size
    - manage risk
    - place MT5 orders

Those responsibilities belong to downstream modules.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class TradingMode(str, Enum):
    """Supported BALLY FLOW operating modes."""

    TECHNICAL = "technical"
    HYBRID = "hybrid"


class ModeController:
    """
    Controls and routes the active BALLY FLOW operating mode.

    The controller is intentionally lightweight.

    It owns mode state and routing metadata only.
    """

    NAME = "BALLY FLOW Mode Controller"
    STATUS = "READY"

    SUPPORTED_MODES = (
        TradingMode.TECHNICAL,
        TradingMode.HYBRID,
    )

    def __init__(
        self,
        mode: TradingMode = TradingMode.TECHNICAL,
    ) -> None:
        self._mode = self._validate_mode(mode)

    # ==============================================================
    # MODE STATE
    # ==============================================================

    @property
    def mode(self) -> TradingMode:
        """Return the currently active trading mode."""

        return self._mode

    def set_mode(self, mode: TradingMode) -> TradingMode:
        """
        Change the active trading mode.

        Returns
        -------
        TradingMode
            The newly active mode.
        """

        self._mode = self._validate_mode(mode)
        return self._mode

    # ==============================================================
    # MODE CHECKS
    # ==============================================================

    def is_technical(self) -> bool:
        """Return True when Technical Mode is active."""

        return self._mode == TradingMode.TECHNICAL

    def is_hybrid(self) -> bool:
        """Return True when Hybrid Mode is active."""

        return self._mode == TradingMode.HYBRID

    # ==============================================================
    # PIPELINE AUTHORIZATION
    # ==============================================================

    def technical_enabled(self) -> bool:
        """
        Determine whether the technical pipeline is enabled.

        Technical analysis is required by both Technical and
        Hybrid modes.
        """

        return self._mode in (
            TradingMode.TECHNICAL,
            TradingMode.HYBRID,
        )

    def fundamental_enabled(self) -> bool:
        """
        Determine whether fundamental analysis is enabled.

        Fundamental analysis is enabled only in Hybrid Mode.
        """

        return self._mode == TradingMode.HYBRID

    def hybrid_enabled(self) -> bool:
        """Return True when the Hybrid pipeline is active."""

        return self._mode == TradingMode.HYBRID

    # ==============================================================
    # PIPELINE NAME
    # ==============================================================

    def active_pipeline(self) -> str:
        """
        Return the logical pipeline associated with the current mode.
        """

        if self.is_hybrid():
            return "hybrid"

        return "technical"

    # ==============================================================
    # ROUTING
    # ==============================================================

    def route(
        self,
        technical_pipeline: Any = None,
        fundamental_pipeline: Any = None,
        hybrid_pipeline: Any = None,
    ) -> Any:
        """
        Route to the pipeline appropriate for the active mode.

        This method does NOT execute analysis by itself.

        It simply returns the supplied pipeline object/callable.

        Parameters
        ----------
        technical_pipeline:
            Technical pipeline supplied by the caller.

        fundamental_pipeline:
            Fundamental pipeline supplied by the caller.

        hybrid_pipeline:
            Hybrid pipeline supplied by the caller.

        Returns
        -------
        Any
            The pipeline selected for the active mode.

        Raises
        ------
        ValueError
            If the required pipeline has not been supplied.
        """

        if self.is_technical():
            if technical_pipeline is None:
                raise ValueError(
                    "Technical pipeline is required in Technical Mode"
                )

            return technical_pipeline

        if self.is_hybrid():
            if hybrid_pipeline is None:
                raise ValueError(
                    "Hybrid pipeline is required in Hybrid Mode"
                )

            return hybrid_pipeline

        raise RuntimeError(
            f"Unsupported active mode: {self._mode}"
        )

    # ==============================================================
    # PIPELINE PERMISSIONS
    # ==============================================================

    def permissions(self) -> Dict[str, bool]:
        """
        Return explicit permissions for downstream orchestration.

        These are routing permissions only.

        They do not activate trading or bypass safety controls.
        """

        return {
            "technical_analysis": self.technical_enabled(),
            "fundamental_analysis": self.fundamental_enabled(),
            "hybrid_analysis": self.hybrid_enabled(),

            # Decision generation is downstream.
            "decision_engine": True,

            # These remain controlled by their own layers.
            "risk_management": True,
            "execution": True,
            "order_placement": True,
        }

    # ==============================================================
    # MODE DESCRIPTION
    # ==============================================================

    def description(self) -> Dict[str, Any]:
        """
        Return a standardized description of the active mode.
        """

        return {
            "mode": self._mode.value,
            "pipeline": self.active_pipeline(),

            "technical_enabled": self.technical_enabled(),
            "fundamental_enabled": self.fundamental_enabled(),
            "hybrid_enabled": self.hybrid_enabled(),

            "analysis_order": self.analysis_order(),

            "permissions": self.permissions(),
        }

    # ==============================================================
    # ANALYSIS ORDER
    # ==============================================================

    def analysis_order(self) -> list[str]:
        """
        Return the logical analysis sequence for the active mode.

        This describes orchestration order only.
        """

        if self.is_technical():
            return [
                "scanner",
                "market_analytics",
                "technical_engine",
                "decision_engine",
                "risk_management",
                "execution",
            ]

        if self.is_hybrid():
            return [
                "scanner",
                "market_analytics",
                "technical_engine",
                "fundamental_engine",
                "hybrid_engine",
                "ai_confidence",
                "decision_engine",
                "risk_management",
                "execution",
            ]

        raise RuntimeError(
            f"Unsupported active mode: {self._mode}"
        )

    # ==============================================================
    # STANDARDIZED STATUS
    # ==============================================================

    def status(self) -> Dict[str, Any]:
        """
        Return complete controller status.
        """

        return {
            "name": self.NAME,
            "status": self.STATUS,
            "mode": self._mode.value,
            "pipeline": self.active_pipeline(),

            "technical_enabled": self.technical_enabled(),
            "fundamental_enabled": self.fundamental_enabled(),
            "hybrid_enabled": self.hybrid_enabled(),

            "supported_modes": [
                mode.value
                for mode in self.SUPPORTED_MODES
            ],

            "analysis_order": self.analysis_order(),

            "permissions": self.permissions(),
        }

    # ==============================================================
    # VALIDATION
    # ==============================================================

    @classmethod
    def _validate_mode(
        cls,
        mode: TradingMode,
    ) -> TradingMode:
        """
        Validate and normalize a trading mode.
        """

        if isinstance(mode, TradingMode):
            return mode

        if isinstance(mode, str):
            normalized = mode.strip().lower()

            for supported_mode in cls.SUPPORTED_MODES:
                if normalized == supported_mode.value:
                    return supported_mode

        raise ValueError(
            "Unsupported trading mode. "
            "Expected 'technical' or 'hybrid'."
        )


# ==================================================================
# GLOBAL CONTROLLER
# ==================================================================

_default_controller = ModeController()


# ==================================================================
# CONVENIENCE API
# ==================================================================

def get_mode_controller() -> ModeController:
    """
    Return the default BALLY FLOW Mode Controller.
    """

    return _default_controller


def get_mode() -> TradingMode:
    """Return the current global trading mode."""

    return _default_controller.mode


def set_mode(
    mode: TradingMode,
) -> TradingMode:
    """Set the global trading mode."""

    return _default_controller.set_mode(mode)


def is_technical() -> bool:
    """Return True when global mode is Technical."""

    return _default_controller.is_technical()


def is_hybrid() -> bool:
    """Return True when global mode is Hybrid."""

    return _default_controller.is_hybrid()


def mode_status() -> Dict[str, Any]:
    """Return global mode-controller status."""

    return _default_controller.status()


def mode_info() -> Dict[str, Any]:
    """
    Return static and active mode information.
    """

    controller = _default_controller

    return {
        "name": controller.NAME,
        "status": controller.STATUS,
        "supported_modes": [
            mode.value
            for mode in controller.SUPPORTED_MODES
        ],
        "current_mode": controller.mode.value,
        "technical_enabled": controller.technical_enabled(),
        "fundamental_enabled": controller.fundamental_enabled(),
        "hybrid_enabled": controller.hybrid_enabled(),
    }


__all__ = [
    "TradingMode",
    "ModeController",
    "get_mode_controller",
    "get_mode",
    "set_mode",
    "is_technical",
    "is_hybrid",
    "mode_status",
    "mode_info",
]
