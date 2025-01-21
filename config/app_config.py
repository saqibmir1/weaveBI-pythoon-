import os
import dotenv

dotenv.load_dotenv()


class Settings:
    APP_NAME: str = os.environ.get('APP_NAME')
    APP_VERSION: str = os.environ.get('APP_VERSION')
    APP_DESCRIPTION: str = os.environ.get('APP_DESCRIPTION')

    APP_PORT: int = int(os.environ.get("APP_PORT"))
    APP_HOST: str = os.environ.get("APP_HOST")


settings = Settings()
