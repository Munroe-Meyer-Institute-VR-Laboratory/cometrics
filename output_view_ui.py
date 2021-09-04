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
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import numpy as np


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

        self.e4_view = ViewE4(self.frame)

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
        elif view == OutputViews.CAMERA_VIEW:
            self.view_buttons[view].config(relief=SUNKEN)


class ViewE4:
    def __init__(self, root):
        self.root = root

        SMALL_SIZE = 8
        MEDIUM_SIZE = 10
        BIGGER_SIZE = 12

        plt.rc('font', size=SMALL_SIZE)  # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)  # fontsize of the axes title
        plt.rc('axes', labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
        plt.rc('xtick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)  # legend fontsize
        plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

        self.fig = Figure(figsize=(6, 1.75), dpi=100)
        self.acc_plt = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.
        self.canvas.draw()

        self.fig1 = Figure(figsize=(6, 1.75), dpi=100)
        self.bvp_plt = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.root)  # A tk.DrawingArea.
        self.canvas1.draw()

        self.fig2 = Figure(figsize=(6, 1.75), dpi=100)
        self.gsr_plt = self.fig2.add_subplot(111)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.root)  # A tk.DrawingArea.
        self.canvas2.draw()

        self.ani = None
        self.ani1 = None
        self.ani2 = None

    def start_plot(self, e4):
        self.e4 = e4

        self.ani = animation.FuncAnimation(self.fig, self.animate, fargs=([]), interval=500)
        self.canvas.get_tk_widget().place(x=10, y=50)
        self.ani1 = animation.FuncAnimation(self.fig1, self.bvp_animate, fargs=([]), interval=500)
        self.canvas1.get_tk_widget().place(x=10, y=225)
        self.ani2 = animation.FuncAnimation(self.fig2, self.gsr_animate, fargs=([]), interval=500)
        self.canvas2.get_tk_widget().place(x=10, y=400)

    def animate(self, e4):
        if self.e4:
            if self.e4.connected:
                # Limit x and y lists to 20 items
                x_ys = self.e4.acc_x[-100:]
                y_ys = self.e4.acc_y[-100:]
                z_ys = self.e4.acc_z[-100:]
                xs = np.arange(0, len(self.e4.acc_x))
                xs = xs[-100:]

                # Draw x and y lists
                self.acc_plt.clear()
                self.acc_plt.plot(xs, x_ys, label="x-axis")
                self.acc_plt.plot(xs, y_ys, label="y-axis")
                self.acc_plt.plot(xs, z_ys, label="z-axis")

                # Format plot
                plt.gcf().subplots_adjust(bottom=0.15)
                self.acc_plt.set_title("Accelerometer Readings")
                self.acc_plt.legend(loc="upper left")

    def bvp_animate(self, e4):
        if self.e4:
            if self.e4.connected:
                xs = np.arange(0, len(self.e4.bvp))
                xs = xs[-100:]
                x_ys = self.e4.bvp[-100:]

                self.bvp_plt.clear()
                self.bvp_plt.plot(xs, x_ys, label="bvp")

                # Format plot
                plt.gcf().subplots_adjust(bottom=0.15)
                self.bvp_plt.set_title("BVP Readings")
                self.bvp_plt.legend(loc="upper left")

    def gsr_animate(self, e4):
        if self.e4:
            if self.e4.connected:
                xs = np.arange(0, len(self.e4.gsr))
                xs = xs[-100:]
                x_ys = self.e4.gsr[-100:]

                self.gsr_plt.clear()
                self.gsr_plt.plot(xs, x_ys, label="gsr")
                # Format plot
                plt.gcf().subplots_adjust(bottom=0.15)
                self.gsr_plt.set_title("GSR Readings")
                self.gsr_plt.legend(loc="upper left")
