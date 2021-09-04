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
    TACTOR_VIEW = 3


class OutputViewPanel:
    def __init__(self, parent):
        self.current_button = 0
        self.view_buttons = []
        self.view_frames = []

        self.frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 255))
        self.frame.place(x=780, y=95)

        e4_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        e4_frame.place(x=780, y=120)
        self.view_frames.append(e4_frame)

        video_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        test_label = Label(video_frame, text="Video Frame")
        test_label.place(x=200, y=200)
        self.view_frames.append(video_frame)

        camera_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        test_label = Label(camera_frame, text="Camera Frame")
        test_label.place(x=200, y=200)
        self.view_frames.append(camera_frame)

        tactor_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        test_label = Label(tactor_frame, text="Tactor Frame")
        test_label.place(x=200, y=200)
        self.view_frames.append(tactor_frame)

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

        tactor_view_button = Button(self.frame, text="Tactor View", command=self.switch_tactor_frame, width=12)
        self.view_buttons.append(tactor_view_button)
        self.view_buttons[3].place(x=276, y=0)

        clean_view = Frame(self.frame, width=(700-(92*len(self.view_buttons))+2), height=25, bg='white')
        clean_view.place(x=(92*len(self.view_buttons))+2, y=0)

        self.e4_view = ViewE4(self.view_frames[OutputViews.E4_VIEW])

    def switch_tactor_frame(self):
        self.switch_frame(OutputViews.TACTOR_VIEW)

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
        self.view_frames[self.current_button].place_forget()
        self.current_button = view
        self.view_buttons[view].config(relief=SUNKEN)
        self.view_frames[view].place(x=780, y=120)

    def close(self):
        self.e4_view.stop_plot()


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

        fig_color = '#%02x%02x%02x' % (240, 240, 237)

        self.hr_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.hr_canvas.place(x=100, y=5)
        self.hr_image = ImageTk.PhotoImage(Image.open('images/heartrate.png').resize((40, 40), Image.ANTIALIAS))
        self.hr_canvas.create_image(0, 0, anchor=NW, image=self.hr_image)

        self.hr_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.hr_label.place(x=150, y=15, anchor=NW)

        self.temp_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.temp_canvas.place(x=300, y=5)
        self.temp_image = ImageTk.PhotoImage(Image.open('images/thermometer.png').resize((40, 40), Image.ANTIALIAS))
        self.temp_canvas.create_image(0, 0, anchor=NW, image=self.temp_image)

        self.temp_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.temp_label.place(x=350, y=15, anchor=NW)

        self.bat_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.bat_canvas.place(x=500, y=5)
        self.bat_image = ImageTk.PhotoImage(Image.open('images/battery100.png').resize((40, 40), Image.ANTIALIAS))
        self.bat_container = self.bat_canvas.create_image(0, 0, anchor=NW, image=self.bat_image)

        self.bat_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.bat_label.place(x=550, y=15, anchor=NW)

        self.fig = Figure(figsize=(6.75, 1.75), dpi=100)
        self.fig.patch.set_facecolor(fig_color)
        self.acc_plt = self.fig.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.acc_plt.set_title("Accelerometer Readings")
        self.acc_plt.legend(loc="upper left")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.
        self.canvas.draw()
        self.ani = animation.FuncAnimation(self.fig, self.animate, fargs=([]), interval=500)
        self.canvas.get_tk_widget().place(x=350, y=50, anchor=N)

        self.fig1 = Figure(figsize=(6.75, 1.75), dpi=100)
        self.fig1.patch.set_facecolor(fig_color)
        self.bvp_plt = self.fig1.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.bvp_plt.set_title("BVP Readings")
        self.bvp_plt.legend(loc="upper left")
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.root)  # A tk.DrawingArea.
        self.canvas1.draw()
        self.ani1 = animation.FuncAnimation(self.fig1, self.bvp_animate, fargs=([]), interval=500)
        self.canvas1.get_tk_widget().place(x=350, y=225, anchor=N)

        self.fig2 = Figure(figsize=(6.75, 1.75), dpi=100)
        self.fig2.patch.set_facecolor(fig_color)
        self.gsr_plt = self.fig2.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.gsr_plt.set_title("GSR Readings")
        self.gsr_plt.legend(loc="upper left")
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.root)  # A tk.DrawingArea.
        self.canvas2.draw()
        self.ani2 = animation.FuncAnimation(self.fig2, self.gsr_animate, fargs=([]), interval=500)
        self.canvas2.get_tk_widget().place(x=350, y=400, anchor=N)

        self.streaming = False
        self.kill = False
        self.e4 = None
        self.bat = 100

        self.update_thread = threading.Thread(target=self.update_labels_thread)
        self.update_thread.start()

    def stop_plot(self):
        self.streaming = False
        self.kill = True

    def start_plot(self, e4):
        self.e4 = e4
        self.streaming = True

    def update_labels_thread(self):
        while not self.streaming:
            if self.kill:
                break
            time.sleep(0.5)
        while self.streaming:
            if self.streaming:
                if self.e4:
                    if self.e4.connected:
                        if len(self.e4.tmp) > 0:
                            self.temp_label['text'] = str(int(self.e4.tmp[-1])) + u"\u00b0"
                        if len(self.e4.hr) > 0:
                            self.hr_label['text'] = str(int(self.e4.hr[-1])) + " BPM"
                        if len(self.e4.bat) > 0:
                            self.bat = int(float(self.e4.bat[-1]) * 100.0)
                            print(self.bat)
                            if 50 < self.bat < 75:
                                self.bat_image = ImageTk.PhotoImage(
                                    Image.open('images/battery75.png').resize((40, 40), Image.ANTIALIAS))
                                self.bat_canvas.itemconfigure(self.bat_container, image=self.bat_image)
                            elif 25 < self.bat < 50:
                                self.bat_image = ImageTk.PhotoImage(
                                    Image.open('images/battery50.png').resize((40, 40), Image.ANTIALIAS))
                                self.bat_canvas.itemconfigure(self.bat_container, image=self.bat_image)
                            elif self.bat < 25:
                                self.bat_image = ImageTk.PhotoImage(
                                    Image.open('images/battery25.png').resize((40, 40), Image.ANTIALIAS))
                                self.bat_canvas.itemconfigure(self.bat_container, image=self.bat_image)
                            self.bat_label['text'] = str(self.bat) + "%"
            time.sleep(0.5)

    def animate(self, e4):
        if self.streaming:
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
        if self.streaming:
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
        if self.streaming:
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


class EmpaticaDataFields:
    def __init__(self, parent, output_view):
        self.ovu = output_view
        self.parent = parent
        self.frame = Frame(parent, width=250, height=(parent.winfo_screenheight() - 280))
        self.frame.place(x=265, y=120)

        self.emp_client = None
        self.e4_client = None
        self.e4_address = None

        empatica_label = Label(self.frame, text="Empatica E4", font=('Purisa', 12))
        empatica_label.place(x=125, y=15, anchor=CENTER)

        self.empatica_button = Button(self.frame, text="Start Server", command=self.start_e4_server)
        self.empatica_button.place(x=125, y=30, anchor=N)

        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 10))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.frame, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=20, y=65, height=(parent.winfo_screenheight() - 450), width=210)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="E4 Name")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_selection)

        self.file_scroll = Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=65, height=(parent.winfo_screenheight() - 450))

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.connect_button = Button(self.frame, text="Connect", command=self.connect_to_e4, width=12)
        self.connect_button.place(x=20, y=(parent.winfo_screenheight() - 385))

        self.streaming_button = Button(self.frame, text="Stream", command=self.start_e4_streaming, width=12)
        self.streaming_button.place(x=230, y=(parent.winfo_screenheight() - 385), anchor=NE)

        self.connected_label = Label(self.frame, text="CONNECTED", fg='green')
        self.streaming_label = Label(self.frame, text="STREAMING", fg='green')

        self.devices_thread = None

    def disconnect_e4(self):
        if self.emp_client:
            self.emp_client.close()
        if self.e4_client:
            if self.e4_client.connected:
                self.e4_client.close()

    def connect_to_e4(self):
        if self.emp_client:
            try:
                self.e4_client = EmpaticaE4(self.e4_address)
                if self.e4_client.connected:
                    for stream in EmpaticaDataStreams.ALL_STREAMS:
                        self.e4_client.subscribe_to_stream(stream)
                    self.connected_label.place(x=125, y=(self.parent.winfo_screenheight() - 350), anchor=N)
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_streaming(self):
        if self.emp_client:
            if self.e4_client:
                if self.e4_client.connected:
                    try:
                        self.e4_client.start_streaming()
                        self.ovu.e4_view.start_plot(self.e4_client)
                        self.streaming_label.place(x=125, y=(self.parent.winfo_screenheight() - 320), anchor=N)
                    except Exception as e:
                        messagebox.showerror("Exception Encountered",
                                             "Encountered an error when connecting to E4:\n" + str(e))
                else:
                    messagebox.showwarning("Warning", "Device is not connected!")
            else:
                messagebox.showwarning("Warning", "Connect to device first!")
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_server(self):
        if not self.emp_client:
            try:
                self.emp_client = EmpaticaClient()
                self.empatica_button['text'] = "List Devices"
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
        else:
            try:
                self.devices_thread = threading.Thread(target=self.list_devices_thread)
                self.devices_thread.start()
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))

    def list_devices_thread(self):
        self.emp_client.list_connected_devices()
        time.sleep(1)
        self.clear_device_list()
        self.populate_device_list()

    def clear_device_list(self):
        for children in self.treeview.get_children():
            self.treeview.delete(children)

    def populate_device_list(self):
        for i in range(0, len(self.emp_client.device_list)):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
                                                          values=(self.emp_client.device_list[i].decode("utf-8"),),
                                                          tags=(self.tags[i % 2])))

    def get_selection(self, event):
        self.current_selection = self.treeview.identify_row(event.y)
        if self.current_selection:
            if self.emp_client:
                if len(self.emp_client.device_list) != 0:
                    self.e4_address = self.emp_client.device_list[int(self.current_selection)]
                else:
                    messagebox.showerror("Error", "No connected E4s!")
            else:
                messagebox.showwarning("Warning", "Connect to server first!")

    def save_session(self, filename):
        if self.e4_client:
            if self.e4_client.connected:
                self.e4_client.save_readings(filename)

    def fixed_map(self, option):
        # https://stackoverflow.com/a/62011081
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        style = Style()
        return [elm for elm in style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]
