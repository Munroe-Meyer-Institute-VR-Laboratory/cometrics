import os
import pathlib
import time
from os import walk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import json
import datetime
from PIL import Image, ImageTk
import threading
from pynput import keyboard
import winsound
# Custom library imports
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams
from logger_util import *


class OutputViews:
    E4_VIEW = 0
    VIDEO_VIEW = 1
    CAMERA_VIEW = 2


class OutputViewPanel:
    def __init__(self, parent):
        self.frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 255))
        self.frame.place(x=780, y=95)

        self.current_button = 0
        self.view_buttons = []

        e4_output_button = Button(self.frame, text="E4 View", command=self.switch_e4_frame, width=12)
        self.view_buttons.append(e4_output_button)
        self.view_buttons[0].place(x=0, y=0)
        self.view_buttons[0].config(relief=SUNKEN)

        video_view_button = Button(self.frame, text="Annotate Video", command=self.switch_video_frame, width=12)
        self.view_buttons.append(video_view_button)
        self.view_buttons[1].place(x=92, y=0)

        camera_view_button = Button(self.frame, text="Video Capture", command=self.switch_camera_frame, width=12)
        self.view_buttons.append(camera_view_button)
        self.view_buttons[2].place(x=184, y=0)

        clean_view = Frame(self.frame, width=(700-(92*len(self.view_buttons))+2), height=25, bg='white')
        clean_view.place(x=(92*len(self.view_buttons))+2, y=0)

    def switch_camera_frame(self):
        self.switch_frame(OutputViews.CAMERA_VIEW)

    def switch_video_frame(self):
        self.switch_frame(OutputViews.VIDEO_VIEW)

    def switch_e4_frame(self):
        self.switch_frame(OutputViews.E4_VIEW)

    def switch_frame(self, view):
        """
        https://stackoverflow.com/a/23354009
        :param view:
        :return:
        """
        self.view_buttons[self.current_button].config(relief=RAISED)
        self.current_button = view
        if view == OutputViews.E4_VIEW:
            self.view_buttons[view].config(relief=SUNKEN)
        elif view == OutputViews.VIDEO_VIEW:
            self.view_buttons[view].config(relief=SUNKEN)
        elif view== OutputViews.CAMERA_VIEW:
            self.view_buttons[view].config(relief=SUNKEN)


