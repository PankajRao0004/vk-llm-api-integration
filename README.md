# LLM API Integration — AI-1 Internship

A beginner-friendly chatbot backend built with Python, FastAPI, and
Google's Gemini API. The application supports multi-turn conversations,
SQLite persistence, and hybrid context management using a running
summary plus recent conversation messages.

## Features

- FastAPI `POST /chat` endpoint for sending messages to Gemini.
- Unique conversation IDs to keep conversations separate.
- SQLite storage for conversation history across server restarts.
- Running summaries of older exchanges combined with recent raw messages.
- System instructions defining the chatbot's role and response style.
- Environment-variable configuration for the Gemini API key.
- Input validation and controlled error responses.
- Automated tests for the SQLite storage layer.

## Architecture

1. The client sends a message and, when continuing a conversation,
   its conversation ID.
2. FastAPI validates the request.
3. The application retrieves the conversation and its saved summary
   from SQLite.
4. When unsummarized history exceeds the configured threshold, Gemini
   creates an updated summary of older completed exchanges.
5. The application sends the summary, recent message history, system
   instructions, and current message to Gemini.
6. After a successful response, the user message and assistant reply
   are saved to SQLite.
7. The response returns the reply and conversation ID to the client.

The original message transcript remains in SQLite. Summarization changes
the context sent to the model, not the original stored conversation.

### Context management

The initial implementation retains the latest six unsummarized messages
as individual context messages. When the threshold is exceeded, older
completed exchanges are incorporated into a running summary.

This threshold is a configurable engineering choice, not a guarantee
that every request fits within a model's token limit. Production systems
should also measure token usage and enforce a suitable context budget.

### Persistence

Conversation records and original messages are stored in the local
`conversations.db` SQLite file. Unlike an in-memory dictionary, this
database survives a server restart.

The database file is local and excluded from Git. It must not be deleted
if you want to preserve your saved conversations.

## Technology stack

- Python 3.10 or later
- FastAPI
- Uvicorn
- Google GenAI Python SDK
- SQLite (`sqlite3`, included with Python)
- Pydantic
- python-dotenv

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

If PowerShell blocks activation, use the Python executable directly
from `.venv\Scripts\python.exe` to install dependencies and run commands.

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Obtain an API key from
[Google AI Studio](https://aistudio.google.com/app/apikey).

Create a local `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Replace the placeholder with your own key.

Never commit `.env`, paste your API key into source code, or publish
the key in screenshots or messages.

Check the current Gemini model availability, usage limits, and pricing
for your account in Google's documentation.

### 5. Test the standalone Gemini connection

```powershell
python test_gemini.py
```

This sends one request to Gemini and prints the generated response.

### 6. Start the backend

```powershell
python -m uvicorn app:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## Using the chat endpoint

Send a `POST` request to `/chat`.

### Start a conversation

```json
{
  "message": "Remember my project code name is MAPLE-82."
}
```

The response contains a generated conversation ID:

```json
{
  "conversation_id": "returned-conversation-id",
  "reply": "Your response from Gemini..."
}
```

### Continue the same conversation

Use the actual ID returned by the first request:

```json
{
  "conversation_id": "returned-conversation-id",
  "message": "What was my project code name?"
}
```

The backend retrieves the saved history for that conversation.

Do not reuse an ID for a different conversation. An unknown conversation
ID returns a `404` response rather than silently starting a new one.

## Testing

Run the database tests:

```powershell
python -m unittest test_database.py -v
```

These tests check conversation creation, exchange storage, retrieval,
and summary progress using temporary databases.

For a complete manual check, use Swagger UI to:

1. Start a conversation and record the returned ID.
2. Send at least five messages using the same ID.
3. Ask the chatbot to recall an earlier detail.
4. Stop and restart Uvicorn.
5. Reuse the same ID and verify that the earlier information is recalled.
6. Send enough messages to trigger summarization and inspect the saved
   summary in SQLite.

## Project files

- `app.py` — FastAPI endpoint, Gemini integration, context selection,
  and summarization.
- `database.py` — SQLite schema, conversation storage, and summary tracking.
- `test_database.py` — automated tests for the storage layer.
- `test_gemini.py` — standalone Gemini connection check.
- `requirements.txt` — direct project dependencies.
- `.env` — local secrets and configuration; not committed to Git.
- `conversations.db` — local conversation storage; not committed to Git.

## Security and limitations

- Keep API keys in environment variables.
- Do not publish `.env` or local conversation databases.
- The current setup is intended for local development, not a publicly
  exposed production service.
- SQLite is appropriate for this small project; larger deployments may
  require a server database, authentication, and additional operational
  controls.
- Summaries can omit details, so the original transcript is retained
  for future retrieval and improved context strategies.

## Internship task

AI-1: LLM API Integration — a chatbot using a real LLM API, multi-turn
conversation history, context-window management, system instructions,
and basic error handling.