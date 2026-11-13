import sqlite3
from pathlib import Path

project_folder = Path(__file__).resolve().parent
database_path = project_folder / "sales.db"

if not database_path.is_file():
    raise FileNotFoundError("Run setup_database.py first.")

connection = sqlite3.connect(database_path)

# Enforce foreign-key relationships on this connection.
connection.execute("PRAGMA foreign_keys = ON")

try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            ordered_at TEXT NOT NULL,
            region_at_order TEXT NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN ('completed', 'cancelled')),
            FOREIGN KEY (customer_id)
                REFERENCES customers(customer_id)
        )
    """)

    orders = [
        (1, 1, "2026-08-05", "West", "Online", "completed"),
        (2, 2, "2026-08-12", "North", "Store", "completed"),
        (3, 1, "2026-09-05", "West", "Online", "completed"),
        (4, 3, "2026-09-12", "South", "Store", "cancelled"),
    ]

    connection.executemany("""
        INSERT INTO orders (
            order_id,
            customer_id,
            ordered_at,
            region_at_order,
            channel,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(order_id) DO NOTHING
    """, orders)

    connection.commit()

    result = connection.execute("""
        SELECT order_id, customer_id, ordered_at, status
        FROM orders
        ORDER BY order_id
    """)

    print("Orders stored in our database:")

    for row in result:
        print(row)

finally:
    connection.close()
