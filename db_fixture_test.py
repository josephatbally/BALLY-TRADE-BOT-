import backend.database as db

print("DATABASE:")
print(db.DB_PATH)

with db.get_db_connection() as conn:
    # Create a temporary test user.
    cursor = conn.execute(
        """
        INSERT INTO users (
            full_name,
            email,
            phone,
            country_code,
            role,
            status,
            email_verified,
            phone_verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "DB Fixture Test",
            "db-fixture-test@example.local",
            "700000000",
            "+255",
            "trader",
            "active",
            1,
            1,
        ),
    )

    user_id = cursor.lastrowid

    # Verify user.
    user = conn.execute(
        "SELECT id, full_name, email, status "
        "FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()

    print("\nUSER CREATED:")
    print(dict(user))

    # Create user settings.
    conn.execute(
        """
        INSERT INTO user_settings (
            user_id,
            min_confidence,
            risk_per_trade_pct,
            max_positions,
            scan_interval_seconds,
            trading_mode,
            theme
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, 70, 1.0, 1, 60, "Technical", "SYSTEM"),
    )

    settings = conn.execute(
        "SELECT user_id, min_confidence, trading_mode "
        "FROM user_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    print("\nSETTINGS CREATED:")
    print(dict(settings))

    # Create risk configuration.
    conn.execute(
        """
        INSERT INTO risk_configurations (
            user_id,
            risk_per_trade_pct,
            max_risk_pct,
            min_risk_pct,
            max_positions,
            min_rr,
            max_rr,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, 1.0, 2.0, 0.10, 1, 1.0, 3.0, 1),
    )

    risk = conn.execute(
        "SELECT user_id, risk_per_trade_pct, max_risk_pct, "
        "min_rr, max_rr, is_active "
        "FROM risk_configurations WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    print("\nRISK CONFIGURATION CREATED:")
    print(dict(risk))

    # Create trading preferences.
    conn.execute(
        """
        INSERT INTO trading_preferences (
            user_id,
            trading_mode,
            approval_required,
            enabled
        )
        VALUES (?, ?, ?, ?)
        """,
        (user_id, "Technical", 1, 0),
    )

    preferences = conn.execute(
        "SELECT user_id, trading_mode, approval_required, enabled "
        "FROM trading_preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    print("\nTRADING PREFERENCES CREATED:")
    print(dict(preferences))

    # Create audit record.
    conn.execute(
        """
        INSERT INTO audit_logs (
            user_id,
            event_type,
            channel,
            metadata_json
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            "DB_FIXTURE_TEST",
            "SYSTEM",
            '{"test":true}',
        ),
    )

    audit = conn.execute(
        "SELECT user_id, event_type, channel "
        "FROM audit_logs WHERE user_id = ? "
        "ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    print("\nAUDIT RECORD CREATED:")
    print(dict(audit))

    # Verify foreign-key relationships.
    print("\nRELATIONSHIP CHECK:")
    checks = {
        "settings": conn.execute(
            "SELECT COUNT(*) FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
        "risk": conn.execute(
            "SELECT COUNT(*) FROM risk_configurations WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
        "preferences": conn.execute(
            "SELECT COUNT(*) FROM trading_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
        "audit": conn.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
    }

    for name, count in checks.items():
        print(f" - {name}: {count}")

    conn.rollback()

print("\nFIXTURE TEST COMPLETE")
print("Test transaction rolled back; no fixture data was retained.")
