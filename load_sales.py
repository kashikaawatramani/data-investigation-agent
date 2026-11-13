import csv
import sqlite3
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

project_folder = Path(__file__).resolve().parent
source_path = project_folder / "sales.db"
output_path = project_folder / "sales_demo.db"
data_folder = project_folder / "synthetic_data"

# Read the generated files before building the database.
with (data_folder / "orders.csv").open(
    newline="", encoding="utf-8"
) as file:
    orders = [
        (
            int(row["order_id"]),
            int(row["customer_id"]),
            row["ordered_at"],
            row["region_at_order"],
            row["channel"],
            row["status"],
        )
        for row in csv.DictReader(file)
    ]

with (data_folder / "order_items.csv").open(
    newline="", encoding="utf-8"
) as file:
    items = [
        (
            int(row["order_item_id"]),
            int(row["order_id"]),
            int(row["product_id"]),
            int(row["quantity"]),
            int(row["unit_price_paise"]),
            int(row["discount_paise"]),
        )
        for row in csv.DictReader(file)
    ]

# Build a temporary database; publish it only after checks pass.
with tempfile.TemporaryDirectory(dir=project_folder) as temp_folder:
    build_path = Path(temp_folder) / "build.db"

    source = sqlite3.connect(
        source_path.as_uri() + "?mode=ro",
        uri=True
    )
    connection = sqlite3.connect(build_path)

    try:
        # Copy existing tables, customers, and products.
        source.backup(connection)
    finally:
        source.close()

    connection.execute("PRAGMA foreign_keys = ON")

    try:
        with connection:
            # Replace sample records only in the temporary copy.
            connection.execute("DELETE FROM order_items")
            connection.execute("DELETE FROM orders")
            connection.execute("DELETE FROM ingestion_status")

            connection.executemany("""
                INSERT INTO orders (
                    order_id, customer_id, ordered_at,
                    region_at_order, channel, status
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, orders)

            connection.executemany("""
                INSERT INTO order_items (
                    order_item_id, order_id, product_id,
                    quantity, unit_price_paise, discount_paise
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, items)

            # Check that every expected date has its generated orders.
            daily_counts = dict(connection.execute("""
                SELECT ordered_at, COUNT(*)
                FROM orders
                GROUP BY ordered_at
            """))

            current_date = date(2026, 5, 1)
            end_date = date(2026, 11, 1)
            completeness = []
            loaded_at = datetime.now(timezone.utc).isoformat()

            while current_date < end_date:
                day = current_date.isoformat()
                expected = 30 if current_date.month == 9 else 60

                if daily_counts.get(day) != expected:
                    raise ValueError(f"Unexpected order count: {day}")

                completeness.append((day, 1, loaded_at))
                current_date += timedelta(days=1)

            if len(daily_counts) != len(completeness):
                raise ValueError("Unexpected dates in the dataset.")

            broken_links = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()

            if broken_links:
                raise ValueError("Broken database relationships found.")

            connection.executemany("""
                INSERT INTO ingestion_status (
                    business_date, is_complete, loaded_at
                )
                VALUES (?, ?, ?)
            """, completeness)

            order_count = connection.execute(
                "SELECT COUNT(*) FROM orders"
            ).fetchone()[0]

            item_count = connection.execute(
                "SELECT COUNT(*) FROM order_items"
            ).fetchone()[0]

            if order_count != len(orders) or item_count != len(items):
                raise ValueError("Loaded counts do not match CSV counts.")

    finally:
        connection.close()

    # Replace the generated demo database after successful validation.
    build_path.replace(output_path)

print("Demo database built successfully.")
print(f"Orders loaded: {order_count}")
print(f"Order items loaded: {item_count}")
print(f"Complete synthetic days: {len(completeness)}")
print("Database: sales_demo.db")
