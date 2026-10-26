
"""Tests for our SQLite conversation storage layer."""

import tempfile
import unittest
from pathlib import Path

import database


class TestConversationDatabase(unittest.TestCase):
    """Check that conversations and messages are stored correctly."""

    def setUp(self):
        # Give each test its own temporary database.
        # This keeps test data separate from real conversations.
        self.temp_directory = tempfile.TemporaryDirectory()
        self.original_database_path = database.DATABASE_PATH

        database.DATABASE_PATH = (
            Path(self.temp_directory.name) / "test_conversations.db"
        )

        # Create the tables in our temporary database.
        database.initialize_database()

    def tearDown(self):
        # Restore the normal database location and clean up test files.
        database.DATABASE_PATH = self.original_database_path
        self.temp_directory.cleanup()

    def test_conversation_can_be_created_and_retrieved(self):
        # Create a conversation, then retrieve its saved details.
        database.create_conversation("test-conversation-1")

        conversation = database.get_conversation("test-conversation-1")

        self.assertIsNotNone(conversation)
        self.assertEqual(
            conversation["conversation_id"],
            "test-conversation-1",
        )
        self.assertEqual(conversation["summary"], "")

    def test_messages_can_be_saved_and_retrieved(self):
        # A conversation must exist before its messages can be saved.
        conversation_id = "test-conversation-2"
        database.create_conversation(conversation_id)

        # Save one user message and one assistant reply.
        user_id, assistant_id = database.save_exchange(
            conversation_id,
            "Remember my project name is VK Chatbot.",
            "Your project is called VK Chatbot.",
        )

        messages = database.get_unsummarized_messages(conversation_id)

        # Verify that both messages were saved in the correct order.
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(
            messages[0]["content"],
            "Remember my project name is VK Chatbot.",
        )
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(
            messages[1]["content"],
            "Your project is called VK Chatbot.",
        )

        # Each saved message should have a unique database ID.
        self.assertGreater(user_id, 0)
        self.assertGreater(assistant_id, user_id)

    def test_summary_progress_is_saved(self):
        # Check that the database can record summary progress.
        conversation_id = "test-conversation-3"
        database.create_conversation(conversation_id)

        _, assistant_id = database.save_exchange(
            conversation_id,
            "I am learning Python.",
            "You're learning Python.",
        )

        database.update_summary(
            conversation_id,
            "The user is learning Python.",
            assistant_id,
        )

        conversation = database.get_conversation(conversation_id)

        self.assertEqual(
            conversation["summary"],
            "The user is learning Python.",
        )
        self.assertEqual(
            conversation["summarized_through_message_id"],
            assistant_id,
        )


if __name__ == "__main__":
    # Run the tests when this file is executed directly.
    unittest.main(verbosity=2)
