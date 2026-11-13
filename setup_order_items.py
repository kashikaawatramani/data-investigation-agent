import sqlite3
from pathlib import Path

project_folder = Path(__file__).resolve().parent
database_path = project_folder / "sales.db"

if not database_path.is_file():
    raise FileNotFoundError("Run setup_database.py first.")

connection = sqlite3.connect(database_path)
connection.execute("PRAGMA foreign_keys = ON")

try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price_paise INTEGER NOT NULL
                CHECK (unit_price_paise >= 0),
            discount_paise INTEGER NOT NULL DEFAULT 0
                CHECK (
                    discount_paise >= 0
                    AND discount_paise <= quantity * unit_price_paise
                ),
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    order_items = [
        # Item ID, order ID, product ID, quantity, price, discount
        (1, 1, 1, 1, 5000000, 0),
        (2, 1, 2, 2, 200000, 0),
        (3, 2, 3, 1, 800000, 0),
        (4, 3, 2, 1, 200000, 0),
        (5, 4, 3, 1, 800000, 0),
    ]

    connection.executemany("""
        INSERT INTO order_items (
            order_item_id,
            order_id,
            product_id,
            quantity,
            unit_price_paise,
            discount_paise
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(order_item_id) DO NOTHING
    """, order_items)

    connection.commit()

    result = connection.execute("""
        SELECT order_item_id, order_id, product_id, quantity
        FROM order_items
        ORDER BY order_item_id
    """)

    print("Order items stored in our database:")

    for row in result:
        print(row)

finally:
    connection.close()
