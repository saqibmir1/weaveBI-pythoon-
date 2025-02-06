import os
import json
import yaml
import asyncio

from typing import List
from fastapi import HTTPException, status
from sqlalchemy import select, update, create_engine, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
import nest_asyncio
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
from nemoguardrails import RailsConfig

from models.databases import Database
from models.queries import Query
from models.users import User
from models.tags import Tag
from models.dashboards import Dashboard, dashboard_queries, dashboard_tags
from schemas.dashboards import DashboardCreate, DashboardUpdate, UpdateQueriesRequest
from utils.logger import logger
from utils.user_queries import result_to_json_updated
from config.llm_config import settings as llm_settings
from config import llm_config

os.environ["OPENAI_API_KEY"] = llm_settings.api_key
nest_asyncio.apply()
model = llm_config.settings.model
config = RailsConfig.from_path("guardrails")
guard_rail = RunnableRails(config=config)

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db


    async def create_dashboard(self, user: User, dashboard_data: DashboardCreate):
    # create dashboard 

        # Check if the dashboard already exists
        existing_dashboard_query = await self.db.execute(
            select(Dashboard).where(
                Dashboard.name == dashboard_data.name,
                Dashboard.user_id == user.id,
                Dashboard.is_deleted == False
            )
        )
        existing_dashboard = existing_dashboard_query.scalars().first()

        if existing_dashboard:
            logger.info(f"Dashboard with name '{dashboard_data.name}' already exists for user id {user.id}.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Dashboard with this name already exists."
            )

        # Create a new dashboard
        new_dashboard = Dashboard(
            name=dashboard_data.name,
            description=dashboard_data.description,
            user_id=user.id,
            db_id=dashboard_data.db_id
        )

        try:
            self.db.add(new_dashboard)
            await self.db.commit()
            await self.db.refresh(new_dashboard)
            logger.info(f"Dashboard with id {new_dashboard.id} and db_id {new_dashboard.db_id} stored in DB.")

            # Save tags and link them to the dashboard
            for tag_name in dashboard_data.tags:
                existing_tag_query = await self.db.execute(
                    select(Tag).where(Tag.name == tag_name)
                )
                existing_tag = existing_tag_query.scalars().first()

                if not existing_tag:
                    new_tag = Tag(name=tag_name)
                    self.db.add(new_tag)
                    await self.db.commit()
                    await self.db.refresh(new_tag)
                    await self.db.refresh(new_dashboard)

                    tag_id = new_tag.id
                else:
                    tag_id = existing_tag.id

                # link dashboard_id -> tag_id
                await self.db.execute(dashboard_tags.insert().values(dashboard_id=new_dashboard.id, tag_id=tag_id))
                await self.db.commit()
                await self.db.refresh(new_dashboard)
                
            logger.info(f"Tags saved in db.")
            return dashboard_data

        except Exception as exc:
            await self.db.rollback()
            logger.info(f'Error while saving dashboard - {exc}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while saving the dashboard."
            )

    async def get_dashboards(self, user: User, page: int, limit: int, search: str):
        try:
            offset = (page - 1) * limit
            
            # Base query
            query = select(Dashboard, func.count().over().label('total_count')).where(
                (Dashboard.user_id == user.id) &
                (Dashboard.is_deleted == False)
            )
            
            # Add search filter if search term is provided
            if search:
                query = query.where(Dashboard.name.ilike(f"%{search}%"))
            
            # Add pagination
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            rows = result.all()
            
            if not rows:
                return [], 0
                
            # Extract total count from first row
            total_count = rows[0].total_count
            
            logger.info(f"Retrieved {len(rows)} dashboards from DB for user {user.id}")
            
            dashboards = [
                {
                    "id": row.Dashboard.id,
                    "name": row.Dashboard.name,
                    "description": row.Dashboard.description,
                    "db_id": row.Dashboard.db_id,
                    "created_on": row.Dashboard.created_at,
                    "updated_at": row.Dashboard.updated_at
                }
                for row in rows
            ]
            
            return dashboards, total_count
            
        except Exception as exc:
            logger.error(f"Error retrieving dashboards - {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while retrieving dashboards."
            )

    async def get_dashboards_count(self, user: User):
        try:
        
            query = select(func.count()).select_from(Dashboard).where(Dashboard.user_id == user.id,Dashboard.is_deleted == False)

            result = await self.db.execute(query)
            count = result.scalar() 
            return count
            
        except Exception as exc:
            logger.error(f"Error retrieving dashboards - {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while retrieving dashboards."
            )
        

    async def update_dashboard(self, updated_dashboard:DashboardUpdate, user:User):
    # update dashboard (name and desciption using id)
        result = await self.db.execute(
            select(Dashboard).where(
                (Dashboard.id==updated_dashboard.dashboard_id) & (Dashboard.user_id==user.id) & (Dashboard.is_deleted==False)###### check is_deleted later ###########
            )
        )

        existing_dashboard =  result.scalar_one_or_none()
        if existing_dashboard:
            existing_dashboard.name = updated_dashboard.name
            existing_dashboard.description = updated_dashboard.description

            await self.db.commit()
            await self.db.refresh(existing_dashboard)
            logger.info(f'Dashboard updated: with new name as {updated_dashboard.name} and new desc. as {updated_dashboard.description}')
            return True
        return False

    async def delete_dashboard(self, user:User, dashboard_id:int):
    # delete dashboard using id
        try:
            # delete from Dashboard
            await self.db.execute(update(Dashboard).where((Dashboard.id == dashboard_id) & (Dashboard.user_id==user.id)).values(is_deleted=True))
            logger.info(f"Soft Deleted dashboard with id: {dashboard_id}")

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"Error deleting dashboard {dashboard_id} - {str(e)}")
            await self.db.rollback()
            return False
        

    async def execute_dashboard_queries(self, dashboard_id: int, user: User):
    # execute dashobard queries

        # Get all queries of that dashboard
        queries_result = await self.db.execute(
        select(Query).join(dashboard_queries).where(dashboard_queries.c.dashboard_id == dashboard_id,Query.is_deleted == False))
        queries = queries_result.scalars().all()

        if not queries:
            logger.warning(f"No queries found for dashboard with ID {dashboard_id}")
            return None

        # Fetch db schema
        schema_result = await self.db.execute(select(Database.schema).join(Dashboard, Dashboard.db_id == Database.id).where(
        Dashboard.id == dashboard_id,
        Database.is_deleted == False))
        schema = schema_result.scalar_one_or_none()

        # fetch connection string
        connection_string_result = await self.db.execute(select(Database.db_connection_string).join(Dashboard, Dashboard.db_id == Database.id).where(
        Dashboard.id == dashboard_id,
        Database.is_deleted == False))

        connection_string = connection_string_result.scalar_one_or_none()

          # Load prompts
        with open("prompts/prompts.yaml", "r") as f:
            prompts = yaml.safe_load(f)
    
        # Create LLM instance
        llm = ChatOpenAI(model=model, temperature=0)

        async def process_single_query(query: Query) -> None:
            try:
                query_text = query.query_text
                output_type = query.output_type
                query_id = query.id

                # Step 1: Get SQL query based on type
                if output_type == "tabular":
                    prompt = (
                        prompts["system_prompts"]["primary"] +
                        f'Schema: {schema}\n'
                    )
                elif output_type == "descriptive":
                    prompt = (
                        prompts["system_prompts"]["primary"] +
                        f'Schema: {schema}\n'
                    )
                else:
                    prompt = (
                        prompts["system_prompts"]["graphical"] +
                        f'Schema: {schema}\n' +
                        f'Graphial Representation type: {output_type}'
                    )

                # Generate SQL
                chat_template = ChatPromptTemplate.from_messages(
                    [
                        SystemMessage(content=prompt),
                        HumanMessagePromptTemplate.from_template("User question: \n{input}"),
                    ]
                )
                output_parser = StrOutputParser()
                llm_chain = chat_template | llm | output_parser
                guard_rail_chain = guard_rail | llm_chain

                sql_query = guard_rail_chain.invoke({"input": query_text})

                # Check for guardrail block
                if isinstance(sql_query, dict) and sql_query.get("output") == "I'm sorry, I can't respond to that.":
                    sql_query = "Query blocked by guardrails"
                    final_data = "Query blocked by guardrails"
                    logger.warning(f'Query with id {query_id} blocked by Guardrails')
                else:
                    # Step 2: Execute SQL query
                    engine = create_engine(connection_string)
                    Session = sessionmaker(bind=engine)
                    session = Session()

                    if sql_query.strip().lower().startswith("select") and "LIMIT" not in sql_query:
                        sql_query = f'{sql_query.strip().rstrip(";")} LIMIT 100;'     # hard coded limit for now :p
                    query = text(sql_query)
                    result = session.execute(query)
                    query_result = result_to_json_updated(result)

                    # Step 3: Process result based on type
                    if output_type == "tabular":
                        final_data = query_result
                    elif output_type == "descriptive":
                        insights_prompt = (
                            prompts["system_prompts"]["descriptive_prompt"] +
                            f'User Query: {query_text}\n' +
                            f'Generated SQL Query: {sql_query}\n' +
                            f'Query Output from database: {query_result}'
                        )
                        insights_response = await llm.agenerate([insights_prompt])
                        final_data = insights_response.generations[0][0].text.strip()
                    else:
                        chart_prompt = (
                            prompts["system_prompts"]["chartjs_formatter"] +
                            f'User Query: {query_text}\n' +
                            f'Generated SQL Query: {sql_query}\n' +
                            f'Query Output From Database: {query_result}\n' +
                            f'Graphical Representation type: {output_type}'
                        )
                        chart_response = await llm.agenerate([chart_prompt])
                        final_data = chart_response.generations[0][0].text.strip()

                # Put final data and generated SQL query in table
                serialized_data = json.dumps(final_data)
                await self.db.execute(update(Query).where(Query.id == query_id).values(data=serialized_data))
                await self.db.execute(update(Query).where(Query.id == query_id).values(generated_sql_query=sql_query))

                logger.info(f'Query with id: {query_id}: {output_type} Output Generated ')

            except Exception as e:
                logger.error(f'Error processing query {query_text}: {str(e)}')
                raise

        try:
            # execute all queries in ||
            await asyncio.gather(
                *(process_single_query(query) for query in queries)
            )
            await self.db.commit()
            logger.info(f'Ouptuts stored in db')
        
        except Exception as e:
            await self.db.rollback()
            logger.error(f'Error in dashboard query exectution: {str(e)}')
            raise

    async def fetch_dashboard_data(self, dashboard_id: int, user: User):
        # fetch dashboard data ie. its queries, output, and their layout etc
        try:
            dashboard_result = await self.db.execute(
                select(Dashboard).where(
                    (Dashboard.id == dashboard_id) &
                    (Dashboard.user_id == user.id) &
                    (Dashboard.is_deleted == False)
                )
            )
            dashboard = dashboard_result.scalar_one_or_none()
            
            if not dashboard:
                logger.warning(f"Dashboard with ID {dashboard_id} not found or not accessible by user {user.id}")
                return None

            # Explicitly select only the columns we need
            query_with_layout = await self.db.execute(
                select(
                    Query,
                    dashboard_queries.c.x,
                    dashboard_queries.c.y,
                    dashboard_queries.c.w,
                    dashboard_queries.c.h
                )
                .join(dashboard_queries, Query.id == dashboard_queries.c.query_id)
                .where(
                    dashboard_queries.c.dashboard_id == dashboard_id,
                    Query.is_deleted == False
                )
            )
            
            results = query_with_layout.all()
            logger.info(f"Fetched all queries with layout for dashboard ID: {dashboard_id}")

            serialized_queries = [
                {
                    "id": query.id,
                    "query_name": query.query_name,
                    "query_text": query.query_text,
                    "output_type": query.output_type,
                    "data": query.data,
                    "updated_at": query.updated_at,
                    "created_at": query.created_at,
                    # Add layout information
                    "layout": {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h,
                    }
                }
                for query, x, y, w, h in results
            ]

            return {
                "queries": serialized_queries,
            }

        except Exception as e:
            logger.error(f"Error while fetching dashboard data for ID {dashboard_id}: {str(e)}")
            await self.db.rollback()
            return None
        
    async def update_dashboard_layout(self, layout_data: UpdateQueriesRequest, user: User):
        # update dashboard layout
        try:
            for query_layout in layout_data.queries:
                await self.db.execute(
                    dashboard_queries.update()
                    .where(
                        (dashboard_queries.c.dashboard_id == layout_data.dashboard_id) &
                        (dashboard_queries.c.query_id == query_layout.query_id)
                    )
                    .values(
                        x=query_layout.x,
                        y=query_layout.y,
                        w=query_layout.w,
                        h=query_layout.h
                    )
                )
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating dashboard layout: {str(e)}")
            await self.db.rollback()
            return False


    async def fetch_database_queries(self,database_id:int,  user: User):
        # fetch all queries for a database
        try:
            result = await self.db.execute(
                select(Query).where(
                    (Query.is_deleted == False) & (Query.db_id==database_id)
                )
            )
            queries = result.scalars().all()
            logger.info(f"Fetched all queries for user {user.id}")

            return [
                {
                    "id": query.id,
                    "query_name": query.query_name,
                    "query_text": query.query_text,
                    "output_type": query.output_type,
                    "created_at": query.created_at,
                    "updated_at": query.updated_at
                }
                for query in queries
            ]
        except Exception as e:
            logger.error(f"Error fetching queries - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while fetching queries."
            )

    async def get_dashboard(self, id: int, user: User):
        # get dashboard by id and its tags
        try:
            result = await self.db.execute(
                select(Dashboard).where(
                    (Dashboard.id == id) & (Dashboard.user_id == user.id) & (Dashboard.is_deleted == False)
                )
            )
            dashboard = result.scalar_one_or_none()

            if not dashboard:
                logger.warning(f"Dashboard with ID {id} not found or not accessible by user {user.id}")
                return None

            # get tags for that dashboard
            tags_result = await self.db.execute(
                select(Tag).join(dashboard_tags).where(
                    dashboard_tags.c.dashboard_id == id
                )
            )
            tags = tags_result.scalars().all()
            dashboard_data = {
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "db_id": dashboard.db_id,
                "created_on": dashboard.created_at,
                "updated_at": dashboard.updated_at,
                "tags": [tag.name for tag in tags]
            }

            return dashboard_data
        except Exception as e:
            logger.error(f"Error fetching dashboard - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while fetching dashboard."
            )
        
    async def get_dashboard_queries(self, dashboard_id: int, user: User, page: int, limit: int):
        # get all queries for a dashboard with pagination and total count
        try:
            offset = (page - 1) * limit

            query = select(Query, func.count().over().label('total_count')).join(dashboard_queries).where(
                (dashboard_queries.c.dashboard_id == dashboard_id) & (Query.is_deleted == False)
            ).limit(limit).offset(offset)

            result = await self.db.execute(query)
            rows = result.all()

            if not rows:
                return [], 0

            total_count = rows[0].total_count

            logger.info(f"Fetched {len(rows)} queries for dashboard with ID {dashboard_id}")

            queries = [
                {
                    "id": row.Query.id,
                    "query_name": row.Query.query_name,
                    "query_text": row.Query.query_text,
                    "output_type": row.Query.output_type,
                    "created_at": row.Query.created_at,
                    "updated_at": row.Query.updated_at
                }
                for row in rows
            ]

            return queries, total_count
        except Exception as e:
            logger.error(f"Error fetching queries - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while fetching queries."
            )

    async def get_dashboards_by_tags(self, tags: List[str], user: User, page: int, limit: int):
        offset = (page - 1) * limit

        # If tags is empty or None, return all dashboards
        if not tags:
            return await self.get_dashboards(user, page, limit)

        query = select(Dashboard, func.count().over().label('total_count')).join(dashboard_tags).join(Tag).where(
            (Dashboard.user_id == user.id) &
            (Dashboard.is_deleted == False) &
            (Tag.name.in_(tags))
        ).distinct().limit(limit).offset(offset)

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return [], 0

        total_count = rows[0].total_count

        logger.info(f"Retrieved {len(rows)} dashboards by tags for user {user.id}")

        dashboards = [
            {
                "id": row.Dashboard.id,
                "name": row.Dashboard.name,
                "description": row.Dashboard.description,
                "db_id": row.Dashboard.db_id,
                "created_on": row.Dashboard.created_at,
                "updated_at": row.Dashboard.updated_at
            }
            for row in rows
        ]

        return dashboards, total_count
