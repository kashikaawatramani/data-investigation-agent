import argparse
import json

from investigate_categories import compare_categories
from sales_metrics import get_sales_metrics
from evidence import save_evidence
from data_quality import check_data_quality


def main():
    parser = argparse.ArgumentParser(
        description="Run a sales investigation tool."
    )

    parser.add_argument(
        "--tool",
        choices=["metrics", "categories"],
        default="categories",
    )

    parser.add_argument("--previous-start")
    parser.add_argument("--current-start", required=True)
    parser.add_argument("--current-end", required=True)

    args = parser.parse_args()

    if args.tool == "categories" and not args.previous_start:
        parser.error("--previous-start is required for categories.")

    try:
        quality = check_data_quality()

        if quality["status"] != "passed":
            raise ValueError(
                "Data quality checks failed: "
                + json.dumps(quality["checks"])
            )

        if args.tool == "metrics":
            result = get_sales_metrics(
                start_date=args.current_start,
                end_date=args.current_end,
            )

        else:
            findings = compare_categories(
                previous_start=args.previous_start,
                current_start=args.current_start,
                current_end=args.current_end,
            )

            result = {
                "previous_start": args.previous_start,
                "current_start": args.current_start,
                "current_end": args.current_end,
                "findings": findings,
                "total_change_paise": sum(
                    finding["change_paise"] for finding in findings
                ),
            }

        inputs = {
            "current_start": args.current_start,
            "current_end": args.current_end,
        }

        if args.tool == "categories":
            inputs["previous_start"] = args.previous_start

        evidence = save_evidence(
            tool_name=args.tool,
            inputs=inputs,
            result=result,
        )

        report = {
            "status": "success",
            "tool": args.tool,
            "evidence": evidence,
            "result": result,
        }

        exit_code = 0

    except ValueError as error:
        report = {
            "status": "blocked",
            "tool": args.tool,
            "error": str(error),
        }

        exit_code = 1

    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())