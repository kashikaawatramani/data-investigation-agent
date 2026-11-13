import json
from urllib.request import Request, urlopen


def call_ollama(endpoint, payload):
    request = Request(
        url=f"http://localhost:11434/api/{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        return json.load(response)


if __name__ == "__main__":
    model = "qwen2.5:0.5b"

    details = call_ollama("show", {"model": model})

    print("Model:", model)
    print("Capabilities:", details.get("capabilities", "Not reported"))

    reply = call_ollama("chat", {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Explain revenue and average order value "
                    "in two short sentences. Do not invent sales figures."
                ),
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": 2048,
            "num_predict": 128,
        },
    })

    print("\nModel response:")
    print(reply["message"]["content"])