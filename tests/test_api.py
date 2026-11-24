"""
Integration tests for Flask Web Application and REST API endpoints.
"""
import os
import sys
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, conversation_manager


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_homepage_loads(self):
        """Test that root route loads HTML frontend with 200 OK."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Smart Assistant", html)
        self.assertIn("Gemini AI", html)
        self.assertIn("New Chat", html)

    def test_health_endpoint(self):
        """Test health check route."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("status", data)
        self.assertIn("model", data)
        self.assertTrue(data["api_configured"])

    def test_chat_validation_empty_message(self):
        """Test chat endpoint rejects empty messages."""
        response = self.client.post(
            "/api/chat",
            data=json.dumps({"message": "   "}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])
        self.assertIn("non-empty", data["error"])

    def test_chat_validation_non_string_message(self):
        """Test chat endpoint rejects non-string message types."""
        response = self.client.post(
            "/api/chat",
            data=json.dumps({"message": 12345}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_conversation_endpoints_lifecycle(self):
        """Test creation, listing, retrieval, clearing and deletion of conversations."""
        # 1. Create conversation
        create_res = self.client.post(
            "/api/conversations/new",
            data=json.dumps({"title": "Test Chat"}),
            content_type="application/json"
        )
        self.assertEqual(create_res.status_code, 201)
        conv_id = create_res.get_json()["conversation_id"]
        self.assertTrue(conv_id)

        # 2. Add a message directly via manager to test retrieval
        conversation_manager.add_message(conv_id, "user", "Hello Test")
        conversation_manager.add_message(conv_id, "assistant", "Hi there!")

        # 3. Retrieve conversation history
        get_res = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(get_res.status_code, 200)
        messages = get_res.get_json()["messages"]
        self.assertEqual(len(messages), 2)

        # 4. List conversations
        list_res = self.client.get("/api/conversations")
        self.assertEqual(list_res.status_code, 200)
        convs = list_res.get_json()["conversations"]
        self.assertTrue(any(c["id"] == conv_id for c in convs))

        # 5. Clear conversation
        clear_res = self.client.post(f"/api/conversations/{conv_id}/clear")
        self.assertEqual(clear_res.status_code, 200)
        get_after_clear = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(len(get_after_clear.get_json()["messages"]), 0)

        # 6. Delete conversation
        del_res = self.client.delete(f"/api/conversations/{conv_id}")
        self.assertEqual(del_res.status_code, 200)
        get_after_del = self.client.get(f"/api/conversations/{conv_id}")
        self.assertEqual(get_after_del.status_code, 404)


if __name__ == "__main__":
    unittest.main()
