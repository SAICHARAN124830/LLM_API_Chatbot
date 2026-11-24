"""
Application configuration for LLM API Chatbot.
Loads settings from environment variables with safe defaults.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Chatbot and Gemini API configuration."""

    # Google Gemini API Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # Model configuration
    # Default to gemini-3.5-flash-lite (high availability and quota)
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()

    # Fallback models in case primary model faces temporary 503 spikes or quota limits
    FALLBACK_MODELS = ["gemini-3.5-flash", "gemma-4-26b-a4b-it", "gemini-3.8-flash"]

    # Context window management
    # Number of most recent messages to send in the context window
    MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

    # Custom System Prompt defining the chatbot persona
    DEFAULT_SYSTEM_PROMPT = (
        "You are Smart Assistant, a friendly, intelligent and helpful AI assistant. "
        "You help users with programming, technology, education, research and everyday questions. "
        "You maintain conversation context, remember relevant information shared earlier in the current "
        "conversation and provide clear, accurate and understandable answers. "
        "Explain technical topics step by step when requested. "
        "Never claim to remember information that is not present in the available conversation context."
    )
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT).strip()

    # Generation parameters
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))

    # Server settings
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    @classmethod
    def validate(cls):
        """Validate critical configuration settings."""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please set GEMINI_API_KEY in your .env file."
            )
        if cls.MAX_HISTORY_MESSAGES < 2:
            cls.MAX_HISTORY_MESSAGES = 2
