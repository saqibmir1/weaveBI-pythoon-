from fastapi import FastAPI
from database.database import engine
from contextlib import asynccontextmanager
from routes.users import UserRouter
from routes.databases import DbRoute
from routes.queries import QueryRoute
from routes.dashboards import DashboardRoute
from config.app_config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.connect()

    yield

    await engine.dispose()


app.include_router(UserRouter, tags=["USERS"], prefix="/users")
app.include_router(DbRoute, tags=["DATABASES"], prefix="/databases")
app.include_router(QueryRoute, tags=["QUERY"], prefix="/query")
app.include_router(DashboardRoute, tags=["DASHBOARD"], prefix="/dashboard")
