"""
Live Multi-Turn 5-Turn Conversation Memory Test with Real Google Gemini API.
Verifies context window retention and multi-turn reasoning as required by prompt:
  Turn 1: My name is Sai.
  Turn 2: I am studying Artificial Intelligence.
  Turn 3: I am currently in my fifth semester.
  Turn 4: What is my name?
  Turn 5: Which subject am I studying and which semester am I in?
"""
import os
import sys
import json
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def run_live_memory_test():
    from app import app, conversation_manager

    print("=" * 70)
    print(" LIVE 5-TURN CONVERSATION MEMORY VERIFICATION TEST")
    print("=" * 70)

    client = app.test_client()

    # Create a clean conversation session
    res = client.post("/api/conversations/new", json={"title": "Multi-Turn Memory Test"})
    conv_data = res.get_json()
    conv_id = conv_data["conversation_id"]
    print(f"[SESSION] Created test conversation: {conv_id}\n")

    turns = [
        {
            "turn": 1,
            "input": "My name is Sai.",
            "expect_keyword": None
        },
        {
            "turn": 2,
            "input": "I am studying Artificial Intelligence.",
            "expect_keyword": None
        },
        {
            "turn": 3,
            "input": "I am currently in my fifth semester.",
            "expect_keyword": None
        },
        {
            "turn": 4,
            "input": "What is my name?",
            "expect_keyword": "Sai"
        },
        {
            "turn": 5,
            "input": "Which subject am I studying and which semester am I in?",
            "expect_keyword": ["Artificial Intelligence", "AI", "fifth", "5th"]
        }
    ]

    all_passed = True

    for t in turns:
        turn_num = t["turn"]
        user_msg = t["input"]
        print(f"--- TURN {turn_num} ---")
        print(f"User: {user_msg}")

        # Small pause to respect rate limits
        time.sleep(1.0)

        response = client.post(
            "/api/chat",
            data=json.dumps({"message": user_msg, "conversation_id": conv_id}),
            content_type="application/json"
        )

        if response.status_code != 200:
            print(f"[FAIL] HTTP Status: {response.status_code}")
            print(f"Error details: {response.data.decode('utf-8')}")
            all_passed = False
            break

        data = response.get_json()
        reply = data.get("reply", "")
        model_used = data.get("model_used", "Unknown")
        print(f"Assistant ({model_used}): {reply.strip()}\n")

        # Verification checks
        if t["expect_keyword"]:
            expected = t["expect_keyword"]
            if isinstance(expected, str):
                if expected.lower() in reply.lower():
                    print(f"[CHECK PASSED] Model remembered: '{expected}'")
                else:
                    print(f"[CHECK FAILED] Model failed to mention '{expected}' in response.")
                    all_passed = False
            elif isinstance(expected, list):
                # Check subject and semester
                subject_found = any(k.lower() in reply.lower() for k in ["artificial intelligence", "ai"])
                semester_found = any(k.lower() in reply.lower() for k in ["fifth", "5th", "5"])
                if subject_found and semester_found:
                    print(f"[CHECK PASSED] Model remembered both subject and semester correctly!")
                else:
                    print(f"[CHECK FAILED] Subject found: {subject_found}, Semester found: {semester_found}")
                    all_passed = False

        print()

    print("=" * 70)
    if all_passed:
        print(" ALL 5 TURNS COMPLETED AND VERIFIED SUCCESSFULLY!")
        print(" Multi-turn context memory is fully functional with Google Gemini API.")
        print("=" * 70)
        return True
    else:
        print(" ONE OR MORE VERIFICATION CHECKS FAILED.")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_live_memory_test()
    sys.exit(0 if success else 1)
