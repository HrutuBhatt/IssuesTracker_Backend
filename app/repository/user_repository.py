from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.models import User, RefreshToken

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, email: str, password_hash: str) -> User:
        user = User(email=email, hashed_password=password_hash)
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during user creation: {str(e)}"
            )

    def add_refresh_token(self, user_id: int, refresh_token: str) -> RefreshToken:
        token_obj = RefreshToken(user_id=user_id, refresh_token=refresh_token)
        try:
            self.db.add(token_obj)
            self.db.commit()
            self.db.refresh(token_obj)
            return token_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during token storage: {str(e)}"
            )

    def get_refresh_token(self, user_id: int, refresh_token: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.refresh_token == refresh_token
        ).first()

    def delete_refresh_token(self, user_id: int, refresh_token: str) -> None:
        token_obj = self.get_refresh_token(user_id, refresh_token)
        if token_obj:
            try:
                self.db.delete(token_obj)
                self.db.commit()
            except SQLAlchemyError as e:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error during token invalidation: {str(e)}"
                )
