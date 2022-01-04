import os
import pathlib
from os import walk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import json

from config_utils import ConfigUtils
from logger_util import *
from tkinter_utils import center, get_display_size, get_treeview_style, build_treeview
from ui_params import project_treeview_params as ptp, treeview_tags


class ProjectSetupWindow:
    def __init__(self, config):
        self.config = config
        # Window setup
        if len(config.get_screen_size()) == 2:
            self.main_root = Tk()
            self.window_height = int(config.get_screen_size()[0] * 0.7)
            self.window_width = int(config.get_screen_size()[1] * 0.7)
        else:
            self.main_root, self.window_height, self.window_width = get_display_size()
            config.set_screen_size(self.window_height, self.window_width)
            self.window_width = int(self.window_width * 0.7)
            self.window_height = int(self.window_height * 0.7)
        # Create global style
        _ = get_treeview_style()
        # Define heading dicts
        project_heading_dict = {"#0": ["Recent Projects", 'w', 1, YES, 'w']}
        patient_heading_dict = {"#0": ["Existing Patients", 'w', 1, YES, 'w']}
        concern_heading_dict = {"#0": ["Presenting Concerns", 'w', 1, YES, 'w']}
        # Build treeviews
        self.project_treeview_parents, self.patient_treeview_parents, self.concern_treeview_parents = [], [], []
        self.project_treeview, self.project_filescroll = build_treeview(self.main_root, ptp[0], ptp[1],
                                                                        int(self.window_height * 0.3),
                                                                        int(self.window_width * 0.45),
                                                                        project_heading_dict,
                                                                        double_bind=self.select_project)
        self.recent_projects = config.get_recent_projects()
        self.populate_recent_projects()
        self.patient_treeview, self.patient_filescroll = build_treeview(self.main_root, ptp[0],
                                                                        ptp[1] + int(self.window_height * 0.35),
                                                                        int(self.window_height * 0.2),
                                                                        int(self.window_width * 0.45),
                                                                        patient_heading_dict)

        self.concern_treeview, self.concern_filescroll = build_treeview(self.main_root, ptp[0],
                                                                        ptp[1] + int(self.window_height * 0.35) + int(
                                                                            self.window_height * 0.25),
                                                                        int(self.window_height * 0.2),
                                                                        int(self.window_width * 0.45),
                                                                        concern_heading_dict)
        # Get phases and create dropbox
        self.phases = config.get_phases()
        if self.phases:
            self.phases_var = StringVar(self.main_root)
            self.phases_var.set("Select a Phase")
            self.phases_menu = OptionMenu(self.main_root, self.phases_var, *self.phases)
            self.phases_menu.place(x=ptp[0],
                                   y=ptp[1] + int(self.window_height * 0.35) + int(self.window_height * 0.25) + int(
                                       self.window_height * 0.22),
                                   width=int(self.window_width * 0.2))
        # Create window geometry, center, and display
        self.main_root.geometry("{0}x{1}+0+0".format(self.window_width, self.window_height))
        center(self.main_root)
        self.main_root.resizable(width=False, height=False)
        self.main_root.mainloop()

    def select_project(self, event):
        selection = self.project_treeview.identify_row(event.y)
        if selection == '0':
            self.create_new_project()
        else:
            self.load_project(self.recent_projects[int(selection) - 1])

    def create_new_project(self):
        print("create new project")

    def load_project(self, dir):
        print("load project from", dir)

    def populate_recent_projects(self):
        self.project_treeview_parents.append(self.project_treeview.insert("", 'end', str(0), text="Create New Project",
                                                                          tags=treeview_tags[0]))
        if self.recent_projects:
            for i in range(1, len(self.recent_projects)):
                self.project_treeview_parents.append(self.project_treeview.insert("", 'end', str(i), text=str(pathlib.Path(
                                                                                          self.recent_projects[i]).stem),
                                                                                  tags=(treeview_tags[i % 2])))


if __name__ == '__main__':
    config = ConfigUtils()
    ProjectSetupWindow(config)
