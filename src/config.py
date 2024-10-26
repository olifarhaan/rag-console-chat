from enum import Enum
import yaml


class ConfigKeys(Enum):
    COLLECTION_NAME = "collection_name"
    PERSIST_DIRECTORY = "persist_directory"
    DOCS_DIRECTORY = "docs_directory"
    LOG_LEVEL = "log_level"


class Config:
    def __init__(self, config_path: str):
        with open(config_path, "r") as config_file:
            self._config = yaml.safe_load(config_file)

    def get(self, key: ConfigKeys, default=None):
        return self._config.get(key.value, default)
