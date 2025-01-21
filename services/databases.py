import datetime
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, select, func
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from fastapi import status
from models.models import Database, User, Query
from schemas.databases import DbCredentials, UpdatedCredentials
from utils.logger import logger
from utils.user_queries import get_connection_string
from passlib.context import CryptContext

hash_helper = CryptContext(schemes="bcrypt")


class DatabaseService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def connect_to_db_and_get_scheme(self, connection_string: str, user: User):
        try:
            engine: AsyncEngine = create_engine(connection_string)
            inspector = inspect(engine)

            tables = inspector.get_table_names()
            scheme = {}

            for table_name in tables:
                columns = inspector.get_columns(table_name)
                scheme[table_name] = columns

            engine.dispose()
            return scheme

        except Exception as e:
            logger.error(
                f"DaoDBCredentilsServices->connect_to_database->connect_to_db_and_get_scheme: {user.id=} couuldn't connect to database. Reason {e}."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Coudn't connect to database",
                    "data": None,
                    "error": {"message": f"Couldn't connect to database:\n {e}."},
                },
            )

    async def connect_to_database(self, user: User, db_credentials: DbCredentials):
        connection_string = get_connection_string(db_credentials)
        schema = await self.connect_to_db_and_get_scheme(connection_string, user)
        if schema:
            db_credentials_for_db = Database(
                db_provider=db_credentials.db_provider,
                db_name=db_credentials.db_name,
                username=db_credentials.db_username,
                password=hash_helper.encrypt(db_credentials.db_password),
               # password=db_credentials.db_password,
                host=db_credentials.db_host,
                port=db_credentials.db_port,
                user_id=user.id,
                db_connection_string=connection_string,
                created_at=datetime.datetime.now(),
                schema=str(schema),
            )

            self.db.add(db_credentials_for_db)
            await self.db.commit()
            await self.db.refresh(user)
            return str(schema)
        logger.error(
            f"DaoDBCredentilsServices->connect_to_database: {user.id=} couldn't connect to database."
        )
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail={
                "success": False,
                "message": "Didn't connect to database",
                "data": None,
                "error": {"message": "Didn't connect to database"},
            },
        )
    
    async def test_connection(dbcredentials:DbCredentials):
        connection_string = get_connection_string(dbcredentials)
        try:
            engine: AsyncEngine = create_engine(connection_string)
            inspector = inspect(engine)

            tables = inspector.get_table_names()
            scheme = {}

            for table_name in tables:
                columns = inspector.get_columns(table_name)
                scheme[table_name] = columns

            engine.dispose()
            return True
        except Exception as e:
            return False




    async def get_users_databases(self, user: User) -> list:
        result = await self.db.execute(
            select(Database).where(
                (Database.user_id == user.id) & (Database.is_deleted == False)
            )
        )
        databases_from_db: list[Database] = result.scalars().all()
        databases = [
            {
                "db_provider": db.db_provider,
                "db_name": db.db_name,
                "db_username": db.username,
                "db_host": db.host,
                "db_port": db.port,
                "db_id": db.id,
                "updated_at": db.updated_at,
                "created_at": db.created_at
            }
            for db in databases_from_db
        ]
        logger.info(
            f"DaoDBCredentilsServices->get_users_databases: Retrieved all databases of {user.id=}."
        )
        return databases
    



    async def get_dbs_count(self, user: User):
        try:
        
            query = select(func.count()).select_from(Database).where(Database.user_id == user.id,Database.is_deleted == False)

            result = await self.db.execute(query)
            count = result.scalar() 
            return count
            
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while retrieving databases count."
            )
    


    async def update_db_credentials_and_get_scheme(
        self, updated_credentials: UpdatedCredentials, user: User
    ) -> UpdatedCredentials:
        result = await self.db.execute(
            select(Database).where(
                (Database.id == updated_credentials.db_id)
                & (Database.user_id == user.id)
                & (Database.is_deleted == False)
            )
        )

        existing_database = result.scalar_one_or_none()
        if existing_database:
            connection_string = get_connection_string(updated_credentials)
            schema = await self.connect_to_db_and_get_scheme(connection_string, user)
            if schema:
                existing_database.db_name = updated_credentials.db_name
                existing_database.db_provider = updated_credentials.db_provider
                existing_database.host = updated_credentials.db_host
                existing_database.port = updated_credentials.db_port
                existing_database.username = updated_credentials.db_username
                existing_database.password = updated_credentials.db_password
                existing_database.password = hash_helper.encrypt(updated_credentials.db_password)
                existing_database.schema = str(schema)
                existing_database.db_connection_string = connection_string
                existing_database.created_at = datetime.datetime.now()
                

                await self.db.commit()
                await self.db.refresh(user)
                logger.info(
                    f"DaoDBCredentilsServices->update_db_credentials_and_get_scheme: Db_credentials updated for {user.id=}"
                )
                updated_credentials = {
                    "db_provider": updated_credentials.db_provider,
                    "db_name": updated_credentials.db_name,
                    "db_username": updated_credentials.db_username,
                    "db_password": updated_credentials.db_password,
                    "db_host": updated_credentials.db_host,
                    "db_port": updated_credentials.db_port,
                    "db_id": updated_credentials.db_id,
                }
                
                return updated_credentials
            logger.error(
                f"DaoDBCredentilsServices->update_db_credentials_and_get_scheme: {user.id=} couldn't connect to database with new credentials."
            )
            raise HTTPException(
                status_code=status.HTTP_418_IM_A_TEAPOT,
                detail={
                    "success": False,
                    "message": "Didn't connect to database",
                    "data": None,
                    "error": {"message": "Didn't connect to database"},
                },
            )

        logger.error(
            f"DaoDBCredentilsServices->update_db_credentials_and_get_scheme: database credentials with id: {updated_credentials.db_id} not found for {user.id=}."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Unauthorized",
                "data": None,
                "error": {
                    "message": f"database credentials with id: {updated_credentials.db_id} not found for {user.id=}."
                },
            },
        )

    async def soft_delete_db(self, db_id: int, user: User):
        result = await self.db.execute(
            select(Database).where(
                ((Database.id == db_id) & (Database.user_id == user.id))
            )
        )
        result2 = await self.db.execute(select(Query).where(Query.db_id == db_id))
        db_credential = result.scalar_one_or_none()
        query = result2.scalar_one_or_none()

        if not db_credential:
            logger.error(
                f"DaoDBCredentilsServices->soft_delete_db: Database with {db_id=} not found for {user.id=}."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database with ID {db_id} not found.",
            )

        # soft delete here (database and its queries)
        db_credential.is_deleted = True
        if query:
            query.is_deleted = True
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(
            f"DaoDBCredentilsServices->soft_delete_db: Soft deleted database with {db_id=} for {user.id=}."
        )
