from backend.database import init_db, get_db_connection

init_db()

conn = get_db_connection()

print("DATABASE:")
print(conn.execute("PRAGMA database_list").fetchall())

print()
print("TABLES:")

rows = conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

for row in rows:
    print(" -", row["name"])

print()
print("SCHEMA VERSION:")

row = conn.execute("""
    SELECT value
    FROM schema_metadata
    WHERE key = 'db_schema_version'
""").fetchone()

print(row["value"] if row else "MISSING")

conn.close()

print()
print("DB TEST COMPLETE")
