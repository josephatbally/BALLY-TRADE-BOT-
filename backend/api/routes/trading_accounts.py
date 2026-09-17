"""Authenticated DB-3 trading-account API routes."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.security.jwt_auth import get_current_user
from backend.trading_engine.trading_account_persistence import (
    create_trading_account,
    deactivate_trading_account,
    get_active_trading_account,
    get_trading_account,
    list_trading_accounts,
    update_trading_account_status,
)

router = APIRouter()


class TradingAccountCreateRequest(BaseModel):
    broker_server: str = Field(min_length=1, max_length=160)
    broker_name: str = Field(min_length=1, max_length=160)
    account_number: str = Field(min_length=1, max_length=80)
    platform: str = Field(default="MT5", min_length=1, max_length=20)
    account_name: str | None = Field(default=None, max_length=120)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    leverage: int | None = Field(default=None, ge=1, le=10000)
    is_demo: bool = True


class TradingAccountStatusRequest(BaseModel):
    status: str = Field(pattern=r"^(DISCONNECTED|CONNECTING|CONNECTED|ERROR)$")


@router.get("")
def list_my_trading_accounts(user: Dict[str, Any] = Depends(get_current_user)):
    accounts = list_trading_accounts(int(user["id"]), include_inactive=True)
    return {"status": "READY", "count": len(accounts), "trading_accounts": accounts}


@router.get("/active")
def get_my_active_trading_account(user: Dict[str, Any] = Depends(get_current_user)):
    account = get_active_trading_account(int(user["id"]))
    if not account:
        raise HTTPException(404, "No active trading account is linked to this user.")
    return {"status": "READY", "trading_account": account}


@router.get("/{account_id}")
def get_my_trading_account(account_id: int, user: Dict[str, Any] = Depends(get_current_user)):
    account = get_trading_account(int(user["id"]), account_id)
    if not account:
        raise HTTPException(404, "Trading account not found.")
    return {"status": "READY", "trading_account": account}


@router.post("")
def create_my_trading_account(
    req: TradingAccountCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = int(user["id"])
    account = create_trading_account(
        user_id=user_id,
        account_number=req.account_number.strip(),
        broker_server=req.broker_server.strip(),
        broker_name=req.broker_name.strip(),
        platform=req.platform.strip().upper(),
        account_name=req.account_name.strip() if req.account_name else None,
        currency=req.currency.strip().upper(),
        leverage=req.leverage,
        is_demo=req.is_demo,
        connection_status="DISCONNECTED",
    )
    return {"status": "SAVED", "trading_account": account}


@router.patch("/{account_id}/status")
def set_my_trading_account_status(
    account_id: int,
    req: TradingAccountStatusRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    account = update_trading_account_status(int(user["id"]), account_id, req.status)
    if not account:
        raise HTTPException(404, "Trading account not found.")
    return {"status": "UPDATED", "trading_account": account}


@router.delete("/{account_id}")
def deactivate_my_trading_account(
    account_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
):
    changed = deactivate_trading_account(int(user["id"]), account_id)
    if not changed:
        raise HTTPException(404, "Active trading account not found.")
    return {"status": "DEACTIVATED", "account_id": account_id}
