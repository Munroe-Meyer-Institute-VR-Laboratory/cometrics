import os
import webbrowser
from tkinter import *
from analysis_ui import AccuracyPopup
from config_utils import ConfigUtils
from ksf_utils import export_columnwise_csv, populate_spreadsheet
from tkinter_utils import ConfigPopup, ExternalButtonPopup


class MenuBar(Frame):
    def __init__(self, parent, caller, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.caller = caller
        self.parent = parent
        menu = Menu(self.parent)
        self.parent.config(menu=menu)

        file_menu = Menu(menu)
        file_menu.add_command(label="Start New Session", command=self.start_new_session)
        file_menu.add_command(label="Open New Project", command=self.open_new_project)
        file_menu.add_command(label="Connect External Input", command=self.connect_external_input)
        file_menu.add_command(label="Edit Config File", command=self.config_popup)
        menu.add_cascade(label="File", menu=file_menu)

        export_menu = Menu(menu)
        export_menu.add_command(label="Export CSV", command=self.export_csv)
        menu.add_cascade(label="Export", menu=export_menu)

        edit_menu = Menu(menu)
        edit_menu.add_command(label="Analyze Sessions", command=self.load_sessions)
        edit_menu.add_command(label="Calculate Session Accuracy", command=self.get_session_acc)
        menu.add_cascade(label="Analyze", menu=edit_menu)

        help_menu = Menu(menu)
        help_menu.add_command(label="Open Documentation", command=self.open_user_guide)
        help_menu.add_command(label="Open Logs", command=self.open_logs)
        help_menu.add_command(label="Open Current Directory", command=self.open_current_dir)
        menu.add_cascade(label="Help", menu=help_menu)

    def config_popup(self):
        ConfigPopup(self.parent, self.caller.config)

    def connect_external_input(self):
        self.caller.button_input_handler = ExternalButtonPopup(self.parent, self.caller)

    def open_new_project(self):
        self.caller.restart_program()

    def open_current_dir(self):
        os.startfile(self.caller.session_dir)

    def open_logs(self):
        os.startfile(self.caller.config.get_logs_dir())

    @staticmethod
    def open_docs():
        docs_url = 'https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics'
        webbrowser.open_new_tab(docs_url)

    @staticmethod
    def open_user_guide():
        config = ConfigUtils()
        cwd = config.get_cwd()
        user_guide_path = os.path.join(cwd, 'reference/Cometrics User Guide.pdf')
        os.startfile(user_guide_path)

    def start_new_session(self):
        self.caller.create_new_session()

    def export_csv(self):
        export_columnwise_csv(self.caller.prim_dir, self.caller.reli_dir, self.caller.export_dir)

    def get_session_acc(self):
        AccuracyPopup(self.caller.root, self.caller.keystroke_file, self.caller)

    def load_sessions(self):
        populate_spreadsheet(self.caller.patient_name, self.caller.tracker_file, self.caller.prim_dir, self.caller.graph_dir)
