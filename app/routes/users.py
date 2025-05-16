"""
User-related routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.models.database import User
from app.models.schemas import UserResponse
from app.config.settings import SECRET_KEY, ALGORITHM
from app.dependencies import get_db, get_current_user, templates

router = APIRouter(tags=["users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    """
    return current_user

@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Display the user profile page.
    """
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user
    }) 