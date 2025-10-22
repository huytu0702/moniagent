"""
Utility script to initialize Vietnamese categories and categorization rules for users
"""

import logging
from sqlalchemy.orm import Session
from src.core.database import SessionLocal
from src.services.category_service import CategoryService
from src.services.categorization_service import CategorizationService
from src.models.user import User

logger = logging.getLogger(__name__)


def init_vietnamese_data_for_all_users():
    """
    Initialize Vietnamese categories and rules for all existing users in the database
    """
    db = SessionLocal()

    try:
        category_service = CategoryService(db)
        categorization_service = CategorizationService()

        # Get all users except system user
        users = db.query(User).filter(User.email != "system@moniagent.local").all()

        logger.info(f"Found {len(users)} users to initialize")

        for user in users:
            try:
                user_id = str(user.id)

                # Check if user already has categories
                from src.models.category import Category

                existing_cats = (
                    db.query(Category).filter(Category.user_id == user_id).count()
                )

                if existing_cats == 0:
                    logger.info(f"Initializing categories for user {user.email}")
                    categories = category_service.initialize_user_categories(user_id)
                    logger.info(
                        f"Created {len(categories)} categories for {user.email}"
                    )
                else:
                    logger.info(
                        f"User {user.email} already has {existing_cats} categories"
                    )

                # Create categorization rules
                logger.info(f"Initializing categorization rules for user {user.email}")
                rules = (
                    categorization_service.initialize_vietnamese_categorization_rules(
                        user_id, db_session=db
                    )
                )
                logger.info(f"Created {len(rules)} rules for {user.email}")

            except Exception as e:
                logger.error(f"Error initializing data for user {user.email}: {str(e)}")
                db.rollback()
                continue

        logger.info("Vietnamese data initialization completed")

    except Exception as e:
        logger.error(f"Error initializing Vietnamese data: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_vietnamese_data_for_all_users()
