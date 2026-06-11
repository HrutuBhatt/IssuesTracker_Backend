from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import User
from app.auth.dependencies import get_current_user
from app.schemas.user import UserRegister, UserLogin, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and return tokens."""
    service = AuthService(db)
    return service.register_user(payload)

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate credentials and return tokens."""
    service = AuthService(db)
    return service.login_user(payload)

@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for new access and refresh tokens."""
    service = AuthService(db)
    return service.refresh_user_token(payload.refresh_token)

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log out a user by invalidating their refresh token."""
    service = AuthService(db)
    service.logout_user(current_user.id, payload.refresh_token)
    return {"detail": "Successfully logged out"}