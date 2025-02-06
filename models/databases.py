from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from database.database import Base

class Database(Base):
    __tablename__ = 'databases'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    db_provider = Column(String, nullable=False)
    db_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(String, nullable=False)
    schema = Column(String, nullable=False)
    db_connection_string = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    user_id = Column(Integer, ForeignKey('users.id'))
    is_deleted = Column(Boolean, default=False)

    # Relationships
    user = relationship('User', back_populates='databases')
    queries = relationship('Query', back_populates='database', cascade="all, delete-orphan")
    dashboards = relationship('Dashboard', back_populates='database', cascade="all, delete-orphan")