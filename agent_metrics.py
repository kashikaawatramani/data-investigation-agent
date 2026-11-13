import json

from data_quality import check_data_quality
from evidence import save_evidence
from investigate_categories import compare_categories
from model_connection import call_ollama
from sales_metrics import get_sales_metrics


MODEL = "qwen2.5:0.5b"
OPTIONS = {"temperature": 0, "num_ctx": 2048, "num_predict": 256}

TOOL_FUNCTIONS = {
    "get_sales_metrics": get_sales_metrics,
    "compare_categories": compare_categories,
}


def tool_schema(name, description, dates):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    key: {
                        "type": "string",
                        "description": f"{meaning} in YYYY-MM-DD format",
                    }
                    for key, meaning in dates.items()
                },
                "required": list(dates),
                "additionalProperties": False,
            },
        },
    }


TOOLS = [
    tool_schema(
        "get_sales_metrics",
        "Calculate revenue, completed orders, and average order value "
        "for one period.",
        {
            "start_date": "Inclusive start date",
            "end_date": "Exclusive end date",
        },
    ),
    tool_schema(
        "compare_categories",
        "Compare category revenue across two adjacent periods. "
        "Use this to investigate which categories contributed to "
        "a revenue increase or decrease.",
        {
            "previous_start": "Inclusive start of the earlier period",
            "current_start": "Start of the later period and end of the earlier period",
            "current_end": "Exclusive end of the later period",
        },
    ),
]


def format_inr(paise):
    return f"{paise / 100:,.2f}" if paise is not None else None


def main():
    question = input("Ask a sales question: ").strip()

    if not question:
        raise SystemExit("Enter a sales question and try again.")

    user_message = {"role": "user", "content": question}

    response = call_ollama("chat", {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Choose get_sales_metrics for metrics for one period. "
                    "Choose compare_categories for category changes "
                    "across two adjacent periods. "
                    "Date ranges include the start and exclude the end. "
                    "Ask for clarification if the period is unclear."
                ),
            },
            user_message,
        ],
        "tools": TOOLS,
        "stream": False,
        "options": OPTIONS,
    })

    message = response["message"]
    tool_calls = message.get("tool_calls") or []

    print("\nRequested tool calls:")
    print(json.dumps(tool_calls, indent=2))

    if not tool_calls:
        print(message.get("content") or "No tool call returned. Try explicit dates.")
        return

    if len(tool_calls) != 1:
        raise SystemExit("Ask one investigation question at a time.")

    function = tool_calls[0].get("function", {})
    tool_name = function.get("name")
    arguments = function.get("arguments")

    if tool_name not in TOOL_FUNCTIONS:
        raise SystemExit(f"Unsupported tool: {tool_name}")

    schema = next(tool["function"] for tool in TOOLS
                  if tool["function"]["name"] == tool_name)
    required_dates = set(schema["parameters"]["required"])

    if not isinstance(arguments, dict) or set(arguments) != required_dates:
        raise SystemExit("The tool request is missing dates or has extra arguments.")

    if not all(isinstance(value, str) for value in arguments.values()):
        raise SystemExit("Dates must be strings.")

    try:
        quality = check_data_quality()

        if quality["status"] != "passed":
            raise ValueError("Data quality checks failed.")

        tool_result = TOOL_FUNCTIONS[tool_name](**arguments)

    except ValueError as error:
        print(json.dumps({"status": "blocked", "error": str(error)}, indent=2))
        raise SystemExit(1)

    if tool_name == "compare_categories":
        total_change = sum(row["change_paise"] for row in tool_result)
        result = {
            **arguments,
            "findings": tool_result,
            "total_change_paise": total_change,
        }
        display_result = {
            **arguments,
            "total_change_inr": format_inr(total_change),
            "categories": [
                {
                    "category": row["category"],
                    "change_inr": format_inr(row["change_paise"]),
                }
                for row in tool_result
            ],
        }
    else:
        result = tool_result
        display_result = {
            "start_date": result["start_date"],
            "end_date_exclusive": result["end_date"],
            "revenue_inr": format_inr(result["revenue_paise"]),
            "completed_orders": result["completed_orders"],
            "average_order_value_inr": format_inr(
                result["average_order_value_paise"]
            ),
            "completeness_status": result["completeness_status"],
        }

    evidence = save_evidence(
        tool_name=tool_name,
        inputs=arguments,
        result=result,
    )

    print("\nExecuted tool result:")
    print(json.dumps({
        "status": "success",
        "tool": tool_name,
        "evidence": evidence,
        "result": result,
    }, indent=2))

    final_response = call_ollama("chat", {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Briefly explain the supplied tool result. "
                    "Use only its facts. Copy monetary values exactly "
                    "and label them INR. End dates are exclusive. "
                    "For category changes, negative means a decrease "
                    "and positive means an increase. "
                    "Do not invent business causes."
                ),
            },
            user_message,
            message,
            {
                "role": "tool",
                "tool_name": tool_name,
                "content": json.dumps(display_result),
            },
        ],
        "stream": False,
        "options": OPTIONS,
    })

    explanation = final_response["message"].get("content", "").strip()
    print("\nModel explanation — check against the tool result:")
    print(explanation or "No explanation returned.")


if __name__ == "__main__":
    main()