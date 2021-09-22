from tkinter import *
from analysis_ui import populate_spreadsheet
from ka_ui import main


class MenuBar(Frame):
    def __init__(self, parent, caller, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.caller = caller
        self.parent = parent
        menu = Menu(self.parent)
        self.parent.config(menu=menu)

        file_menu = Menu(menu)
        file_menu.add_command(label="Start New Session", command=self.restart_program)
        menu.add_cascade(label="File", menu=file_menu)

        export_menu = Menu(menu)
        export_menu.add_command(label="Export CSV", command=self.export_csv)
        menu.add_cascade(label="Export", menu=export_menu)

        edit_menu = Menu(menu)
        edit_menu.add_command(label="Analyze Sessions", command=self.load_sessions)
        edit_menu.add_command(label="Calculate Session Accuracy", command=self.get_session_acc)
        menu.add_cascade(label="Analyze", menu=edit_menu)

    def restart_program(self):
        """Restarts the current program.
        Note: this function does not return. Any cleanup action (like
        saving data) must be done before calling this function."""
        self.caller.stf.stop_timer()
        self.caller.root.destroy()
        main()

    def export_csv(self):
        pass

    def get_session_acc(self):
        pass

    def load_sessions(self):
        populate_spreadsheet(self.caller.patient_file, self.caller.keystroke_file, self.caller.session_dir)
