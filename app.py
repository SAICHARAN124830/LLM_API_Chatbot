"""
Flask Web Application for LLM API Chatbot.
Provides web UI routes and RESTful API endpoints with multi-turn memory and context management.
"""
import logging
from flask import Flask, render_template, request, jsonify
from config import Config
from conversation_manager import ConversationManager
from gemini_service import GeminiService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Validate configuration on startup
try:
    Config.validate()
except ValueError as e:
    logger.warning(f"Configuration warning: {e}")

# Initialize Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "gemini-chatbot-secret-key-2026"

# Initialize Core Services
conversation_manager = ConversationManager(default_max_messages=Config.MAX_HISTORY_MESSAGES)
gemini_service = None

if Config.GEMINI_API_KEY:
    try:
        gemini_service = GeminiService(
            api_key=Config.GEMINI_API_KEY,
            primary_model=Config.GEMINI_MODEL,
            fallback_models=Config.FALLBACK_MODELS
        )
        logger.info(f"GeminiService initialized with model '{Config.GEMINI_MODEL}'")
    except Exception as e:
        logger.error(f"Failed to initialize GeminiService: {e}")


# ==========================================
# Frontend Route
# ==========================================
@app.route("/")
def index():
    """Render the modern chatbot web interface."""
    return render_template(
        "index.html",
        model_name=Config.GEMINI_MODEL,
        max_history=Config.MAX_HISTORY_MESSAGES
    )


# ==========================================
# API Endpoints
# ==========================================
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main Chat API Endpoint.
    Accepts:
      - message (str): User message.
      - conversation_id (Optional[str]): Conversation identifier.
    Returns:
      - JSON with AI reply, conversation_id, and model used.
    """
    if not gemini_service:
        return jsonify({
            "success": False,
            "error": "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file."
        }), 500

    data = request.get_json(silent=True) or {}
    user_message = data.get("message")
    conversation_id = data.get("conversation_id")

    # Validate message input
    if not user_message or not isinstance(user_message, str) or not user_message.strip():
        return jsonify({
            "success": False,
            "error": "Please provide a valid, non-empty text message."
        }), 400

    user_message = user_message.strip()

    # Enforce maximum single message character length to prevent abuse
    if len(user_message) > 4000:
        return jsonify({
            "success": False,
            "error": "Message exceeds maximum allowed length of 4000 characters."
        }), 400

    try:
        # Retrieve or create conversation session
        conv_id = conversation_manager.get_or_create_conversation(conversation_id)

        # Record user message in conversation memory
        conversation_manager.add_message(conv_id, role="user", content=user_message)

        # Context Window Management: extract the most recent N messages
        context_messages = conversation_manager.get_context_messages(
            conv_id,
            max_messages=Config.MAX_HISTORY_MESSAGES
        )

        logger.info(
            f"Conversation '{conv_id}': Sending {len(context_messages)} messages to Gemini "
            f"(Context limit: {Config.MAX_HISTORY_MESSAGES})"
        )

        # Generate response using Gemini Service
        result = gemini_service.generate_chat_response(
            messages=context_messages,
            system_prompt=Config.SYSTEM_PROMPT,
            temperature=Config.TEMPERATURE,
            max_output_tokens=Config.MAX_OUTPUT_TOKENS
        )

        if not result["success"]:
            # On failure, return clean error message without recording broken assistant reply
            return jsonify({
                "success": False,
                "error": result["error"],
                "conversation_id": conv_id
            }), result.get("status_code", 502)

        # Record assistant reply in conversation memory
        ai_reply = result["reply"]
        conversation_manager.add_message(conv_id, role="assistant", content=ai_reply)

        return jsonify({
            "success": True,
            "reply": ai_reply,
            "conversation_id": conv_id,
            "model_used": result.get("model_used", Config.GEMINI_MODEL)
        }), 200

    except Exception as exc:
        logger.exception("Unexpected error in /api/chat endpoint")
        return jsonify({
            "success": False,
            "error": "An unexpected server error occurred while processing your message."
        }), 500


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    """List all conversation sessions with metadata."""
    conversations = conversation_manager.list_conversations()
    return jsonify({
        "success": True,
        "conversations": conversations
    }), 200


@app.route("/api/conversations/new", methods=["POST"])
def new_conversation():
    """Create a new conversation session."""
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    conv_id = conversation_manager.create_conversation(title=title)
    return jsonify({
        "success": True,
        "conversation_id": conv_id,
        "message": "New conversation created successfully."
    }), 201


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation_history(conversation_id):
    """Retrieve full history of a specific conversation."""
    if not conversation_manager.conversation_exists(conversation_id):
        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    history = conversation_manager.get_history(conversation_id)
    return jsonify({
        "success": True,
        "conversation_id": conversation_id,
        "messages": history
    }), 200


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a conversation session completely."""
    success = conversation_manager.delete_conversation(conversation_id)
    if not success:
        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    return jsonify({
        "success": True,
        "message": "Conversation deleted successfully."
    }), 200


@app.route("/api/conversations/<conversation_id>/clear", methods=["POST"])
def clear_conversation(conversation_id):
    """Clear messages in a conversation session."""
    success = conversation_manager.clear_conversation(conversation_id)
    if not success:
        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    return jsonify({
        "success": True,
        "message": "Conversation history cleared."
    }), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    api_ready = bool(gemini_service and Config.GEMINI_API_KEY)
    return jsonify({
        "status": "healthy" if api_ready else "degraded",
        "api_configured": api_ready,
        "model": Config.GEMINI_MODEL,
        "max_history_messages": Config.MAX_HISTORY_MESSAGES
    }), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
