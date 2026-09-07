
"""
BALLY FLOW API - Health Routes
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.main import APP_NAME, APP_VERSION


router = APIRouter()


@router.get("")
def health():
    """
    Basic API health check.

    This confirms that the HTTP API process itself is alive.
    It does not claim that MT5 or the trading engine is healthy.
    """

    return {
        "status": "ONLINE",
        "application": APP_NAME,
        "version": APP_VERSION,
        "service": "api",
    }
