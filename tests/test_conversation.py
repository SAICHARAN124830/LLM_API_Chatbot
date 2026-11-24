"""
Unit tests for ConversationManager and Context Window Management.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from conversation_manager import ConversationManager


class TestConversationManager(unittest.TestCase):
    def setUp(self):
        self.manager = ConversationManager(default_max_messages=6)

    def test_create_and_exists(self):
        conv_id = self.manager.create_conversation("AI Discussion")
        self.assertTrue(self.manager.conversation_exists(conv_id))
        self.assertFalse(self.manager.conversation_exists("non-existent-id"))

    def test_add_messages_and_get_history(self):
        conv_id = self.manager.create_conversation()
        msg1 = self.manager.add_message(conv_id, "user", "Hello there!")
        msg2 = self.manager.add_message(conv_id, "assistant", "Hello! How can I assist you?")

        history = self.manager.get_history(conv_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello there!")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Hello! How can I assist you?")

    def test_auto_title_generation(self):
        conv_id = self.manager.create_conversation()
        self.manager.add_message(conv_id, "user", "What is Machine Learning and Deep Learning?")
        summary = self.manager.list_conversations()
        conv_entry = next(c for c in summary if c["id"] == conv_id)
        self.assertTrue(conv_entry["title"].startswith("What is Machine Learning"))

    def test_context_window_last_n_strategy(self):
        """
        Verify that only the most recent N messages are returned
        and that the context window always starts with a user turn.
        """
        conv_id = self.manager.create_conversation()
        # Add 10 messages (5 user, 5 assistant)
        for i in range(1, 6):
            self.manager.add_message(conv_id, "user", f"User message {i}")
            self.manager.add_message(conv_id, "assistant", f"Assistant reply {i}")

        full_history = self.manager.get_history(conv_id)
        self.assertEqual(len(full_history), 10)

        # Request context window of max 4 messages
        context_4 = self.manager.get_context_messages(conv_id, max_messages=4)
        self.assertEqual(len(context_4), 4)
        self.assertEqual(context_4[0]["role"], "user")
        self.assertEqual(context_4[0]["content"], "User message 4")
        self.assertEqual(context_4[-1]["content"], "Assistant reply 5")

        # Request context window of 3 messages (slice would be assistant, user, assistant)
        # Slicing must drop leading assistant message so context starts with user
        context_3 = self.manager.get_context_messages(conv_id, max_messages=3)
        self.assertEqual(context_3[0]["role"], "user")
        self.assertEqual(context_3[0]["content"], "User message 5")
        self.assertEqual(context_3[-1]["content"], "Assistant reply 5")

    def test_separate_conversation_histories(self):
        """Verify that multiple conversations do not cross-talk or share messages."""
        conv_a = self.manager.create_conversation("User A")
        conv_b = self.manager.create_conversation("User B")

        self.manager.add_message(conv_a, "user", "My favorite color is Blue.")
        self.manager.add_message(conv_b, "user", "My favorite color is Green.")

        history_a = self.manager.get_history(conv_a)
        history_b = self.manager.get_history(conv_b)

        self.assertEqual(len(history_a), 1)
        self.assertEqual(len(history_b), 1)
        self.assertIn("Blue", history_a[0]["content"])
        self.assertIn("Green", history_b[0]["content"])
        self.assertNotIn("Green", history_a[0]["content"])

    def test_clear_conversation(self):
        conv_id = self.manager.create_conversation()
        self.manager.add_message(conv_id, "user", "Temporary message")
        self.assertEqual(len(self.manager.get_history(conv_id)), 1)

        success = self.manager.clear_conversation(conv_id)
        self.assertTrue(success)
        self.assertEqual(len(self.manager.get_history(conv_id)), 0)
        self.assertTrue(self.manager.conversation_exists(conv_id))

    def test_delete_conversation(self):
        conv_id = self.manager.create_conversation()
        self.assertTrue(self.manager.conversation_exists(conv_id))
        success = self.manager.delete_conversation(conv_id)
        self.assertTrue(success)
        self.assertFalse(self.manager.conversation_exists(conv_id))


if __name__ == "__main__":
    unittest.main()
