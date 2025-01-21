import os

import dotenv

dotenv.load_dotenv()


class Settings:
    api_key = os.environ.get("API_KEY")
    model = os.environ.get("MODEL")


settings = Settings()
