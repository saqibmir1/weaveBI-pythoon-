import os
import dotenv

dotenv.load_dotenv()


class Settings:

    prompt_path: str = os.environ.get("PROMPT_PATH")


settings = Settings()
