
"""
BALLY FLOW API - Application Routes
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.main import (
    app as application,
)

from backend.trading_engine.modes.mode_controller import (
    TradingMode,
)


router = APIRouter()


# =====================================================================
# REQUEST SCHEMAS
# =====================================================================

class ModeRequest(BaseModel):
    mode: TradingMode


# =====================================================================
# STATUS
# =====================================================================

@router.get("/status")
def get_status():
    """
    Return complete BALLY FLOW application status.
    """

    return application.status()


# =====================================================================
# START
# =====================================================================

@router.post("/start")
def start_application():
    """
    Start BALLY FLOW application orchestration.
    """

    return application.start()


# =====================================================================
# STOP
# =====================================================================

@router.post("/stop")
def stop_application():
    """
    Stop BALLY FLOW application orchestration.
    """

    return application.stop()


# =====================================================================
# MODE
# =====================================================================

@router.get("/mode")
def get_mode():
    """
    Return the currently selected trading mode.
    """

    return {
        "mode": application.mode.value,
        "technical_enabled": application.is_technical(),
        "hybrid_enabled": application.is_hybrid(),
    }


@router.put("/mode")
def set_mode(request: ModeRequest):
    """
    Change BALLY FLOW trading mode.

    Only:
        technical
        hybrid

    are accepted.
    """

    try:
        selected_mode = application.set_mode(
            request.mode
        )

        return {
            "status": "UPDATED",
            "mode": selected_mode.value,
            "technical_enabled": application.is_technical(),
            "hybrid_enabled": application.is_hybrid(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
