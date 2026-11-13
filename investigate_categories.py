import sqlite3
from datetime import date
from pathlib import Path
from quality_checks import check_completeness

def compare_categories(previous_start, current_start, current_end):
    """Compare category revenue across two adjacent date ranges."""

    # Validate dates before querying the database.
    boundaries = [
        date.fromisoformat(previous_start),
        date.fromisoformat(current_start),
        date.fromisoformat(current_end),
    ]

    if not boundaries[0] < boundaries[1] < boundaries[2]:
        raise ValueError("Dates must be in increasing order.")

    # Use a consistent YYYY-MM-DD format.
    previous_start, current_start, current_end = [
        boundary.isoformat() for boundary in boundaries
    ]
    check_completeness(previous_start, current_start)
    check_completeness(current_start, current_end)
    database_path = Path(__file__).resolve().parent / "sales_demo.db"

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        result = connection.execute("""
            SELECT
                p.category,
                SUM(
                    CASE
                        WHEN o.ordered_at < :current_start
                        THEN oi.quantity * oi.unit_price_paise
                             - oi.discount_paise
                        ELSE 0
                    END
                ) AS previous_paise,
                SUM(
                    CASE
                        WHEN o.ordered_at >= :current_start
                        THEN oi.quantity * oi.unit_price_paise
                             - oi.discount_paise
                        ELSE 0
                    END
                ) AS current_paise
            FROM orders AS o
            JOIN order_items AS oi ON o.order_id = oi.order_id
            JOIN products AS p ON oi.product_id = p.product_id
            WHERE o.status = 'completed'
              AND o.ordered_at >= :previous_start
              AND o.ordered_at < :current_end
            GROUP BY p.category
            ORDER BY p.category
        """, {
            "previous_start": previous_start,
            "current_start": current_start,
            "current_end": current_end,
        })

        findings = []

        for category, previous_paise, current_paise in result:
            findings.append({
                "category": category,
                "previous_paise": previous_paise,
                "current_paise": current_paise,
                "change_paise": current_paise - previous_paise,
            })

        return findings

    finally:
        connection.close()


if __name__ == "__main__":
    findings = compare_categories(
        previous_start="2026-08-01",
        current_start="2026-09-01",
        current_end="2026-10-01",
    )

    total_change_paise = 0

    for finding in findings:
        print(finding["category"])
        print(f"  Previous: INR {finding['previous_paise'] / 100:,.2f}")
        print(f"  Current: INR {finding['current_paise'] / 100:,.2f}")
        print(f"  Change: INR {finding['change_paise'] / 100:,.2f}")

        total_change_paise += finding["change_paise"]

    print(
        "\nTotal category change: "
        f"INR {total_change_paise / 100:,.2f}"
    )
