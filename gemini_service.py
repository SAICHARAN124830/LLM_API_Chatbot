"""
Gemini Service Module.
Handles communication with Google GenAI SDK, error handling, retries, and fallbacks.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Encapsulates interaction with Google Gemini API.
    Provides robust retry mechanism, fallback model support, and user-friendly error diagnostics.
    """

    def __init__(self, api_key: str, primary_model: str = "gemini-3.5-flash", fallback_models: Optional[List[str]] = None):
        if not api_key:
            raise ValueError("Gemini API key is required to initialize GeminiService.")
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_models = fallback_models or ["gemini-3.5-flash-lite"]
        self.client = genai.Client(api_key=api_key)

    def _convert_messages_to_contents(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """
        Converts generic message dictionaries into google.genai types.Content objects.
        Maps 'assistant' role to Gemini's expected 'model' role.
        """
        contents = []
        for msg in messages:
            raw_role = msg.get("role", "user")
            role = "model" if raw_role in ("assistant", "model") else "user"
            text_content = msg.get("content", "")
            
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text_content)]
                )
            )
        return contents

    def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024
    ) -> Dict[str, Any]:
        """
        Sends conversation history to Gemini and retrieves response.
        Handles retries with backoff and model fallbacks for resilience.
        """
        if not messages:
            return {
                "success": False,
                "error": "No messages provided for generation.",
                "status_code": 400
            }

        contents = self._convert_messages_to_contents(messages)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens
        )

        candidate_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        last_error = None

        for model in candidate_models:
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    logger.info(f"Calling Gemini model '{model}' (attempt {attempt + 1})...")
                    response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config
                    )

                    if response and response.text:
                        return {
                            "success": True,
                            "reply": response.text.strip(),
                            "model_used": model
                        }
                    else:
                        return {
                            "success": False,
                            "error": "The AI model returned an empty response. Please rephrase your message.",
                            "status_code": 502
                        }

                except Exception as exc:
                    last_error = exc
                    error_str = str(exc)
                    logger.warning(f"Error calling Gemini model '{model}' (attempt {attempt + 1}): {error_str}")

                    # If temporary demand spike (503) or rate limit (429), back off and retry or switch model
                    if "503" in error_str or "UNAVAILABLE" in error_str:
                        if attempt < max_retries - 1:
                            time.sleep(1.0 * (attempt + 1))
                            continue
                        else:
                            # Move to next fallback model
                            logger.info(f"Model '{model}' unavailable (503). Trying fallback model...")
                            break

                    elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        logger.warning(f"Model '{model}' exceeded quota or rate limit (429). Trying fallback model...")
                        # Move directly to the next fallback model
                        break

                    elif "401" in error_str or "403" in error_str or "API_KEY_INVALID" in error_str:
                        return {
                            "success": False,
                            "error": "Invalid or unauthorized Gemini API key. Please verify your .env configuration.",
                            "status_code": 401
                        }

                    elif "404" in error_str or "NOT_FOUND" in error_str:
                        logger.info(f"Model '{model}' not found (404). Trying next fallback model...")
                        break

                    elif "getaddrinfo failed" in error_str or "Connection" in error_str:
                        return {
                            "success": False,
                            "error": "Network connection error: Unable to reach Gemini API servers. Please check your internet connection.",
                            "status_code": 503
                        }
                    else:
                        # Non-retryable error
                        break

        # If all candidate models and retries failed
        error_msg = self._format_user_friendly_error(last_error)
        return {
            "success": False,
            "error": error_msg,
            "status_code": 502
        }

    def _format_user_friendly_error(self, exc: Optional[Exception]) -> str:
        """Translates low-level exceptions into clear, secure user-facing explanations."""
        if not exc:
            return "Unable to generate a response from the AI model. Please try again."

        err = str(exc)
        if "503" in err or "UNAVAILABLE" in err:
            return "The Gemini AI service is currently experiencing high demand. Please try again in a few moments."
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "API request limit reached. Please wait a few seconds before sending another message."
        if "401" in err or "403" in err:
            return "Authentication failure: The configured Gemini API key is invalid or lacks permissions."
        if "404" in err:
            return "The requested Gemini model is not supported or accessible for your account."
        if "getaddrinfo" in err or "Connection" in err:
            return "Network connection issue: Unable to connect to Google Gemini services."

        return "Gemini service temporarily encountered an issue processing your request. Please try again."
