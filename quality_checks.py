import sqlite3
from datetime import date
from pathlib import Path


def check_completeness(start_date, end_date):
    """Verify every date in [start_date, end_date) is complete."""

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if start >= end:
        raise ValueError("Start date must come before end date.")

    expected_days = (end - start).days
    database_path = Path(__file__).resolve().parent / "sales_demo.db"

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        result = connection.execute("""
            SELECT
                COUNT(*) AS tracked_days,
                COALESCE(SUM(is_complete), 0) AS complete_days
            FROM ingestion_status
            WHERE business_date >= ?
              AND business_date < ?
        """, (start.isoformat(), end.isoformat()))

        tracked_days, complete_days = result.fetchone()

    finally:
        connection.close()

    if tracked_days != expected_days or complete_days != expected_days:
        raise ValueError(
            f"Incomplete period: {complete_days} of "
            f"{expected_days} required days confirmed complete."
        )

    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "complete_days": complete_days,
        "status": "passed",
    }


if __name__ == "__main__":
    print(check_completeness("2026-08-01", "2026-09-01"))
    print(check_completeness("2026-09-01", "2026-10-01"))
