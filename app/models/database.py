"""
Database connection and model definitions for the ARCA API application.
"""
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config.settings import SQLALCHEMY_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    """
    User model for authentication and identification.
    
    Attributes:
        id: Unique identifier for the user
        email: User's email address (unique)
        password: Hashed password
        cuit: User's CUIT number (unique)
        company_name: Name of the user's company
        is_active: Whether the user account is active
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    cuit = Column(String, unique=True, index=True)
    company_name = Column(String)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)
