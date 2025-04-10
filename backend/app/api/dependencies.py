"""
Dependencies for the API endpoints.
This module provides reusable dependencies for FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, status, Header
from typing import Dict, Any, Optional

from ..services.auth_service import get_current_user as auth_get_current_user
import logging

logger = logging.getLogger(__name__)

# Create a dependency factory function that returns a dependency function with the desired parameters
def get_current_user_dependency(use_cache: bool = False):
    async def get_current_user_with_logging(
        authorization: Optional[str] = Header(None)
    ) -> Optional[Dict[str, Any]]:
        """
    Get the current authenticated user with detailed logging.
    This is a wrapper around the auth_service.get_current_user function
    that adds detailed logging to help diagnose authentication issues.
    
    Args:
        authorization: Authorization header containing the JWT token
        
    Returns:
        User object as dictionary
    """
        logger.info(f"Authorization header: {authorization[:15] if authorization else 'None'}...")
        
        if not authorization:
            logger.info("No Authorization header provided")
            if use_cache:
                # If use_cache is True, return None instead of raising an exception
                # This allows endpoints to handle unauthenticated users by using client-side caching
                return None
            else:
                # If use_cache is False, raise an exception as before
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated. Authorization header missing.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    
        # Extract token from Authorization header
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                logger.error(f"Invalid authentication scheme: {scheme}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme. Use Bearer.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            logger.error(f"Invalid Authorization header format: {authorization[:15]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Extracted token: {token[:10]}...")
        
        try:
            # Use the existing get_current_user function with the extracted token
            user = await auth_get_current_user(token)
            logger.info(f"Successfully authenticated user: {user['id']}")
            return user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
    return get_current_user_with_logging

# Default dependency for backward compatibility
get_current_user_with_logging = get_current_user_dependency(use_cache=False)
