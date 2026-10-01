from config_manager import ConfigManager
from cli_manager import CLIManager
from translator import Translator

if __name__ == "__main__":
    config_manager = ConfigManager()
    traslator = Translator(config_manager.api_keys)
    interface = CLIManager(config_manager, traslator)

print("Konec")
