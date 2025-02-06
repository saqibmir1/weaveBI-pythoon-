import datetime
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from fastapi import status
from models.databases import Database
from models.users import User
from models.queries import Query
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
            # Create sync engine for schema inspection
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            try:
                tables = inspector.get_table_names()
                scheme = {}
                
                for table_name in tables:
                    # Get basic column info
                    columns = inspector.get_columns(table_name)
                    
                    # Enhance column information
                    for column in columns:
                        # Convert SQLAlchemy type to string representation
                        column['type'] = str(column['type'])
                        
                        # Add foreign key information
                        fk_info = []
                        for fk in inspector.get_foreign_keys(table_name):
                            if column['name'] in fk['constrained_columns']:
                                fk_info.append({
                                    'referred_table': fk['referred_table'],
                                    'referred_column': fk['referred_columns'][0]
                                })
                        if fk_info:
                            column['foreign_keys'] = fk_info
                        
                        # Add primary key information
                        pk_constraint = inspector.get_pk_constraint(table_name)
                        column['primary_key'] = column['name'] in pk_constraint.get('constrained_columns', [])
                        
                        # Clean up any database-specific attributes
                        column.pop('dialect_options', None)
                        
                    scheme[table_name] = columns
                
                logger.info(f'Connected to database and retrieved schema for user {user.id}')
                engine.dispose()
                return scheme
                
            except Exception as schema_error:
                logger.error(
                    f"{user.id=} couldn't extract schema. Reason: {schema_error}"
                )
                raise schema_error
                
        except Exception as e:
            logger.error(
                f"{user.id=} couldn't connect to database. Reason {e}."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Couldn't connect to database",
                    "data": None,
                    "error": {"message": f"Couldn't connect to database:\n {e}."},
                },
            )
        finally:
            if 'engine' in locals():
                engine.dispose()


    # async def connect_to_db_and_get_scheme(self, connection_string: str, user: User): # this is more consise, can lead to edge cases and errors.
    #     try:
    #         engine: AsyncEngine = create_engine(connection_string)
    #         inspector = inspect(engine)

    #         tables = inspector.get_table_names()
    #         scheme = {}

    #         for table_name in tables:
    #             columns = inspector.get_columns(table_name)
    #             scheme[table_name] = columns

    #         engine.dispose()
    #         logger.info('Connected to database and retrieved schema')
    #         print(scheme)
    #         return scheme

    #     except Exception as e:
    #         logger.error(
    #             f"{user.id=} couuldn't connect to database. Reason {e}."
    #         )
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail={
    #                 "success": False,
    #                 "message": f"Coudn't connect to database",
    #                 "data": None,
    #                 "error": {"message": f"Couldn't connect to database:\n {e}."},
    #             },
    #         )

    async def connect_to_database(self, user: User, db_credentials: DbCredentials):
        connection_string = get_connection_string(db_credentials)
        schema = await self.connect_to_db_and_get_scheme(connection_string, user)
        
        if schema:
            db_credentials_for_db = Database(
                db_provider=db_credentials.db_provider,
                db_name=db_credentials.db_name,
                username=db_credentials.db_username,
                password=hash_helper.encrypt(db_credentials.db_password),
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
            f"{user.id=} couldn't connect to database."
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
    
    async def test_connection(db_credentials: DbCredentials) -> bool:
        engine = None
        try:
            connection_string = get_connection_string(db_credentials)
            
            engine = create_engine(connection_string)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            logger.info('Connection tested successfully')
            return True
            
        except Exception as e:
            logger.error(f'Error while connecting to database: Reason - {e}')
            return False
            
        finally:
            if engine is not None:
                engine.dispose()

    async def get_users_databases(self, user: User, page: int, limit: int, search: str = None):
        try:
            offset = (page - 1) * limit
            
            # Base query
            query = select(
                Database,
                func.count().over().label('total_count')
            ).where(
                (Database.user_id == user.id) & 
                (Database.is_deleted == False)
            )
            
            # Add search condition if search term is provided
            if search:
                query = query.where(Database.db_name.ilike(f'%{search}%'))
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            rows = result.all()
            
            if not rows:
                return [], 0
                
            # Get total count from first row
            total_count = rows[0].total_count
            
            databases = [
                {
                    "db_provider": row.Database.db_provider,
                    "db_name": row.Database.db_name,
                    "db_username": row.Database.username,
                    "db_host": row.Database.host,
                    "db_port": row.Database.port,
                    "db_id": row.Database.id,
                    "updated_at": row.Database.updated_at,
                    "created_at": row.Database.created_at
                }
                for row in rows
            ]
            
            logger.info(f"Retrieved databases for {user.id=}")
            
            return databases, total_count
            
        except Exception as exc:
            logger.error(f"Error retrieving databases - {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while retrieving databases."
            )

    async def get_dbs_count(self, user: User):
        try:
            query = select(func.count()).select_from(Database).where(Database.user_id == user.id,Database.is_deleted == False)

            result = await self.db.execute(query)
            count = result.scalar() 
            logger.info('Retrieved databases count')
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
                    f"Db_credentials updated for {user.id=}"
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
                f"{user.id=} couldn't connect to database with new credentials."
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
            f"database credentials with id: {updated_credentials.db_id} not found for {user.id=}."
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

    async def soft_delete_db(self, id: int, user: User):
        database = await self.db.execute(select(Database).where(((Database.id == id))))
        database = database.scalar_one_or_none()

        queries = await self.db.execute(select(Query).where(Query.db_id == id))
        queries = queries.scalars().all()

        if not database:
            logger.error(
                f"Database with {id=} not found for {user.id=}."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Database with ID {id} not found.",
            )

        # soft delete here (database and its queries)
        database.is_deleted = True
        for query in queries:
            query.is_deleted = True
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(
            f"Soft deleted database with {id=} for {user.id=}."
        )
