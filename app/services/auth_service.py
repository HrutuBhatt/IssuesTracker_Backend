from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repository.user_repository import UserRepository
from app.schemas.user import UserRegister, UserLogin
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register_user(self, payload: UserRegister) -> dict:
        existing = self.repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed = hash_password(payload.password)
        user = self.repo.create(payload.email, hashed)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        self.repo.add_refresh_token(user.id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def login_user(self, payload: UserLogin) -> dict:
        user = self.repo.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        self.repo.add_refresh_token(user.id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_user_token(self, refresh_token: str) -> dict:
        user_id = decode_token(refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        # Verify token exists in database (hasn't been logged out)
        token_record = self.repo.get_refresh_token(user_id, refresh_token)
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or has been revoked"
            )

        # Generate ONLY a new access token
        new_access = create_access_token(user_id)

        return {
            "access_token": new_access,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def logout_user(self, user_id: int, refresh_token: str) -> None:
        self.repo.delete_refresh_token(user_id, refresh_token)
