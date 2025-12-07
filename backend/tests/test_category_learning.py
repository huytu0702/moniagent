"""
Test script for Category Learning Service
"""

import sys
sys.path.insert(0, ".")

from src.services.category_learning_service import CategoryLearningService

def test_keyword_extraction():
    """Test keyword extraction from Vietnamese expense text"""
    service = CategoryLearningService()

    test_cases = [
        ("vừa đi taxi 25k", ["taxi"]),
        ("ăn phở ở Phở 24 50000đ", ["phở", "phở"]),  # "24" is a number, filtered out
        ("mua cà phê Highlands Coffee 35k", ["cà", "phê", "highlands", "coffee"]),
        ("đổ xăng 100 nghìn", ["xăng"]),
        ("grab 30k đi làm", ["grab", "làm"]),
        ("mua nước ở Circle K 15k", ["circle"]),  # "nước" is stopword
    ]

    print("Testing keyword extraction:")
    print("-" * 50)
    
    all_passed = True
    for text, expected_subset in test_cases:
        keywords = service.extract_keywords_from_text(text)
        print(f"Text: {text}")
        print(f"Keywords: {keywords}")
        
        # Check if expected keywords are present
        for expected in expected_subset:
            if expected not in keywords:
                print(f"  ⚠️ Missing expected keyword: {expected}")
                all_passed = False
        print()
    
    if all_passed:
        print("✅ All keyword extraction tests passed!")
    else:
        print("❌ Some tests failed")
    
    return all_passed


def test_stopwords_filtered():
    """Test that stopwords are properly filtered"""
    service = CategoryLearningService()
    
    # These are all stopwords and should be filtered
    text = "vừa của và là để cho với"
    keywords = service.extract_keywords_from_text(text)
    
    print("Testing stopword filtering:")
    print(f"Text: {text}")
    print(f"Keywords (should be empty): {keywords}")
    
    if len(keywords) == 0:
        print("✅ Stopwords correctly filtered!")
        return True
    else:
        print("❌ Stopwords not filtered properly")
        return False


def test_amount_patterns_filtered():
    """Test that amount patterns are filtered"""
    service = CategoryLearningService()
    
    text = "mua 25k 100nghìn 50000đ"
    keywords = service.extract_keywords_from_text(text)
    
    print("Testing amount pattern filtering:")
    print(f"Text: {text}")
    print(f"Keywords: {keywords}")
    
    # Only "mua" should remain
    if keywords == ["mua"]:
        print("✅ Amount patterns correctly filtered!")
        return True
    else:
        print(f"❌ Amount patterns not filtered properly. Expected ['mua']")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("CATEGORY LEARNING SERVICE - UNIT TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(test_keyword_extraction())
    print()
    
    results.append(test_stopwords_filtered())
    print()
    
    results.append(test_amount_patterns_filtered())
    print()
    
    print("=" * 60)
    if all(results):
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️ SOME TESTS FAILED")
    print("=" * 60)
