from sqlalchemy import (
    Column,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from database.database import Base



class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    # Relationship to Dashboards
    dashboards = relationship("Dashboard", secondary="dashboard_tags", back_populates="tags")
