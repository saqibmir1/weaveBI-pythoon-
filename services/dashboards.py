from fastapi import HTTPException
from sqlalchemy import select, join, update, create_engine, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from models.models import User, Dashboard, Database, Query, dashboard_queries
from utils.logger import logger
from schemas.dashboards import DashboardCreate,DashboardUpdate, PostQueriesRequest, UpdateQueriesRequest
from sqlalchemy.exc import IntegrityError
import json, yaml, os
from utils.user_queries import result_to_json_updated
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import sessionmaker
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
from config.llm_config import settings as llm_settings
import nest_asyncio
import asyncio
from config import llm_config
from nemoguardrails import RailsConfig
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

os.environ["OPENAI_API_KEY"] = llm_settings.api_key
model = llm_config.settings.model

nest_asyncio.apply()
config = RailsConfig.from_path("guardrails")
guard_rail = RunnableRails(config=config)



class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # create dashboard 
    async def create_dashboard(self, user: User, dashboard_data: DashboardCreate):
        # Check if the dashboard already exists
        existing_dashboard_query = await self.db.execute(
            select(Dashboard).where(
                Dashboard.name == dashboard_data.name,
                Dashboard.user_id == user.id
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
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while saving the dashboard."
            )
    
   
    

    # get all dashboards
    async def get_dashboards(self, user: User):
        try:
            # Query dashboards for the user that are not deleted
            result = await self.db.execute(
                select(Dashboard).where(
                    (Dashboard.user_id == user.id) & (Dashboard.is_deleted == False)
                )
            )
            dashboards_from_db = result.scalars().all()
            logger.info(f"Retrieved all dashboards from the DB for user {user.id}")

            
            return [
                {
                    "id": dashboard.id,
                    "name": dashboard.name,
                    "description": dashboard.description,
                    "db_id": dashboard.db_id,
                    "created_on": dashboard.created_at,
                    "updated_at": dashboard.updated_at
                    
                }
                for dashboard in dashboards_from_db
            ]
        except Exception as exc:
            logger.error(f"DashboardService->get_dashboards: Error retrieving dashboards - {exc}")
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
            logger.error(f"DashboardService->get_dashboards: Error retrieving dashboards - {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while retrieving dashboards."
            )
        

    # update dashboard (name and desciption using id)
    async def update_dashboard(self, updated_dashboard:DashboardUpdate, user:User):
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





    # delete dashboard using id
    async def delete_dashboard(self, user:User, dashboard_id:int):
        try:
            # delete from Dashboard
            await self.db.execute(update(Dashboard).where((Dashboard.id == dashboard_id) & (Dashboard.user_id==user.id)).values(is_deleted=True))
            logger.info(f"Soft Deleted dashboard with id: {dashboard_id}")


            await self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"DashboardService->delete_dashboard: Error deleting dashboard {dashboard_id} - {str(e)}")
            await self.db.rollback()
            return False
        


    # execute dashobard queries
    async def execute_dashboard_queries(self, dashboard_id: int, user: User):

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
                        sql_query = f'{sql_query.strip().rstrip(";")} LIMIT 50;'
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





    # fetch dashboard data
    async def fetch_dashboard_data(self, dashboard_id: int, user: User):
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
            

            # Get all queries of that dashboard
            queries_result = await self.db.execute(
            select(Query).join(dashboard_queries).where(dashboard_queries.c.dashboard_id == dashboard_id,Query.is_deleted == False))
            dashboard_queries_list = queries_result.scalars().all()

            logger.info(f"Fetched all queries for the dashboard with ID: {dashboard_id} from db")

            serialized_queries = [
                {
                    "id": query.id,
                    "query_name": query.query_name,
                    "query_text": query.query_text,
                    "output_type": query.output_type,
                    "data": query.data,
                    "updated_at": query.updated_at,
                    "created_at": query.created_at
                }
                for query in dashboard_queries_list
            ]

            return {
              
                "queries": serialized_queries,
            }

        except Exception as e:
            logger.error(f"Error while fetching dashboard data for ID {dashboard_id}: {str(e)}")
            await self.db.rollback() 
            return None









    async def fetch_database_queries(self,database_id:int,  user: User):
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
            logger.error(f"DashboardService->fetch_database_queries: Error fetching queries - {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while fetching queries."
            )


