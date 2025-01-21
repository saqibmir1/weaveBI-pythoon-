import os

import dotenv

dotenv.load_dotenv()


class Settings:
    username = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")
    hostname = os.environ.get("MAIL_HOSTNAME")
    port = os.environ.get("MAIL_PORT")
    start_tls = os.environ.get("MAIL_START_TLS")

settings = Settings()
