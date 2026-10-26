# LLM API Integration — AI-1 Internship

A beginner-friendly chatbot backend built with Python, FastAPI, and Google's Gemini API. The application supports multi-turn conversations, persistent conversation history using SQLite, and hybrid context management using a running summary and recent messages.

## Features

- FastAPI `POST /chat` endpoint for sending user messages to Gemini.
- Unique conversation IDs to keep conversations separate.
- SQLite storage for conversation history across server restarts.
- Running summaries of older exchanges combined with recent messages.
- System instructions defining the chatbot's role and response style.
- API key configuration through environment variables.
- Input validation and controlled error responses.
- Interactive command-line interface (CLI).
- Automated tests for the SQLite storage layer.

## Architecture

The application follows this request flow:

1. The client sends a message and, when continuing an existing conversation, its conversation ID.
2. FastAPI validates the incoming request.
3. The application retrieves the conversation and its saved summary from SQLite.
4. When the number of unsummarized messages exceeds the configured threshold, Gemini generates an updated summary of older completed exchanges.
5. The application combines the summary, recent conversation history, system instructions, and current message, then sends the request to Gemini.
6. After receiving a valid response, the application saves the user message and assistant reply to SQLite.
7. The backend returns the reply and conversation ID to the client.

The original message transcript remains in SQLite. Summarization changes the context sent to the model, not the original stored conversation.

## Context Management

The application uses a hybrid context-management strategy:

- **Running summary:** Older exchanges are compressed into a summary that preserves important facts, preferences, decisions, and constraints.
- **Recent messages:** The latest six unsummarized messages are retained individually to preserve more precise conversational details.
- **System instruction:** Defines the chatbot's role and behaviour and is included with each model request.

When the number of unsummarized messages exceeds the configured threshold, the application summarizes older completed exchanges and retains recent messages.

The six-message threshold is an implementation choice, not a guarantee that every request fits within a model's token limit. Summaries can omit important details or lose nuance. The original transcript is retained in SQLite, and a production implementation should also measure token usage and enforce an appropriate context budget.

## Persistence

Conversation records, summaries, and original messages are stored in the local `conversations.db` SQLite file.

Unlike an in-memory dictionary, the database survives a server restart. Clients can continue an existing conversation by supplying its saved conversation ID to the API.

The current CLI automatically reuses the conversation ID returned by the backend during a single session. It does not currently prompt for a previously saved ID when starting a new CLI session; use the API or Swagger UI to resume an existing conversation after a restart.

The database file is local and excluded from Git. Do not delete it if you want to preserve your saved conversations.

## Technology Stack

- Python 3.10 or later
- FastAPI
- Uvicorn
- Google GenAI Python SDK
- SQLite (`sqlite3`, included with Python)
- Pydantic
- `python-dotenv`

## Setup on Windows

### 1. Clone the repository

```powershell
git clone https://github.com/PankajRao0004/vk-llm-api-integration.git
cd vk-llm-api-integration
```

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the virtual environment's Python executable directly to install dependencies and run commands.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

Create a local `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Replace the placeholder with your actual key. The configured model must be available to your Gemini API account.

Never commit `.env`, hardcode your API key in source code, or publish the key in screenshots or messages. The root `.gitignore` excludes `.env` and local database files from Git.

### 5. Test the standalone Gemini connection

```powershell
python test_gemini.py
```

This sends one request to Gemini and prints the generated response.

### 6. Start the backend

```powershell
python -m uvicorn app:app --reload
```

Keep this terminal running while using the application.

Open the interactive API documentation in your browser:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Interactive CLI

The project includes a simple command-line interface for chatting with the backend without manually sending JSON requests.

### Run the CLI

Start the FastAPI backend in one terminal:

```powershell
python -m uvicorn app:app --reload
```

Open a second terminal in the project folder and run:

```powershell
python chat_cli.py
```

Type a message at the `You:` prompt. The CLI automatically reuses the conversation ID returned by the backend, allowing you to continue the same conversation during that session.

Type `exit` or `quit` to end the session.

The CLI displays clear messages for HTTP errors, connection failures, and invalid JSON responses. To resume a previous conversation after restarting the server, use its saved conversation ID with the API as described below.

## Using the Chat Endpoint

Send a `POST` request to `/chat`.

### Start a conversation

Send a JSON request body containing the message:

```json
{
  "message": "Remember my project code name is MAPLE-82."
}
```

The response contains a generated conversation ID and the chatbot's reply:

```json
{
  "conversation_id": "returned-conversation-id",
  "reply": "Your response from Gemini..."
}
```

Copy the actual conversation ID from the response.

### Continue the same conversation

Include the returned ID in subsequent requests:

```json
{
  "conversation_id": "returned-conversation-id",
  "message": "What was my project code name?"
}
```

The backend retrieves the saved history for that conversation and constructs the context sent to Gemini.

Do not reuse a conversation ID for an unrelated conversation. An unknown conversation ID returns a `404` response rather than silently starting a new conversation.

## Testing

Run the database tests:

```powershell
python -m unittest test_database.py -v
```

The automated tests check conversation creation and retrieval, message storage, and summary-progress tracking using temporary databases.

For a complete manual verification:

1. Start the backend and open the CLI or Swagger UI.
2. Send at least five messages within one conversation, reusing the same conversation ID.
3. Ask the chatbot to recall a detail from an earlier message without repeating it.
4. Stop and restart Uvicorn.
5. Reuse the same conversation ID and verify that earlier information can still be recalled.
6. Send enough messages to exceed the context threshold.
7. Inspect the saved summary in SQLite and verify that older messages remain stored.

API-backed tests require a valid Gemini API key, network access, and an available model. A provider outage or rate limit may cause requests to fail even when the local application is configured correctly.

## Project Files

- `app.py` — FastAPI endpoint, Gemini integration, conversation context selection, and summarization.
- `database.py` — SQLite schema, conversation storage, original model-step storage, and summary tracking.
- `chat_cli.py` — interactive terminal interface for the chatbot.
- `test_database.py` — automated tests for the database storage layer.
- `test_gemini.py` — standalone Gemini connection check.
- `requirements.txt` — project dependencies.
- `README.md` — setup, architecture, usage, and testing instructions.
- `.gitignore` — excludes private configuration and local development files.

The local `.env` file and `conversations.db` file are intentionally not committed to the public repository.

## Security and Limitations

- Keep API keys in environment variables.
- Never publish `.env` or local conversation databases.
- The application is intended for local development and learning, not as a publicly exposed production service.
- The current implementation does not include user authentication or authorization. Anyone who can access the local endpoint may be able to interact with it.
- SQLite is appropriate for this small project. Larger deployments or multiple concurrent application instances may require a server-based database and additional operational controls.
- Conversation history is stored locally and persists until the database is removed.
- Summaries can omit details, so the original transcript is retained for future retrieval and improved context strategies.
- API failures are returned as controlled error responses, but a response-generation failure can still occur because of network problems, rate limits, invalid configuration, or provider availability.

## Internship Task

**AI-1: LLM API Integration** — a chatbot backed by a real LLM API, supporting multi-turn conversation history, context-window management, a defined system prompt, basic error handling, and secure API key configuration.
