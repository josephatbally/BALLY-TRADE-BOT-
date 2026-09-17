import sqlite3
from pathlib import Path

db_path = Path("backend") / "bally_flow.db"

expected_tables = [
    "users",
    "verification_codes",
    "sessions",
    "user_settings",
    "broker_profiles",
    "risk_configurations",
    "trading_preferences",
    "audit_logs",
    "ai_pattern_knowledge",
    "ai_symbol_learning",
    "user_orders",
    "schema_metadata",
]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("DATABASE:")
print(db_path.resolve())

print("\nTABLES:")
tables = [
    row["name"]
    for row in conn.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' ORDER BY name"
    )
]

for table in tables:
    print(" -", table)

print("\nDB-1 REQUIRED TABLE CHECK:")
for table in expected_tables:
    print(f" - {table}: {'OK' if table in tables else 'MISSING'}")

print("\nSCHEMA VERSION:")
row = conn.execute(
    "SELECT value FROM schema_metadata "
    "WHERE key='db_schema_version'"
).fetchone()
print(row["value"] if row else "MISSING")

print("\nFOREIGN KEYS:")
print(conn.execute("PRAGMA foreign_keys").fetchone()[0])

print("\nDATABASE INTEGRITY:")
print(conn.execute("PRAGMA integrity_check").fetchone()[0])

print("\nROW COUNTS:")
for table in expected_tables:
    if table in tables:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f" - {table}: {count}")

conn.close()
