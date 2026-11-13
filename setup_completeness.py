import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta, timezone

database_path = Path(__file__).resolve().parent / "sales.db"

if not database_path.is_file():
    raise FileNotFoundError("Run setup_database.py first.")

connection = sqlite3.connect(database_path)

try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_status (
            business_date TEXT PRIMARY KEY,
            is_complete INTEGER NOT NULL
                CHECK (is_complete IN (0, 1)),
            loaded_at TEXT
        )
    """)

    # Register every date in our two sample months.
    start_date = date(2026, 8, 1)
    end_date = date(2026, 10, 1)

    records = []
    current_date = start_date

    while current_date < end_date:
        # 0 means completeness has not been established.
        records.append((current_date.isoformat(), 0, None))
        current_date += timedelta(days=1)

    connection.executemany("""
        INSERT INTO ingestion_status (
            business_date, is_complete, loaded_at
        )
        VALUES (?, ?, ?)
        ON CONFLICT(business_date) DO NOTHING
    """, records)

    connection.commit()

    result = connection.execute("""
        SELECT
            COUNT(*) AS tracked_days,
            COALESCE(SUM(is_complete), 0) AS complete_days
        FROM ingestion_status
        WHERE business_date >= ?
          AND business_date < ?
    """, (start_date.isoformat(), end_date.isoformat()))

    tracked_days, complete_days = result.fetchone()
    expected_days = (end_date - start_date).days

    print(f"Expected days: {expected_days}")
    print(f"Tracked days: {tracked_days}")
    print(f"Confirmed complete days: {complete_days}")

    if tracked_days == expected_days and complete_days == expected_days:
        print("Status: comparison period is complete.")
    else:
        print("Status: completeness not established.")
        print("Sales findings describe the loaded sample only.")

finally:
    connection.close()
