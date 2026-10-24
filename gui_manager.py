import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from config_manager import ConfigManager
from translator import Translator


class TranslatorGUI(tk.Tk):
    def __init__(self, config_manager: ConfigManager, translator: Translator):
        super().__init__()
        self.config_manager = config_manager
        self.translator = translator
        self.result_queue = queue.Queue()

        self.title("Weblate Translator")
        self.geometry("820x580")
        self.minsize(650, 450)
        self._build_ui()
        self._refresh_projects()
        self.after(100, self._process_queue)

    def _build_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Weblate Translator", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(container, text="Upravljanje projektov in prevodov").pack(anchor="w", pady=(0, 12))

        self.tabs = ttk.Notebook(container)
        self.tabs.pack(fill="both", expand=True)
        self.translation_tab = ttk.Frame(self.tabs, padding=16)
        self.projects_tab = ttk.Frame(self.tabs, padding=12)
        self.settings_tab = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(self.translation_tab, text="Prevajanje")
        self.tabs.add(self.projects_tab, text="Projekti")
        self.tabs.add(self.settings_tab, text="Nastavitve")
        self._build_translation_tab()
        self._build_projects_tab()
        self._build_settings_tab()

    def _build_translation_tab(self):
        controls = ttk.Frame(self.translation_tab)
        controls.pack(fill="x")
        ttk.Label(controls, text="Projekt").pack(side="left")
        self.project_choice = tk.StringVar()
        self.project_combo = ttk.Combobox(controls, textvariable=self.project_choice, state="readonly", width=42)
        self.project_combo.pack(side="left", padx=8)
        self.translate_button = ttk.Button(controls, text="Zaženi prevajanje", command=self._start_translation)
        self.translate_button.pack(side="left")
        batch_controls = ttk.Frame(self.translation_tab)
        batch_controls.pack(fill="x", pady=(8, 0))
        ttk.Label(batch_controls, text="Prevodov naenkrat").pack(side="left")
        self.units_size = tk.StringVar(value="100")
        ttk.Spinbox(batch_controls, from_=1, to=100, textvariable=self.units_size, width=6).pack(side="left", padx=(8, 0))
        self.status_button = ttk.Button(controls, text="Prikaži stanje", command=self._show_status)
        self.status_button.pack(side="left", padx=(8, 0))
        self.reset_button = ttk.Button(controls, text="Ponastavi prevode", command=self._reset_needs_editing)
        self.reset_button.pack(side="left", padx=(8, 0))
        self.status_text = tk.StringVar(value="Pripravljen")
        ttk.Label(self.translation_tab, textvariable=self.status_text).pack(anchor="w", pady=(12, 6))
        self.log = tk.Text(self.translation_tab, height=18, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True)

    def _build_projects_tab(self):
        columns = ("name", "source", "target", "link")
        table_frame = ttk.Frame(self.projects_tab)
        table_frame.pack(fill="both", expand=True)
        self.project_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for column, title, width, anchor in (
            ("name", "Ime", 150, "w"), ("source", "Izvorni jezik", 80, "c"),
            ("target", "Ciljni jezik", 80, "c"), ("link", "Povezava prevoda", 500, "w"),
        ):
            self.project_table.heading(column, text=title)
            self.project_table.column(column, width=width, anchor=anchor, stretch=False)
        self.project_table.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.project_table.xview)
        self.project_table.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(side="bottom", fill="x")
        buttons = ttk.Frame(self.projects_tab)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Dodaj", command=self._add_project).pack(side="left")
        ttk.Button(buttons, text="Uredi", command=self._edit_project).pack(side="left", padx=6)
        ttk.Button(buttons, text="Odstrani", command=self._delete_project).pack(side="left")

    def _build_settings_tab(self):
        ttk.Label(self.settings_tab, text="LeeBudy API ključ").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(self.settings_tab, text="Weblate API ključ").grid(row=1, column=0, sticky="w", pady=6)
        keys = self.config_manager.api_keys
        self.leemeta_key = tk.StringVar(value=keys.get("leemeta", ""))
        self.weblate_key = tk.StringVar(value=keys.get("weblate", ""))
        ttk.Entry(self.settings_tab, textvariable=self.leemeta_key, width=55).grid(row=0, column=1, sticky="ew", padx=(12, 0), pady=6)
        ttk.Entry(self.settings_tab, textvariable=self.weblate_key, width=55).grid(row=1, column=1, sticky="ew", padx=(12, 0), pady=6)
        ttk.Button(self.settings_tab, text="Shrani ključe", command=self._save_keys).grid(row=2, column=1, sticky="e", pady=(8, 0))
        self.settings_tab.columnconfigure(1, weight=1)

    def _refresh_projects(self):
        projects = self.config_manager.projects
        for row in self.project_table.get_children():
            self.project_table.delete(row)
        for index, project in enumerate(projects):
            self.project_table.insert("", "end", iid=str(index), values=(
                project.get("name", ""), project.get("source_lang", ""),
                project.get("target_lang", ""), project.get("translations_link", ""),
            ))
        choices = [
            f"{index + 1}. {project.get('name', 'Brez imena')}"
            for index, project in enumerate(projects)
        ]
        self.project_combo["values"] = choices
        if self.project_choice.get() not in choices:
            self.project_choice.set(choices[0])

    def _project_dialog(self, title, project=None):
        project = project or {}
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        fields = (
            ("Ime projekta", "name"), ("Izvorni jezik", "source_lang"),
            ("Ciljni jezik", "target_lang"), ("Povezava prevoda", "translations_link"),
        )
        values = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky="w", padx=12, pady=7)
            values[key] = tk.StringVar(value=project.get(key, ""))
            ttk.Entry(dialog, textvariable=values[key], width=50).grid(row=row, column=1, padx=(8, 12), pady=7)

        def save():
            result = {key: variable.get().strip() for key, variable in values.items()}
            if not all(result.values()):
                messagebox.showerror("Manjkajoči podatki", "Izpolni vsa polja.", parent=dialog)
                return
            dialog.result = result
            dialog.destroy()

        actions = ttk.Frame(dialog)
        actions.grid(row=len(fields), column=0, columnspan=2, sticky="e", padx=12, pady=(4, 12))
        ttk.Button(actions, text="Prekliči", command=dialog.destroy).pack(side="right")
        ttk.Button(actions, text="Shrani", command=save).pack(side="right", padx=(0, 6))
        self.update_idletasks()
        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - dialog.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - dialog.winfo_reqheight()) // 2
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
        return getattr(dialog, "result", None)

    def _add_project(self):
        project = self._project_dialog("Dodaj projekt")
        if project is not None:
            self.config_manager.projects.append(project)
            self._save_projects()

    def _edit_project(self):
        selected = self.project_table.selection()
        if not selected:
            messagebox.showinfo("Izberi projekt", "Najprej izberi projekt.", parent=self)
            return
        index = int(selected[0])
        project = self._project_dialog("Uredi projekt", self.config_manager.projects[index])
        if project is not None:
            self.config_manager.projects[index] = project
            self._save_projects()

    def _delete_project(self):
        selected = self.project_table.selection()
        if not selected:
            messagebox.showinfo("Izberi projekt", "Najprej izberi projekt.", parent=self)
            return
        index = int(selected[0])
        name = self.config_manager.projects[index].get("name", "projekt")
        if messagebox.askyesno("Odstrani projekt", f"Res želiš odstraniti projekt '{name}'?", parent=self):
            del self.config_manager.projects[index]
            self._save_projects()

    def _save_projects(self):
        self.config_manager.set_projects(self.config_manager.projects)
        self._refresh_projects()

    def _save_keys(self):
        keys = {"leemeta": self.leemeta_key.get().strip(), "weblate": self.weblate_key.get().strip()}
        self.config_manager.set_api_keys(keys)
        self.translator.api_keys = keys
        messagebox.showinfo("Nastavitve", "API ključi so shranjeni.", parent=self)

    def _start_translation(self):
        projects = self.config_manager.projects
        if not projects:
            messagebox.showinfo("Ni projektov", "Najprej dodaj projekt.", parent=self)
            return
        if not all(self.translator.api_keys.get(key) for key in ("leemeta", "weblate")):
            messagebox.showerror("Manjkajoči API ključi", "V zavihku Nastavitve vnesi in shrani oba API ključa.", parent=self)
            return
        project_index = self.project_combo.current()
        selected_project = projects[project_index]
        try:
            translate_units_size = int(self.units_size.get())
        except ValueError:
            translate_units_size = 0
        if not 1 <= translate_units_size <= 100:
            messagebox.showerror("Neveljavno število", "Vnesi število prevodov od 1 do 100.", parent=self)
            return
        self.translate_button.configure(state="disabled")
        self.status_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self.status_text.set("Prevajanje poteka ...")
        self._append_log(f"Začenjam prevajanje za '{selected_project['name']}'.")
        threading.Thread(target=self._translate_worker, args=(selected_project, translate_units_size), daemon=True).start()

    def _show_status(self):
        projects = self.config_manager.projects
        if not projects:
            messagebox.showinfo("Ni projektov", "Najprej dodaj projekt.", parent=self)
            return
        if not self.translator.api_keys.get("weblate"):
            messagebox.showerror("Manjkajoči API ključ", "V zavihku Nastavitve vnesi in shrani Weblate API ključ.", parent=self)
            return

        project_index = self.project_combo.current()
        project = projects[project_index]
        self.translate_button.configure(state="disabled")
        self.status_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self.status_text.set("Pridobivam stanje projekta ...")
        threading.Thread(target=self._status_worker, args=(project,), daemon=True).start()

    def _reset_needs_editing(self):
        projects = self.config_manager.projects
        if not projects:
            messagebox.showinfo("Ni projektov", "Najprej dodaj projekt.", parent=self)
            return
        if not self.translator.api_keys.get("weblate"):
            messagebox.showerror("Manjkajoči API ključ", "V zavihku Nastavitve vnesi in shrani Weblate API ključ.", parent=self)
            return
        project_index = self.project_combo.current()
        selected_project = projects[project_index]
        try:
            reset_units_size = int(self.units_size.get())
        except ValueError:
            reset_units_size = 0
        if not 1 <= reset_units_size <= 100:
            messagebox.showerror("Neveljavno število", "Vnesi število prevodov od 1 do 100.", parent=self)
            return

        scope = f"projektu '{selected_project.get('name', 'Projekt')}'"
        if not messagebox.askyesno(
            "Ponastavi prevode",
            f"V {scope} spremenim vse prevode, označene za prevod, v neprevedene?",
            parent=self,
        ):
            return

        self.translate_button.configure(state="disabled")
        self.status_button.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        self.status_text.set("Ponastavljam prevode ...")
        threading.Thread(target=self._reset_worker, args=(selected_project, reset_units_size), daemon=True).start()

    def _status_worker(self, project: dict):
        try:
            status = self.translator.get_project_status(project["translations_link"])
            self.result_queue.put(("status_success", (project.get("name", "Projekt"), status)))
        except Exception as error:
            self.result_queue.put(("status_error", str(error)))

    def _translate_worker(self, project: dict, translate_units_size: int=100):
        try:
            self.translator.translate_project(project, translate_units_size)
            self.result_queue.put(("success", "Prevajanje je zaključeno."))
        except Exception as error:
            self.result_queue.put(("error", str(error)))

    def _reset_worker(self, project: dict, reset_units_size: int):
        try:
            reset_count = self.translator.reset_needs_editing(project["translations_link"], reset_units_size)
            self.result_queue.put(("reset_success", reset_count))
        except Exception as error:
            self.result_queue.put(("reset_error", str(error)))

    def _process_queue(self):
        try:
            while True:
                kind, message = self.result_queue.get_nowait()
                self.status_text.set("Pripravljeno" if kind in ("success", "status_success", "reset_success") else "Napaka")
                if kind == "success":
                    self._append_log(message)
                elif kind == "reset_success":
                    self._append_log(f"Ponastavljenih prevodov: {message}")
                elif kind == "status_success":
                    project_name, status = message
                    self._append_log(f"Stanje projekta '{project_name}'")
                    self._append_log(f"Vsi nizi: {status['total']}")
                    self._append_log(f"Prevedeni nizi: {status['translated']}")
                    self._append_log(f"Neprevedeni nizi: {status['untranslated']}")
                    self._append_log(f"Nizi označeni za prevod: {status['needs_editing']}")
                    self._append_log("")  # prazna vrstica za ločilo
                else:
                    self._append_log(message)
                self.translate_button.configure(state="normal")
                self.status_button.configure(state="normal")
                self.reset_button.configure(state="normal")
                if kind in ("error", "status_error", "reset_error"):
                    title = {
                        "error": "Napaka pri prevajanju",
                        "status_error": "Napaka pri pridobivanju stanja",
                        "reset_error": "Napaka pri ponastavljanju prevodov",
                    }[kind]
                    messagebox.showerror(title, message, parent=self)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def _append_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
