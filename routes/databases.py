from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from auth.deps import get_current_user, get_db
from models.users import User
from schemas.databases import DbCredentials, UpdatedCredentials
from controllers.databases import DatabaseController
from schemas.generic_response_models import ApiResponse
from utils.logger import logger


DbRoute = APIRouter()


@DbRoute.post("/", response_model=ApiResponse, summary="Save database credentials")
async def create_database_credentials(
    db_credentials: DbCredentials,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    schema = await DatabaseController.save_credentials_and_get_scheme(
        db_credentials, user, db
    )
    logger.info(
        f'[DbRoute->create-new_db_credentials] New database credentaials saved for user_id {user.id}]'
    )
    return ApiResponse(
        message="Schema generated successfully",
        success=True
    )

@DbRoute.put("/test-connection", response_model=ApiResponse, summary="Test a database connection")
async def test_connection(db_credentials:DbCredentials):
    response = await DatabaseController.test_connection(db_credentials)
    if response:
        logger.info(f'[DbRoute->test_connection] Database connection successful.')
        return ApiResponse(
            success=True,
            message="Connection is OK."
        )
    logger.warning('[DbRoute->test_connection] Database connection failed.')
    return ApiResponse(
        success=False,
        message="Couldn't connect to database."
    )




@DbRoute.get("/", summary="Get all databases of current user")
async def get_user_databases(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    user_databases = await DatabaseController.get_user_dbs(user, db)
    logger.info(f"DbRoute->get_user_dbs: Retrieved all databases of {user.id=}.")
    return {
     
        "databases": user_databases
    }


@DbRoute.get("/count", response_model=ApiResponse, summary="Get count of all user databases")
async def get_database_count(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    user_databases_count = await DatabaseController.get_dbs_count(user, db)
    return ApiResponse(
        success=True,
        message=f"databases of {user.id=}",
        data={"count": user_databases_count},
    )

@DbRoute.put("/", summary="Update database credentials")
async def update_database_credentials(
    updated_credentials: UpdatedCredentials,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_db_credentials_schema = await DatabaseController.update_db_credentials(
        updated_credentials, user, db
    )
    logger.info(f"DbRoute->get_user_dbs: Retrieved all databases of {user.id=}.")
    return {
        "data": updated_db_credentials_schema
    }



@DbRoute.delete("/{id}", response_model=ApiResponse, summary="Delete a database")
async def delete_database_credentials(
    id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await DatabaseController.delete_db_credentials(id, user, db)
    logger.info(
        f"DbRoute->delete_db_credentials: Deleted database {id=} for {user.id=}."
    )
    return ApiResponse(
        success=True,
        message=f"Deleted database credentials with {id=}.",
        data=None,
    )
