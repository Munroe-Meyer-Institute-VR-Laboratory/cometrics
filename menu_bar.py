import sys
from tkinter import *
from analysis_ui import populate_spreadsheet, export_columnwise_csv, AccuracyPopup
import os
import pathlib


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
        help_menu.add_command(label="Open documentation", command=self.open_docs)
        menu.add_cascade(label="Help", menu=help_menu)

    def open_new_project(self):
        self.caller.restart_program()

    def open_docs(self):
        pass

    def start_new_session(self):
        """Restarts the current program.
        Note: this function does not return. Any cleanup action (like
        saving data) must be done before calling this function."""
        self.caller.create_new_session()

    def export_csv(self):
        export_columnwise_csv(self.caller, self.caller.session_dir)

    def get_session_acc(self):
        AccuracyPopup(self.caller.root, self.caller.keystroke_file)

    def load_sessions(self):
        populate_spreadsheet(self.caller, self.caller.patient_file, self.caller.keystroke_file, self.caller.session_dir)
