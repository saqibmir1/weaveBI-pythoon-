from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from auth.deps import get_current_user, get_db
from models.users import User
from schemas.generic_response_models import ApiResponse
from schemas.users import Token, UserCreate, Token, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.users import UserController
from sqlalchemy.ext.asyncio import AsyncSession


UserRouter = APIRouter()

@UserRouter.post("/sign-up", response_model=ApiResponse, summary="Create new user")
async def sign_up_user(user: UserCreate, db:AsyncSession=Depends(get_db)):
    signed_jwt = await UserController.create_new_users(user,db)
    return ApiResponse(
        success=True,
        message="User has been created",
        data=signed_jwt
    )

@UserRouter.post("/log-in", response_model=Token, summary="Login user")
async def log_in_user(
    db:AsyncSession=Depends(get_db),
    user_credentials: OAuth2PasswordRequestForm=Depends()
):
    signed_jwt = await UserController.login_user(user_credentials, db)
    return signed_jwt



@UserRouter.put("/update", response_model=ApiResponse, summary="Update user details")
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

@UserRouter.delete("/delete-account", response_model=ApiResponse, summary="Delete user account")
async def delete_user_acccount(
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


    
@UserRouter.get("/forgot-password", response_model=ApiResponse, summary="Generate and send OTP to user's email")
async def generate_user_otp(email:str, db:AsyncSession=Depends(get_db)):
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

@UserRouter.post("/reset-password", response_model=ApiResponse, summary="Reset password")
async def reset_user_password(email:str, otp:str,new_password:str, db:AsyncSession=Depends(get_db)):
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