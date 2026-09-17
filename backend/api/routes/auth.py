"""BALLY FLOW authentication with provider-managed OTP delivery."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.database import get_db_connection
from backend.config.env import load_local_env
load_local_env()

from backend.security.jwt_auth import create_access_token, get_current_user, get_current_user_optional
from backend.trading_engine.trading_account_persistence import create_trading_account, get_active_trading_account

router = APIRouter()
OTP_TTL_SECONDS = 600
OTP_RESEND_SECONDS = 30
AUTH_VERIFICATION_MODE = os.getenv("AUTH_VERIFICATION_MODE", "provider").strip().lower()
ALLOWED_CHANNELS = {"email", "sms", "whatsapp"}


class RegisterInitiateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    phone: str = Field(min_length=5, max_length=30)
    country_code: str = Field(default="+255", min_length=2, max_length=8)
    channel: str = "email"


class LoginInitiateRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=160)
    channel: str = "email"


class VerifyCodeRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=160)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendCodeRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=160)
    channel: str = "email"


class BrokerProfileRequest(BaseModel):
    broker_server: str
    broker_name: str
    account_number: str
    password: Optional[str] = None
    currency: str = "USD"
    leverage: int = 100
    is_demo: bool = True



def _local_verification_enabled() -> bool:
    return AUTH_VERIFICATION_MODE in {"local", "dev", "development"}


def _local_code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _issue_local_verification(conn, user: Any, channel: str) -> dict[str, Any]:
    """Development-only OTP flow. The code is returned only to the local UI."""
    destination = _destination(user, channel)
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    cur = conn.cursor()
    cur.execute(
        "UPDATE verification_codes SET is_used=1 WHERE user_id=? AND is_used=0",
        (user["id"],),
    )
    cur.execute(
        """
        INSERT INTO verification_codes
        (user_id, identifier, channel, code, code_hash, destination, provider,
         provider_verification_id, expires_at, attempts, is_used, delivery_status)
        VALUES (?, ?, ?, NULL, ?, ?, 'local_dev', NULL, ?, 0, 0, 'generated')
        """,
        (
            user["id"],
            destination,
            channel,
            _local_code_hash(code),
            destination,
            expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    return {
        "status": "SENT",
        "verification_required": True,
        "identifier": destination,
        "channel": channel,
        "expires_in_seconds": OTP_TTL_SECONDS,
        "dev_code": code,
        "message": "Development verification code generated. Enter the displayed 6-digit code to continue.",
    }


def _channel(value: str) -> str:
    value = value.strip().lower()
    if value not in ALLOWED_CHANNELS:
        raise HTTPException(400, "Unsupported verification channel.")
    return value


def _normalise_identifier(identifier: str) -> str:
    value = identifier.strip()
    return value.lower() if "@" in value else value


def _twilio_request(path: str, fields: dict[str, str]) -> dict[str, Any]:
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    service_sid = os.getenv("TWILIO_VERIFY_SERVICE_SID", "").strip()
    if not sid or not token or not service_sid:
        raise HTTPException(503, "OTP delivery is not configured. Set the Twilio Verify credentials on the backend.")
    url = f"https://verify.twilio.com/v2/Services/{service_sid}/{path}"
    body = urllib.parse.urlencode(fields).encode()
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req = urllib.request.Request(url, data=body, method="POST", headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as exc:
        print(f"[BALLY FLOW OTP] provider request failed: {exc}")
        raise HTTPException(503, "Verification service is temporarily unavailable. Please try again.")


def _start_provider_verification(destination: str, channel: str) -> dict[str, Any]:
    # Twilio Verify generates and delivers the OTP. BALLY FLOW never generates,
    # returns, logs, or stores the plaintext code.
    result = _twilio_request("Verifications", {"To": destination, "Channel": channel})
    return {"provider_id": result.get("sid"), "status": result.get("status", "pending")}


def _check_provider_verification(destination: str, code: str) -> dict[str, Any]:
    return _twilio_request("VerificationCheck", {"To": destination, "Code": code})


def _destination(user: Any, channel: str) -> str:
    if channel == "email":
        return user["email"]
    phone = (user["country_code"] or "") + (user["phone"] or "")
    phone = re.sub(r"[^0-9+]", "", phone)
    if not phone.startswith("+"):
        raise HTTPException(400, "A verified phone number in international format is required.")
    return phone


def _issue_verification(conn, user: Any, channel: str) -> dict[str, Any]:
    destination = _destination(user, channel)
    cur = conn.cursor()
    cur.execute("UPDATE verification_codes SET is_used=1 WHERE user_id=? AND is_used=0", (user["id"],))
    provider = _start_provider_verification(destination, channel)
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    cur.execute("""
        INSERT INTO verification_codes
        (user_id, identifier, channel, code, code_hash, destination, provider, provider_verification_id,
         expires_at, attempts, is_used, delivery_status)
        VALUES (?, ?, ?, NULL, NULL, ?, 'twilio_verify', ?, ?, 0, 0, ?)
    """, (user["id"], destination, channel, destination, provider["provider_id"],
          expires_at.strftime("%Y-%m-%d %H:%M:%S"), "sent" if provider["status"] == "pending" else provider["status"]))
    conn.commit()
    return {"status": "SENT", "identifier": destination, "channel": channel, "expires_in_seconds": OTP_TTL_SECONDS}


@router.post("/register-initiate")
def register_initiate(req: RegisterInitiateRequest):
    email = req.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(400, "Enter a valid email address.")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user:
            user_id = user["id"]
            cur.execute("UPDATE users SET full_name=?, phone=?, country_code=?, status='pending_verification', updated_at=CURRENT_TIMESTAMP WHERE id=?", (req.full_name.strip(), req.phone.strip(), req.country_code.strip(), user_id))
        else:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            role = "admin" if cur.fetchone()["total"] == 0 else "trader"
            cur.execute("INSERT INTO users (full_name,email,phone,country_code,role,status) VALUES (?,?,?,?,?,'pending_verification')", (req.full_name.strip(), email, req.phone.strip(), req.country_code.strip(), role))
            user_id = cur.lastrowid
        cur.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        cur.execute("INSERT OR IGNORE INTO trading_preferences (user_id) VALUES (?)", (user_id,))
        cur.execute("INSERT OR IGNORE INTO risk_configurations (user_id) VALUES (?)", (user_id,))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cur.fetchone()
        channel = _channel(req.channel)
        if _local_verification_enabled():
            return _issue_local_verification(conn, user, channel)
        return _issue_verification(conn, user, channel)
    finally:
        conn.close()


@router.post("/login-initiate")
def login_initiate(req: LoginInitiateRequest):
    identifier = _normalise_identifier(req.identifier)
    channel = _channel(req.channel)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? OR phone=? OR (country_code || phone)=? ORDER BY id DESC LIMIT 1", (identifier, identifier, identifier))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "No user found with this email or phone. Please create an account.")
        if user["status"] != "active":
            raise HTTPException(403, "Account is not verified. Complete registration verification first.")
        if _local_verification_enabled():
            return _issue_local_verification(conn, user, channel)
        return _issue_verification(conn, user, channel)
    finally:
        conn.close()


@router.post("/verify-code")
def verify_code(req: VerifyCodeRequest):
    identifier = _normalise_identifier(req.identifier)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM verification_codes WHERE destination=? AND is_used=0 ORDER BY id DESC LIMIT 1", (identifier,))
        otp = cur.fetchone()
        if not otp:
            raise HTTPException(400, "No pending verification code found. Please request a new code.")
        if datetime.utcnow() > datetime.strptime(otp["expires_at"], "%Y-%m-%d %H:%M:%S"):
            cur.execute("UPDATE verification_codes SET is_used=1 WHERE id=?", (otp["id"],)); conn.commit()
            raise HTTPException(400, "Verification code has expired. Please request a new one.")
        if otp["attempts"] >= 5:
            cur.execute("UPDATE verification_codes SET is_used=1 WHERE id=?", (otp["id"],)); conn.commit()
            raise HTTPException(400, "Maximum verification attempts exceeded. Please request a new code.")
        submitted_code = req.code.strip()
        if otp["provider"] == "local_dev":
            valid = hmac.compare_digest(
                _local_code_hash(submitted_code),
                otp["code_hash"] or "",
            )
            if not valid:
                cur.execute("UPDATE verification_codes SET attempts=attempts+1 WHERE id=?", (otp["id"],))
                conn.commit()
                raise HTTPException(400, "Invalid verification code. Please check the displayed code and try again.")
        else:
            result = _check_provider_verification(
                identifier if otp["channel"] != "email" else otp["destination"],
                submitted_code,
            )
            if result.get("status") != "approved":
                cur.execute("UPDATE verification_codes SET attempts=attempts+1 WHERE id=?", (otp["id"],))
                conn.commit()
                raise HTTPException(400, "Invalid verification code. Please check and try again.")
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("UPDATE verification_codes SET is_used=1, verified_at=? WHERE id=?", (now, otp["id"]))
        if otp["channel"] == "email":
            cur.execute("UPDATE users SET status='active', email_verified=1, updated_at=CURRENT_TIMESTAMP WHERE id=?", (otp["user_id"],))
        else:
            cur.execute("UPDATE users SET status='active', phone_verified=1, updated_at=CURRENT_TIMESTAMP WHERE id=?", (otp["user_id"],))
        cur.execute("SELECT * FROM users WHERE id=?", (otp["user_id"],))
        user = cur.fetchone()
        conn.commit()
        token = create_access_token(str(user["id"]), user["email"], user["role"])
        return {"status":"VERIFIED","message":"Account successfully verified.","token":token,"token_type":"bearer","user":{k:user[k] for k in ("id","full_name","email","phone","country_code","role","status","email_verified","phone_verified")}}
    finally:
        conn.close()


@router.post("/resend-code")
def resend_code(req: ResendCodeRequest):
    identifier = _normalise_identifier(req.identifier)
    channel = _channel(req.channel)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? OR phone=? OR (country_code || phone)=? ORDER BY id DESC LIMIT 1", (identifier, identifier, identifier))
        user = cur.fetchone()
        if not user:
            raise HTTPException(404, "User record not found.")
        cur.execute("SELECT created_at FROM verification_codes WHERE user_id=? ORDER BY id DESC LIMIT 1", (user["id"],))
        last = cur.fetchone()
        if last and (datetime.utcnow() - datetime.strptime(last["created_at"], "%Y-%m-%d %H:%M:%S")).total_seconds() < OTP_RESEND_SECONDS:
            raise HTTPException(429, "Please wait 30 seconds before requesting another code.")
        if _local_verification_enabled():
            return _issue_local_verification(conn, user, channel)
        return _issue_verification(conn, user, channel)
    finally:
        conn.close()


@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        active_account = get_active_trading_account(int(user["id"]), conn=conn)
        if active_account:
            broker = {
                "broker_server": active_account["broker_server"],
                "broker_name": active_account["broker_name"],
                "account_number": active_account["account_number"],
                "currency": active_account["currency"],
                "leverage": active_account["leverage"],
                "is_demo": bool(active_account["is_demo"]),
            }
        else:
            cur = conn.cursor()
            cur.execute("SELECT broker_server,broker_name,account_number,currency,leverage,is_demo FROM broker_profiles WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1", (int(user["id"]),))
            legacy = cur.fetchone()
            broker = dict(legacy) if legacy else None
        return {"user": user, "broker": broker}
    finally:
        conn.close()


@router.post("/broker-profile")
def save_broker_profile(req: BrokerProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        user_id = int(user["id"])
        cur.execute("UPDATE broker_profiles SET is_active=0 WHERE user_id=?", (user_id,))
        cur.execute("INSERT INTO broker_profiles (user_id,broker_server,broker_name,account_number,password_encrypted,currency,leverage,is_demo,is_active) VALUES (?,?,?,?,?,?,?,?,1)", (user_id, req.broker_server.strip(), req.broker_name.strip(), req.account_number.strip(), req.password.strip() if req.password else None, req.currency.strip().upper(), req.leverage, int(req.is_demo)))
        broker_profile_id = cur.lastrowid
        create_trading_account(
            user_id=user_id,
            broker_profile_id=broker_profile_id,
            platform="MT5",
            account_number=req.account_number,
            broker_server=req.broker_server,
            broker_name=req.broker_name,
            currency=req.currency,
            leverage=req.leverage,
            is_demo=req.is_demo,
            connection_status="DISCONNECTED",
            conn=conn,
        )
        conn.commit()
        return {"status":"SAVED","message":"Broker profile successfully linked to trader account.","account_number":req.account_number.strip(),"broker_server":req.broker_server.strip()}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@router.get("/admin/users")
def get_all_users(admin: Dict[str, Any] = Depends(get_current_user_optional)):
    if not admin or admin.get("role") != "admin":
        raise HTTPException(403, "Administrator access required.")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id,full_name,email,phone,country_code,role,status,email_verified,phone_verified,created_at FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        return {"total_users": len(rows), "users": [dict(r) for r in rows]}
    finally:
        conn.close()
