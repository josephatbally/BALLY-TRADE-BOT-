import backend.database as db

print("DATABASE:")
print(db.DB_PATH)

with db.get_db_connection() as conn:
    print("\nFOREIGN KEYS:")
    print(conn.execute("PRAGMA foreign_keys").fetchone()[0])

    print("\nJOURNAL MODE:")
    print(conn.execute("PRAGMA journal_mode").fetchone()[0])

    print("\nINTEGRITY:")
    print(conn.execute("PRAGMA integrity_check").fetchone()[0])

    print("\nSCHEMA VERSION:")
    row = conn.execute(
        "SELECT value FROM schema_metadata "
        "WHERE key='db_schema_version'"
    ).fetchone()
    print(row["value"] if row else "MISSING")
