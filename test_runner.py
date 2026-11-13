import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from run_investigation import main


class RunnerTests(unittest.TestCase):

    def test_bad_data_blocks_investigation(self):
        failed_quality = {
            "status": "failed",
            "checks": {
                "completed_orders_without_items": 1,
                "broken_relationships": 0,
                "invalid_items": 0,
                "invalid_order_statuses": 0,
            },
        }

        command = [
            "run_investigation.py",
            "--tool", "metrics",
            "--current-start", "2026-09-01",
            "--current-end", "2026-10-01",
        ]

        output = io.StringIO()

        with (
            patch("sys.argv", command),
            patch(
                "run_investigation.check_data_quality",
                return_value=failed_quality,
            ),
            patch(
                "run_investigation.get_sales_metrics"
            ) as metrics_tool,
            patch(
                "run_investigation.save_evidence"
            ) as evidence_writer,
            redirect_stdout(output),
        ):
            exit_code = main()

        report = json.loads(output.getvalue())

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("Data quality checks failed", report["error"])

        metrics_tool.assert_not_called()
        evidence_writer.assert_not_called()


if __name__ == "__main__":
    unittest.main()

    

    