"""
Diagnostic test script for Google Gemini API connection.
Validates API key and checks model responsiveness.
"""
import os
import sys
from dotenv import load_dotenv
from google import genai

# Step 1: Load environment variables
load_dotenv()

# Step 2: Read configuration
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

print("=" * 60)
print(" Gemini API Connection Diagnostic Test")
print("=" * 60)

# Step 3: Validate API key existence
if not api_key:
    print("[ERROR] GEMINI_API_KEY is missing from .env file.")
    print("Please set your API key in .env:")
    print("  GEMINI_API_KEY=your_actual_key_here")
    sys.exit(1)

# Mask API key for secure logging
masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
print(f"[OK] API Key loaded successfully (Key: {masked_key})")
print(f"[INFO] Target Model: {model_name}")

try:
    print("\nConnecting to Google Gemini API...")
    client = genai.Client(api_key=api_key)
    
    # Test generation
    prompt = "Hello Gemini! Confirm in one short sentence that the API connection is active."
    print(f"[SENDING] Prompt: '{prompt}'")
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    
    if response and response.text:
        print("\n[SUCCESS] Gemini Response Received:")
        print("-" * 50)
        print(response.text.strip())
        print("-" * 50)
        print("[STATUS] Connection is working perfectly!\n")
    else:
        print("\n[WARNING] Gemini responded, but the text was empty.")
        sys.exit(1)

except Exception as err:
    print(f"\n[ERROR] Unable to communicate with Gemini API.")
    print(f"Details: {err}\n")
    print("Troubleshooting tips:")
    print("1. If 503 UNAVAILABLE: Model is busy, switch GEMINI_MODEL in .env to 'gemini-3.5-flash-lite'.")
    print("2. If 404 NOT_FOUND: Verify model name or check availability for your account.")
    print("3. If 403 or 401: Verify that your API key is active and has Gemini API enabled.")
    print("4. If network error: Verify internet connectivity.")
    sys.exit(1)
