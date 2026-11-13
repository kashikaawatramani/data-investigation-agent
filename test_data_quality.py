import sqlite3
import tempfile
import unittest
from pathlib import Path

from data_quality import check_data_quality


class DataQualityTests(unittest.TestCase):

    def test_clean_database_passes(self):
        result = check_data_quality()

        self.assertEqual(result["status"], "passed")

    def test_completed_order_without_items_is_detected(self):
        source_path = (
            Path(__file__).resolve().parent / "sales_demo.db"
        )

        with tempfile.TemporaryDirectory() as temp_folder:
            test_path = Path(temp_folder) / "test.db"

            source = sqlite3.connect(
                source_path.as_uri() + "?mode=ro",
                uri=True,
            )
            test_database = sqlite3.connect(test_path)

            try:
                source.backup(test_database)

                order = test_database.execute("""
                    SELECT order_id
                    FROM orders
                    WHERE status = 'completed'
                    ORDER BY order_id
                    LIMIT 1
                """).fetchone()

                self.assertIsNotNone(order)

                test_database.execute("""
                    DELETE FROM order_items
                    WHERE order_id = ?
                """, (order[0],))

                test_database.commit()

            finally:
                source.close()
                test_database.close()

            result = check_data_quality(test_path)

            self.assertEqual(result["status"], "failed")

            self.assertEqual(
                result["checks"]["completed_orders_without_items"],
                1,
            )


if __name__ == "__main__":
    unittest.main()