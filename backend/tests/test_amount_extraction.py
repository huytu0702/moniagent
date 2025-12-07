"""Test amount extraction"""
import sys
sys.path.insert(0, ".")

from src.services.expense_processing_service import ExpenseProcessingService

service = ExpenseProcessingService(None)

test_cases = [
    ('vừa đi ăn 2 triệu', 2000000),
    ('mua đồ 500 nghìn', 500000),
    ('cafe 25k', 25000),
    ('grab 30000đ', 30000),
    ('1.5 triệu mua quần áo', 1500000),
    ('ăn sáng 50 ngàn', 50000),
    ('2tr mua sách', 2000000),
]

print('Testing amount extraction:')
print('-' * 50)
all_passed = True
for text, expected in test_cases:
    result = service.extract_expense_from_text(text)
    actual = result.get("amount")
    status = "✅" if actual == expected else "❌"
    if actual != expected:
        all_passed = False
    print(f'{status} "{text}" -> {actual} (expected: {expected})')

print('-' * 50)
if all_passed:
    print("🎉 ALL TESTS PASSED!")
else:
    print("⚠️ SOME TESTS FAILED")
