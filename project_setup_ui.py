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
from ui_params import project_treeview_params as ptp


class ProjectSetupWindow:
    def __init__(self, config):
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
        # Define heading and column dicts, TODO: Move to config
        heading_dict = {"#0": ["Recent Projects", 'w', 65, YES, 'w']}
        column_dict = {"1": ["Col 1", 'c', 65, YES, 'c'],
                       "2": ["Col 2", 'c', 65, YES, 'c']}
        # Build treeviews, TODO: Parameterize the placements?
        project_treeview, project_filescroll = build_treeview(self.main_root, ptp[0], ptp[1],
                                                              int(self.window_height * 0.3),
                                                              int(self.window_width * 0.45), heading_dict)

        patient_treeview, patient_filescroll = build_treeview(self.main_root, ptp[0], ptp[1] + int(self.window_height * 0.35),
                                                              int(self.window_height * 0.2),
                                                              int(self.window_width * 0.45), heading_dict)

        concern_treeview, concern_filescroll = build_treeview(self.main_root, ptp[0], ptp[1] + int(self.window_height * 0.35) + int(self.window_height * 0.25),
                                                              int(self.window_height * 0.2),
                                                              int(self.window_width * 0.45), heading_dict)
        # Create window geometry, center, and display
        self.main_root.geometry("{0}x{1}+0+0".format(self.window_width, self.window_height))
        center(self.main_root)
        self.main_root.mainloop()


if __name__ == '__main__':
    config = ConfigUtils()
    ProjectSetupWindow(config)
