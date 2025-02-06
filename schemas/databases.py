from pydantic import BaseModel, Field


class DbCredentials(BaseModel):
    db_provider: str = Field(examples=["postgres"])
    db_name: str = Field(examples=["signal"])
    db_username: str = Field(examples=["postgres"])
    db_password: str = Field(examples=["secret"])
    db_host: str = Field(examples=["localhost", "0.0.0.0"])
    db_port: str = Field(examples=["5432"])


class UpdatedCredentials(BaseModel):
    db_provider: str = Field(examples=["postgres"])
    db_name: str = Field(examples=["signal"])
    db_username: str = Field(examples=["postgres"])
    db_password: str = Field(examples=["secret"])
    db_host: str = Field(examples=["localhost", "0.0.0.0"])
    db_port: str = Field(examples=["5432"])
    db_id: int = Field(examples=[5])
