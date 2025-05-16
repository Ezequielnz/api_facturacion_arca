"""
Dependency functions for the FastAPI application.
"""
from fastapi import Depends, HTTPException, status, Request, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, HTTPBearer, HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import datetime

from app.models.database import SessionLocal, User
from app.config.settings import SECRET_KEY, ALGORITHM

# Define context processor to provide current year
def current_year_processor(request: Request):
    return {"current_year": datetime.datetime.now().year}

# Templates setup with context processor
templates = Jinja2Templates(directory="app/templates")
templates.env.globals["current_year"] = datetime.datetime.now().year

# OAuth2 scheme with auto error disabled to handle authentication from cookies too
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

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

async def get_token(
    request: Request, 
    token: Optional[str] = Depends(oauth2_scheme),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[str]:
    """
    Extracts JWT token from various sources: OAuth2 header, HTTP Bearer, or cookies.
    
    Args:
        request: FastAPI request object
        token: Token from OAuth2 header
        credentials: Credentials from HTTP Bearer
        
    Returns:
        Token string if found, None otherwise
    """
    # Try to get from OAuth2 header
    if token:
        return token
    
    # Try to get from HTTP bearer
    if credentials:
        return credentials.credentials
    
    # Try to get from cookies
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # Remove Bearer prefix if present
        if cookie_token.startswith("Bearer "):
            return cookie_token.replace("Bearer ", "")
        return cookie_token
    
    return None

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(get_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user.
    
    Args:
        request: FastAPI request object
        token: JWT token from various sources
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
    
    if not token:
        print("No token found")
        raise credentials_exception
    
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("No email in token")
            raise credentials_exception
    except JWTError as e:
        print(f"JWT Error: {str(e)}")
        raise credentials_exception
    
    # Get the user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        print(f"User not found: {email}")
        raise credentials_exception
    
    if not user.is_active:
        print(f"User inactive: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return user 