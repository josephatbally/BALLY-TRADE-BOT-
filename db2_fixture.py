import sqlite3

from backend.database import get_db_connection
from backend.db2_migration import migrate_db2
from backend.trading_engine.execution.trade_persistence import (
    create_trade_plan_record,
    create_order_record,
    create_execution_record,
    create_trade_record,
    update_order_record,
    update_trade_record,
)


# Ensure DB-2 schema exists.
migrate_db2()

conn = get_db_connection()

try:
    conn.execute("BEGIN")

    # Temporary fixture user.
    cur = conn.execute(
        """
        INSERT INTO users (
            full_name,
            email,
            phone,
            country_code,
            role,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "DB-2 Fixture User",
            "db2-fixture@example.invalid",
            "0000000000",
            "TZ",
            "trader",
            "active",
        ),
    )
    user_id = cur.lastrowid

    # 1. Trade plan
    plan = create_trade_plan_record(
        user_id=user_id,
        symbol="XAUUSD",
        decision="BUY",
        timeframe="M15",
        entry=2500.0,
        stop_loss=2490.0,
        take_profit=2520.0,
        volume=0.01,
        risk_percent=1.0,
        risk_amount=10.0,
        risk_reward=2.0,
        opportunity_score=85.0,
        market_context={"fixture": True},
        structural_context={"fixture": True},
        metadata={"source": "db2_fixture"},
        status="READY",
        conn=conn,
    )

    # 2. Order
    order = create_order_record(
        user_id=user_id,
        trade_plan_id=plan["id"],
        symbol="XAUUSD",
        action="BUY",
        volume=0.01,
        magic_number=20260817,
        status="SUBMITTED",
        request_json={"fixture": True},
        conn=conn,
    )

    # 3. Simulate broker submission.
    order = update_order_record(
        order["id"],
        mt5_order_ticket=123456789,
        status="FILLED",
        broker_retcode=10009,
        response_json={"fixture": True},
        conn=conn,
    )

    # 4. Execution / deal
    execution = create_execution_record(
        order_id=order["id"],
        user_id=user_id,
        symbol="XAUUSD",
        action="BUY",
        deal_ticket=987654321,
        order_ticket=123456789,
        position_ticket=555555555,
        volume=0.01,
        price=2500.5,
        commission=-0.10,
        swap=0.0,
        profit=5.0,
        broker_retcode=10009,
        status="EXECUTED",
        response_json={"fixture": True},
        conn=conn,
    )

    # 5. Open trade record
    trade = create_trade_record(
        user_id=user_id,
        trade_plan_id=plan["id"],
        order_id=order["id"],
        symbol="XAUUSD",
        direction="BUY",
        position_ticket=execution["position_ticket"],
        volume=0.01,
        entry_price=2500.5,
        stop_loss=2490.0,
        take_profit=2520.0,
        opened_at="2026-09-17T20:00:00",
        status="OPEN",
        metadata={"fixture": True},
        conn=conn,
    )

    # 6. Simulate close / final outcome.
    trade = update_trade_record(
        trade["id"],
        close_price=2510.5,
        closed_at="2026-09-17T20:05:00",
        gross_profit=10.0,
        commission=-0.20,
        swap=0.0,
        net_profit=9.80,
        outcome="WIN",
        status="CLOSED",
        metadata_json={"fixture": True, "closed": True},
        conn=conn,
    )

    # Verify lifecycle while transaction is still open.
    assert plan["id"] > 0
    assert order["id"] > 0
    assert execution["id"] > 0
    assert trade["id"] > 0
    assert trade["status"] == "CLOSED"
    assert trade["outcome"] == "WIN"

    # IMPORTANT:
    # Roll back everything. This fixture must leave the real DB clean.
    conn.rollback()

    print("DB-2 TRANSACTION FIXTURE: PASS")

finally:
    conn.close()