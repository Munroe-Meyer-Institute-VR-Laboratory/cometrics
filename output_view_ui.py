import json
import pathlib
import pickle
import threading
import time
import traceback
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Style
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import tkvideo
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
from pyempatica.empaticae4 import EmpaticaE4, EmpaticaDataStreams, EmpaticaClient
# Custom library imports
from tkinter_utils import build_treeview, clear_treeview
from ui_params import treeview_bind_tag_dict, treeview_tags, treeview_bind_tags


class OutputViews:
    KEY_VIEW = 0
    E4_VIEW = 1
    VIDEO_VIEW = 2


class OutputViewPanel:
    def __init__(self, parent, x, y, height, width, button_size, ksf,
                 field_font, header_font):
        self.height, self.width = height, width
        self.x, self.y, self.button_size = x, y, button_size
        self.current_button = 0
        self.view_buttons = []
        self.view_frames = []

        self.frame = Frame(parent, width=width, height=height)
        self.frame.place(x=x, y=y)

        clean_view = Frame(self.frame, width=width,
                           height=button_size[1], bg='white')
        clean_view.place(x=0, y=0)

        key_frame = Frame(parent, width=width, height=height)
        key_frame.place(x=x, y=y + self.button_size[1])
        self.view_frames.append(key_frame)

        e4_frame = Frame(parent, width=width, height=height)
        self.view_frames.append(e4_frame)

        video_frame = Frame(parent, width=width, height=height)
        self.view_frames.append(video_frame)

        # tactor_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        # test_label = Label(tactor_frame, text="Tactor Frame")
        # test_label.place(x=200, y=200)
        # self.view_frames.append(tactor_frame)

        key_button = Button(self.frame, text="Key Bindings", command=self.switch_key_frame, width=12,
                            font=field_font)
        self.view_buttons.append(key_button)
        self.view_buttons[OutputViews.KEY_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
                                                      width=button_size[0], height=button_size[1])
        self.view_buttons[OutputViews.KEY_VIEW].config(relief=SUNKEN)

        e4_output_button = Button(self.frame, text="E4 Streams", command=self.switch_e4_frame, width=12,
                                  font=field_font)
        self.view_buttons.append(e4_output_button)
        self.view_buttons[OutputViews.E4_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
                                                     width=button_size[0], height=button_size[1])

        video_button = Button(self.frame, text="Video View", command=self.switch_video_frame, width=12,
                              font=field_font)
        self.view_buttons.append(video_button)
        self.view_buttons[OutputViews.VIDEO_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
                                                        width=button_size[0], height=button_size[1])

        # tactor_view_button = Button(self.frame, text="Tactor View", command=self.switch_tactor_frame, width=12)
        # self.view_buttons.append(tactor_view_button)
        # self.view_buttons[3].place(x=276, y=0)

        self.e4_view = ViewE4(self.view_frames[OutputViews.E4_VIEW],
                              height=self.height - self.button_size[1], width=self.width,
                              field_font=field_font, header_font=header_font, button_size=button_size)
        self.key_view = KeystrokeDataFields(self.view_frames[OutputViews.KEY_VIEW], ksf,
                                            height=self.height - self.button_size[1], width=self.width,
                                            field_font=field_font, header_font=header_font, button_size=button_size)
        self.video_view = ViewVideo(self.view_frames[OutputViews.VIDEO_VIEW],
                                    height=self.height - self.button_size[1], width=self.width,
                                    field_font=field_font, header_font=header_font, button_size=button_size)

    def switch_key_frame(self):
        self.switch_frame(OutputViews.KEY_VIEW)

    def switch_tactor_frame(self):
        self.switch_frame(OutputViews.TACTOR_VIEW)

    def switch_e4_frame(self):
        self.switch_frame(OutputViews.E4_VIEW)

    def switch_video_frame(self):
        self.switch_frame(OutputViews.VIDEO_VIEW)

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
        self.view_frames[view].place(x=self.x, y=self.y + self.button_size[1])

    def close(self):
        self.e4_view.stop_plot()

    def start_session(self):
        self.e4_view.session_started = True

    def stop_session(self):
        self.e4_view.session_started = False

    def save_session(self, filename, keystrokes):
        if self.e4_view.windowed_readings:
            try:
                for keystroke in keystrokes:
                    try:
                        if type(keystroke[1]) is tuple:
                            self.e4_view.windowed_readings[int(keystroke[1][0]) - 1][-1].append(keystroke[0])
                            self.e4_view.windowed_readings[int(keystroke[1][1]) - 1][-1].append(keystroke[0])
                        else:
                            self.e4_view.windowed_readings[int(keystroke[1]) - 1][-1].append(keystroke[0])
                    except Exception as e:
                        print(str(e))
                        print(traceback.print_exc())
                with open(filename, 'wb') as f:
                    pickle.dump(self.e4_view.windowed_readings, f)
            except TypeError as e:
                with open(filename, 'wb') as f:
                    pickle.dump(self.e4_view.windowed_readings, f)
                print(str(e))


class ViewVideo:
    def __init__(self, root, height, width, field_font, header_font, button_size, field_offset=60):
        self.root = root
        self.video_label = Label(self.root, bg='white')
        self.video_height, self.video_width = height - 200, width - 10
        self.video_label.place(x=width / 2, y=5, width=width - 10, height=height - 200, anchor=N)
        self.load_video_button = Button(self.root, text="Load Video", font=field_font, command=self.load_video)
        self.load_video_button.place(x=width / 2, y=5 + (self.video_height / 2), height=button_size[1],
                                     width=button_size[0],
                                     anchor=CENTER)
        self.play_image = PhotoImage(file='images/video-start.png')
        self.pause_image = PhotoImage(file='images/video-pause.png')
        self.play_button = Button(self.root, image=self.play_image)
        self.play_button.place(x=5, y=self.video_height + 40, anchor=NW)
        self.frame_var = IntVar(self.root)
        self.video_slider = Scale(self.root, orient=HORIZONTAL, variable=self.frame_var)
        self.video_slider.config(length=self.video_width)
        self.video_slider.place(x=5, y=self.video_height, anchor=NW)

        event_header_dict = {"#0": ["Event Time", 'w', 1, YES, 'w']}
        event_column_dict = {"1": ["Event Tag", 'w', 1, YES, 'w'],
                             "2": ["Event Frame", 'w', 1, YES, 'w']}
        self.event_treeview, self.event_fs = build_treeview(self.root,
                                                            x=20, y=self.video_height + 90,
                                                            height=120,
                                                            width=width - 25,
                                                            heading_dict=event_header_dict,
                                                            column_dict=event_column_dict)

    def load_video(self):
        video_file = filedialog.askopenfilename(filetypes=(("Videos", "*.mp4"),))
        if video_file:
            if pathlib.Path(video_file).suffix == ".mp4":
                self.load_video_button.place_forget()
                self.video_file = video_file
                self.player = tkvideo.tkvideo(video_file, self.video_label, loop=False,
                                              size=(self.video_width, self.video_height),
                                              keep_ratio=True,
                                              play_button=self.play_button,
                                              pause_image=self.pause_image,
                                              play_image=self.play_image,
                                              slider=self.video_slider,
                                              slider_var=self.frame_var)


class ViewE4:
    def __init__(self, root, height, width, field_font, header_font, button_size, field_offset=60):
        self.root = root
        self.session_started = False
        self.height, self.width = height, width

        self.emp_client = None
        self.e4_client = None
        self.e4_address = None
        fs_offset = 10 + ((width * 0.25) * 0.5)
        connection_offset = width * 0.15
        start_y = 25
        empatica_label = Label(self.root, text="E4 Connection", font=header_font)
        empatica_label.place(x=connection_offset, y=start_y, anchor=CENTER)

        self.empatica_button = Button(self.root, text="Start Server", command=self.start_e4_server, font=field_font)
        self.empatica_button.place(x=connection_offset, y=start_y + (field_offset / 2),
                                   width=button_size[0], height=button_size[1], anchor=CENTER)

        e4_heading_dict = {"#0": ["Visible E4s", 'c', 1, YES, 'c']}
        self.e4_treeview, self.e4_filescroll = build_treeview(self.root,
                                                              x=connection_offset,
                                                              y=start_y + field_offset,
                                                              height=height * 0.5, width=width * 0.25,
                                                              heading_dict=e4_heading_dict, anchor=N,
                                                              fs_offset=fs_offset)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.connect_button = Button(self.root, text="Connect",
                                     command=self.connect_to_e4, width=12, font=field_font)
        self.connect_button.place(x=connection_offset, y=start_y + field_offset + height * 0.5,
                                  width=(width * 0.25) * 0.5, height=button_size[1], anchor=NE)

        self.streaming_button = Button(self.root, text="Stream",
                                       command=self.start_e4_streaming, width=12, font=field_font)
        self.streaming_button.place(x=connection_offset, y=start_y + field_offset + height * 0.5,
                                    width=(width * 0.25) * 0.5, height=button_size[1], anchor=NW)

        self.disconnected_image = PhotoImage(file='images/disconnected.png')
        self.connected_image = PhotoImage(file='images/connected.png')
        self.connected_label = Label(self.root, image=self.disconnected_image)
        self.connected_label.place(x=connection_offset - ((width * 0.25) * 0.5) * 0.5,
                                   y=(start_y + field_offset + height * 0.5) + button_size[1], anchor=N)

        self.streaming_image = PhotoImage(file='images/streaming.png')
        self.nostreaming_image = PhotoImage(file='images/nostreaming.png')
        self.streaming_label = Label(self.root, image=self.nostreaming_image)
        self.streaming_label.place(x=connection_offset + ((width * 0.25) * 0.5) * 0.5,
                                   y=(start_y + field_offset + height * 0.5) + button_size[1], anchor=N)

        self.error_thread = None
        self.devices_thread = None

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

        fig_offset = width * 0.25
        fig_width = width - fig_offset
        fig_height = (height - 70) / 3

        self.hr_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.hr_canvas.place(x=fig_offset + (fig_width * 0.2), y=start_y)
        self.hr_image = PhotoImage(file='images/heartrate.png')
        self.hr_canvas.create_image(0, 0, anchor=NW, image=self.hr_image)

        self.hr_label = Label(self.root, text="N/A", font=field_font)
        self.hr_label.place(x=fig_offset + (fig_width * 0.2) + 50, y=start_y + 10, anchor=NW)

        self.temp_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.temp_canvas.place(x=fig_offset + (fig_width * 0.4), y=start_y)
        self.temp_image = PhotoImage(file='images/thermometer.png')
        self.temp_canvas.create_image(0, 0, anchor=NW, image=self.temp_image)

        self.temp_label = Label(self.root, text="N/A", font=field_font)
        self.temp_label.place(x=fig_offset + (fig_width * 0.4) + 50, y=start_y + 10, anchor=NW)

        self.wrist_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.wrist_canvas.place(x=fig_offset + (fig_width * 0.6), y=start_y, anchor=NW)
        self.on_wrist_image = PhotoImage(file='images/onwrist.png')
        self.off_wrist_image = PhotoImage(file='images/offwrist.png')
        self.wrist_container = self.wrist_canvas.create_image(20, 20, anchor=CENTER, image=self.off_wrist_image)
        self.wrist = False

        self.wrist_label = Label(self.root, text="Off", font=field_font)
        self.wrist_label.place(x=fig_offset + (fig_width * 0.6) + 50, y=start_y + 10, anchor=NW)

        self.bat_image_100 = PhotoImage(file='images/battery100.png')
        self.bat_image_75 = PhotoImage(file='images/battery75.png')
        self.bat_image_50 = PhotoImage(file='images/battery50.png')
        self.bat_image_25 = PhotoImage(file='images/battery25.png')
        self.bat_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.bat_canvas.place(x=fig_offset + (fig_width * 0.8), y=start_y)
        self.bat_container = self.bat_canvas.create_image(20, 20, anchor=CENTER, image=self.bat_image_100)

        self.bat_label = Label(self.root, text="N/A", font=field_font)
        self.bat_label.place(x=fig_offset + (fig_width * 0.8) + 50, y=start_y + 10, anchor=NW)

        px = 1 / plt.rcParams['figure.dpi']
        self.fig = Figure(figsize=(fig_width * px, fig_height * px), dpi=100)
        self.fig.patch.set_facecolor(fig_color)
        self.acc_plt = self.fig.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.acc_plt.set_title("Accelerometer Readings")
        self.acc_plt.legend(loc="upper left")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.ani = animation.FuncAnimation(self.fig, self.animate, fargs=([]), interval=500)
        self.canvas.get_tk_widget().place(x=fig_offset + 30, y=70, anchor=NW)

        self.fig1 = Figure(figsize=(fig_width * px, fig_height * px), dpi=100)
        self.fig1.patch.set_facecolor(fig_color)
        self.bvp_plt = self.fig1.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.bvp_plt.set_title("BVP Readings")
        self.bvp_plt.legend(loc="upper left")
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self.root)  # A tk.DrawingArea.
        self.canvas1.draw()
        self.ani1 = animation.FuncAnimation(self.fig1, self.bvp_animate, fargs=([]), interval=500)
        self.canvas1.get_tk_widget().place(x=fig_offset + 30, y=70 + fig_height, anchor=NW)

        self.fig2 = Figure(figsize=(fig_width * px, fig_height * px), dpi=100)
        self.fig2.patch.set_facecolor(fig_color)
        self.gsr_plt = self.fig2.add_subplot(111)
        plt.gcf().subplots_adjust(bottom=0.15)
        self.gsr_plt.set_title("GSR Readings")
        self.gsr_plt.legend(loc="upper left")
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=self.root)  # A tk.DrawingArea.
        self.canvas2.draw()
        self.ani2 = animation.FuncAnimation(self.fig2, self.gsr_animate, fargs=([]), interval=500)
        self.canvas2.get_tk_widget().place(x=fig_offset + 30, y=70 + (fig_height * 2), anchor=NW)

        self.save_reading = False
        self.streaming = False
        self.kill = False
        self.e4 = None
        self.bat = 100
        self.windowed_readings = []
        self.update_thread = threading.Thread(target=self.update_labels_thread)

    def check_e4_error(self):
        while self.e4_client:
            if self.e4_client.client.last_error:
                messagebox.showerror("E4 Error", "Encountered error from E4!\n" + self.e4_client.client.last_error)
                self.connect_to_e4()
            time.sleep(0.5)

    def disconnect_e4(self):
        if self.emp_client:
            self.emp_client.close()
        if self.e4_client:
            if self.e4_client.connected:
                self.e4_client.close()

    def connect_to_e4(self):
        if self.emp_client:
            try:
                if self.e4_client:
                    self.e4_client.disconnect()
                    self.connect_button.config(text="Connect")
                    self.connected_label.config(image=self.disconnected_image)
                    self.streaming_label.config(image=self.nostreaming_image)
                    self.e4_client = None
                else:
                    self.e4_client = EmpaticaE4(self.e4_address)
                    if self.e4_client.connected:
                        if self.error_thread is None:
                            self.error_thread = threading.Thread(target=self.check_e4_error)
                            self.error_thread.start()
                        for stream in EmpaticaDataStreams.ALL_STREAMS:
                            self.e4_client.subscribe_to_stream(stream)
                        self.connected_label.config(image=self.connected_image)
                        self.connect_button.config(text="Disconnect")
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
                print(traceback.print_exc())
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_streaming(self):
        if self.emp_client:
            if self.e4_client:
                if self.e4_client.connected:
                    try:
                        self.e4_client.start_streaming()
                        self.start_plot(self.e4_client)
                        self.streaming_label.config(image=self.streaming_image)
                    except Exception as e:
                        messagebox.showerror("Exception Encountered",
                                             "Encountered an error when connecting to E4:\n" + str(e))
                        print(traceback.print_exc())
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
                print(traceback.print_exc())
        else:
            try:
                self.devices_thread = threading.Thread(target=self.list_devices_thread)
                self.devices_thread.start()
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
                print(traceback.print_exc())

    def list_devices_thread(self):
        self.emp_client.list_connected_devices()
        time.sleep(1)
        self.clear_device_list()
        self.populate_device_list()

    def clear_device_list(self):
        for children in self.e4_treeview.get_children():
            self.e4_treeview.delete(children)
        self.e4_treeview_parents = []

    def populate_device_list(self):
        for i in range(0, len(self.emp_client.device_list)):
            self.e4_treeview_parents.append(
                self.e4_treeview.insert("", 'end', str(i),
                                        text=str(self.emp_client.device_list[i].decode("utf-8")),
                                        tags=(treeview_tags[i % 2])))

    def get_selection(self, event):
        self.current_selection = self.e4_treeview.identify_row(event.y)
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

    def stop_plot(self):
        self.streaming = False
        self.kill = True

    def start_plot(self, e4):
        self.e4 = e4
        if not self.streaming:
            self.streaming = True
            self.update_thread.start()

    def update_labels_thread(self):
        while self.streaming:
            if self.streaming:
                if self.e4:
                    if self.e4.connected:
                        if self.wrist != self.e4.on_wrist:
                            if self.e4.on_wrist:
                                self.wrist_canvas.delete(self.wrist_container)
                                self.wrist_container = self.wrist_canvas.create_image(20, 20, anchor=CENTER,
                                                                                      image=self.on_wrist_image)
                                self.wrist_label['text'] = "On"
                            else:
                                self.wrist_canvas.delete(self.wrist_container)
                                self.wrist_container = self.wrist_canvas.create_image(20, 20, anchor=CENTER,
                                                                                      image=self.off_wrist_image)
                                self.wrist_label['text'] = "Off"
                            self.wrist = self.e4.on_wrist
                        if len(self.e4.tmp) > 0:
                            self.temp_label['text'] = str(int(self.e4.tmp[-1])) + u"\u00b0"
                        if len(self.e4.hr) > 0:
                            self.hr_label['text'] = str(int(self.e4.hr[-1])) + " BPM"
                        if len(self.e4.bat) > 0:
                            bat = int(float(self.e4.bat[-1]) * 100.0)
                            if bat != self.bat:
                                self.bat = bat
                                if 50 < self.bat < 75:
                                    self.bat_canvas.delete(self.bat_container)
                                    self.bat_container = self.bat_canvas.create_image(20, 20, anchor=CENTER,
                                                                                      image=self.bat_image_75)
                                elif 25 < self.bat < 50:
                                    self.bat_canvas.delete(self.bat_container)
                                    self.bat_container = self.bat_canvas.create_image(20, 20, anchor=CENTER,
                                                                                      image=self.bat_image_50)
                                elif self.bat < 25:
                                    self.bat_canvas.delete(self.bat_container)
                                    self.bat_container = self.bat_canvas.create_image(20, 20, anchor=CENTER,
                                                                                      image=self.bat_image_25)
                                self.bat_label['text'] = str(self.bat) + "%"
            time.sleep(0.5)

    def animate(self, e4):
        if self.streaming:
            if self.e4:
                if self.e4.connected:
                    if self.session_started:
                        if self.save_reading:
                            self.save_reading = False
                            self.windowed_readings.append(
                                (self.e4.acc_3d[-(32 * 3):],
                                 self.e4.acc_x[-32:], self.e4.acc_y[-32:], self.e4.acc_z[-32:],
                                 self.e4.acc_timestamps[-32:],
                                 self.e4.bvp[-64:], self.e4.bvp_timestamps[-64:],
                                 self.e4.gsr[-4:], self.e4.gsr_timestamps[-4:],
                                 self.e4.tmp[-4:], self.e4.tmp_timestamps[-4:],
                                 [])
                            )
                        else:
                            self.save_reading = True
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


class KeystrokeDataFields:
    def __init__(self, parent, keystroke_file, height, width,
                 field_font, header_font, button_size):
        separation_distance = 30
        fs_offset = 10 + ((width * 0.25) * 0.5)
        t_width = width * 0.25

        start_y = 25
        t_y = start_y + 15
        th_offset = t_y * 2
        sh_exp_offset = th_offset

        self.height, self.width = height, width
        self.frame = parent

        keystroke_label = Label(self.frame, text="Frequency Bindings", font=header_font)
        keystroke_label.place(x=(width * 0.25) - 30, y=start_y, anchor=CENTER)
        freq_heading_dict = {"#0": ["Char", 'c', 1, YES, 'c']}
        freq_column_dict = {"1": ["Freq", 'c', 1, YES, 'c'],
                            "2": ["Tag", 'c', 1, YES, 'c']}
        self.freq_treeview, self.freq_filescroll = build_treeview(self.frame,
                                                                  x=(width * 0.25) - separation_distance, y=t_y,
                                                                  height=height - th_offset, width=t_width,
                                                                  column_dict=freq_column_dict,
                                                                  heading_dict=freq_heading_dict,
                                                                  button_1_bind=self.get_freq_selection,
                                                                  double_bind=self.change_freq_keybind,
                                                                  anchor=N,
                                                                  tag_dict=treeview_bind_tag_dict,
                                                                  fs_offset=fs_offset)

        dur_label = Label(self.frame, text="Duration Bindings", font=header_font)
        dur_label.place(x=width * 0.5, y=start_y, anchor=CENTER)
        dur_heading_dict = {"#0": ["Char", 'c', 1, YES, 'c']}
        dur_column_dict = {"1": ["Dur", 'c', 1, YES, 'c'],
                           "2": ["Total", 'c', 1, YES, 'c'],
                           "3": ["Tag", 'c', 1, YES, 'c']}
        self.dur_treeview, self.dur_filescroll = build_treeview(self.frame,
                                                                x=width * 0.5, y=t_y,
                                                                height=height - th_offset, width=t_width,
                                                                column_dict=dur_column_dict,
                                                                heading_dict=dur_heading_dict,
                                                                button_1_bind=self.get_dur_selection,
                                                                double_bind=self.change_dur_keybind,
                                                                anchor=N,
                                                                tag_dict=treeview_bind_tag_dict,
                                                                fs_offset=fs_offset)

        sh_label = Label(self.frame, text="Session History", font=header_font)
        sh_label.place(x=(width * 0.75) + 30, y=start_y, anchor=CENTER)
        sh_heading_dict = {"#0": ["Event", 'c', 1, YES, 'c']}
        sh_column_dict = {"1": ["Time", 'c', 1, YES, 'c']}
        self.sh_treeview, self.sh_filescroll = build_treeview(self.frame,
                                                              x=(width * 0.75) + separation_distance, y=t_y,
                                                              height=height - th_offset, width=t_width,
                                                              column_dict=sh_column_dict,
                                                              heading_dict=sh_heading_dict,
                                                              double_bind=self.delete_event,
                                                              anchor=N,
                                                              tag_dict=treeview_bind_tag_dict,
                                                              fs_offset=fs_offset)

        self.key_explanation = Label(self.frame, font=field_font, text="Delete Last Event: Backspace"
                                                                       "\nDouble Click Any Event to Delete"
                                                                       "\nUndo Delete: +/= Button", justify=LEFT)
        self.key_explanation.place(x=((width * 0.75) + 30) - ((width * 0.25) * 0.5),
                                   y=height - (th_offset / 2), anchor=NW)

        self.init_background_vars(keystroke_file)

    def init_background_vars(self, keystroke_file):
        # Setup variables used
        self.keystroke_json = None
        self.new_keystroke = False
        self.bindings = []
        self.event_history = []
        self.dur_bindings = []
        self.bindings_freq = []
        self.key_file = keystroke_file
        self.conditions = []
        self.freq_strings = []
        self.freq_key_strings = []
        self.dur_sticky = []
        self.sticky_start = []
        self.sticky_dur = []
        self.sh_treeview_parents, self.freq_treeview_parents, self.dur_treeview_parents = [], [], []
        self.sh_c_selection, self.freq_c_selection, self.dur_c_selection = "I000", "I000", "I000"
        # Access files and populate on screen
        self.open_keystroke_file()
        self.populate_freq_bindings()
        self.populate_dur_bindings()
        self.populate_sh_bindings()

    def add_session_event(self, events):
        for event in events:
            if type(event[1]) is list:
                start_time = int(event[1][1]) - int(event[1][0])
            else:
                start_time = event[1]
            self.event_history.append(event)
            self.sh_treeview_parents.append(self.sh_treeview.insert("", 'end', str(len(self.event_history)),
                                                                    values=(self.event_history[-1][0], start_time),
                                                                    tags=(treeview_tags[len(self.event_history) % 2])))
        self.sh_treeview.see(self.sh_treeview_parents[-1])

    def delete_event(self, event):
        self.current_selection2 = self.sh_treeview.identify_row(event.y)
        if self.current_selection2:
            index = self.sh_treeview_parents.index(str(self.current_selection2))
            self.sh_treeview.delete(self.sh_treeview_parents[index])
            self.sh_treeview_parents.pop(index)
            self.event_history.pop(index)

    def delete_last_event(self):
        if self.event_history:
            self.sh_treeview.delete(self.sh_treeview_parents[len(self.event_history) - 1])
            self.sh_treeview_parents.pop(len(self.event_history) - 1)
            self.event_history.pop(len(self.event_history) - 1)

    def delete_dur_binding(self):
        if self.current_selection1:
            self.dur_bindings.pop(int(self.current_selection1))
            clear_treeview(self.dur_treeview)
            self.populate_dur_bindings()

    def add_dur_popup(self):
        NewKeyPopup(self, self.frame, True)

    def check_key(self, key_char, start_time):
        return_bindings = []
        for i in range(0, len(self.bindings)):
            if self.bindings[i][1] == key_char:
                self.bindings_freq[i] += 1
                self.freq_treeview.set(str(i), column="2", value=self.bindings_freq[i])
                return_bindings.append((self.bindings[i][0], start_time))
        for i in range(0, len(self.dur_bindings)):
            if self.dur_bindings[i][1] == key_char:
                if self.dur_sticky[i]:
                    self.dur_treeview.item(str(i), tags=treeview_bind_tags[i % 2])
                    self.dur_sticky[i] = False
                    duration = [self.sticky_start[i], start_time]
                    return_bindings.append((self.dur_bindings[i][0], duration))
                    self.sticky_dur[i] += start_time - self.sticky_start[i]
                    self.sticky_start[i] = 0
                    self.dur_treeview.set(str(i), column="3", value=self.sticky_dur[i])
                else:
                    self.dur_treeview.item(str(i), tags=treeview_bind_tags[2])
                    self.dur_sticky[i] = True
                    self.sticky_start[i] = start_time
        if return_bindings:
            self.add_session_event(return_bindings)
            return return_bindings

    def add_key_popup(self):
        NewKeyPopup(self, self.frame, False)

    def get_sh_selection(self, event):
        self.current_selection2 = self.sh_treeview.identify_row(event.y)

    def get_dur_selection(self, event):
        self.current_selection1 = self.dur_treeview.identify_row(event.y)

    def get_freq_selection(self, event):
        self.current_selection = self.freq_treeview.identify_row(event.y)

    def import_binding(self):
        pass

    def save_binding(self):
        x = {
            "Name": self.keystroke_json["Name"],
            "Frequency": self.bindings,
            "Duration": self.dur_bindings
        }
        with open(self.key_file, 'w') as f:
            json.dump(x, f)

    def delete_freq_binding(self):
        if self.current_selection:
            self.bindings.pop(int(self.current_selection))
            clear_treeview(self.freq_treeview)
            self.populate_freq_bindings()

    def change_dur_keybind(self, event):
        selection = self.dur_treeview.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), True)

    def change_freq_keybind(self, event):
        selection = self.freq_treeview.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), False)

    def update_dur_keybind(self, tag, key):
        self.dur_bindings[key] = (self.dur_bindings[key][0], tag)
        self.dur_treeview.set(str(key), column="1", value=tag)

    def update_freq_keybind(self, tag, key):
        self.bindings[key] = (self.bindings[key][0], tag)
        self.freq_treeview.set(str(key), column="1", value=tag)

    def add_freq_keybind(self, tag, key):
        self.bindings.append((tag, key))
        self.bindings_freq.append(0)
        clear_treeview(self.freq_treeview)
        self.populate_freq_bindings()

    def add_dur_keybind(self, tag, key):
        self.dur_bindings.append((tag, key))
        clear_treeview(self.dur_treeview)
        self.populate_dur_bindings()

    def open_keystroke_file(self):
        with open(self.key_file) as f:
            self.keystroke_json = json.load(f)
        if len(self.keystroke_json) == 1:
            self.new_keystroke = True
        else:
            for key in self.keystroke_json:
                if key == "Frequency":
                    for binding in self.keystroke_json[key]:
                        self.bindings.append(binding)
                        self.bindings_freq.append(0)
                elif key == "Duration":
                    for binding in self.keystroke_json[key]:
                        self.dur_bindings.append(binding)
                elif key == "Conditions":
                    for binding in self.keystroke_json[key]:
                        self.conditions.append(binding)

    def populate_freq_bindings(self):
        for i in range(0, len(self.bindings)):
            bind = self.bindings[i]
            self.freq_treeview_parents.append(self.freq_treeview.insert("", 'end', text=str(bind[1]),
                                                                        values=(self.bindings_freq[i], bind[0]),
                                                                        tags=(treeview_bind_tags[i % 2])))

    def populate_dur_bindings(self):
        for i in range(0, len(self.dur_bindings)):
            bind = self.dur_bindings[i]
            self.dur_sticky.append(False)
            self.sticky_start.append(0)
            self.sticky_dur.append(0)
            self.dur_treeview_parents.append(self.dur_treeview.insert("", 'end', text=str(bind[1]),
                                                                      values=(0, 0, bind[0]),
                                                                      tags=(treeview_bind_tags[i % 2])))

    def populate_sh_bindings(self):
        if self.event_history:
            for i in range(0, len(self.event_history)):
                print(str(i))
                bind = self.event_history[i]
                self.sh_treeview_parents.append(self.sh_treeview.insert("", 'end', text=str(bind[0]),
                                                                        values=(bind[1]),
                                                                        tags=(treeview_bind_tags[i % 2])))


class NewKeyPopup:
    def __init__(self, top, root, dur_freq):
        self.caller = top
        self.dur_freq = dur_freq
        self.tag_entry = None
        self.key_entry = None
        self.popup_root = None
        self.patient_name_entry_pop_up(root)

    def patient_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = self.popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x100")
        popup_root.title("Enter New Binding")

        # Create an Entry Widget in the Toplevel window
        self.tag_label = Label(popup_root, text="Key Tag", bg='white')
        self.tag_label.place(x=30, y=20, anchor=W)
        self.tag_entry = Entry(popup_root, bd=2, width=25, bg='white')
        self.tag_entry.place(x=90, y=20, anchor=W)

        self.key_label = Label(popup_root, text="Key", bg='white')
        self.key_label.place(x=30, y=50, anchor=W)
        self.key_entry = Entry(popup_root, bd=2, width=25, bg='white')
        self.key_entry.place(x=90, y=50, anchor=W)

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win)
        button.place(x=150, y=70, anchor=N)

    def close_win(self):
        if len(self.key_entry.get()) == 1:
            if not self.dur_freq:
                self.caller.add_keybind(self.tag_entry.get(), self.key_entry.get())
            else:
                self.caller.add_durbind(self.tag_entry.get(), self.key_entry.get())
            self.popup_root.destroy()


class Popup:
    def __init__(self, top, root, tag, dur_key):
        self.caller = top
        self.dur_key = dur_key
        self.entry = None
        self.popup_root = None
        self.tag = tag
        self.patient_name_entry_pop_up(root)

    def patient_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = self.popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x50")
        popup_root.title("Enter New Key Bind")

        # Create an Entry Widget in the Toplevel window
        self.entry = Entry(popup_root, bd=2, width=25)
        self.entry.pack()

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)

    def close_win(self):
        if len(self.entry.get()) == 1:
            if not self.dur_key:
                self.caller.update_keybind(self.entry.get(), self.tag)
            else:
                self.caller.update_durbind(self.entry.get(), self.tag)
            self.popup_root.destroy()


class ViewTactor:
    pass
