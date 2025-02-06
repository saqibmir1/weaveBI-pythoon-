from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    name: str = Field(examples=["John Doe"])
    email: EmailStr = Field(examples=["johndoe@example.com"])
    password: str = Field(examples=["secret12345"], min_length=8)

    @field_validator("email")
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class Token(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class UserUpdate(BaseModel):
    name:str = Field(examples=["John Doe"])
    email: EmailStr = Field(examples=["johndoe@example.com"])
    password: str = Field(examples=["secret12345"], min_length=8)

    @field_validator("email")
    def lowercase_email(cls, value: str) -> str:
        return value.lower()
    
