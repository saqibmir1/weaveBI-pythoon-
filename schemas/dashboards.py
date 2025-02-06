from pydantic import BaseModel
from typing import Optional, List


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    db_id: int
    tags: Optional[List[str]] = None


class DashboardUpdate(BaseModel):
    name:str
    description: Optional[str] = None
    dashboard_id:int


class UpdateQuery(BaseModel):
    query_id: int
    query_name: Optional[str]
    query_text: Optional[str]
    output_type: Optional[str]


class UpdateQueriesRequest(BaseModel):
    dashboard_id: int
    queries: List[UpdateQuery]


class QueryLayout(BaseModel):
    query_id: int
    x: int
    y: int
    w: int
    h: int


class UpdateQueriesRequest(BaseModel):
    dashboard_id: int
    queries: List[QueryLayout]