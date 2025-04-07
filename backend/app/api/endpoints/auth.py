from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Any

from ...db.base import get_db
from ...schemas.user import GoogleAuthRequest, Token, UserCreate, UserResponse
from ...services.auth_service import AuthService
from datetime import timedelta

router = APIRouter()

@router.post("/google", response_model=Token)
async def login_with_google(
    auth_data: GoogleAuthRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    Authenticate with Google OAuth.
    
    This endpoint verifies a Google ID token and either creates a new user
    or logs in an existing user, returning a JWT access token.
    """
    try:
        # Verify the Google token
        user_data = await AuthService.verify_google_token(auth_data.token)
        
        # Check if user exists
        user = AuthService.get_user_by_google_id(db, user_data["google_id"])
        
        if not user:
            # Create a new user
            user_create = UserCreate(
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture"),
                google_id=user_data["google_id"]
            )
            user = AuthService.create_user(db, user_create)
        
        # Create access token
        from ...core.config import settings
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        # Return token and user data
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
    except Exception as e:
        import traceback
        print(f"Google login error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user = Depends(AuthService.get_current_user)
) -> Any:
    """
    Get information about the currently authenticated user.
    """
    return current_user
