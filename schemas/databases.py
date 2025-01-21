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


class Schema(BaseModel):
    db_schema: str


class UserDatabase(BaseModel):
    db_provider: str
    db_name: str
    db_username: str
    db_password: str
    db_host: str
    db_port: str
    db_id: int
    db_created_at: str
    db_updated_at: str
    


class UserDatabases(BaseModel):
    databases: list[UserDatabase]
