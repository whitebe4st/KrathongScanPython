import json
import sqlite3

db_path = "data/db/scanner.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  {table[0]}")
    cursor.execute(f"SELECT * FROM {table[0]}")
    rows = cursor.fetchall()
    print(f"    Rows: {len(rows)}")
    if rows:
        print(f"    Sample: {rows[0] if rows else None}")
        if table[0] == "templates":
            print("    All templates:")
            for row in rows:
                print(
                    f"      ID: {row[0]}, Name: {row[1]}, Markers: {row[2]}, Template: {row[3]}, Mask: {row[4]}"
                )
                try:
                    markers = json.loads(row[2])
                    print(f"        Parsed markers: {markers}")
                except:
                    print(f"        Raw markers: {row[2]}")

conn.close()
