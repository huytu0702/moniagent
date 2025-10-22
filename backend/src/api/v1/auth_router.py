from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.core.database import get_db
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User
from src.services.category_service import CategoryService
from src.services.categorization_service import CategorizationService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""


class UserRegisterResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str  # email in this case
    password: str


@router.post("/register", response_model=UserRegisterResponse)
async def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    # Create new user
    hashed_password = hash_password(request.password)
    user = User(
        email=request.email,
        password_hash=hashed_password,  # Changed from hashed_password to match Supabase
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize Vietnamese categories and rules for the new user
    try:
        category_service = CategoryService(db)
        categorization_service = CategorizationService()

        # Create user's copy of Vietnamese categories
        category_service.initialize_user_categories(str(user.id))

        # Create categorization rules for automatic categorization
        categorization_service.initialize_vietnamese_categorization_rules(
            str(user.id), db_session=db
        )
    except Exception as e:
        # Log but don't fail registration if category initialization fails
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize categories for user {user.id}: {str(e)}")

    return UserRegisterResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        created_at=user.created_at.isoformat(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """Login with email and password"""
    # Find user by email (username in the form data)
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(
        form_data.password, user.password_hash
    ):  # Changed from hashed_password
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/init-vietnamese-data")
async def init_vietnamese_data_for_all(
    db: Session = Depends(get_db),
):
    """
    Admin endpoint to initialize Vietnamese categories and rules for all users
    This should be called once after adding system categories
    """
    try:
        category_service = CategoryService(db)
        categorization_service = CategorizationService()

        # Get all users except system user
        users = db.query(User).filter(User.email != "system@moniagent.local").all()

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Initializing Vietnamese data for {len(users)} users")

        initialized_count = 0
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
                initialized_count += 1

            except Exception as e:
                logger.error(f"Error initializing data for user {user.email}: {str(e)}")
                db.rollback()
                continue

        return {
            "status": "success",
            "message": f"Initialized Vietnamese data for {initialized_count} users",
            "users_initialized": initialized_count,
        }

    except Exception as e:
        logger.error(f"Error initializing Vietnamese data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize data: {str(e)}",
        )
