"""
Test script to verify the enhanced confirmation flow
Tests the fix for "không" being incorrectly interpreted as confirmation
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.langgraph_agent import LangGraphAIAgent
from src.database.session import get_db
from sqlalchemy import text

def setup_test_db():
    """Setup test database connection"""
    db = next(get_db())
    return db

def cleanup_test_expenses(db, user_id: str):
    """Clean up test expenses from database"""
    try:
        # Delete test expenses
        result = db.execute(
            text("DELETE FROM expenses WHERE user_id = :user_id AND merchant_name LIKE '%Test%'"),
            {"user_id": user_id}
        )
        db.commit()
        print(f"✓ Cleaned up {result.rowcount} test expenses")
    except Exception as e:
        print(f"⚠ Cleanup warning: {str(e)}")
        db.rollback()

def count_expenses(db, user_id: str) -> int:
    """Count expenses for a user"""
    result = db.execute(
        text("SELECT COUNT(*) as count FROM expenses WHERE user_id = :user_id"),
        {"user_id": user_id}
    ).fetchone()
    return result.count if result else 0

def test_scenario(scenario_name: str, user_message: str, user_response: str, expected_saved: bool):
    """Test a confirmation scenario"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {scenario_name}")
    print(f"{'='*60}")
    
    db = setup_test_db()
    test_user_id = "test_user_123"
    test_session_id = f"test_session_{scenario_name.replace(' ', '_')}"
    
    try:
        # Clean up before test
        cleanup_test_expenses(db, test_user_id)
        initial_count = count_expenses(db, test_user_id)
        print(f"📊 Initial expense count: {initial_count}")
        
        # Create agent
        agent = LangGraphAIAgent(db_session=db)
        
        # Step 1: Send expense message
        print(f"\n📝 User sends: '{user_message}'")
        result1 = agent.run(
            user_message=user_message,
            user_id=test_user_id,
            session_id=test_session_id,
            message_type="text"
        )
        
        print(f"🤖 Agent response: {result1.get('response', 'No response')[:200]}...")
        print(f"🔄 Interrupted: {result1.get('interrupted', False)}")
        
        if not result1.get('interrupted'):
            print("❌ FAIL: Expected interruption for confirmation")
            return False
        
        # Step 2: Resume with user response
        print(f"\n💬 User responds: '{user_response}'")
        result2 = agent.resume(
            session_id=test_session_id,
            user_response=user_response
        )
        
        print(f"🤖 Agent final response: {result2.get('response', 'No response')}")
        
        # Check database
        final_count = count_expenses(db, test_user_id)
        expense_saved = final_count > initial_count
        
        print(f"\n📊 Final expense count: {final_count}")
        print(f"💾 Expense saved: {expense_saved}")
        print(f"✅ Expected saved: {expected_saved}")
        
        # Verify
        if expense_saved == expected_saved:
            print(f"\n✅ PASS: {scenario_name}")
            cleanup_test_expenses(db, test_user_id)
            return True
        else:
            print(f"\n❌ FAIL: {scenario_name}")
            print(f"   Expected saved={expected_saved}, but got saved={expense_saved}")
            cleanup_test_expenses(db, test_user_id)
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR in {scenario_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        cleanup_test_expenses(db, test_user_id)
        return False
    finally:
        db.close()

def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("🚀 VERIFICATION TEST SUITE")
    print("   Testing Enhanced Confirmation Flow")
    print("="*60)
    
    test_cases = [
        {
            "name": "Test 1: 'không' should NOT save",
            "message": "chi 50000 ăn sáng",
            "response": "không",
            "expected_saved": False
        },
        {
            "name": "Test 2: 'hủy' should NOT save",
            "message": "chi 30000 cà phê",
            "response": "hủy",
            "expected_saved": False
        },
        {
            "name": "Test 3: 'lưu' should SAVE",
            "message": "chi 100000 ăn trưa",
            "response": "lưu",
            "expected_saved": True
        },
        {
            "name": "Test 4: 'ok' should SAVE",
            "message": "chi 45000 xe",
            "response": "ok",
            "expected_saved": True
        },
        {
            "name": "Test 5: 'không muốn' should NOT save",
            "message": "chi 200000d điện thoại",
            "response": "không muốn",
            "expected_saved": False
        },
    ]
    
    results = []
    for test_case in test_cases:
        result = test_scenario(
            scenario_name=test_case["name"],
            user_message=test_case["message"],
            user_response=test_case["response"],
            expected_saved=test_case["expected_saved"]
        )
        results.append({"name": test_case["name"], "passed": result})
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status}: {result['name']}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
