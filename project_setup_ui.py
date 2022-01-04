import os
import pathlib
from os import walk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import json

from config_utils import ConfigUtils
from logger_util import *
import tkinter

from tkinter_utils import center, get_display_size


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
        self.main_root.geometry("{0}x{1}+0+0".format(int(self.window_width * 0.7), int(self.window_height * 0.7)))
        center(self.main_root)
        self.main_root.mainloop()


if __name__ == '__main__':
    config = ConfigUtils()
    ProjectSetupWindow(config)