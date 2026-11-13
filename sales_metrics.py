import json
import sqlite3
from pathlib import Path

from quality_checks import check_completeness


def get_sales_metrics(start_date, end_date):
    """Calculate sales metrics for [start_date, end_date)."""

    completeness = check_completeness(start_date, end_date)

    database_path = Path(__file__).resolve().parent / "sales_demo.db"

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        revenue_paise, order_count = connection.execute("""
            SELECT
                COALESCE(SUM(order_revenue_paise), 0),
                COUNT(*)
            FROM (
                SELECT
                    o.order_id,
                    COALESCE(
                        SUM(
                            oi.quantity * oi.unit_price_paise
                            - oi.discount_paise
                        ),
                        0
                    ) AS order_revenue_paise
                FROM orders AS o
                LEFT JOIN order_items AS oi
                    ON o.order_id = oi.order_id
                WHERE o.status = 'completed'
                  AND o.ordered_at >= ?
                  AND o.ordered_at < ?
                GROUP BY o.order_id
            )
        """, (
            completeness["start_date"],
            completeness["end_date"],
        )).fetchone()

        average_order_value_paise = (
            revenue_paise / order_count
            if order_count > 0
            else None
        )

        return {
            "start_date": completeness["start_date"],
            "end_date": completeness["end_date"],
            "revenue_paise": revenue_paise,
            "completed_orders": order_count,
            "average_order_value_paise": average_order_value_paise,
            "completeness_status": completeness["status"],
        }

    finally:
        connection.close()


if __name__ == "__main__":
    result = get_sales_metrics("2026-08-01", "2026-09-01")
    print(json.dumps(result, indent=2))
