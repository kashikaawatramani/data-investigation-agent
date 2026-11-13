import sqlite3
from pathlib import Path

project_folder = Path(__file__).resolve().parent
database_path = project_folder / "sales.db"

# Stop if our existing database is missing.
if not database_path.is_file():
    raise FileNotFoundError("Run setup_database.py first.")

connection = sqlite3.connect(database_path)

try:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            region TEXT NOT NULL
        )
    """)

    customers = [
        (1, "West"),
        (2, "North"),
        (3, "South"),
    ]

    connection.executemany("""
        INSERT INTO customers (customer_id, region)
        VALUES (?, ?)
        ON CONFLICT(customer_id) DO NOTHING
    """, customers)

    connection.commit()

    result = connection.execute("""
        SELECT customer_id, region
        FROM customers
        ORDER BY customer_id
    """)

    print("Customers stored in our database:")

    for row in result:
        print(row)

finally:
    connection.close()
