from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User
from services.dashboards import DashboardService
from schemas.dashboards import DashboardCreate, DashboardUpdate, UpdateQueriesRequest



class DashboardController:


    async def create_dashboard(user:User, db:AsyncSession, dashboard_data: DashboardCreate):
          dashboard_service = DashboardService(db)
          return await dashboard_service.create_dashboard(user, dashboard_data)

    async def get_dashboards(user: User, db: AsyncSession, page: int, limit: int):
        dashboard_service = DashboardService(db)
        return await dashboard_service.get_dashboards(user, page, limit)  

    
    async def get_dashboard(id:int, user:User, db:AsyncSession):
            dashboard_service = DashboardService(db)
            return await dashboard_service.get_dashboard(id, user)


    async def update_dashboard(updated_dashboard:DashboardUpdate, user:User,db:AsyncSession):
          dashboard_service = DashboardService(db)
          return await dashboard_service.update_dashboard(updated_dashboard, user)

    async def get_dashboards_count(user:User, db:AsyncSession):
          dashboard_service = DashboardService(db)
          return await dashboard_service.get_dashboards_count(user)
    

    async def delete_dashboard(user:User, db:AsyncSession, dashboard_id:int):
          dashboard_service = DashboardService(db)
          return await dashboard_service.delete_dashboard(user, dashboard_id)
    

    async def execute_dashboard_queries(dashboard_id:int, db:AsyncSession, user:User):
          dashboard_service = DashboardService(db)
          return await dashboard_service.execute_dashboard_queries(dashboard_id,user)
    


    async def fetch_dashboard_data(dashboard_id:int, db:AsyncSession, user:User):
          dashboard_service = DashboardService(db)
          return await dashboard_service.fetch_dashboard_data(dashboard_id, user)


    async def get_dashboard_queries(dashboard_id:int, user:User, db:AsyncSession):
          dashboard_service = DashboardService(db)
          return await dashboard_service.get_dashboard_queries(dashboard_id, user)
    

    async def update_dashboard_layout( layout:UpdateQueriesRequest, user:User, db:AsyncSession):
          dashboard_service = DashboardService(db)
          return await dashboard_service.update_dashboard_layout(layout, user)
    
    async def get_dashboards_by_tags(tags, user:User, db:AsyncSession):
          dashboard_service = DashboardService(db)
          return await dashboard_service.get_dashboards_by_tags(tags, user)