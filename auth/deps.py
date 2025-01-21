from fastapi import Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import AsyncSessionLocal
from auth.jwt_handler import decode_jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from services.users import UserService


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db), token=Depends(oauth2_scheme)
):

    users_exits = decode_jwt(token=token)

    if not users_exits:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_service = UserService(db=db)
    user = await user_service.get_user_by_email(email=users_exits["email"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user