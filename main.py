import argparse

from config_manager import ConfigManager
from translator import Translator
from gui_manager import TranslatorGUI

def main():
    parser = argparse.ArgumentParser(description="Weblate Translator")
    parser.add_argument("--cli", action="store_true", help="Zaženi CLI namesto grafičnega vmesnika")
    args = parser.parse_args()

    config_manager = ConfigManager()
    translator = Translator(config_manager.api_keys)
    if args.cli:
        from cli_manager import CLIManager
        CLIManager(config_manager, translator)
        return

    app = TranslatorGUI(config_manager, translator)
    app.mainloop()

if __name__ == "__main__":
    main()
