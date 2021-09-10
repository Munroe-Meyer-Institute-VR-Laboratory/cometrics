from tkinter import *
from analysis_ui import populate_spreadsheet


class MenuBar(Frame):
    def __init__(self, parent, caller, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.caller = caller
        self.parent = parent
        menu = Menu(self.parent)
        self.parent.config(menu=menu)

        file_menu = Menu(menu)
        menu.add_cascade(label="File", menu=file_menu)

        export_menu = Menu(menu)
        export_menu.add_command(label="Export CSV", command=self.export_data_as_csv)
        menu.add_cascade(label="Export", menu=export_menu)

        edit_menu = Menu(menu)
        edit_menu.add_command(label="View Sessions", command=self.load_sessions)
        menu.add_cascade(label="Analyze", menu=edit_menu)

    def export_data_as_csv(self):
        pass

    def load_sessions(self):
        populate_spreadsheet(self.caller.patient_file, self.caller.keystroke_file, self.caller.session_dur)
