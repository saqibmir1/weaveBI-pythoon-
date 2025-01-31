from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from auth.deps import get_current_user, get_db
from models.users import User
from controllers.dashboards import DashboardController
from schemas.dashboards import DashboardCreate,  DashboardUpdate, UpdateQueriesRequest
from schemas.generic_response_models import  ApiResponse
from typing import List


DashboardRoute = APIRouter()


@DashboardRoute.post("/", response_model=ApiResponse, summary="Create a dashboard")
async def create_dashboard(
    dashboard_data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        dashboard_data = await DashboardController.create_dashboard(
            dashboard_data=dashboard_data,
            db=db,
            user=user
        )
        return ApiResponse(
            success=True,
            message="Dashboard created successfully.",
            data={"dashboard": dashboard_data}
        )

    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An unexpected error occurred.",
            error=str(exc)
        )






@DashboardRoute.get("/", response_model=ApiResponse, summary="Get all dashboards")
async def get_dashboards(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit:int = 10,
):
    try:
        user_dashboards, total_count = await DashboardController.get_dashboards(user, db, page, limit)
        return ApiResponse(
            success=True,
            message="Dashboards retrieved successfully.",
            data={
                "dashboards": user_dashboards,
                "total_count": total_count,
                "page": page,
                "limit": limit
            }
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An unexpected error occurred while retrieving dashboards.",
            error=str(exc)
        )
    


@DashboardRoute.get("/by-tags", summary="Get dashboards filtered by tags")
async def get_dashboards_by_tags(
    tags: List[str] = Query(None),  # Use Query for multiple tag parameters
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page:int=1,
    limit:int=10
):
    try:
        user_dashboards, total_count = await DashboardController.get_dashboards_by_tags(tags, user, db, page, limit)
        return {
            "user_dashboards": user_dashboards,
            "total_count": total_count,
        }
    except Exception as exc:
        return None


    

@DashboardRoute.get("/count", response_model=ApiResponse, summary="Get count of all dashboards")
async def get_dashboards_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        user_dashboards_count = await DashboardController.get_dashboards_count(user, db)
        return ApiResponse(
            success=True,
            message="Dashboards count retrieved successfully.",
            data={"count": user_dashboards_count}
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An unexpected error occurred while retrieving dashboards.",
            error=str(exc)
        )





@DashboardRoute.get("/dashboard/{id}", summary="Get a particular dashboard info")
async def get_dashboard(
    id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        dashboard = await DashboardController.get_dashboard(id, user, db)
        return dashboard
    except HTTPException as http_exc:
        return ApiResponse(
            success=False,
            message=http_exc.detail,
            error=str(http_exc)
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An unexpected error occurred while retrieving the dashboard.",
            error=str(exc)
        )



@DashboardRoute.get("/queries/{dashboard_id}", response_model=ApiResponse, summary="Get all queries associated with a dashboard")
async def get_dashboard_queries(
    dashboard_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page:int = 1,
    limit:int = 10,
):
    try:
        queries, total_count = await DashboardController.get_dashboard_queries(dashboard_id, user, db, page, limit)
        return ApiResponse(
            success=True,
            message="Queries retrieved successfully.",
            data = {
                "queries": queries,
                "total_count": total_count,
                "page": page,
                "limit": limit
            }
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An error occurred while retrieving queries for the dashboard.",
            error=str(exc)
        )




@DashboardRoute.delete("/{id}", response_model=ApiResponse, summary="Delete a dashboard")
async def delete_dashboard(
    id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        dashboard_deleted = await DashboardController.delete_dashboard(user, db, id)

        if not dashboard_deleted:
            return ApiResponse(
                success=False,
                message=f"Failed to delete dashboard with ID {id}.",
                error="Dashboard could not be deleted."
            )
        
        return ApiResponse(
            success=True,
            message=f"Dashboard with ID {id} successfully deleted."
        )

    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Error occurred while deleting the dashboard.",
            error=str(exc)
        )





@DashboardRoute.put("/", response_model=ApiResponse, summary="Update a dashboard")
async def update_dashboard(updated_dashboard:DashboardUpdate, user:User=Depends(get_current_user), db:AsyncSession=Depends(get_db)):
    try:
        updated_dashboard_info = await DashboardController.update_dashboard(updated_dashboard, user, db)
        return ApiResponse(
            success=True,
            message="Dashboard updated successfully",
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="Error occurred while updating the dashboard.",
            error=str(exc)
        )



# @DashboardRoute.post("/queries", response_model=ApiResponse)
# async def post_queries_for_dashboard(
#     post_queries: PostQueriesRequest,
#     db:AsyncSession=Depends(get_db),
#     user:User=Depends(get_current_user)
# ):
#     try:
#         queries = await DashboardController.post_queries_for_dashboard(post_queries, db, user)
#         if not queries:
#             return ApiResponse(
#             success=False,
#             message=f'Dashboard with ID {post_queries.dashboard_id} not found',
#             error="Unable to add queries to dashboard"
#             )
#         return ApiResponse(
#         success=True,
#         message=f'Queries submitted successfully.',
#         )
#     except Exception as exc:
#         return ApiResponse(
#             success=False,
#             message="An error occurred while adding queries to the dashboard.",
#             error=str(exc)
#         )



@DashboardRoute.get("/refresh/{id}", response_model=ApiResponse, summary="Re-execute all queries in a dashboard parallely")
async def execute_dashboard_queries(
    id:int,
    db:AsyncSession=Depends(get_db),
    user:User=Depends(get_current_user)
):
    try:
        data = await DashboardController.execute_dashboard_queries(id, db, user)
        return ApiResponse(
            success=True,
            message="Queries executed successfully"
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message=f"An error occured while executing queries for dashboard {id}",
            error=str(exc)
        )


@DashboardRoute.get("/fetch-data/{id}", response_model=ApiResponse, summary="Fetch dashboard data (queries, layout, etc)")
async def fetch_dashboard_data(
    id:int,
    db:AsyncSession=Depends(get_db),
    user:User=Depends(get_current_user)
):
    try:
        data = await DashboardController.fetch_dashboard_data(id, db, user)
        return ApiResponse(
            success=True,
            message="Fetched dashboard data successfully",
            data = data,
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message=f"An error occured while fetching dashboad data with ID {id}",
            error=str(exc)
        )




@DashboardRoute.patch("/dashboard-query-layout", response_model=ApiResponse, summary="Update dashboard layout")
async def update_dashboard_layout(
    layout: UpdateQueriesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        success = await DashboardController.update_dashboard_layout(layout, current_user, db)
        if success:
            return ApiResponse(
                success=True,
                message="Dashboard layout updated successfully."
            )
        else:
            return ApiResponse(
                success=False,
                message="Failed to update dashboard layout."
            )
    except Exception as exc:
        return ApiResponse(
            success=False,
            message="An error occurred while updating dashboard layout.",
            error=str(exc)
        )
    



# @DashboardRoute.put("/queries", response_model=ApiResponse)
# async def update_queries(
#     update_queries: UpdateQueriesRequest,
#     db: AsyncSession = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     try:
#         success = await DashboardController.update_queries(update_queries, db, user)
#         if not success:
#             return ApiResponse(
#                 success=False,
#                 message="Failed to update queries.",
#                 error="Unable to update queries for the dashboard."
#             )
#         return ApiResponse(
#             success=True,
#             message="Queries updated successfully."
#         )
#     except Exception as exc:
#         return ApiResponse(
#             success=False,
#             message="An error occurred while updating queries.",
#             error=str(exc)
#         )



# @DashboardRoute.get("/insights/{query_id}", response_model=ApiResponse)
# async def get_insights(
#     query_id: int,
#     use_web:bool=False,
#     request: InsightsRequest = Depends(),
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):

#     try:
#         insights = await DashboardController.get_insights(
#             query_id=query_id,
#             use_web=use_web,
#             custom_instructions=request.custom_instructions,
#             db=db,
#             user=current_user
#         )
#         return ApiResponse(
#             success=True,
#             message="Insights generated successfully",
#             data={
#                 "Insights": insights
#             }
#         )
#     except Exception as exc:
#         return ApiResponse(
#             success=False,
#             message=f"An error occured while generating insights for query {query_id}",
#             error=str(exc)
#         )

