import os
import dotenv

dotenv.load_dotenv()


class Settings:

    secret_key: str = os.environ.get("SECRET")
    algorithm: str = os.environ.get("ALGO")


settings = Settings()
