"""Regression tests for executed-order tenant ownership registration.

The test verifies that a successfully executed MT5 position is added to the
DB-3 user_orders ownership index used by authenticated position filtering and
close authorization. No real MT5 call is made.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from backend.api.routes.orders import _persist_execution_lifecycle


class DB3Step6ExecutionOwnershipTest(unittest.TestCase):
    def test_real_execution_records_position_ticket_for_authenticated_tenant(self) -> None:
        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=None)

        plan_row = {"id": 11}
        order_row = {"id": 22}
        execution_row = {"id": 33}
        trade_row = {"id": 44}
        execution = {
            "status": "EXECUTED",
            "order": {
                "magic_number": 20260817,
                "comment": "BALLY_TRADES_BOT",
                "stop_loss": 3390.0,
                "take_profit": 3430.0,
            },
            "risk": {
                "trade_plan": {
                    "entry": 3400.0,
                    "stop_loss": 3390.0,
                    "take_profit": 3430.0,
                    "volume": 0.01,
                    "risk_percent": 1.0,
                    "risk_reward": 3.0,
                }
            },
            "executor": {
                "executor_result": {
                    "real_trade": True,
                    "order_ticket": 7001,
                    "deal_ticket": 7002,
                    "position_ticket": 7003,
                    "retcode": 10009,
                    "price": 3400.25,
                    "volume": 0.01,
                }
            },
        }
        trade_plan = {
            "symbol": "XAUUSD",
            "decision": "BUY",
            "timeframe": "M15",
        }

        with patch("backend.api.routes.orders.get_db_connection", return_value=conn), \
             patch("backend.api.routes.orders.create_trade_plan_record", return_value=plan_row), \
             patch("backend.api.routes.orders.create_order_record", return_value=order_row), \
             patch("backend.api.routes.orders.create_execution_record", return_value=execution_row), \
             patch("backend.api.routes.orders.create_trade_record", return_value=trade_row), \
             patch("backend.api.routes.orders.tenant_router.record_user_order", return_value=True) as record_order:
            result = _persist_execution_lifecycle(
                user_id=101,
                requested_lot_size=0.01,
                requested_comment="test",
                trade_plan=trade_plan,
                execution=execution,
            )

        record_order.assert_called_once_with(
            user_id=101,
            ticket=7003,
            symbol="XAUUSD",
            action="BUY",
            lot_size=0.01,
            status="SUBMITTED",
            magic_number=20260817,
        )
        conn.commit.assert_called_once()
        self.assertEqual(result["persistence_status"], "EXECUTED")
        self.assertEqual(result["trade_record_id"], 44)

    def test_blocked_execution_does_not_create_tenant_ownership(self) -> None:
        conn = MagicMock()
        execution = {
            "status": "BLOCKED",
            "order": {
                "magic_number": 20260817,
            },
            "risk": {
                "trade_plan": {
                    "entry": 1.1,
                    "stop_loss": 1.09,
                    "take_profit": 1.12,
                    "volume": 0.01,
                }
            },
            "executor": {
                "executor_result": {
                    "real_trade": False,
                    "reason": "Final gate blocked execution",
                }
            },
        }
        trade_plan = {
            "symbol": "EURUSD",
            "decision": "BUY",
            "timeframe": "M15",
        }

        with patch("backend.api.routes.orders.get_db_connection", return_value=conn), \
             patch("backend.api.routes.orders.create_trade_plan_record", return_value={"id": 1}), \
             patch("backend.api.routes.orders.create_order_record", return_value={"id": 2}), \
             patch("backend.api.routes.orders.create_execution_record", return_value={"id": 3}), \
             patch("backend.api.routes.orders.tenant_router.record_user_order") as record_order:
            result = _persist_execution_lifecycle(
                user_id=101,
                requested_lot_size=0.01,
                requested_comment="test",
                trade_plan=trade_plan,
                execution=execution,
            )

        record_order.assert_not_called()
        self.assertEqual(result["persistence_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
