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


app.include_router(UserRouter, tags=["user"], prefix="/user")
app.include_router(DbRoute, tags=["database"], prefix="/database")
app.include_router(QueryRoute, tags=["query"], prefix="/query")
app.include_router(DashboardRoute, tags=["dashboard"], prefix="/dashboard")


## ci cd test
