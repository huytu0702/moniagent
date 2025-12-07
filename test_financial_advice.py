"""
Test script for FinancialAdviceService implementation
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from src.services.financial_advice_service import FinancialAdviceService
from unittest.mock import Mock


def test_financial_advice_service():
    """Test the FinancialAdviceService with mock data"""

    print("🧪 Testing FinancialAdviceService Implementation")
    print("=" * 50)

    # Initialize service
    advice_service = FinancialAdviceService()

    # Mock spending data (Vietnam context)
    mock_analysis = {
        "period": "monthly",
        "total_spending": 15000000,  # 15 triệu VND
        "average_daily": 500000,  # 500k VND/day
        "by_category": {
            "Ăn uống": 6000000,  # 6 triệu
            "Đi lại": 4500000,  # 4.5 triệu
            "Mua sắm": 3000000,  # 3 triệu
            "Giải trí": 1500000,  # 1.5 triệu
        },
        "top_category": "Ăn uống",
        "top_amount": 6000000,
    }

    print("📊 Mock Spending Analysis:")
    print(f"   Total: {mock_analysis['total_spending']:,.0f}đ")
    print(f"   Daily Avg: {mock_analysis['average_daily']:,.0f}đ")
    print(
        f"   Top Category: {mock_analysis['top_category']} ({mock_analysis['top_amount']:,.0f}đ)"
    )
    print()

    # Test spending pattern determination
    pattern = advice_service._determine_spending_pattern(mock_analysis)
    print(f"🎯 Spending Pattern: {pattern}")
    print()

    # Test prompt creation
    prompt = advice_service._create_advice_prompt(mock_analysis, pattern)
    print("📝 Generated Prompt (first 300 chars):")
    print(f"   {prompt[:300]}...")
    print()

    # Test advice generation (with mock DB session)
    mock_db = Mock()

    try:
        print("🤖 Generating AI Advice...")
        result = advice_service.get_financial_advice(
            user_id="test_user_123", period="monthly", db_session=mock_db
        )

        print("✅ AI Advice Generated Successfully!")
        print()
        print("💡 Advice:")
        print(f"   {result.get('advice', 'No advice generated')}")
        print()
        print("📋 Recommendations:")
        for i, rec in enumerate(result.get("recommendations", []), 1):
            print(f"   {i}. {rec}")
        print()
        print("📈 Additional Info:")
        print(f"   Pattern: {result.get('spending_pattern')}")
        print(f"   Top Category: {result.get('top_spending_category')}")
        print(
            f"   Top Amount: {result.get('top_spending_amount'):,.0f}đ"
            if result.get("top_spending_amount")
            else ""
        )

    except Exception as e:
        print(f"❌ Error generating advice: {str(e)}")
        print("🔄 Testing with default advice...")

        # Test default advice
        default_advice = advice_service._get_default_advice(mock_analysis, pattern)
        print(f"💡 Default Advice: {default_advice}")

    print()
    print("🧪 Test completed!")


if __name__ == "__main__":
    test_financial_advice_service()
