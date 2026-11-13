import unittest

from investigate_categories import compare_categories
from sales_metrics import get_sales_metrics


class InvestigationTests(unittest.TestCase):

    def test_september_metrics(self):
        result = get_sales_metrics(
            "2026-09-01",
            "2026-10-01",
        )

        self.assertEqual(
            result["revenue_paise"],
            6592800000,
        )

        self.assertEqual(
            result["completed_orders"],
            814,
        )

        self.assertAlmostEqual(
            result["average_order_value_paise"],
            6592800000 / 814,
            places=5,
        )

    def test_category_changes_reconcile(self):
        august = get_sales_metrics(
            "2026-08-01",
            "2026-09-01",
        )

        september = get_sales_metrics(
            "2026-09-01",
            "2026-10-01",
        )

        findings = compare_categories(
            "2026-08-01",
            "2026-09-01",
            "2026-10-01",
        )

        category_change = sum(
            finding["change_paise"]
            for finding in findings
        )

        overall_change = (
            september["revenue_paise"]
            - august["revenue_paise"]
        )

        self.assertEqual(
            category_change,
            overall_change,
        )

    def test_missing_period_is_blocked(self):
        with self.assertRaisesRegex(
            ValueError,
            "Incomplete period",
        ):
            get_sales_metrics(
                "2026-11-01",
                "2026-12-01",
            )


if __name__ == "__main__":
    unittest.main()