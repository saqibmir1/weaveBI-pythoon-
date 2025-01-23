from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    func
)
from sqlalchemy.orm import relationship
from database.database import Base


# User Table
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    databases = relationship('Database', back_populates='user', cascade="all, delete-orphan")
    dashboards = relationship('Dashboard', back_populates='user', cascade="all, delete-orphan")
    queries = relationship('Query', back_populates='user', cascade="all, delete-orphan")