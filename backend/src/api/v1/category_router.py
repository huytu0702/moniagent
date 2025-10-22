"""
Category API router
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.schemas.category import (
    CategoryResponse,
    CategoryListResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CategorizationRuleResponse,
    CategorizationRuleListResponse,
    CreateCategorizationRuleRequest,
    UpdateCategorizationRuleRequest,
    CategorizationSuggestionResponse,
    CategorizeExpenseRequest,
    CategorizeExpenseResponse,
)
from src.services.category_service import CategoryService, CategoryServiceError
from src.services.categorization_service import (
    CategorizationService,
    CategorizationServiceError,
)
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.category import Category
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategoryResponse)
async def create_category(
    request: CreateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new category for the current user
    """
    try:
        service = CategoryService()
        result = service.create_category(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            color=request.color,
            display_order=request.display_order,
            db_session=db,
        )

        return CategoryResponse(**result)

    except CategoryServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating category: {str(e)}",
        )


@router.get("/", response_model=CategoryListResponse)
async def get_user_categories(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get all categories for the current user
    """
    try:
        service = CategoryService()
        categories = service.get_user_categories(current_user.id, db)

        return CategoryListResponse(
            categories=[CategoryResponse(**c) for c in categories]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving categories: {str(e)}",
        )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific category by ID
    """
    try:
        service = CategoryService()
        category = service.get_category_by_id(current_user.id, category_id, db)

        return CategoryResponse(**category)

    except CategoryServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving category: {str(e)}",
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    request: UpdateCategoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing category
    """
    try:
        service = CategoryService()
        result = service.update_category(
            user_id=current_user.id,
            category_id=category_id,
            name=request.name,
            description=request.description,
            icon=request.icon,
            color=request.color,
            display_order=request.display_order,
            db_session=db,
        )

        return CategoryResponse(**result)

    except CategoryServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating category: {str(e)}",
        )


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a category
    """
    try:
        service = CategoryService()
        result = service.delete_category(current_user.id, category_id, db)

        return result

    except CategoryServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting category: {str(e)}",
        )


@router.post("/rules", response_model=CategorizationRuleResponse)
async def create_categorization_rule(
    request: CreateCategorizationRuleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new categorization rule
    """
    try:
        service = CategoryService()
        result = service.create_categorization_rule(
            user_id=current_user.id,
            category_id=request.category_id,
            store_name_pattern=request.store_name_pattern,
            rule_type=request.rule_type,
            confidence_threshold=request.confidence_threshold,
            db_session=db,
        )

        return CategorizationRuleResponse(**result)

    except CategoryServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating rule: {str(e)}",
        )


@router.get("/rules/{category_id}", response_model=CategorizationRuleListResponse)
async def get_category_rules(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all categorization rules for a category
    """
    try:
        service = CategoryService()
        rules = service.get_categorization_rules_for_category(category_id, db)

        return CategorizationRuleListResponse(
            rules=[CategorizationRuleResponse(**r) for r in rules]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving rules: {str(e)}",
        )


@router.post("/suggest", response_model=CategorizationSuggestionResponse)
async def suggest_category(
    request: CategorizeExpenseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a category suggestion for an expense
    """
    try:
        service = CategorizationService()
        result = service.suggest_category(current_user.id, request.expense_id, db)

        return CategorizationSuggestionResponse(**result)

    except CategorizationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error suggesting category: {str(e)}",
        )


@router.post("/confirm", response_model=CategorizeExpenseResponse)
async def confirm_categorization(
    request: CategorizeExpenseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirm or correct the categorization for an expense
    """
    try:
        service = CategorizationService()

        if not request.category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="category_id is required for confirming categorization",
            )

        result = service.confirm_categorization(
            user_id=current_user.id,
            expense_id=request.expense_id,
            category_id=request.category_id,
            db_session=db,
        )

        return CategorizeExpenseResponse(**result)

    except CategorizationServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming categorization: {str(e)}",
        )


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all categories for the current user"""
    try:
        categories = (
            db.query(Category)
            .filter(Category.user_id == current_user.id)
            .order_by(Category.display_order)
            .all()
        )
        return [c.to_dict() for c in categories]
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {str(e)}",
        )


@router.post("/initialize-vietnamese", response_model=dict)
async def initialize_vietnamese_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initialize Vietnamese categories and categorization rules for the current user

    This endpoint creates:
    - 10 Vietnamese expense categories with icons and colors
    - 170+ categorization rules for automatic expense categorization
    """
    try:
        from src.services.category_service import CategoryService
        from src.services.categorization_service import CategorizationService

        category_service = CategoryService(db)
        categorization_service = CategorizationService()

        # Initialize categories
        categories = category_service.initialize_user_categories(str(current_user.id))
        logger.info(
            f"Initialized {len(categories)} categories for user {current_user.id}"
        )

        # Initialize categorization rules
        rules = categorization_service.initialize_vietnamese_categorization_rules(
            str(current_user.id), db_session=db
        )
        logger.info(
            f"Initialized {len(rules)} categorization rules for user {current_user.id}"
        )

        return {
            "status": "success",
            "message": f"Initialized {len(categories)} categories and {len(rules)} categorization rules",
            "categories_created": len(categories),
            "rules_created": len(rules),
            "categories": [c.to_dict() for c in categories],
        }

    except Exception as e:
        logger.error(f"Error initializing Vietnamese categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize categories: {str(e)}",
        )
