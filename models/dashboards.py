from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    func
)
from sqlalchemy.orm import relationship
from database.database import Base

# Many-to-Many Join Table: dashboard_queries
dashboard_queries = Table(
    'dashboard_queries',
    Base.metadata,
    Column('dashboard_id', Integer, ForeignKey('dashboards.id'), primary_key=True, nullable=False),
    Column('query_id', Integer, ForeignKey('queries.id'), primary_key=True, nullable=False),
    # Add GridStack layout columns
    Column('x', Integer, nullable=True, default=0),  # horizontal position
    Column('y', Integer, nullable=True, default=0),  # vertical position
    Column('w', Integer, nullable=True, default=6),  # width
    Column('h', Integer, nullable=True, default=4),  # height
)

# Many-to-Many Join Table: dashboard_tags
dashboard_tags = Table(
    'dashboard_tags',
    Base.metadata,
    Column('dashboard_id', ForeignKey('dashboards.id'), primary_key=True),
    Column('tag_id', ForeignKey('tags.id'), primary_key=True)
)

# Dashboard Table
class Dashboard(Base):
    __tablename__ = 'dashboards'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(225), nullable=False)
    description = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    db_id = Column(Integer, ForeignKey('databases.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    user = relationship('User', back_populates='dashboards')
    database = relationship('Database', back_populates='dashboards')
    queries = relationship('Query',secondary='dashboard_queries',back_populates='dashboards')
    tags = relationship("Tag", secondary='dashboard_tags', back_populates="dashboards")