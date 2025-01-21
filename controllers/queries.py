from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.queries import UserQueryRequest, QueryInsightsRequest, SaveQueryRequest
from services.queries import QueryService
from models.models import User
from typing import List
from utils.logger import logger



class QueryController:

    
    
    async def save_queries(post_queries: SaveQueryRequest, db: AsyncSession, user: User) -> bool:
            query_service = QueryService(db=db)
            return await query_service.save_queries(post_queries=post_queries, user=user)



    async def execute_query(query_id, db: AsyncSession, user: User):
        query_service = QueryService(db=db)
        return await query_service.execute_query(query_id, user)


    async def get_insights(query_id: int, use_web:bool, custom_instructions:QueryInsightsRequest, db: AsyncSession, user: User) -> str:
        query_service = QueryService(db=db)
        insights = await query_service.get_insights(query_id, use_web, custom_instructions)
        return insights
    

    async def link_query_to_dashboard(query_id: int, dashboard_id: int, db: AsyncSession, user: User):
        query_service = QueryService(db=db)
        return await query_service.link_query_to_dashboard(query_id, dashboard_id, user)
    


    async def fetch_database_queries(database_id:int, user: User,  db: AsyncSession):
        dashboard_service = QueryService(db)
        return await dashboard_service.fetch_database_queries(database_id, user)


    
    async def get_queries_count(dashboard_id:int, user: User,  db: AsyncSession):
            dashboard_service = QueryService(db)
            return await dashboard_service.get_queries_count(dashboard_id, user)
    

    async def delete_query(query_id: int, user: User, db: AsyncSession,):
        query_service = QueryService(db=db)
        return await query_service.delete_query(query_id, user)