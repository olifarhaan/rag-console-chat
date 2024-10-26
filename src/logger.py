import logging
import os
import yaml
from logging.handlers import RotatingFileHandler

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self._load_config()
        self._setup_logger()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logging_config.yml")
        with open(config_path, 'r') as config_file:
            self.config = yaml.safe_load(config_file)

    def _setup_logger(self):
        log_level = self.config.get('log_level', 'INFO')
        log_file = self.config.get('log_file', 'rag_pipeline.log')

        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s"
        )

        file_handler = RotatingFileHandler(
            os.path.join(log_dir, log_file),
            maxBytes=self.config.get('max_file_size', 10000000),
            backupCount=self.config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)

        self.logger = logging.getLogger("rag_pipeline")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

def get_logger():
    return Logger().get_logger()
