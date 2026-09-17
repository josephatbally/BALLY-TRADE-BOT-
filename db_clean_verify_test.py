import backend.database as db

with db.get_db_connection() as conn:
    print("DATABASE:")
    print(db.DB_PATH)

    print("\nREMAINING USERS:")
    print(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    print("\nREMAINING SETTINGS:")
    print(conn.execute("SELECT COUNT(*) FROM user_settings").fetchone()[0])

    print("\nREMAINING RISK CONFIGURATIONS:")
    print(conn.execute("SELECT COUNT(*) FROM risk_configurations").fetchone()[0])

    print("\nREMAINING TRADING PREFERENCES:")
    print(conn.execute("SELECT COUNT(*) FROM trading_preferences").fetchone()[0])

    print("\nREMAINING AUDIT LOGS:")
    print(conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])

    print("\nDATABASE INTEGRITY:")
    print(conn.execute("PRAGMA integrity_check").fetchone()[0])
