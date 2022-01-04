import os
import pathlib
from os import walk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import json
from logger_util import *
import tkinter

from tkinter_utils import center, get_display_size


class ProjectSetupWindow:
    def __init__(self):
        self.main_root, self.window_height, self.window_width = get_display_size()
        self.main_root.geometry("{0}x{1}+0+0".format(int(self.window_width * 0.7), int(self.window_height * 0.7)))
        center(self.main_root)
        self.main_root.mainloop()


if __name__ == '__main__':
    ProjectSetupWindow()