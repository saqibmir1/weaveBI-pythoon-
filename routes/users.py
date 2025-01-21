from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth.deps import get_current_user, get_db
from models.models import User
from schemas.generic_response_models import ApiResponse
from schemas.users import Token, UserCreate, Token, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.users import UserController
from sqlalchemy.ext.asyncio import AsyncSession
from utils.logger import logger


UserRouter = APIRouter()

@UserRouter.post("/signup", response_model=ApiResponse)
async def create_new_users(user: UserCreate, db:AsyncSession=Depends(get_db)):
    signed_jwt = await UserController.create_new_users(user,db)
    return ApiResponse(
        success=True,
        message="User has been created",
        data=signed_jwt
    )

@UserRouter.post("/login", response_model=Token)
async def login_user(
    db:AsyncSession=Depends(get_db),
    user_credentials: OAuth2PasswordRequestForm=Depends()
):
    signed_jwt = await UserController.login_user(user_credentials, db)
    return signed_jwt



@UserRouter.put("/update", response_model=ApiResponse)
async def update_user(updated_user:UserUpdate, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        updated_user_info = await UserController.update_user(updated_user, user, db)
        return ApiResponse(
            success=True,
            message="User data updated successfully"
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Error occured while updating user",
            error=(str(e))
        )

@UserRouter.delete("/delete", response_model=ApiResponse)
async def delete_user(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    deletion_result = await UserController.delete_user(user, db)
    if deletion_result:
        return ApiResponse(success=True, message="User deleted successfully")
    return ApiResponse(
        success=False,
        message="Failed to delete user",
        error={"message": "Unknown error"},
    )


    
@UserRouter.get("/generate_otp", response_model=ApiResponse)
async def generate_otp(email:str, db:AsyncSession=Depends(get_db)):
    otp = await UserController.generate_otp(email, db)
    if otp:
        return ApiResponse(
            success=True,
            message= "OTP sent to your email."
        )
   
    return ApiResponse(
        success=False,
        message="Failed to send OTP"
    )

@UserRouter.post("/reset_password", response_model=ApiResponse)
async def reset_password(email:str, otp:str,new_password:str, db:AsyncSession=Depends(get_db)):
    result = await UserController.reset_password(email, otp, new_password, db)
    if result:
        return ApiResponse(
            success=True,
            message="Password reset successfully"
        )
    return ApiResponse(
        success=False,
        message="Failed to reset password"
    )