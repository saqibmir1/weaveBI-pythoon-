from fastapi import APIRouter, Depends, HTTPException, status
from auth.deps import get_current_user, get_db
from models.users import User
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.queries import UserQueryRequest, QueryInsightsRequest, SaveQueryRequest, UpdateQueryRequest
from schemas.generic_response_models import ApiResponse
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.queries import QueryController

QueryRoute = APIRouter()

@QueryRoute.post("/", response_model=ApiResponse, summary="Save multiple queries")
async def save_queries(
    post_queries: list[SaveQueryRequest],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        success = await QueryController.save_queries(post_queries, db, user)
        if not success:
            return ApiResponse(
            success=False,
            message="Couldn't save queries."
            )
        return ApiResponse(
            success=True,
            message="Queries saved successfully."
    )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
            "success": False,
            "message": "Couldn't save queries.",
            "error": {"message": f"{e}"},
            },
        )

@QueryRoute.post("/execute", summary="Run a query and save output in database")
async def execute_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):

    try:
        data = await QueryController.execute_query(query_id, db, user)
        return data
        
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error occured while executing query"
        )
    
@QueryRoute.get("/insights/{id}", response_model=ApiResponse, summary="Get insights for an existing query")
async def get_insights(
    id: int,
    use_web:bool=False,
    request: QueryInsightsRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    try:
        insights = await QueryController.get_insights(
            query_id=id,
            use_web=use_web,
            custom_instructions=request.custom_instructions,
            db=db,
            user=current_user
        )
        return ApiResponse(
            success=True,
            message="Insights generated successfully",
            data={
                "Insights": insights
            }
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message=f"An error occured while generating insights for query {id}",
            error=str(exc)
        )

@QueryRoute.post("/link-to-dashboard", response_model=ApiResponse, summary="Associate a query with a dashboard")
async def link_query_to_dashboard(
    query_id: int,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        success = await QueryController.link_query_to_dashboard(query_id, dashboard_id, db, user)
        if not success:
            return ApiResponse(
                success=False,
                message="Couldn't link query to dashboard."
            )
        return ApiResponse(
            success=True,
            message="Query linked to dashboard successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't link query to dashboard.",
                "error": {"message": f"{e}"},
                },
            )
    
@QueryRoute.post("/unlink-from-dashboard", response_model=ApiResponse, summary="'Disassociate' a query with a dashboard")
async def unlink_query_to_dashboard(
    query_id: int,
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        success = await QueryController.unlink_query_to_dashboard(query_id, dashboard_id, db, user)
        if not success:
            return ApiResponse(
                success=False,
                message="Couldn't unlink query to dashboard."
            )
        return ApiResponse(
            success=True,
            message="Query unlinked to dashboard successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't unlink query to dashboard.",
                "error": {"message": f"{e}"},
                },
            )

@QueryRoute.get("/fetch-database-queries/{database_id}", summary="Fetch all queries associated with a database.")
async def fetch_database_queries(
    database_id:int,
    user:User=Depends(get_current_user),
    db:AsyncSession=Depends(get_db),
    page:int=1,
    limit:int=10,
    search:str=None
    ):
    try:
        queries, total_count = await QueryController.fetch_database_queries(database_id, user, db, page, limit, search)
        return {
            "queries": queries,
            "total_count": total_count,
            "page": page,
            "limit": limit
    }

    except Exception as exc:
        return exc
    
@QueryRoute.get("/count/{dashboard_id}", response_model=ApiResponse, summary="Fetch count of queries in a dashboard.")
async def get_queries_count(database_id:int, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        queries_count = await QueryController.get_queries_count(database_id, user, db)
        return ApiResponse(
            data={"count": queries_count}
        )
    
    except Exception as exc:
        return exc

@QueryRoute.delete("/{id}", response_model=ApiResponse, summary="Delete a query")
async def delete_query(id:int, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        success = await QueryController.delete_query(id, user, db)
        if not success:
            return ApiResponse(
                success=False,
                message="Couldn't delete query."
            )
        return ApiResponse(
            success=True,
            message="Query deleted successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't delete query.",
                "error": {"message": f"{e}"},
            },
        )
    
@QueryRoute.put("/", response_model=ApiResponse, summary="Update a query")
async def update_query(
    post_queries: UpdateQueryRequest, 
    user:User=Depends(get_current_user), 
    db:AsyncSession=Depends(get_db)
    ):
    try:
        await QueryController.update_query(post_queries, user, db)
        return ApiResponse(
            success=True,
            message="Query updated successfully.",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't update query.",
                "error": {"message": f"{exc}"},
            },
        )
    

@QueryRoute.post("/run", response_model=ApiResponse, summary="Execute a query and show output without saving it to the database")
async def run_query(
    post_queries: UserQueryRequest, 
    user:User=Depends(get_current_user), 
    db:AsyncSession=Depends(get_db)
    ):
    try:
        data = await QueryController.run_query(post_queries, user, db)
        return ApiResponse(
            success=True,
            message="Query executed successfully.",
            data=data
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't execute query.",
                "error": {"message": f"{exc}"},
            },
        )
    

@QueryRoute.get("/suggest" ,summary="Suggest queries using LLM based on database schema")
async def suggest_queries(db_id: int, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        queries = await QueryController.suggest_queries(db_id, user, db)
        return queries

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't suggest queries.",
                "error": {"message": f"{exc}"},
            },
        )