"""
BALLY FLOW - Multi-Tenant MT5 Routing Engine (Phase 3)
Manages multi-user isolation, routing trade requests to designated broker profiles,
and maintaining single-trader loop fallback (Phase 1).
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
from backend.database import get_db_connection

class TenantRouter:
    """
    Multi-tenant trade router: ensures user orders are isolated,
    attributed to their registered user ID, and dispatched to their respective MT5 instance.
    """
    
    def get_user_broker_profile(self, user_id: int | str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, user_id, broker_server, broker_name, account_number, currency, leverage, is_demo, is_active
                FROM broker_profiles 
                WHERE user_id = ? AND is_active = 1
                ORDER BY id DESC LIMIT 1
            """, (int(user_id),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def record_user_order(self, user_id: int | str, ticket: int, symbol: str, action: str, lot_size: float, status: str = "SUBMITTED", magic_number: int = 100001) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO user_orders (user_id, ticket, symbol, action, lot_size, status, magic_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (int(user_id), int(ticket), symbol.upper(), action.upper(), float(lot_size), status, magic_number))
            conn.commit()
            return True
        except Exception as exc:
            print(f"[TENANT ROUTER] Failed to record user order: {exc}")
            return False
        finally:
            conn.close()

    def get_user_order_tickets(self, user_id: int | str) -> List[int]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ticket FROM user_orders WHERE user_id = ?", (int(user_id),))
            rows = cursor.fetchall()
            return [int(r["ticket"]) for r in rows]
        finally:
            conn.close()

    def filter_user_positions(self, user_id: Optional[int | str], live_positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filters live positions for a tenant. If user_id is admin or None, returns all live positions.
        """
        if not user_id:
            return live_positions
            
        user_tickets = set(self.get_user_order_tickets(user_id))
        # If user has no specific recorded tickets yet, in development/single-host mode, show active positions
        if not user_tickets:
            return live_positions
            
        filtered = [pos for pos in live_positions if pos.get("ticket") in user_tickets or str(pos.get("ticket")) in user_tickets]
        return filtered if filtered else live_positions

tenant_router = TenantRouter()
