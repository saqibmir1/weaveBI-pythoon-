from fastapi import HTTPException, status
from sqlalchemy import create_engine, select, text, update, func, insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI

from nemoguardrails import RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails
import nest_asyncio
from config import llm_config
from sqlalchemy.ext.asyncio import AsyncSession

import os, json

from utils.logger import logger
from utils.user_queries import  result_to_json, load_prompts, limit_query, generate_sql_query
from config.llm_config import settings as llm_settings
from models.databases import Database
from models.queries import Query
from models.users import User
from models.dashboards import Dashboard, dashboard_queries
from schemas.queries import  SaveQueryRequest, UpdateQueryRequest, UserQueryRequest

os.environ["OPENAI_API_KEY"] = llm_settings.api_key
model = llm_config.settings.model
nest_asyncio.apply()
config = RailsConfig.from_path("guardrails")
guard_rail = RunnableRails(config=config)
llm = ChatOpenAI(model=model, temperature=0)


class QueryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_queries(self, post_queries: SaveQueryRequest, user: User):
        try:
            new_query = Query(
                user_id= user.id,
                db_id= post_queries.db_id,
                query_name= post_queries.query_name,
                query_text= post_queries.query_text,
                output_type= post_queries.output_type,
            )
            self.db.add(new_query)
            await self.db.commit()
            await self.db.refresh(new_query)
            logger.info('Query saved in db')
            return True
        
        except Exception as e:
            logger.error(f"Failed to save query for user_id={user.id}, db_id={post_queries.db_id}, query_name={post_queries.query_name}. Reason: {e}.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Couldn't save queries.",
                    "error": f"{e}",
                },
            ) 
        
    async def execute_query(self, query_id, user: User):

        # get query, schema, connection string, and database provider
        query_result = await self.db.execute(
            select(Query, Database.schema, Database.db_connection_string, Database.db_provider)
            .join(Database, Query.db_id == Database.id)
            .where(Query.id == query_id, Query.is_deleted == False)
        )
        result = query_result.one_or_none()
        if not result:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with id {query_id} not found"
            )
        query, schema, connection_string, database_provider = result

        try:
            output_type = query.output_type
            query_text = query.query_text

            # step 1: get sql query based on type
            sql_query, final_data = await generate_sql_query(llm, guard_rail, query_text, output_type, schema, database_provider)

            if final_data is None:
                # step 2: execute sql query
                engine = create_engine(connection_string)
                Session = sessionmaker(bind=engine)
                session = Session()
                limit_query(sql_query)
                result = session.execute(text(sql_query))
                query_result = result_to_json(result)

                # Step 3: Process result based on type
                prompts = load_prompts()
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

            # put final data and generated sql query in queries table
            serialized_data = json.dumps(final_data)
            await self.db.execute(
                update(Query)
                .where(Query.id == query_id)
                .values(data=serialized_data, generated_sql_query=sql_query)
            )
            await self.db.commit()

            logger.info(f'Output stored in db')

            # return api response
            return {
                "success": True,
                "message": "Query executed successfully",
                "data": {
                    "generated_sql_query": sql_query,
                    "query_result": final_data,
                }
            }
        
        except Exception as e:
            logger.error(f"{user.id=} Error occured while executing query. Reason: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occured while executing query"
            )

    async def get_insights(self, query_id: int, use_web: bool, custom_instructions:str | None, user:User) -> str:
        try:
            result = await self.db.execute(select(Query).where( (Query.id==query_id) & (Query.is_deleted==False) & (Query.user_id==user.id))) 
            query_data = result.scalar_one_or_none()
            logger.info(f'Selected {query_data.query_text} for insights')
            if not query_data:
                logger.info(f'Query with id {query_id} not found')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Query with id {query_id} not found')
            
            # Load prompts
            prompts = load_prompts()
            prompt = (
                prompts["system_prompts"]["Insights"]+
                f'User Query: {query_data.query_text}\n'+
                f'Generated SQL Query: {query_data.generated_sql_query}\n'+
                f'Query Output from database: {query_data.data}')
            logger.info("Using prompt Insights")

            if custom_instructions:
                prompt+=f'\nCustom User Instructions: {custom_instructions}'
                logger.info("Adding custom instructions to the prompt")

            if use_web:
                prompt += f'\nUse your knowledge and reliable internet sources to analyze and compare this data. Provide additional insights, trends, or actionable suggestions based on the query results and any relevant external information you can find online. Ensure that your insights are well-supported and cite credible sources where applicable.'
                logger.info("Setting use_web to True")
            logger.info(f'Generating insights for query id: {query_id}...')

            # generate insights using llm
            response = await llm.agenerate([prompt])
            
            if response:
                insights = response.generations[0][0].text.strip()
                logger.info("Inights Generated successfully")

                return insights
            
        except Exception as e:
            logger.error(f'Error generating insights: {e}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'An error occured while generating insights: {str(e)}'
            )

    async def link_query_to_dashboard(
        self,
        query_id: int,
        dashboard_id: int,
        user: User,
    ):
        try:
            # Verify both query and dashboard exist and belong to the user
            query_stmt = select(Query).where(
                Query.id == query_id,
                Query.is_deleted == False,
                Query.user_id == user.id
            )
            dashboard_stmt = select(Dashboard).where(
                Dashboard.id == dashboard_id,
                Dashboard.is_deleted == False,
                Dashboard.user_id == user.id
            )
            query_result = await self.db.execute(query_stmt)
            dashboard_result = await self.db.execute(dashboard_stmt)
            
            query = query_result.scalar_one_or_none()
            dashboard = dashboard_result.scalar_one_or_none()

            # Validate query exists
            if not query:
                logger.debug(f"Query {query_id} not found or is deleted or doesn't belong to user.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Query with id {query_id} not found"
                )

            # Validate dashboard exists
            if not dashboard:
                logger.debug(f"Dashboard {dashboard_id} not found or is deleted or doesn't belong to user.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dashboard with id {dashboard_id} not found"
                )

            # Check if the relationship already exists
            existing_stmt = select(dashboard_queries).where(
                dashboard_queries.c.dashboard_id == dashboard_id,
                dashboard_queries.c.query_id == query_id
            )
            existing = await self.db.execute(existing_stmt)
            
            if existing.first():
                return {
                    "success": True,
                    "message": f"Query {query_id} is already linked to dashboard {dashboard_id}"
                }

            # Insert the relationship directly into the junction table
            stmt = insert(dashboard_queries).values(
                dashboard_id=dashboard_id,
                query_id=query_id
            )
            await self.db.execute(stmt)
            await self.db.commit()

            logger.info(f"Successfully linked query {query_id} to dashboard {dashboard_id}")
            return {
                "success": True,
                "message": f"Query {query_id} linked to dashboard {dashboard_id} successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in link_query_to_dashboard: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error while linking query to dashboard: {str(e)}"
            )

    async def fetch_database_queries(self, dashboard_id: int, user: User, page: int, limit: int, search_term: str = None):
        try:
            offset = (page - 1) * limit
            query = select(
                Query,
                func.count().over().label('total_count')
            ).where(
                (Query.user_id == user.id) & 
                (Query.is_deleted == False) &
                (Query.db_id == dashboard_id)
            )
            
            if search_term:
                search_term = f"%{search_term}%"
                query = query.where(
                    Query.query_name.ilike(search_term) |
                    Query.query_text.ilike(search_term) |
                    Query.output_type.ilike(search_term)
                )
            
            query = query.limit(limit).offset(offset)
            result = await self.db.execute(query)
            rows = result.all()
            
            if not rows:
                return [], 0
                
            # Get total count from first row
            total_count = rows[0].total_count
            logger.info(f"Fetched all queries for user {user.id}")

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

    async def get_queries_count(self, database_id: int, user: User):
        try:
            query = select(func.count()).select_from(Query).where(
                Query.db_id == database_id,
                Query.is_deleted == False,
                Query.user_id == user.id
            )

            result = await self.db.execute(query)
            count = result.scalar()
            return count
        except Exception as e:
            logger.error(f'Error fetching count - {str(e)}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while fetching queries count."
            )
        
    async def delete_query(self, id:int, user:User):
        try:
            # soft delete query
            await self.db.execute(
                update(Query).where((Query.id == id) & (Query.user_id == user.id)).values(is_deleted=True)
            )
            logger.info(f" query {id} soft deleted")

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(
                f"Error deleting query {id} - {str(e)}"
            )
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while deleting query."
            )
        
    async def update_query(self, post_queries: UpdateQueryRequest, user: User):
        try:
            query = await self.db.execute(select(Query).where((Query.id == post_queries.query_id) & (Query.user_id == user.id) & (Query.is_deleted == False)))
            query = query.scalar_one_or_none()
            if not query:
                logger.error(f"Query with id {post_queries.id} not found or deleted")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Query with id {post_queries.id} not found"
                )
            query.query_name = post_queries.query_name
            query.query_text = post_queries.query_text
            query.output_type = post_queries.output_type

            await self.db.commit()
            await self.db.refresh(query)
            logger.info(f"Query {post_queries.query_id} updated successfully")
            
        
        except Exception as e:
            logger.error(f"Error updating query {post_queries.id} - {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while updating query."
            )
        
    async def run_query(self, post_queries: UserQueryRequest, user: User):
        try:
            query_text = post_queries.query_text
            output_type = post_queries.output_type
            database_id = post_queries.db_id

            logger.info(f"Running query for user {user.id} on database {database_id}")

            # get schema, connection string, and database provider
            query_result = await self.db.execute(
                select(Database.schema, Database.db_connection_string, Database.db_provider)
                .where((Database.id == database_id) & (Database.user_id == user.id))
            )
            result = query_result.one_or_none()
            if not result:
                logger.error(f"Database with id {database_id} not found for user {user.id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Database not found"
                )
            schema, connection_string, database_provider = result

            # step 1: get sql query based on type
            sql_query, final_data = await generate_sql_query(llm, guard_rail, query_text, output_type, schema, database_provider)

            if final_data is None:
                # step 2: execute sql query
                engine = create_engine(connection_string)
                Session = sessionmaker(bind=engine)
                session = Session()
                limit_query(sql_query)
                result = session.execute(text(sql_query))
                query_result = result_to_json(result)

                # Step 3: Process result based on type
                prompts = load_prompts()
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

            logger.info(f"Query executed successfully for user {user.id}")

            # return api response
            return {
                "success": True,
                "message": "Query executed successfully",
                "data": {
                    "generated_sql_query": sql_query,
                    "query_result": final_data,
                }
            }
        except Exception as e:
            logger.error(f"{user.id=} Error occurred while executing query. Reason: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error occurred while executing query"
            )