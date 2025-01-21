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
)


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


# Database Table
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


# Query Table
class Query(Base):
    __tablename__ = 'queries'

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    db_id = Column(Integer, ForeignKey('databases.id'), nullable=True)
    query_name = Column(String, nullable=True)
    query_text = Column(Text, nullable=True)
    output_type = Column(String, nullable=True)
    generated_sql_query = Column(String, nullable=True)
    data = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    user = relationship('User', back_populates='queries')
    database = relationship('Database', back_populates='queries')
    dashboards = relationship(
        'Dashboard',
        secondary=dashboard_queries,
        back_populates='queries'
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
    queries = relationship(
        'Query',
        secondary=dashboard_queries,
        back_populates='dashboards'
    )
