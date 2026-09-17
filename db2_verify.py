import sqlite3
from backend.database import DB_PATH

c = sqlite3.connect(DB_PATH)

print("DB:", DB_PATH)
print("Integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
print("FK:", c.execute("PRAGMA foreign_keys").fetchone()[0])
print("Schema:", c.execute(
    "SELECT value FROM schema_metadata WHERE key='db_schema_version'"
).fetchone())

print("trade_plans:", c.execute("SELECT COUNT(*) FROM trade_plans").fetchone()[0])
print("orders:", c.execute("SELECT COUNT(*) FROM orders").fetchone()[0])
print("executions:", c.execute("SELECT COUNT(*) FROM executions").fetchone()[0])
print("trade_records:", c.execute("SELECT COUNT(*) FROM trade_records").fetchone()[0])

c.close()
