from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from database.database import Base
from models.dashboards import dashboard_queries



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