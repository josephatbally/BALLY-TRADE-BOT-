"""BALLY FLOW authentication and multi-channel OTP delivery."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

from backend.database import get_db_connection
from backend.security.jwt_auth import create_access_token, get_current_user, get_current_user_optional

router = APIRouter()
OTP_TTL_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_SECONDS = 30
ALLOWED_CHANNELS = {"email", "sms", "whatsapp"}


class RegisterInitiateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
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


def _channel(value: str) -> str:
    value = value.strip().lower()
    if value not in ALLOWED_CHANNELS:
        raise HTTPException(status_code=400, detail="Unsupported verification channel.")
    return value


def _otp_hash(code: str) -> str:
    secret = os.getenv("OTP_HASH_SECRET", "").strip()
    if not secret:
        raise RuntimeError("OTP_HASH_SECRET is not configured")
    return hmac.new(secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def _send_email_otp(to_email: str, code: str, user_name: str) -> bool:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    port_raw = os.getenv("SMTP_PORT", "587").strip()
    port = int(port_raw) if port_raw.isdigit() else 587
    username = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    from_email = os.getenv("SMTP_FROM", username).strip()
    if not username or not password or not from_email:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{code} is your BALLY FLOW verification code"
    msg["From"] = f"BALLY FLOW Security <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(
        f"Hello {user_name},\n\nYour BALLY FLOW verification code is {code}. "
        f"It expires in 5 minutes. Never share this code.", "plain"
    ))
    msg.attach(MIMEText(
        f"<div style='font-family:Arial;padding:24px'><h2>BALLY FLOW</h2>"
        f"<p>Hello <b>{user_name}</b>,</p><p>Your verification code is:</p>"
        f"<h1 style='letter-spacing:8px'>{code}</h1><p>Expires in 5 minutes.</p>"
        f"<p>Never share this code with anyone.</p></div>", "html"
    ))
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=12) as server:
                server.login(username, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=12) as server:
                server.ehlo(); server.starttls(); server.ehlo()
                server.login(username, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"[BALLY FLOW EMAIL] delivery failed: {exc}")
        return False


def _send_sms_otp(phone: str, code: str, user_name: str) -> bool:
    """Provider-neutral SMS adapter. Configure the provider in the backend, never in mobile."""
    provider_url = os.getenv("SMS_PROVIDER_URL", "").strip()
    api_key = os.getenv("SMS_PROVIDER_API_KEY", "").strip()
    if not provider_url or not api_key:
        return False
    # HTTP transport is intentionally isolated here; wire the selected provider's exact
    # payload in deployment configuration/module rather than exposing credentials to the app.
    try:
        import urllib.request
        payload = json.dumps({"to": phone, "message": f"BALLY FLOW verification code: {code}"}).encode()
        request = urllib.request.Request(provider_url, data=payload, method="POST", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=12) as response:
            return 200 <= response.status < 300
    except Exception as exc:
        print(f"[BALLY FLOW SMS] delivery failed: {exc}")
        return False


def _send_whatsapp_otp(phone: str, code: str, user_name: str) -> bool:
    """Provider-neutral WhatsApp adapter for a WhatsApp Business API-compatible gateway."""
    provider_url = os.getenv("WHATSAPP_PROVIDER_URL", "").strip()
    api_key = os.getenv("WHATSAPP_PROVIDER_API_KEY", "").strip()
    if not provider_url or not api_key:
        return False
    try:
        import urllib.request
        payload = json.dumps({"to": phone, "message": f"BALLY FLOW verification code: {code}"}).encode()
        request = urllib.request.Request(provider_url, data=payload, method="POST", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=12) as response:
            return 200 <= response.status < 300
    except Exception as exc:
        print(f"[BALLY FLOW WHATSAPP] delivery failed: {exc}")
        return False


def _dispatch(channel: str, email: str, phone: str, code: str, user_name: str) -> bool:
    if channel == "email":
        return _send_email_otp(email, code, user_name)
    if channel == "sms":
        return _send_sms_otp(phone, code, user_name)
    return _send_whatsapp_otp(phone, code, user_name)


def _issue_otp(conn, user_id: int, email: str, phone: str, user_name: str, channel: str) -> dict:
    channel = _channel(channel)
    code = _generate_otp()
    destination = email if channel == "email" else phone
    code_hash = _otp_hash(code)
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS)
    cur = conn.cursor()
    cur.execute("UPDATE verification_codes SET is_used = 1 WHERE user_id = ? AND is_used = 0", (user_id,))
    cur.execute("""
        INSERT INTO verification_codes
        (user_id, identifier, channel, code, code_hash, destination, expires_at, attempts, is_used, delivery_status)
        VALUES (?, ?, ?, NULL, ?, ?, ?, 0, 0, 'pending')
    """, (user_id, destination, channel, code_hash, destination, expires_at.strftime("%Y-%m-%d %H:%M:%S")))
    otp_id = cur.lastrowid
    conn.commit()

    delivered = _dispatch(channel, email, phone, code, user_name)
    cur.execute("UPDATE verification_codes SET delivery_status = ? WHERE id = ?", ("sent" if delivered else "failed", otp_id))
    conn.commit()
    if not delivered:
        raise HTTPException(status_code=503, detail=f"Unable to deliver verification code via {channel}. Please try again or choose another method.")
    return {"status": "SENT", "identifier": destination, "channel": channel, "expires_in_seconds": OTP_TTL_SECONDS}


def _normalise_identifier(identifier: str) -> str:
    value = identifier.strip()
    return value.lower() if "@" in value else value


@router.post("/register-initiate")
def register_initiate(req: RegisterInitiateRequest):
    email = str(req.email).strip().lower()
    phone = req.phone.strip()
    channel = _channel(req.channel)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            user_id = row["id"]
            cur.execute("UPDATE users SET full_name=?, phone=?, country_code=?, status='pending_verification', updated_at=CURRENT_TIMESTAMP WHERE id=?", (req.full_name.strip(), phone, req.country_code.strip(), user_id))
        else:
            cur.execute("SELECT COUNT(*) AS total FROM users")
            role = "admin" if cur.fetchone()["total"] == 0 else "trader"
            cur.execute("INSERT INTO users (full_name,email,phone,country_code,role,status) VALUES (?,?,?,?,?,'pending_verification')", (req.full_name.strip(), email, phone, req.country_code.strip(), role))
            user_id = cur.lastrowid
        cur.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
        cur.execute("INSERT OR IGNORE INTO trading_preferences (user_id) VALUES (?)", (user_id,))
        cur.execute("INSERT OR IGNORE INTO risk_configurations (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return _issue_otp(conn, user_id, email, phone, req.full_name.strip(), channel)
    finally:
        conn.close()


@router.post("/login-initiate")
def login_initiate(req: LoginInitiateRequest):
    identifier = _normalise_identifier(req.identifier)
    channel = _channel(req.channel)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? OR phone = ? OR (country_code || phone) = ? ORDER BY id DESC LIMIT 1", (identifier, identifier, identifier))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="No user found with this email or phone. Please create an account.")
        if user["status"] != "active":
            raise HTTPException(status_code=403, detail="Account is not verified. Complete registration verification first.")
        return _issue_otp(conn, user["id"], user["email"], user["phone"], user["full_name"], channel)
    finally:
        conn.close()


@router.post("/verify-code")
def verify_code(req: VerifyCodeRequest):
    identifier = _normalise_identifier(req.identifier)
    code = req.code.strip()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM verification_codes WHERE destination = ? AND is_used = 0 ORDER BY id DESC LIMIT 1", (identifier,))
        otp = cur.fetchone()
        if not otp:
            raise HTTPException(status_code=400, detail="No pending verification code found. Please request a new code.")
        if otp["attempts"] >= OTP_MAX_ATTEMPTS:
            cur.execute("UPDATE verification_codes SET is_used=1 WHERE id=?", (otp["id"],)); conn.commit()
            raise HTTPException(status_code=400, detail="Maximum verification attempts exceeded. Please request a new code.")
        expires_at = datetime.strptime(otp["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() > expires_at:
            cur.execute("UPDATE verification_codes SET is_used=1 WHERE id=?", (otp["id"],)); conn.commit()
            raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")
        if not hmac.compare_digest(otp["code_hash"] or "", _otp_hash(code)):
            cur.execute("UPDATE verification_codes SET attempts=attempts+1 WHERE id=?", (otp["id"],)); conn.commit()
            raise HTTPException(status_code=400, detail="Invalid verification code. Please check and try again.")

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
            raise HTTPException(status_code=404, detail="User record not found.")
        cur.execute("SELECT created_at FROM verification_codes WHERE user_id=? ORDER BY id DESC LIMIT 1", (user["id"],))
        last = cur.fetchone()
        if last:
            last_time = datetime.strptime(last["created_at"], "%Y-%m-%d %H:%M:%S")
            if (datetime.utcnow() - last_time).total_seconds() < OTP_RESEND_SECONDS:
                raise HTTPException(status_code=429, detail="Please wait 30 seconds before requesting another code.")
        return _issue_otp(conn, user["id"], user["email"], user["phone"], user["full_name"], channel)
    finally:
        conn.close()


@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT broker_server, broker_name, account_number, currency, leverage, is_demo FROM broker_profiles WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1", (int(user["id"]),))
        broker = cur.fetchone()
        return {"user": user, "broker": dict(broker) if broker else None}
    finally:
        conn.close()


@router.post("/broker-profile")
def save_broker_profile(req: BrokerProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE broker_profiles SET is_active=0 WHERE user_id=?", (int(user["id"]),))
        cur.execute("INSERT INTO broker_profiles (user_id,broker_server,broker_name,account_number,password_encrypted,currency,leverage,is_demo,is_active) VALUES (?,?,?,?,?,?,?,?,1)", (int(user["id"]), req.broker_server.strip(), req.broker_name.strip(), req.account_number.strip(), req.password.strip() if req.password else None, req.currency.strip().upper(), req.leverage, 1 if req.is_demo else 0))
        conn.commit()
        return {"status":"SAVED","message":"Broker profile successfully linked to trader account.","account_number":req.account_number.strip(),"broker_server":req.broker_server.strip()}
    finally:
        conn.close()


@router.get("/admin/users")
def get_all_users(admin: Dict[str, Any] = Depends(get_current_user_optional)):
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id,full_name,email,phone,country_code,role,status,created_at FROM users ORDER BY id DESC")
        rows = cur.fetchall()
        return {"total_users": len(rows), "users": [dict(r) for r in rows]}
    finally:
        conn.close()
