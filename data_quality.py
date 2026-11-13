import json
import sqlite3
from pathlib import Path


def check_data_quality(database_path=None):
    """Inspect the loaded database for structural data defects."""

    if database_path is None:
        database_path = (
            Path(__file__).resolve().parent / "sales_demo.db"
        )

    database_path = Path(database_path).resolve()

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=ro",
        uri=True,
    )

    try:
        # Completed orders must contain at least one item.
        orders_without_items = connection.execute("""
            SELECT COUNT(*)
            FROM orders AS o
            WHERE o.status = 'completed'
              AND NOT EXISTS (
                  SELECT 1
                  FROM order_items AS oi
                  WHERE oi.order_id = o.order_id
              )
        """).fetchone()[0]

        # Check relationships declared through foreign keys.
        broken_relationships = len(
            connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
        )

        # Check item quantities, prices, and line discounts.
        invalid_items = connection.execute("""
            SELECT COUNT(*)
            FROM order_items
            WHERE quantity IS NULL
               OR quantity <= 0
               OR unit_price_paise IS NULL
               OR unit_price_paise < 0
               OR discount_paise IS NULL
               OR discount_paise < 0
               OR discount_paise > quantity * unit_price_paise
        """).fetchone()[0]

        # Only our supported order statuses are allowed.
        invalid_statuses = connection.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status IS NULL
               OR status NOT IN ('completed', 'cancelled')
        """).fetchone()[0]

        checks = {
            "completed_orders_without_items": orders_without_items,
            "broken_relationships": broken_relationships,
            "invalid_items": invalid_items,
            "invalid_order_statuses": invalid_statuses,
        }

        return {
            "status": (
                "passed"
                if all(count == 0 for count in checks.values())
                else "failed"
            ),
            "checks": checks,
        }

    finally:
        connection.close()


if __name__ == "__main__":
    print(json.dumps(check_data_quality(), indent=2))