import subprocess
import json
from os import path

from .path import qtile_path


class ConfigManager:
    DEFAULT_CONFIG_PATH = path.join(qtile_path, "default-config.json")

    def __init__(self):
        config_path = ""

        try:
            config_path = self.__check_config()
        except:
            config_path = DEFAULT_CONFIG_PATH

        with open(config_path) as f:
            self.config = json.load(f)

    def __check_config(self):
        config_path = path.join(qtile_path, "config.json")

        if not path.isfile(config_path):
            raise Exception(f"Config file does not exist")

        return config_path

    def read_config(self, key: string):
        if key not in self.config:
            raise Exception(f"{key} does not exist in config file")

        return self.config[key]


config = ConfigManager()
