"""
User API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.ranking import RankingHistory
from app.services.ranking_service import RankingService

router = APIRouter(prefix="/api", tags=["Users"])


# Pydantic schemas
class UserCreate(BaseModel):
    name: str
    email: str
    github_username: Optional[str] = None
    repo_url: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    github_username: Optional[str] = None
    repo_url: Optional[str] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    github_username: Optional[str]
    repo_url: Optional[str]
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/users", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get list of all users"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """Update user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}/ranking/history", response_model=List[RankingHistory])
def get_user_ranking_history(
    user_id: int,
    weeks: int = 4,
    db: Session = Depends(get_db)
):
    """
    Get ranking history for a user over N weeks.

    - **user_id**: User ID
    - **weeks**: Number of weeks to look back (1-52, default 4)

    Returns rankings ordered by week (most recent first).
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    service = RankingService()
    history = service.get_user_ranking_history(user_id, weeks, db)

    return history
