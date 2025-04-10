from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Any, Dict

from ...schemas.user import GoogleAuthRequest, Token, UserResponse
from ...services.auth_service import AuthService, get_current_user
from ...db.supabase_client import get_supabase_client
from datetime import timedelta

router = APIRouter()

@router.post("/google", response_model=Token)
async def login_with_google(
    auth_data: GoogleAuthRequest
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
        user = await AuthService.get_user_by_google_id(user_data["google_id"])
        
        if not user:
            # Create a new user
            user = await AuthService.create_user(user_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
        
        # Create access token
        from ...core.config import settings
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user["email"], "user_id": user["id"]},
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
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get information about the currently authenticated user.
    """
    return UserResponse.model_validate(current_user)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    This endpoint is mainly for compatibility with the OAuth2 specification.
    """
    # For simplicity, we'll use a mock user for this endpoint
    # In a real application, you would validate username/password here
    user_data = {
        "email": form_data.username,
        "name": "Test User",
        "picture": "https://ui-avatars.com/api/?name=Test+User&background=random",
        "google_id": "mock-direct-login"
    }
    
    # Check if user exists
    user = await AuthService.get_user_by_email(form_data.username)
    
    if not user:
        # Create a new user
        user = await AuthService.create_user(user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    # Create access token
    from ...core.config import settings
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    # Return token and user data
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }
