"""
Dependency functions for the FastAPI application.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Annotated

from app.models.database import SessionLocal, User
from app.config.settings import SECRET_KEY, ALGORITHM

# Templates setup
templates = Jinja2Templates(directory="app/templates")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    """
    Dependency for database session management.
    
    Yields:
        SQLAlchemy Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_token_from_cookie(request: Request) -> str:
    """
    Extract the JWT token from cookies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Extracted token or empty string
    """
    token = request.cookies.get("access_token", "")
    if token.startswith("Bearer "):
        return token.split(" ")[1]
    return ""

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)] = None,
    request: Request = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        token: JWT token from Authorization header
        request: FastAPI request object (for cookie authentication)
        db: Database session
        
    Returns:
        User object for the authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if not provided in header
    if not token and request:
        token = get_token_from_cookie(request)
        
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user 