import os
import webbrowser
from tkinter import *
from analysis_ui import AccuracyPopup
from ksf_utils import export_columnwise_csv, populate_spreadsheet


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
        menu.add_cascade(label="File", menu=file_menu)

        export_menu = Menu(menu)
        export_menu.add_command(label="Export CSV", command=self.export_csv)
        menu.add_cascade(label="Export", menu=export_menu)

        edit_menu = Menu(menu)
        edit_menu.add_command(label="Analyze Sessions", command=self.load_sessions)
        edit_menu.add_command(label="Calculate Session Accuracy", command=self.get_session_acc)
        menu.add_cascade(label="Analyze", menu=edit_menu)

        help_menu = Menu(menu)
        help_menu.add_command(label="Open Documentation", command=self.open_docs)
        help_menu.add_command(label="Open Logs", command=self.open_logs)
        help_menu.add_command(label="Open Current Directory", command=self.open_current_dir)
        menu.add_cascade(label="Help", menu=help_menu)

    def open_new_project(self):
        self.caller.restart_program()

    def open_current_dir(self):
        os.startfile(self.caller.session_dir)

    def open_logs(self):
        os.startfile(self.caller.config.get_logs_dir())

    def open_docs(self):
        docs_url = 'https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics'
        webbrowser.open_new_tab(docs_url)

    def start_new_session(self):
        self.caller.create_new_session()

    def export_csv(self):
        export_columnwise_csv(self.caller.prim_dir, self.caller.reli_dir, self.caller.export_dir)

    def get_session_acc(self):
        AccuracyPopup(self.caller.root, self.caller.keystroke_file, self.caller)

    def load_sessions(self):
        populate_spreadsheet(self.caller.patient_name, self.caller.tracker_file, self.caller.prim_dir, self.caller.graph_dir)
