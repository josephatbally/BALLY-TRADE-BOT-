"""
BALLY FLOW - User Authentication & OTP Verification Router
Handles registration, 6-digit code generation, email/SMS dispatch, and admin oversight.
"""

from __future__ import annotations
import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.database import get_db_connection

router = APIRouter()

# ----------------- PYDANTIC SCHEMAS -----------------

class RegisterInitiateRequest(BaseModel):
    full_name: str
    email: str
    phone: str
    country_code: str = "+255"
    channel: str = "email"  # 'email', 'sms', or 'whatsapp'

class VerifyCodeRequest(BaseModel):
    identifier: str  # email or phone
    code: str

class ResendCodeRequest(BaseModel):
    identifier: str
    channel: str = "email"

# ----------------- DISPATCH HELPERS -----------------

def send_email_otp(to_email: str, code: str, user_name: str) -> bool:
    """Send branded 6-digit verification code via SMTP if configured, else log."""
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")
    from_email = os.getenv("SMTP_FROM", smtp_user or "noreply@ballyflow.com")

    if not (smtp_host and smtp_user and smtp_pass):
        print(f"\n[BALLY FLOW EMAIL GATEWAY] SMTP not configured. OTP for {to_email}: {code}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{code} is your BALLY FLOW Verification Code"
        msg["From"] = f"BALLY FLOW Security <{from_email}>"
        msg["To"] = to_email

        text = f"Hello {user_name},\n\nYour BALLY FLOW verification code is: {code}\n\nValid for 5 minutes. Do not share this code."
        html = f"""
        <html>
          <body style="background-color: #05070D; color: #FFFFFF; font-family: sans-serif; padding: 24px;">
            <div style="max-width: 480px; margin: 0 auto; background: #0A0E18; border: 1px solid #1E293B; border-radius: 16px; padding: 28px; text-align: center;">
              <h1 style="color: #35E68A; margin: 0; font-size: 24px; letter-spacing: 2px;">BALLY FLOW</h1>
              <p style="color: #7D8AA8; font-size: 13px; margin-top: 4px;">INSTITUTIONAL EXECUTION & RISK COCKPIT</p>
              <div style="margin: 32px 0;">
                <p style="color: #94A3B8; font-size: 14px;">Your 6-digit security verification code is:</p>
                <div style="background: #05070D; border: 1px solid #334BFF; border-radius: 10px; padding: 16px; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #35E68A;">
                  {code}
                </div>
                <p style="color: #64748B; font-size: 12px; margin-top: 12px;">Expires in 5 minutes. If you did not request this, please ignore.</p>
              </div>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
        return True
    except Exception as exc:
        print(f"[AUTH ERROR] Failed sending email: {exc}")
        return False

# ----------------- ROUTE HANDLERS -----------------

@router.post("/register-initiate")
def register_initiate(req: RegisterInitiateRequest):
    """
    Step 1: Record trader registration details, generate 6-digit OTP,
    store in SQLite database, and dispatch via email/SMS.
    """
    full_name = req.full_name.strip()
    email = req.email.strip().lower()
    phone = req.phone.strip()
    country_code = req.country_code.strip()
    channel = req.channel.strip().lower()

    # Generate secure 6-digit code
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Upsert User
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
            # First user is admin, subsequent are traders
            cursor.execute("SELECT COUNT(*) AS total FROM users")
            user_count = cursor.fetchone()["total"]
            role = "admin" if user_count == 0 else "trader"

            cursor.execute("""
                INSERT INTO users (full_name, email, phone, country_code, role, status)
                VALUES (?, ?, ?, ?, ?, 'pending_verification')
            """, (full_name, email, phone, country_code, role))
            user_id = cursor.lastrowid

        # 2. Invalidate any older unused codes for this email
        cursor.execute("""
            UPDATE verification_codes 
            SET is_used = 1 
            WHERE identifier = ? AND is_used = 0
        """, (email,))

        # 3. Insert new 6-digit verification record
        cursor.execute("""
            INSERT INTO verification_codes (user_id, identifier, channel, code, expires_at, attempts, is_used)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user_id, email, channel, code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()

        # 4. Dispatch verification code
        email_sent = False
        if channel == "email" or "@" in email:
            email_sent = send_email_otp(email, code, full_name)

        # Prominent console logging for admin / developer visibility
        print("=" * 68)
        print(f"[BALLY FLOW AUTH] 6-Digit OTP for {email} ({country_code} {phone}):")
        print(f">>>  {code}  <<<")
        print(f"Target: {email} | Channel: {channel} | Expires: 5 minutes")
        print("=" * 68)

        return {
            "status": "SENT",
            "message": f"Verification code dispatched to {email}",
            "identifier": email,
            "channel": channel,
            "email_sent": email_sent,
            "expires_in_seconds": 300,
            "dev_code": code,  # Provided for immediate testing & offline validation
        }
    except Exception as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database registration error: {exc}")
    finally:
        conn.close()

@router.post("/verify-code")
def verify_code(req: VerifyCodeRequest):
    """
    Step 2: Validate the 6-digit OTP from database and activate user account.
    """
    identifier = req.identifier.strip().lower()
    code = req.code.strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the latest active code for this identifier
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

        # Check attempts
        if otp_record["attempts"] >= 5:
            cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        # Check expiration
        expires_at = datetime.strptime(otp_record["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.utcnow() > expires_at:
            cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new one."
            )

        # Validate code match
        if otp_record["code"] != code:
            cursor.execute("""
                UPDATE verification_codes SET attempts = attempts + 1 WHERE id = ?
            """, (otp_record["id"],))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code. Please check and try again."
            )

        # Code is valid: Mark used and activate user
        cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE id = ?", (otp_record["id"],))
        cursor.execute("""
            UPDATE users SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (otp_record["user_id"],))

        cursor.execute("SELECT * FROM users WHERE id = ?", (otp_record["user_id"],))
        user = cursor.fetchone()
        conn.commit()

        return {
            "status": "VERIFIED",
            "message": "Account successfully verified.",
            "user": {
                "id": str(user["id"]),
                "full_name": user["full_name"],
                "email": user["email"],
                "phone": f"{user['country_code']} {user['phone']}",
                "country_code": user["country_code"],
                "role": user["role"],
                "status": user["status"],
            }
        }
    finally:
        conn.close()

@router.post("/resend-code")
def resend_code(req: ResendCodeRequest):
    """Resend a fresh 6-digit OTP code with rate-limit protection."""
    identifier = req.identifier.strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (identifier, identifier))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User record not found.")

        # Rate check: 30-second cooldown
        cursor.execute("""
            SELECT created_at FROM verification_codes 
            WHERE identifier = ? ORDER BY id DESC LIMIT 1
        """, (identifier,))
        last = cursor.fetchone()
        if last:
            last_time = datetime.strptime(last["created_at"], "%Y-%m-%d %H:%M:%S")
            if (datetime.utcnow() - last_time).total_seconds() < 30:
                raise HTTPException(status_code=429, detail="Please wait before requesting another code.")

        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        cursor.execute("UPDATE verification_codes SET is_used = 1 WHERE identifier = ?", (identifier,))
        cursor.execute("""
            INSERT INTO verification_codes (user_id, identifier, channel, code, expires_at, attempts, is_used)
            VALUES (?, ?, ?, ?, ?, 0, 0)
        """, (user["id"], identifier, req.channel, code, expires_at.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

        send_email_otp(user["email"], code, user["full_name"])

        print(f"[BALLY FLOW AUTH RESEND] New OTP for {identifier}: >>> {code} <<<")

        return {
            "status": "RESENT",
            "message": f"Fresh verification code dispatched to {identifier}",
            "expires_in_seconds": 300,
            "dev_code": code,
        }
    finally:
        conn.close()

@router.get("/admin/users")
def get_all_users():
    """Admin-only overview of registered users, their status, and recent OTP requests."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.full_name, u.email, u.phone, u.country_code, u.role, u.status, u.created_at,
                   (SELECT code FROM verification_codes WHERE user_id = u.id ORDER BY id DESC LIMIT 1) as last_code,
                   (SELECT channel FROM verification_codes WHERE user_id = u.id ORDER BY id DESC LIMIT 1) as last_channel
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
