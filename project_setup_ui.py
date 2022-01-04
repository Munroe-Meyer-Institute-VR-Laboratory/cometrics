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


class ProjectSetupWindow:
    def __init__(self, config):
        # Window setup
        if len(config.get_screen_size()) == 2:
            self.main_root = Tk()
            self.window_height = config.get_screen_size()[0]
            self.window_width = config.get_screen_size()[1]
        else:
            self.main_root, self.window_height, self.window_width = get_display_size()
            config.set_screen_size(self.window_height, self.window_width)
        style = get_treeview_style()
        heading_dict = {"#0": ["#", 'c', 65, NO, 'c']}
        column_dict = {"1": ["Col 1", 'c', 65, YES, 'c'],
                       "2": ["Col 2", 'c', 65, YES, 'c']}
        project_treeview, project_filescroll = build_treeview(self.main_root, 20, 20, 400, 300, heading_dict, column_dict)
        self.main_root.geometry("{0}x{1}+0+0".format(int(self.window_width * 0.7), int(self.window_height * 0.7)))
        center(self.main_root)
        self.main_root.mainloop()


if __name__ == '__main__':
    config = ConfigUtils()
    ProjectSetupWindow(config)
