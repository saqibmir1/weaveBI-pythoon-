import logging
from logging.config import dictConfig
from config.log_config import LogConfig

dictConfig(LogConfig().model_dump())
logger = logging.getLogger("app")
