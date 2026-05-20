"""Unified Automated Test Runner for SkillSwap."""
import os
import sys
import unittest

def execute_complete_test_suite():
    # Configure stdout to support terminal emojis under Windows CMD
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("=" * 80)
    print("🛸 SKILLSWAP: UNIFIED QA AND TESTING RUNNER")
    print("=" * 80)

    # 1. Discover all test classes in tests/ directory
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Import test cases explicitly to ensure in-memory SQLite isolation is active
    from tests.test_backend import SkillSwapBackendTests
    from tests.test_sockets import SkillSwapSocketTests
    from tests.test_security import SkillSwapSecurityTests

    suite.addTests(loader.loadTestsFromTestCase(SkillSwapBackendTests))
    suite.addTests(loader.loadTestsFromTestCase(SkillSwapSocketTests))
    suite.addTests(loader.loadTestsFromTestCase(SkillSwapSecurityTests))

    print(f"📦 Successfully compiled test suite containing {suite.countTestCases()} test cases.")
    print("🚀 Triggering all diagnostic checks sequentially...")
    print("-" * 80)

    # 2. Run tests and collect logs
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("-" * 80)
    print("📈 DIAGNOSTICS QA TALLY REPORT:")
    print("-" * 80)
    print(f"✔️ Total Automated Tests Executed: {result.testsRun}")
    print(f"✔️ Successful Verifications: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"❌ Failed Test Assertions: {len(result.failures)}")
    print(f"❌ Execution Errors Encountered: {len(result.errors)}")
    print("=" * 80)

    if result.wasSuccessful():
        print("🎉 ALL SYSTEM QA TESTS PASSED SUCCESSFULLY! IMMUTABLE INTEGRITY SECURED!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("🚨 CRITICAL QA CHECKS FAILED! REVIEW DIAGNOSTIC ERROR LOGS.")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    execute_complete_test_suite()
