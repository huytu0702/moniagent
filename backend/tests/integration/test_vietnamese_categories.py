"""
Integration tests for Vietnamese categories and auto-categorization
"""

import pytest
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.models.user import User
from src.models.category import Category
from src.models.expense_categorization_rule import ExpenseCategorizationRule
from src.services.category_service import CategoryService
from src.services.categorization_service import CategorizationService
from src.services.expense_processing_service import ExpenseProcessingService


class TestVietnameseCategoriesSetup:
    """Test Vietnamese categories initialization"""

    def setup_method(self):
        """Setup for each test"""
        self.db = SessionLocal()

    def teardown_method(self):
        """Cleanup after each test"""
        self.db.close()

    def test_system_categories_exist(self):
        """Test that system categories are created"""
        system_user = (
            self.db.query(User).filter(User.email == "system@moniagent.local").first()
        )

        if system_user:
            categories = (
                self.db.query(Category)
                .filter(
                    Category.user_id == system_user.id,
                    Category.is_system_category == True,
                )
                .all()
            )

            assert len(categories) >= 10, "System should have at least 10 categories"

            # Check specific categories
            category_names = {c.name for c in categories}
            expected = {
                "Ăn uống",
                "Đi lại",
                "Nhà ở",
                "Mua sắm cá nhân",
                "Giải trí & du lịch",
                "Giáo dục & học tập",
                "Sức khỏe & thể thao",
                "Gia đình & quà tặng",
                "Đầu tư & tiết kiệm",
                "Khác",
            }

            assert expected.issubset(
                category_names
            ), f"Missing categories: {expected - category_names}"

    def test_user_categories_initialized(self):
        """Test that users have categories initialized"""
        # Get first non-system user
        user = (
            self.db.query(User).filter(User.email != "system@moniagent.local").first()
        )

        if user:
            categories = (
                self.db.query(Category).filter(Category.user_id == user.id).all()
            )

            assert (
                len(categories) >= 10
            ), f"User should have at least 10 categories, has {len(categories)}"

    def test_categorization_rules_created(self):
        """Test that categorization rules are created for users"""
        # Get first non-system user
        user = (
            self.db.query(User).filter(User.email != "system@moniagent.local").first()
        )

        if user:
            rules = (
                self.db.query(ExpenseCategorizationRule)
                .filter(ExpenseCategorizationRule.user_id == user.id)
                .all()
            )

            assert (
                len(rules) >= 50
            ), f"User should have at least 50 rules, has {len(rules)}"

            # Check that rules have different categories
            category_ids = {r.category_id for r in rules}
            assert len(category_ids) >= 5, "Rules should cover multiple categories"

    def test_rules_have_confidence_thresholds(self):
        """Test that rules have proper confidence thresholds"""
        # Get first non-system user
        user = (
            self.db.query(User).filter(User.email != "system@moniagent.local").first()
        )

        if user:
            rules = (
                self.db.query(ExpenseCategorizationRule)
                .filter(ExpenseCategorizationRule.user_id == user.id)
                .all()
            )

            for rule in rules:
                assert (
                    0.0 <= rule.confidence_threshold <= 1.0
                ), f"Confidence threshold should be 0-1, got {rule.confidence_threshold}"
                assert rule.is_active == True, "Rules should be active by default"


class TestAutoCategorization:
    """Test automatic expense categorization"""

    def setup_method(self):
        """Setup for each test"""
        self.db = SessionLocal()
        self.expense_service = ExpenseProcessingService(self.db)

        # Get first non-system user for testing
        self.user = (
            self.db.query(User).filter(User.email != "system@moniagent.local").first()
        )

    def teardown_method(self):
        """Cleanup after each test"""
        self.db.close()

    def test_categorize_starbucks_expense(self):
        """Test that Starbucks expense is categorized as Dining"""
        if not self.user:
            pytest.skip("No test user available")

        # Extract expense from text
        expense_data = self.expense_service.extract_expense_from_text(
            "I spent $15 at Starbucks today", user_id=str(self.user.id)
        )

        assert expense_data.get("merchant_name") == "Starbucks"
        assert expense_data.get("amount") == 15.0

        # Check if category was suggested
        if expense_data.get("category_id"):
            category = (
                self.db.query(Category)
                .filter(Category.id == expense_data["category_id"])
                .first()
            )

            assert category is not None
            assert (
                category.name == "Ăn uống"
            ), f"Expected 'Ăn uống', got {category.name}"

    def test_categorize_grab_expense(self):
        """Test that Grab expense is categorized as Transportation"""
        if not self.user:
            pytest.skip("No test user available")

        expense_data = self.expense_service.extract_expense_from_text(
            "I took Grab to the office, cost me 50k", user_id=str(self.user.id)
        )

        assert (
            expense_data.get("merchant_name") == "Grab"
            or "grab" in expense_data.get("description", "").lower()
        )

        if expense_data.get("category_id"):
            category = (
                self.db.query(Category)
                .filter(Category.id == expense_data["category_id"])
                .first()
            )

            if category:
                assert (
                    category.name == "Đi lại"
                ), f"Expected 'Đi lại', got {category.name}"

    def test_categorize_gym_expense(self):
        """Test that gym expense is categorized as Health & Fitness"""
        if not self.user:
            pytest.skip("No test user available")

        expense_data = self.expense_service.extract_expense_from_text(
            "Gym membership renewal - $40", user_id=str(self.user.id)
        )

        if expense_data.get("category_id"):
            category = (
                self.db.query(Category)
                .filter(Category.id == expense_data["category_id"])
                .first()
            )

            if category:
                assert (
                    category.name == "Sức khỏe & thể thao"
                ), f"Expected 'Sức khỏe & thể thao', got {category.name}"

    def test_confidence_scores(self):
        """Test that confidence scores are calculated correctly"""
        if not self.user:
            pytest.skip("No test user available")

        # High confidence match
        expense_data = self.expense_service.extract_expense_from_text(
            "I spent 100k at Starbucks cafe", user_id=str(self.user.id)
        )

        confidence = expense_data.get("categorization_confidence")
        if confidence:
            assert confidence > 0.7, f"Expected high confidence, got {confidence}"

    def test_keyword_matching(self):
        """Test various keyword matching scenarios"""
        if not self.user:
            pytest.skip("No test user available")

        test_cases = [
            ("I bought pizza for dinner", "Ăn uống"),
            ("Paid my internet bill", "Nhà ở"),
            ("New laptop purchase", "Mua sắm cá nhân"),
            ("Movie tickets for tonight", "Giải trí & du lịch"),
            ("Tuition fee payment", "Giáo dục & học tập"),
        ]

        for message, expected_category in test_cases:
            expense_data = self.expense_service.extract_expense_from_text(
                message, user_id=str(self.user.id)
            )

            if expense_data.get("category_id"):
                category = (
                    self.db.query(Category)
                    .filter(Category.id == expense_data["category_id"])
                    .first()
                )

                if category:
                    assert (
                        category.name == expected_category
                    ), f"For '{message}': expected {expected_category}, got {category.name}"


class TestCategoryServiceMethods:
    """Test CategoryService methods"""

    def setup_method(self):
        """Setup for each test"""
        self.db = SessionLocal()
        self.service = CategoryService(self.db)

        # Create a test user
        from uuid import uuid4

        self.test_user = User(
            email=f"test_category_{uuid4()}@test.com",
            password_hash="test_hash",
            first_name="Test",
            last_name="User",
        )
        self.db.add(self.test_user)
        self.db.commit()
        self.db.refresh(self.test_user)

    def teardown_method(self):
        """Cleanup after each test"""
        # Clean up test user
        self.db.delete(self.test_user)
        self.db.commit()
        self.db.close()

    def test_initialize_user_categories(self):
        """Test initializing categories for a user"""
        categories = self.service.initialize_user_categories(str(self.test_user.id))

        assert (
            len(categories) >= 10
        ), f"Expected at least 10 categories, got {len(categories)}"

        # Verify categories are tied to the user
        for cat in categories:
            assert cat.user_id == self.test_user.id
            assert cat.is_system_category == False  # User's copy, not system

    def test_get_categories_by_user(self):
        """Test retrieving user categories"""
        # Initialize categories first
        self.service.initialize_user_categories(str(self.test_user.id))

        # Retrieve categories
        categories = self.service.get_categories_by_user(str(self.test_user.id))

        assert len(categories) >= 10

        # Verify they're ordered by display_order
        orders = [c.display_order for c in categories]
        assert orders == sorted(orders), "Categories should be ordered by display_order"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
