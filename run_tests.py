"""
Automated Test Runner for LLM API Chatbot.
Executes both unit/integration tests and live 5-turn Gemini multi-turn memory verification.
"""
import sys
import unittest
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def run_all_tests():
    print("=" * 70)
    print(" 🧪 RUNNING LLM API CHATBOT TEST SUITE")
    print("=" * 70)

    # Step 1: Run Unit and Integration Tests
    print("\n[PHASE 1] Executing Unit & API Integration Tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromName("tests.test_conversation"))
    suite.addTests(loader.loadTestsFromName("tests.test_api"))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        print("\n❌ Phase 1 Unit/API Tests FAILED.")
        return False

    print("\n✅ Phase 1: All Unit and Integration Tests PASSED!")

    # Step 2: Run Live 5-Turn Conversation Memory Test
    print("\n" + "=" * 70)
    print("[PHASE 2] Executing Live 5-Turn Gemini API Memory Verification...")
    print("=" * 70)
    
    from tests.test_multi_turn_live import run_live_memory_test
    live_success = run_live_memory_test()

    if not live_success:
        print("\n❌ Phase 2 Live Multi-Turn Test FAILED.")
        return False

    print("\n" + "=" * 70)
    print("🎉 ALL TESTS PASSED! Chatbot is verified and ready for production.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
