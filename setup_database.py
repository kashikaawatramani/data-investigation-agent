
import sqlite3
from pathlib import Path

# Find this script's folder.
project_folder = Path(__file__).resolve().parent
database_path = project_folder / "sales.db"

# Open or create the database.
connection = sqlite3.connect(database_path)

try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    products = [
        (1, "Laptop", "Electronics"),
        (2, "Headphones", "Electronics"),
        (3, "Office Chair", "Furniture"),
    ]

    connection.executemany("""
        INSERT INTO products (
            product_id, product_name, category
        )
        VALUES (?, ?, ?)
        ON CONFLICT(product_id) DO NOTHING
    """, products)

    connection.commit()

    result = connection.execute("""
        SELECT product_id, product_name, category
        FROM products
        ORDER BY product_id
    """)

    print("Products stored in our database:")

    for row in result:
        print(row)

finally:
    connection.close()

