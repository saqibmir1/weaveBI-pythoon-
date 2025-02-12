import datetime
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from models.users import User
from models.databases import Database
from models.queries import Query
from schemas.users import UserCreate, UserUpdate
from passlib.context import CryptContext
from utils.logger import logger
import random
from redis.asyncio import Redis
from aiosmtplib import send
from email.mime.text import MIMEText
from config.mail_config import settings

hash_helper = CryptContext(schemes="bcrypt")


class UserService:
    db:AsyncSession

    def __init__(self,db:AsyncSession)-> None:
        self.db=db


    async def get_user_by_email(self,email:str):
        result = await self.db.execute(
            select(User).where((User.email==email) & (User.is_deleted==False))
        )
        user = result.scalar_one_or_none()
        return user
    
    async def create_new_users(self,user:UserCreate):
        if await self.get_user_by_email(user.email):
            logger.error(f'{user.email=} already exists')
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with email: {user.email} already exists"
            )
        user_db = User(
            email=user.email,
            name=user.name,
            password=hash_helper.encrypt(user.password),
            created_at=datetime.datetime.now()
        )

        self.db.add(user_db)
        await self.db.commit()
        await self.db.refresh(user_db)
        logger.info(f'New user {user.name} added to db successfully')
        return user_db

    async def update_user(self, updated_user:UserUpdate, user:User):
        result = await self.db.execute(
            select(User).where(
                (User.id==user.id) & (User.is_deleted==False)
            )
        )

        existing_user =  result.scalar_one_or_none()
        if existing_user:
            existing_user.name = updated_user.name
            existing_user.email = updated_user.email
            existing_user.password = updated_user.password
            existing_user.password = hash_helper.encrypt(updated_user.password)

            await self.db.commit()
            await self.db.refresh(existing_user)
            logger.info(f'User updated: with new name as {updated_user.name} and new email. as {updated_user.email}')
            return True
        return False

    async def delete_user(self, user_id: int) -> bool:
        try:
            # soft delete user
            await self.db.execute(
                update(User).where(User.id == user_id).values(is_deleted=True)
            )
            logger.info(f"user {user_id} soft deleted")

            # soft delete  records in dbs_credentials table
            await self.db.execute(update(Database).where(Database.user_id == user_id).values(is_deleted=True))


            # soft delete records in queries
            await self.db.execute(update(Query).where(Query.user_id == user_id).values(is_deleted=True))


            await self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"Error deleting user {user_id} - {str(e)}"
            )
            return False

    async def generate_otp(self, email:str):
        result = await self.db.execute(select(User).where(User.email==email))
        user = result.scalar_one_or_none()
        if user:
            otp= str(random.randint(100000, 999999))
            redis_client = Redis(decode_responses=True, host='redis')
            await redis_client.setex(f"otp:{email}", 300, otp)
            await redis_client.close()
            logger.info(f"OTP generated for {email}")

            subject = "Your OTP for Password Reset"
            body = f"""
            <html>
            <body>
                <img src="https://c.tenor.com/274Jq71u-zQAAAAd/tenor.gif" alt="OTP GIF" style="width: 300px; height: auto; margin-top: 10px;" />
                <h2>Hello,</h2>
                <p>Your OTP for resetting your password is:</p>
                <p><strong style="font-size: 24px; color: #FF5733;">{otp}</strong></p>
                <p>This OTP will expire in 5 minutes.</p>
                <p>Thank you!</p>
            </body>
            </html>
            """
            sender_email = settings.username
            sender_password = settings.password

            message = MIMEText(body, "html")
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = subject

            await send(
                message, 
                hostname=settings.hostname,
                port=settings.port,
                start_tls=True,
                username=sender_email,
                password=sender_password
          
            )
            logger.info(f"OTP sent to {email}")
            return otp
        
    async def reset_password(self, email:str, otp:str, new_password:str):
        redis_client = Redis(host=settings.redis_host, decode_responses=True)
        saved_otp = await redis_client.get(f"otp:{email}")
        await redis_client.close()
        if saved_otp == otp and new_password:
            result = await self.db.execute(select(User).where(User.email==email))
            user = result.scalar_one_or_none()
            if user:
                user.password = hash_helper.encrypt(new_password)
                await self.db.commit()
                logger.info(f"Password reset for {email}")
                return True
        return False