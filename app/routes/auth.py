"""
Authentication related routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt
from typing import Annotated

from app.models.database import User
from app.models.schemas import UserCreate, UserResponse, Token
from app.config.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.services.auth import verify_password, get_password_hash, create_access_token
from app.dependencies import get_db, templates

router = APIRouter(tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/register-form", response_class=HTMLResponse)
async def register_form(request: Request):
    """
    Display the user registration form.
    """
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/login-form", response_class=HTMLResponse)
async def login_form(request: Request):
    """
    Display the login form.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/register")
async def register(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    cuit: Annotated[str, Form()],
    company_name: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    # Check if user already exists
    user = db.query(User).filter(User.email == email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        password=hashed_password,
        cuit=cuit,
        company_name=company_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return RedirectResponse(url="/login-form", status_code=303)

@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return an access token.
    """
    # Verificar credenciales
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Configurar redirección y cookie
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="lax"
    )
    
    print(f"Login exitoso para usuario: {user.email}")
    return response

@router.get("/logout")
async def logout():
    """
    Log out a user by deleting the access token cookie.
    """
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response 