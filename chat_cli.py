
"""A simple terminal interface for our Gemini chatbot."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Address of the FastAPI backend running on our own computer.
CHAT_ENDPOINT = "http://127.0.0.1:8000/chat"


def send_message(message: str, conversation_id: str | None) -> dict:
    """Send a message to FastAPI and return its JSON response."""

    # Include the conversation ID when continuing an existing conversation.
    # Omitting it tells the backend to start a new conversation.
    payload = {"message": message}

    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    # Convert the Python dictionary into JSON bytes for the HTTP request.
    request = Request(
        CHAT_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    # Wait for the backend response. Model requests can take some time.
    with urlopen(request, timeout=120) as response:
        response_text = response.read().decode("utf-8")
        return json.loads(response_text)


def main() -> None:
    """Run the interactive chat until the user exits."""

    # None means our first message will start a new conversation.
    conversation_id = None

    print("Welcome to the Gemini Chatbot!")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        try:
            message = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            # Allow a clean exit with Ctrl+C or the terminal's end-of-input.
            print("\nChat ended.")
            break

        if not message:
            # Ignore empty input rather than sending it to the API.
            continue

        if message.lower() in {"exit", "quit"}:
            print("Chat ended.")
            break

        try:
            # Send the message using the current conversation ID.
            result = send_message(message, conversation_id)

            # The backend returns the ID that future messages must reuse.
            returned_id = result.get("conversation_id")
            reply = result.get("reply")

            if not returned_id or not reply:
                print("The backend returned an unexpected response.")
                continue

            # Save the ID after the first successful response.
            conversation_id = returned_id

            print(f"\nBot: {reply}\n")

        except HTTPError as error:
            # FastAPI may return a JSON error such as {"detail": "..."}.
            error_body = error.read().decode("utf-8")

            try:
                detail = json.loads(error_body).get("detail", error_body)
            except json.JSONDecodeError:
                detail = error_body or str(error.reason)

            print(f"\nRequest failed (HTTP {error.code}): {detail}\n")

        except (URLError, TimeoutError) as error:
            # Explain connection problems without crashing the CLI.
            print(f"\nCould not reach the backend: {error}\n")

        except json.JSONDecodeError:
            print("\nThe backend returned an invalid JSON response.\n")


# Start the chat only when we run this file directly.
if __name__ == "__main__":
    main()
