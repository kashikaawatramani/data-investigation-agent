import csv
import random
from datetime import date, timedelta
from pathlib import Path

# A fixed seed makes the generated records reproducible.
rng = random.Random(42)

project_folder = Path(__file__).resolve().parent
output_folder = project_folder / "synthetic_data"
output_folder.mkdir(exist_ok=True)

# Match the customers and products already in our database.
customers = [
    (1, "West"),
    (2, "North"),
    (3, "South"),
]

product_prices = {
    1: 5000000,  # Laptop: INR 50,000
    2: 200000,   # Headphones: INR 2,000
    3: 800000,   # Office Chair: INR 8,000
}

order_count = 0
item_count = 0

orders_path = output_folder / "orders.csv"
items_path = output_folder / "order_items.csv"

with (
    orders_path.open("w", newline="", encoding="utf-8") as orders_file,
    items_path.open("w", newline="", encoding="utf-8") as items_file
):
    orders_writer = csv.writer(orders_file)
    items_writer = csv.writer(items_file)

    orders_writer.writerow([
        "order_id",
        "customer_id",
        "ordered_at",
        "region_at_order",
        "channel",
        "status",
    ])

    items_writer.writerow([
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price_paise",
        "discount_paise",
    ])

    current_date = date(2026, 5, 1)
    end_date = date(2026, 11, 1)

    while current_date < end_date:
        # Intentionally create fewer orders in September.
        daily_orders = 30 if current_date.month == 9 else 60

        for _ in range(daily_orders):
            order_count += 1

            customer_id, region = rng.choice(customers)
            channel = rng.choice(["Online", "Store"])
            status = (
                "cancelled" if rng.random() < 0.1 else "completed"
            )

            orders_writer.writerow([
                order_count,
                customer_id,
                current_date.isoformat(),
                region,
                channel,
                status,
            ])

            # Each order contains between one and three products.
            selected_products = rng.sample(
                list(product_prices),
                k=rng.randint(1, 3)
            )

            for product_id in selected_products:
                item_count += 1

                items_writer.writerow([
                    item_count,
                    order_count,
                    product_id,
                    rng.randint(1, 3),
                    product_prices[product_id],
                    0,
                ])

        current_date += timedelta(days=1)

print("Synthetic sales files created.")
print("Period: 2026-05-01 to 2026-10-31")
print(f"Orders: {order_count}")
print(f"Order items: {item_count}")
print(f"Files saved in: {output_folder}")
