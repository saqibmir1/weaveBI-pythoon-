from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DashBoardResponse(BaseModel):
    id:int
    name:str
    description: Optional[str]
    user_id:int
    created_on:datetime
    updated_at:datetime



class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    db_id: int



class DashboardUpdate(BaseModel):
    name:str
    description: Optional[str] = None
    dashboard_id:int


class QueryInput(BaseModel):
    query_name: str
    query_text: str 
    output_type: str

class PostQueriesRequest(BaseModel):
    dashboard_id:int
    queries: List[QueryInput]


class UpdateQuery(BaseModel):
    query_id: int
    query_name: Optional[str]
    query_text: Optional[str]
    output_type: Optional[str]

class UpdateQueriesRequest(BaseModel):
    dashboard_id: int
    queries: List[UpdateQuery]