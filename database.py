
"""SQLite storage for conversations, messages, and Gemini response steps."""

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3


# Keep the database beside this file, regardless of the terminal's location.
DATABASE_PATH = Path(__file__).resolve().parent / "conversations.db"


def current_timestamp() -> str:
    """Return the current time in UTC for saved records."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    """Open a connection, commit successful changes, and always close it."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the tables and safely update an older messages table."""

    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL DEFAULT '',
                summarized_through_message_id INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                model_steps_json TEXT,

                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(conversation_id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id_id
                ON messages(conversation_id, id);
            """
        )

        # CREATE TABLE IF NOT EXISTS does not add columns to an existing
        # table. Check first so this works with an older database too.
        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        }

        if "model_steps_json" not in columns:
            connection.execute(
                "ALTER TABLE messages ADD COLUMN model_steps_json TEXT"
            )


def create_conversation(conversation_id: str) -> None:
    """Create a new conversation without overwriting existing records."""
    timestamp = current_timestamp()

    with database_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO conversations (
                conversation_id, summary,
                summarized_through_message_id, created_at, updated_at
            )
            VALUES (?, '', NULL, ?, ?)
            """,
            (conversation_id, timestamp, timestamp),
        )


def get_conversation(conversation_id: str) -> dict | None:
    """Retrieve conversation metadata, or None if its ID is unknown."""

    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT conversation_id, summary,
                   summarized_through_message_id, created_at, updated_at
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

        return dict(row) if row is not None else None


def get_unsummarized_messages(conversation_id: str) -> list[dict]:
    """Return messages not yet included in the running summary."""

    with database_connection() as connection:
        conversation = connection.execute(
            """
            SELECT summarized_through_message_id
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,),
        ).fetchone()

        if conversation is None:
            return []

        last_summarized_id = conversation["summarized_through_message_id"]

        rows = connection.execute(
            """
            SELECT id, role, content, created_at, model_steps_json
            FROM messages
            WHERE conversation_id = ?
              AND (? IS NULL OR id > ?)
            ORDER BY id
            """,
            (
                conversation_id,
                last_summarized_id,
                last_summarized_id,
            ),
        ).fetchall()

        return [dict(row) for row in rows]


def save_exchange(
    conversation_id: str,
    user_message: str,
    assistant_reply: str,
    assistant_steps: list[dict] | None = None,
) -> tuple[int, int]:
    """
    Save a successful exchange in one transaction.

    Keep the human-readable reply for the database transcript, and also
    preserve Gemini's original model-generated steps for later requests.
    """

    timestamp = current_timestamp()

    # Store the exact returned steps as JSON instead of reconstructing them
    # from the assistant's text. JSON lets us save structured Python data.
    steps_json = json.dumps(assistant_steps or [], ensure_ascii=False)

    with database_connection() as connection:
        user_cursor = connection.execute(
            """
            INSERT INTO messages (
                conversation_id, role, content, created_at, model_steps_json
            )
            VALUES (?, 'user', ?, ?, NULL)
            """,
            (conversation_id, user_message, timestamp),
        )
        user_message_id = int(user_cursor.lastrowid)

        assistant_cursor = connection.execute(
            """
            INSERT INTO messages (
                conversation_id, role, content, created_at, model_steps_json
            )
            VALUES (?, 'assistant', ?, ?, ?)
            """,
            (
                conversation_id,
                assistant_reply,
                timestamp,
                steps_json,
            ),
        )
        assistant_message_id = int(assistant_cursor.lastrowid)

        connection.execute(
            """
            UPDATE conversations
            SET updated_at = ?
            WHERE conversation_id = ?
            """,
            (timestamp, conversation_id),
        )

    return user_message_id, assistant_message_id


def update_summary(
    conversation_id: str,
    summary: str,
    summarized_through_message_id: int,
) -> None:
    """Save the updated summary and the last message it represents."""

    with database_connection() as connection:
        connection.execute(
            """
            UPDATE conversations
            SET summary = ?,
                summarized_through_message_id = ?,
                updated_at = ?
            WHERE conversation_id = ?
            """,
            (
                summary,
                summarized_through_message_id,
                current_timestamp(),
                conversation_id,
            ),
        )
