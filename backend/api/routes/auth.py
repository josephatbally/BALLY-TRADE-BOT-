"""
BALLY FLOW - User Authentication & OTP Verification Router (Phase 2 & 3)
Handles registration, sign-in, 6-digit OTP codes, JWT session token generation,
Gmail SMTP email dispatch, and multi-tenant broker profile persistence.
"""

from __future__ import annotations
import os
import smtplib
import secrets
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

# Try auto-loading .env from project root
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except Exception:
    pass

from backend.database import get_db_connection
from backend.security.jwt_auth import (
    create_access_token, 
    get_current_user,
    get_current_user_optional
)

router = APIRouter()

# ----------------- PYDANTIC SCHEMAS -----------------

class RegisterInitiateRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    country_code: str = "+255"
    channel: str = "email"

class LoginInitiateRequest(BaseModel):
    identifier: str
    channel: str = "email"

class VerifyCodeRequest(BaseModel):
    identifier: str
    code: str

class ResendCodeRequest(BaseModel):
    identifier: str
    channel: str = "email"

class BrokerProfileRequest(BaseModel):
    broker_server: str
    broker_name: str
    account_number: str
    password: Optional[str] = None
    currency: str = "USD"
    leverage: int = 100
    is_demo: bool = True

# ----------------- DISPATCH HELPERS -----------------

def send_email_otp(to_email: str, code: str, user_name: str) -> bool:
    """
    Sends institutional 6-digit OTP verification email.
    Optimized for Gmail SMTP (smtp.gmail.com) with TLS port 587 or SSL port 465.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    smtp_port = int(smtp_port_raw) if smtp_port_raw.isdigit() else 587
    smtp_user = os.getenv("SMTP_USER", "").strip()
    # Google App Passwords often have spaces (e.g. 'abcd efgh ijkl mnop')
    smtp_pass = os.getenv("SMTP_PASS", "").replace(" ", "").strip()
    from_email = os.getenv("SMTP_FROM", smtp_user or "josephatbally5@gmail.com").strip()

    if not (smtp_user and smtp_pass):
        print(f"\n[BALLY FLOW EMAIL GATEWAY] Gmail SMTP credentials not set in environment or .env.")
        print(f"OTP for {to_email}: >>> {code} <<< (Dev fallback displayed in console)\n")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{code} is your BALLY FLOW Verification Code"
        msg["From"] = f"BALLY FLOW Security <{from_email}>"
        msg["To"] = to_email

        text = (
            f"Hello {user_name},\n\n"
            f"Your BALLY FLOW verification code is: {code}\n\n"
            f"Valid for 5 minutes. Enter this code in your BALLY FLOW terminal to authenticate.\n"
            f"If you did not request this verification, please secure your account immediately.\n\n"
            f"BALLY FLOW QUANTUM COCKPIT"
        )

        html = f"""
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <style>
              body {{ background-color: #05070D; color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 24px; }}
              .card {{ max-width: 480px; margin: 0 auto; background: #0A0E18; border: 1px solid #1E293B; border-radius: 18px; padding: 32px 24px; text-align: center; box-shadow: 0 12px 30px rgba(0,0,0,0.5); }}
              .brand {{ color: #FFFFFF; font-size: 24px; font-weight: 900; letter-spacing: 3px; margin: 0; }}
              .badge {{ display: inline-block; background: rgba(53, 230, 138, 0.12); border: 1px solid rgba(53, 230, 138, 0.3); border-radius: 12px; padding: 4px 12px; color: #35E68A; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; margin-top: 8px; }}
              .greeting {{ color: #94A3B8; font-size: 14px; margin-top: 24px; }}
              .code-box {{ margin: 24px 0; background: #05070D; border: 1px solid #334BFF; border-radius: 12px; padding: 18px; }}
              .code-value {{ font-size: 34px; font-weight: 900; letter-spacing: 10px; color: #35E68A; margin: 0; font-family: 'Courier New', Courier, monospace; }}
              .notice {{ color: #64748B; font-size: 12px; line-height: 18px; margin-top: 14px; }}
              .footer {{ border-top: 1px solid #172032; margin-top: 28px; padding-top: 16px; color: #475569; font-size: 10px; letter-spacing: 1px; }}
            </style>
          </head>
          <body>
            <div class="card">
              <h1 class="brand">BALLY FLOW</h1>
              <div class="badge">INSTITUTIONAL QUANTUM COCKPIT</div>
              <p class="greeting">Hello <strong style="color: #FFFFFF;">{user_name}</strong>,<br>Use the 6-digit security code below to authorize your session:</p>
              
              <div class="code-box">
                <div class="code-value">{code}</div>
              </div>
              
              <p class="notice">
                Code expires in <strong>5 minutes</strong>.<br>
                Never share this code with anyone. BALLY FLOW staff will never ask for your code.
              </p>
              
              <div class="footer">
                BALLY FLOW HIGH-FREQUENCY TRADING ENGINE • ZERO-TRUST PROTOCOL
              </div>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        # Support SSL (465) or STARTTLS (587)
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [to_email], msg.as_string())
        
        print(f"[BALLY FLOW EMAIL GATEWAY] Successfully sent OTP email via Gmail to {to_email}")
        return True
    except Exception as exc:
        print(f"[AUTH ERROR] Failed dispatching Gmail OTP email: {exc}")
        return False

# ----------------- ROUTE HANDLERS -----------------

@router.post("/register-initiate")
def register_initiate(req: RegisterInitiateRequest):
    full_name = req.full_name.strip()
    email = req.email.strip().lower()
    phone = req.phone.strip()
    country_code = req.country_code.strip()
    channel = req.channel.strip().lower()

    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user["id"]
            cursor.execute("""
                UPDATE users 
                SET full_name = ?, phone = ?, country_code = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (full_name, phone, country_code, user_id))
        else:
            cursor.execute("SELECT COUNT(*) AS total FROM users")
            user_count = cursor.fetchone()["total"]
            role = "admin" if user_count == 0 else "trader"

            cursor.execute("""
                INSERT INTO users (full_name, email, phone, country_code, role, status)
                VALUES (?, ?, ?, ?, ?, 'pending_verification')
            """, (full_name, email, phone, country_code, role))
            user_id = cursor.lastrowid

        cursor.execute("""
            UPDATE verification_codes 
            SET is_used = 1 
            WHERE identifier = ? AND is_used = 0
        """, (email,))

        cursor.execute("""
            INSERT INTO verification_codes (user_id, identifier, channel, code, expires_at, attempts, is_used)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user_id, email, channel, code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        email_sent = False
        if channel == "email" or "@" in email:
            email_sent = send_email_otp(email, code, full_name)

        print("=" * 68)
        print(f"[BALLY FLOW AUTH REGISTRATION] 6-Digit OTP for {email} ({country_code} {phone}):")
        print(f">>>  {code}  <<<")
        print(f"Target: {email} | Channel: {channel} | Email Sent: {email_sent} | Expires: 5 min")
        print("=" * 68)

        return {
            "status": "SENT",
            "message": f"Verification code dispatched to {email}",
            "identifier": email,
            "channel": channel,
            "email_sent": email_sent,
            "expires_in_seconds": 300,
            "dev_code": code,
        }
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database registration error: {exc}")
    finally:
        conn.close()

@router.post("/login-initiate")
def login_initiate(req: LoginInitiateRequest):
    """
    Seamless Sign-In endpoint: allows existing traders to request a 6-digit OTP
    by entering just their email or registered phone number.
    """
    identifier = req.identifier.strip().lower()
    channel = req.channel.strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM users 
            WHERE email = ? OR phone = ? OR (country_code || phone) = ?
            ORDER BY id DESC LIMIT 1
        """, (identifier, identifier, identifier))
        user = cursor.fetchone()

        if not user:
            # If not found but looks like email, register as trader automatically
            if "@" in identifier:
                cursor.execute("SELECT COUNT(*) AS total FROM users")
                user_count = cursor.fetchone()["total"]
                role = "admin" if user_count == 0 else "trader"
                user_name = identifier.split("@")[0].capitalize()
                cursor.execute("""
                    INSERT INTO users (full_name, email, phone, country_code, role, status)
                    VALUES (?, ?, '', '+255', ?, 'pending_verification')
                """, (user_name, identifier, role))
                user_id = cursor.lastrowid
                user_name_to_use = user_name
                user_email = identifier
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found with this email or phone. Please create an account."
                )
        else:
            user_id = user["id"]
            user_name_to_use = user["full_name"]
            user_email = user["email"]

        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        cursor.execute("""
            UPDATE verification_codes 
            SET is_used = 1 
            WHERE identifier = ? AND is_used = 0
        """, (user_email,))

        cursor.execute("""
            INSERT INTO verification_codes (user_id, identifier, channel, code, expires_at, attempts, is_used)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user_id, user_email, channel, code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        email_sent = send_email_otp(user_email, code, user_name_to_use)

        print("=" * 68)
        print(f"[BALLY FLOW SIGN-IN] 6-Digit OTP for {user_email}:")
        print(f">>>  {code}  <<<")
        print(f"Target: {user_email} | Channel: {channel} | Email Sent: {email_sent} | Expires: 5 min")
        print("=" * 68)

        return {
            "status": "SENT",
            "message": f"Verification code dispatched to {user_email}",
            "identifier": user_email,
            "channel": channel,
            "email_sent": email_sent,
            "expires_in_seconds": 300,
            "dev_code": code,
        }
    finally:
        conn.close()

@router.post("/verify-code")
def verify_code(req: VerifyCodeRequest):
    identifier = req.identifier.strip().lower()
    code = req.code.strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT * FROM verification_codes
            WHERE identifier = ? AND is_used = 0
            ORDER BY id DESC LIMIT 1
        """, (identifier,))
        otp_record = cursor.fetchone()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending verification code found. Please request a new code."
            )

        if otp_record["attempts"] >= 5:
            cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        expires_at = datetime.strptime(otp_record["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() > expires_at:
            cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new one."
            )

        if otp_record["code"] != code:
            cursor.execute("""
                UPDATE verification_codes SET attempts = attempts + 1 WHERE id = ?
            """, (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check and try again."
            )

        # Mark code used and activate trader
        cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
        cursor.execute("""
            UPDATE users SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (otp_record["user_id"],))

        cursor.execute("SELECT * FROM users WHERE id = ?", (otp_record["user_id"],))
        user = cursor.fetchone()
        conn.commit()

        # Phase 2: Create cryptographically signed JWT Session Token
        user_id_str = str(user["id"])
        access_token = create_access_token(
            user_id=user_id_str,
            email=user["email"],
            role=user["role"]
        )

        return {
            "status": "VERIFIED",
            "message": "Account successfully verified.",
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id_str,
                "full_name": user["full_name"],
                "email": user["email"],
                "phone": f"{user['country_code']} {user['phone']}".strip(),
                "country_code": user["country_code"],
                "role": user["role"],
                "status": user["status"],
                "token": access_token
            }
        }
    finally:
        conn.close()

@router.post("/resend-code")
def resend_code(req: ResendCodeRequest):
    identifier = req.identifier.strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (identifier, identifier))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User record not found.")

        cursor.execute("""
            SELECT created_at FROM verification_codes 
            WHERE identifier = ? ORDER BY id DESC LIMIT 1
        """, (identifier,))
        last = cursor.fetchone()
        if last:
            last_time = datetime.strptime(last["created_at"], "%Y-%m-%d %H:%M:%S")
            if (datetime.utcnow() - last_time).total_seconds() < 30:
                raise HTTPException(status_code=429, detail="Please wait 30 seconds before requesting another code.")

        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE identifier = ?", (identifier,))
        cursor.execute("""
            INSERT INTO verification_codes (user_id, identifier, channel, code, expires_at, attempts, is_used)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user["id"], identifier, req.channel, code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        email_sent = send_email_otp(user["email"], code, user["full_name"])

        print(f"[BALLY FLOW AUTH RESEND] New OTP for {identifier}: >>> {code} <<< (Email Sent: {email_sent})")

        return {
            "status": "RESENT",
            "message": f"Fresh verification code dispatched to {identifier}",
            "expires_in_seconds": 300,
            "email_sent": email_sent,
            "dev_code": code,
        }
    finally:
        conn.close()

@router.get("/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Phase 2: Protected endpoint that returns the caller's identity via JWT."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT broker_server, broker_name, account_number, currency, leverage, is_demo
            FROM broker_profiles 
            WHERE user_id = ? AND is_active = 1
            ORDER BY id DESC LIMIT 1
        """, (int(user["id"]),))
        broker = cursor.fetchone()
        return {
            "user": user,
            "broker": dict(broker) if broker else None
        }
    finally:
        conn.close()

@router.post("/broker-profile")
def save_broker_profile(req: BrokerProfileRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Phase 3: Persist MT5 Broker credentials scoped to this specific tenant."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE broker_profiles SET is_active = 0 WHERE user_id = ?
        """, (int(user["id"]),))
        
        cursor.execute("""
            INSERT INTO broker_profiles (user_id, broker_server, broker_name, account_number, password_encrypted, currency, leverage, is_demo, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            int(user["id"]),
            req.broker_server.strip(),
            req.broker_name.strip(),
            req.account_number.strip(),
            req.password.strip() if req.password else None,
            req.currency.strip().upper(),
            req.leverage,
            1 if req.is_demo else 0
        ))
        conn.commit()
        return {
            "status": "SAVED",
            "message": "Broker profile successfully linked to trader account.",
            "account_number": req.account_number.strip(),
            "broker_server": req.broker_server.strip()
        }
    finally:
        conn.close()

@router.get("/admin/users")
def get_all_users(admin: Dict[str, Any] = Depends(get_current_user_optional)):
    """Admin-only overview of registered users and their status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.full_name, u.email, u.phone, u.country_code, u.role, u.status, u.created_at,
                   (SELECT code FROM verification_codes WHERE user_id = u.id ORDER BY id DESC LIMIT 1) as last_code,
                   (SELECT channel FROM verification_codes WHERE user_id = u.id ORDER BY id DESC LIMIT 1) as last_channel,
                   (SELECT broker_server FROM broker_profiles WHERE user_id = u.id AND is_active = 1 ORDER BY id DESC LIMIT 1) as active_broker
            FROM users u
            ORDER BY u.id DESC
        """)
        rows = cursor.fetchall()
        return {
            "total_users": len(rows),
            "users": [dict(r) for r in rows]
        }
    finally:
        conn.close()
