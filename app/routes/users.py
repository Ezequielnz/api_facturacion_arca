"""
User-related routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import User
from app.models.schemas import UserResponse
from app.config.settings import SECRET_KEY, ALGORITHM
from app.dependencies import get_db, get_current_user, templates, get_token

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
    token: Optional[str] = Depends(get_token),
    db: Session = Depends(get_db)
):
    """
    Display the user profile page.
    """
    if not token:
        return RedirectResponse(url="/login-form", status_code=303)
    
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return RedirectResponse(url="/login-form", status_code=303)
            
        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return RedirectResponse(url="/login-form", status_code=303)
            
        # Render profile template
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user
        })
        
    except JWTError as e:
        print(f"Error de token JWT en perfil: {str(e)}")
        return RedirectResponse(url="/login-form", status_code=303) 