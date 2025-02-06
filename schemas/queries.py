from pydantic import BaseModel, Field


class UserQueryRequest(BaseModel):
    query_name: str = "Count"
    query_text: str = "Count of all films"
    output_type: str = "tabular"
    db_id: int = 1


class QueryInsightsRequest(BaseModel):
    custom_instructions: str | None = Field(default=None, description="Optional instructions for insights generation")
    

class SaveQueryRequest(BaseModel):
    query_name: str
    query_text: str
    output_type: str
    db_id: int


class UpdateQueryRequest(BaseModel):
    query_id: int
    query_name: str
    query_text: str
    output_type: str