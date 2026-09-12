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
    """
    return {
        "status": "ONLINE",
        "application": APP_NAME,
        "version": APP_VERSION,
        "service": "api",
    }
