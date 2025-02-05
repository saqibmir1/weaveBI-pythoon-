from models.users import User
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.databases import DbCredentials, UpdatedCredentials
from services.databases import DatabaseService


class DatabaseController:

    async def save_credentials_and_get_scheme(
        db_credentials: DbCredentials, user: User, db: AsyncSession):
        daoDbCredentials = DatabaseService(db=db)
        return await daoDbCredentials.connect_to_database(user, db_credentials)


    async def get_user_dbs(user: User, db: AsyncSession, page:int, limit:int):
        daoDbCredentials = DatabaseService(db=db)
        return await daoDbCredentials.get_users_databases(user, page, limit)
    
    async def search_databases(user: User, db: AsyncSession, search:str, page:int, limit:int):
        daoDbCredentials = DatabaseService(db=db)
        return await daoDbCredentials.search_databases(user, search, page, limit)
    
    
    async def get_dbs_count(user: User, db: AsyncSession):
        daoDbCredentials = DatabaseService(db=db)
        return await daoDbCredentials.get_dbs_count(user)

    
    async def test_connection(dbcredentials:DbCredentials):
        return await DatabaseService.test_connection(dbcredentials)


    async def update_db_credentials(
        updated_credentials: UpdatedCredentials, user: User, db: AsyncSession):
        daoDbCredentials = DatabaseService(db=db)
        return await daoDbCredentials.update_db_credentials_and_get_scheme(updated_credentials, user)


    async def delete_db_credentials(id: int, user: User, db: AsyncSession):
        daoDbCredentials = DatabaseService(db=db)
        await daoDbCredentials.soft_delete_db(id, user)


