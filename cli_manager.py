import enum
import os
import platform

from config_manager import ConfigManager
from translator import Translator


class MainMenuActions(enum.Enum):
    """Main menu actions for the CLI."""
    TRANSLATE_SEGMENTS = 1
    VIEW_CONFIGURATION = 2
    EDIT_CONFIGURATION = 3
    EXIT = 4

class EditConfigMenuActions(enum.Enum):
    """Edit configuration menu actions for the CLI."""
    SET_API_KEYS = 1
    SET_PROJECTS = 2
    BACK = 3

class CLIManager:
    """Command-line interface manager for the Weblate Translator."""
    def __init__(self, config_manager: ConfigManager, translator: Translator):
        self.config_manager = config_manager
        self.translator = translator
        self.main_menu()

    def main_menu(self):
        """Display the main menu and handle user input."""
        while True:
            print("Welcome to the Weblate Translator CLI!")
            print("1. Translate segments")
            print("2. View configuration")
            print("3. Edit configuration")
            print("4. Exit")
            choice = int(input("Enter your choice: "))
            self.clear_screen()

            if choice == MainMenuActions.TRANSLATE_SEGMENTS.value:
                self.translate_menu()
            elif choice == MainMenuActions.VIEW_CONFIGURATION.value:
                self.view_configuration()
            elif choice == MainMenuActions.EDIT_CONFIGURATION.value:
                self.edit_configuration()
            elif choice == MainMenuActions.EXIT.value:
                print("Exiting the program.")
                break

    def clear_screen(self):
        """Clear the terminal screen."""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')

    def view_configuration(self):
        """View configuration menu."""
        config = self.config_manager.config_file
        print("Config file contents:")
        for key, value in config.items():
            print(f"{key}: {value}")
        print("")

    def edit_configuration(self):
        """Edit configuration menu."""
        while True:
            print("Edit Configuration Menu:")
            print("1. Set API keys")
            print("2. Set projects")
            print("3. Back to main menu")
            choice = int(input("Enter your choice: "))
            self.clear_screen()

            if choice == EditConfigMenuActions.SET_API_KEYS.value:
                self.set_api_keys()
            elif choice == EditConfigMenuActions.SET_PROJECTS.value:
                self.set_projects()
            elif choice == EditConfigMenuActions.BACK.value:
                break

    def set_api_keys(self):
        api_keys = {
                    "leemeta": input("Enter your leemeta API key: "),
                    "weblate": input("Enter your Weblate API key: ")
                    }
        self.config_manager.set_api_keys(api_keys)
        print("API keys updated successfully.")

    def set_projects(self):
        projects = []
        while True:
            project_name = input("Enter project name (or 'done' to finish): ")
            if project_name.lower() == 'done':
                break
            source_lang = input(f"Enter source language for {project_name}: ")
            target_lang = input(f"Enter target language for {project_name}: ")
            translations_link = input(f"Enter translations link for {project_name}: ")
            project = {"name": project_name, "source_lang": source_lang, "target_lang": target_lang,
                       "translations_link": translations_link}
            projects.append(project)
        self.config_manager.set_projects(projects)
        print("Projects updated successfully.")

    def translate_menu(self):
        print("Translation Menu:")
        print("Available projects:")
        for index, project in enumerate(self.config_manager.projects):
            print(f"{index}. {project["name"]}")

        project_nr = int(input("Choose a project to translate (or -1 to select all):"))

        if project_nr == -1:
            self.translator.translate_projects(self.config_manager.projects)
        else:
            self.translator.translate_projects([self.config_manager.projects[project_nr]])
        return
    
if __name__ == "__main__":
    cfg_manager = ConfigManager()
    traslator = Translator(cfg_manager.api_keys)
    interface = CLIManager(cfg_manager, traslator)

print("Konec")
