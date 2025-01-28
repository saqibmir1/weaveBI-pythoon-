from fastapi import HTTPException, status
from datetime import datetime
from config.prompt_config import settings as prompt_settings
from schemas.databases import DbCredentials, UpdatedCredentials
from decimal import Decimal


def get_connection_string(db_credentials: DbCredentials | UpdatedCredentials):
    connection_strings = {
        "mysql": f"mysql+pymysql://{db_credentials.db_username}:{db_credentials.db_password}@{db_credentials.db_host}:{db_credentials.db_port}/{db_credentials.db_name}",
        
        "postgres": f"postgresql+psycopg2://{db_credentials.db_username}:{db_credentials.db_password}@{db_credentials.db_host}:{db_credentials.db_port}/{db_credentials.db_name}",
        
        "sqlite": f"sqlite:///{db_credentials.db_name}",
        
        "sqlserver": f"mssql+pyodbc://{db_credentials.db_username}:{db_credentials.db_password}@{db_credentials.db_host}:{db_credentials.db_port}/{db_credentials.db_name}?driver=ODBC+Driver+17+for+SQL+Server",
        
        "mariadb": f"mysql+pymysql://{db_credentials.db_username}:{db_credentials.db_password}@{db_credentials.db_host}:{db_credentials.db_port}/{db_credentials.db_name}",
        
    }

    if db_credentials.db_provider in connection_strings:
        return connection_strings[db_credentials.db_provider]
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "Database not supported",
                "error": {"message": "Database not supported"},
            },
        )





def result_to_json_updated(result):
    # Get column names
    columns = result.keys()

    # Get all rows
    rows = result.all()

    # Convert rows to dictionaries
    json_result = []
    for row in rows:
        row_dict = {}
        for column, value in zip(columns, row):
            # Handle datetime objects
            if isinstance(value, datetime):
                row_dict[column] = value.isoformat()
            # Handle Decimal objects
            elif isinstance(value, Decimal):
                row_dict[column] = float(value)  # Or str(value) if preferred
            else:
                row_dict[column] = value
        json_result.append(row_dict)
    return json_result


