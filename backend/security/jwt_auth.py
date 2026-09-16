"""
BALLY FLOW - Pure Python HS256 JWT Token & Session Security Engine.
Zero external C/binary dependencies for resilient, fail-safe token signing and verification.
"""

from __future__ import annotations
import hmac
import hashlib
import base64
import json
import time
import os
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from backend.database import get_db_connection

JWT_SECRET = os.getenv("JWT_SECRET", "bally_flow_institutional_super_secret_jwt_key_2026")
JWT_ALGORITHM = "HS256"
DEFAULT_EXPIRY_SECONDS = 30 * 24 * 60 * 60  # 30 days session persistence

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4)) if len(data) % 4 != 0 else ''
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(user_id: int | str, email: str, role: str = "trader", expires_in: int = DEFAULT_EXPIRY_SECONDS) -> str:
    """Creates a cryptographically signed HMAC-SHA256 JWT session token."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email.strip().lower(),
        "role": role,
        "iat": now,
        "exp": now + expires_in
    }
    
    encoded_header = _base64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    encoded_signature = _base64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates signature and expiration of an HS256 JWT token."""
    parts = token.strip().split('.')
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token format.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode('utf-8')
    expected_signature = hmac.new(JWT_SECRET.encode('utf-8'), signing_input, hashlib.sha256).digest()
    
    try:
        actual_signature = _base64url_decode(encoded_signature)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token signature.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature verification failed. Token is invalid.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    try:
        payload_bytes = _base64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    if "exp" in payload and int(time.time()) > payload["exp"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    return payload

def get_current_user(request: Request) -> Dict[str, Any]:
    """FastAPI route dependency that requires a valid authenticated user."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    token = auth_header[7:].strip()
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, full_name, email, phone, country_code, role, status FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")
        user_dict = dict(user_row)
        user_dict["id"] = str(user_dict["id"])
        return user_dict
    finally:
        conn.close()

def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """FastAPI route dependency that returns the authenticated user if provided, else None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, full_name, email, phone, country_code, role, status FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if user_row:
                user_dict = dict(user_row)
                user_dict["id"] = str(user_dict["id"])
                return user_dict
        finally:
            conn.close()
    except Exception:
        return None
    return None
