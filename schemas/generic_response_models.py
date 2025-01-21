from typing import Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: Optional[bool] = None
    message: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None