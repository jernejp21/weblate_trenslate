import os
import platform
import json

class ConfigManager:
    def __init__(self):
        self.config_file = ""
        self.config_file_path = ""
        self.get_config_file()
        self.api_keys = self.load_api_keys()
        self.projects = self.load_projects()

    def get_config_file(self):
        if platform.system() == "Windows":
            config_file_path = os.path.join(os.getenv("LOCALAPPDATA"), "weblate", "config.json")
        elif platform.system() == "Linux":
            if os.getenv("XDG_DATA_HOME") is None:
                os.environ["XDG_DATA_HOME"] = os.path.join(os.path.expanduser("~"), ".local", "share")
            config_file_path = os.path.join(os.getenv("XDG_DATA_HOME"), "weblate", "config.json")
        else:
            raise NotImplementedError(f"Unsupported platform: {platform.system()}")

        config_file = {}
        if not os.path.exists(config_file_path):
            os.makedirs(os.path.dirname(config_file_path), exist_ok=True)

            with open(config_file_path, "w", encoding="utf-8") as file:
                json.dump(config_file, file, indent=4)
        else:
            with open(config_file_path, "r", encoding="utf-8") as file:
                config_file = json.load(file)

        self.config_file = config_file
        self.config_file_path = config_file_path

    def load_api_keys(self) -> dict:
        with open(self.config_file_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        if "api_keys" not in config:
            self.config_file["api_keys"] = {}

        return config["api_keys"]

    def set_api_keys(self, api_keys: dict):
        self.config_file["api_keys"] = api_keys

        with open(self.config_file_path, "w", encoding="utf-8") as file:
            json.dump(self.config_file, file, indent=4)

    def load_projects(self) -> dict:
        with open(self.config_file_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        if "projects" not in config:
            self.config_file["projects"] = {}

        return config["projects"]

    def set_projects(self, projects: list[dict]):
        self.config_file["projects"] = projects
        with open(self.config_file_path, "w", encoding="utf-8") as file:
            json.dump(self.config_file, file, indent=4)