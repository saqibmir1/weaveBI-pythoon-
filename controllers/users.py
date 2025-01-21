from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from auth.jwt_handler import sign_jwt
from models.models import User
from schemas.users import UserCreate, UserUpdate
from services.users import UserService
from passlib.context import CryptContext
from utils.logger import logger


hash_helper = CryptContext(schemes=["bcrypt"])


class UserController:
    async def create_new_users(user:UserCreate, db:AsyncSession):
        user_service = UserService(db=db)
        user_create = await user_service.create_new_users(user=user)
        return sign_jwt(email=user_create.email)
    

    async def login_user(user_credentials: OAuth2PasswordRequestForm, db:AsyncSession):
        user_service = UserService(db=db)
        user: User = await user_service.get_user_by_email(user_credentials.username)
        if user:
            password = hash_helper.verify(user_credentials.password,user.password)
            if password:
                return sign_jwt(email=user.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    async def update_user(updated_user:UserUpdate, user:User,db:AsyncSession):
          user_service = UserService(db)
          return await user_service.update_user(updated_user, user)



    async def delete_user(user: User, db: AsyncSession):
        user_service = UserService(db=db)
        if user:
            success = await user_service.delete_user(user.id)
            if success:
                return {"success": True, "message": "user deleted successfully"}
        logger.error(
            f"UserController->delete_user: {user.id=} User id not found in the database"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "invalid user Id",
                "data": None,
                "error": {"message": "Invalid user ID"},
            },
        )

    async def generate_otp(email:str, db:AsyncSession):
          user_service = UserService(db)
          otp = await user_service.generate_otp(email)
          return otp

    async def reset_password(email:str, otp:str, new_password:str, db:AsyncSession):
          user_service = UserService(db)
          return await user_service.reset_password(email, otp, new_password)
    
    

