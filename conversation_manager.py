"""
Conversation Manager for LLM API Chatbot.
Maintains separate multi-turn conversation histories and handles context window management.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ConversationManager:
    """
    Manages in-memory multi-turn conversations with context window management.
    Ensures conversation separation and prevents memory leaks or cross-talk.
    """

    def __init__(self, default_max_messages: int = 10):
        self.default_max_messages = default_max_messages
        # Store conversations: conversation_id -> conversation_data
        self._conversations: Dict[str, dict] = {}

    def create_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation session and return its unique ID."""
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self._conversations[conv_id] = {
            "id": conv_id,
            "title": title or "New Conversation",
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
        return conv_id

    def conversation_exists(self, conversation_id: str) -> bool:
        """Check if a conversation ID exists."""
        return conversation_id in self._conversations

    def get_or_create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Get an existing conversation ID or create a new one if invalid/missing."""
        if conversation_id and self.conversation_exists(conversation_id):
            return conversation_id
        return self.create_conversation()

    def add_message(self, conversation_id: str, role: str, content: str) -> dict:
        """
        Add a message (user or assistant) to a conversation.
        Auto-generates a title from the first user message if title is default.
        """
        conv_id = self.get_or_create_conversation(conversation_id)
        conv = self._conversations[conv_id]

        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        message = {
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": now
        }
        conv["messages"].append(message)
        conv["updated_at"] = now

        # Update title from the first user message if still default
        if role == "user" and (conv["title"] == "New Conversation" or not conv["title"]):
            clean_text = content.strip().replace("\n", " ")
            conv["title"] = (clean_text[:32] + "...") if len(clean_text) > 35 else clean_text

        return message

    def get_history(self, conversation_id: str) -> List[dict]:
        """Retrieve full conversation history for UI display."""
        if not self.conversation_exists(conversation_id):
            return []
        return list(self._conversations[conversation_id]["messages"])

    def get_context_messages(self, conversation_id: str, max_messages: Optional[int] = None) -> List[dict]:
        """
        Context Window Management: Last N Messages Strategy.
        - Retrieves the most recent `max_messages` turns.
        - Ensures context always starts with a 'user' turn for valid LLM dialogue flow.
        """
        if not self.conversation_exists(conversation_id):
            return []

        messages = self._conversations[conversation_id]["messages"]
        if not messages:
            return []

        limit = max_messages if max_messages is not None else self.default_max_messages
        if limit <= 0:
            limit = 10

        # Take the last N messages
        recent_messages = messages[-limit:]

        # Gemini requires conversation turns to begin with a 'user' message.
        # If the slice begins with an 'assistant' message, drop the leading assistant message.
        while recent_messages and recent_messages[0]["role"] != "user":
            recent_messages = recent_messages[1:]

        return recent_messages

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages from a conversation while preserving the session."""
        if not self.conversation_exists(conversation_id):
            return False
        self._conversations[conversation_id]["messages"] = []
        self._conversations[conversation_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._conversations[conversation_id]["title"] = "New Conversation"
        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation completely."""
        if not self.conversation_exists(conversation_id):
            return False
        del self._conversations[conversation_id]
        return True

    def list_conversations(self) -> List[dict]:
        """Return list of conversations with metadata sorted by recent update."""
        summary = []
        for conv in self._conversations.values():
            summary.append({
                "id": conv["id"],
                "title": conv["title"],
                "message_count": len(conv["messages"]),
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"]
            })
        # Sort newest first
        summary.sort(key=lambda x: x["updated_at"], reverse=True)
        return summary
