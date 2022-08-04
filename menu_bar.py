import os
import pathlib
import webbrowser
from tkinter import *
from analysis_ui import AccuracyPopup
from config_utils import ConfigUtils
from ksf_utils import export_columnwise_csv, populate_spreadsheet
from tkinter_utils import ConfigPopup, ExternalButtonPopup, GitHubIssue
from e4_utils import export_e4_metrics
from pat import token
from ui_params import cometrics_ver_root


class MenuBar(Frame):
    def __init__(self, parent, caller, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.caller = caller
        self.parent = parent
        menu = Menu(self.parent, tearoff=0)
        self.parent.config(menu=menu)

        file_menu = Menu(menu, tearoff=0)
        file_menu.add_command(label="Start New Session", command=self.start_new_session)
        file_menu.add_command(label="Open New Project", command=self.open_new_project)
        file_menu.add_command(label="Connect External Input", command=self.connect_external_input)
        file_menu.add_command(label="Edit Config File", command=self.config_popup)
        menu.add_cascade(label="File", menu=file_menu)

        export_menu = Menu(menu, tearoff=0)
        export_menu.add_command(label="Export CSV", command=self.export_csv)
        menu.add_cascade(label="Export", menu=export_menu)

        edit_menu = Menu(menu, tearoff=0)
        edit_menu.add_command(label="Analyze Sessions", command=self.load_sessions)
        edit_menu.add_command(label="Calculate Session Accuracy", command=self.get_session_acc)
        edit_menu.add_command(label="Calculate E4 Metrics", command=self.get_e4_metrics)
        menu.add_cascade(label="Analyze", menu=edit_menu)

        help_menu = Menu(menu, tearoff=0)
        help_menu.add_command(label="Open Documentation", command=self.open_user_guide)
        help_menu.add_command(label="Open Logs", command=self.open_logs)
        help_menu.add_command(label="Open Current Directory", command=self.open_current_dir)
        help_menu.add_command(label="Download E4 Streaming Server", command=self.download_e4_ss)
        help_menu.add_command(label="Open Source Code", command=self.open_source_code)
        help_menu.add_command(label="View Privacy Policy", command=self.view_privacy_policy)
        help_menu.add_command(label="Submit Feedback", command=self.submit_feedback)
        menu.add_cascade(label="Help", menu=help_menu)

    @staticmethod
    def view_privacy_policy():
        config = ConfigUtils()
        cwd = config.get_cwd()
        webbrowser.open_new_tab(os.path.join(cwd, 'reference/PRIVACY_POLICY.html'))

    def submit_feedback(self):
        log_pattern = r'*.txt'
        latest_log_file = max(pathlib.Path(os.path.join(cometrics_ver_root, 'logs')).glob(log_pattern),
                              key=lambda f: f.stat().st_ctime)
        GitHubIssue(self.caller.root, token, latest_log_file)

    @staticmethod
    def open_source_code():
        source_code_link = 'https://github.com/Munroe-Meyer-Institute-VR-Laboratory/cometrics'
        webbrowser.open_new_tab(source_code_link)

    @staticmethod
    def download_e4_ss():
        e4_ss_link = 'http://get.empatica.com/win/EmpaticaBLEServer.html'
        webbrowser.open_new_tab(e4_ss_link)
        e4_doc_link = 'https://developer.empatica.com/windows-streaming-server-usage.html'
        webbrowser.open_new_tab(e4_doc_link)

    def get_e4_metrics(self):
        export_e4_metrics(self.caller.root, self.caller.prim_dir, self.caller.reli_dir, self.caller.export_dir)

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
