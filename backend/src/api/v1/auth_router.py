from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.core.database import get_db
from src.core.security import create_access_token, hash_password, verify_password
from src.models.user import User
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
