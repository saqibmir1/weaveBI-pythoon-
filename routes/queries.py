from fastapi import APIRouter, Depends, HTTPException, status
from auth.deps import get_current_user, get_db
from models.users import User
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.queries import UserQueryRequest, QueryInsightsRequest, SaveQueryRequest, UpdateQueryRequest
from schemas.generic_response_models import ApiResponse
from sqlalchemy.ext.asyncio import AsyncSession
from controllers.queries import QueryController


QueryRoute = APIRouter()


@QueryRoute.post("/", response_model=ApiResponse, summary="Save a query")
async def save_query(
        post_queries: SaveQueryRequest,
        db:AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
):
    try:
        success = await QueryController.save_queries(post_queries, db, user)
        if not success:
            return ApiResponse(
                success=False,
                message="Couldn't save query."
            )
        return ApiResponse(
            success=True,
            message="Query saved successfully."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Couldn't save query.",
                "error": {"message": f"{e}"},
            },
        )





@QueryRoute.post("/execute", summary="Run a query")
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
    



@QueryRoute.post("/link-query-to-dashboard", response_model=ApiResponse, summary="Associate a query with a dashboard")
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
    




@QueryRoute.get("/fetch-database-queries/{database_id}", summary="Fetch all queries associated with a database.")
async def fetch_database_queries(database_id:int, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        queries = await QueryController.fetch_database_queries(database_id, user, db)
        return queries
    except Exception as exc:
        return exc

    
@QueryRoute.get("/count/{dashboard_id}", response_model=ApiResponse, summary="Fetch count of dashboards for current user")
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