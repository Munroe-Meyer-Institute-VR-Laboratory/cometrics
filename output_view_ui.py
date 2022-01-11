import json
import pickle
import threading
import time
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
from pyempatica.empaticae4 import EmpaticaE4, EmpaticaDataStreams, EmpaticaClient
import traceback
from gif_player import ImageLabel

# Custom library imports
from tkinter_utils import build_treeview
from ui_params import treeview_bind_tag_dict


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

        self.e4_view = ViewE4(self.view_frames[OutputViews.E4_VIEW])
        self.key_view = KeystrokeDataFields(self.view_frames[OutputViews.KEY_VIEW], ksf, self.height, self.width,
                                            field_font=field_font, header_font=header_font, button_size=button_size)
        self.edf_view = EmpaticaDataFields(self.view_frames[OutputViews.E4_VIEW], self, self.height, self.width,
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


class ViewE4:
    def __init__(self, root):
        self.root = root
        self.session_started = False
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
        self.hr_canvas.place(x=90, y=10)
        self.hr_image = PhotoImage(file='images/heartrate.png')
        self.hr_canvas.create_image(0, 0, anchor=NW, image=self.hr_image)

        self.hr_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.hr_label.place(x=140, y=20, anchor=NW)

        self.temp_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.temp_canvas.place(x=240, y=10)
        self.temp_image = PhotoImage(file='images/thermometer.png')
        self.temp_canvas.create_image(0, 0, anchor=NW, image=self.temp_image)

        self.temp_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.temp_label.place(x=290, y=20, anchor=NW)

        self.wrist_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.wrist_canvas.place(x=390, y=10, anchor=NW)
        self.on_wrist_image = PhotoImage(file='images/onwrist.png')
        self.off_wrist_image = PhotoImage(file='images/offwrist.png')
        self.wrist_container = self.wrist_canvas.create_image(20, 20, anchor=CENTER, image=self.off_wrist_image)
        self.wrist = False

        self.wrist_label = Label(self.root, text="Off", font=("TkDefaultFont", 12))
        self.wrist_label.place(x=440, y=20, anchor=NW)

        self.bat_image_100 = PhotoImage(file='images/battery100.png')
        self.bat_image_75 = PhotoImage(file='images/battery75.png')
        self.bat_image_50 = PhotoImage(file='images/battery50.png')
        self.bat_image_25 = PhotoImage(file='images/battery25.png')
        self.bat_canvas = Canvas(self.root, width=40, height=40, bg=fig_color, bd=-2)
        self.bat_canvas.place(x=540, y=10)
        self.bat_container = self.bat_canvas.create_image(20, 20, anchor=CENTER, image=self.bat_image_100)

        self.bat_label = Label(self.root, text="N/A", font=("TkDefaultFont", 12))
        self.bat_label.place(x=590, y=20, anchor=NW)

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

        self.save_reading = False
        self.streaming = False
        self.kill = False
        self.e4 = None
        self.bat = 100
        self.windowed_readings = []
        self.update_thread = threading.Thread(target=self.update_labels_thread)

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
        self.height, self.width = height, width
        self.frame = parent
        self.keystroke_json = None
        self.new_keystroke = False
        self.bindings = []
        self.event_history = []
        self.dur_bindings = []
        self.bindings_freq = []
        self.key_file = keystroke_file
        self.conditions = []
        self.open_keystroke_file()
        self.freq_strings = []
        self.freq_key_strings = []

        self.dur_sticky = []
        self.sticky_start = []
        self.sticky_dur = []

        keystroke_label = Label(self.frame, text="Frequency Bindings", font=header_font)
        keystroke_label.place(x=(width * 0.25) - 30, y=15, anchor=CENTER)

        freq_heading_dict = {"#0": ["Char", 'c', 1, YES, 'c']}
        freq_column_dict = {"1": ["Freq", 'c', 1, YES, 'c'],
                            "2": ["Tag", 'c', 1, YES, 'c']}
        self.freq_treeview, self.freq_filescroll = build_treeview(self.frame,
                                                                  x=(width * 0.25) - 30, y=30,
                                                                  height=height - 100, width=width * 0.25,
                                                                  column_dict=freq_column_dict,
                                                                  heading_dict=freq_heading_dict,
                                                                  button_1_bind=self.get_selection,
                                                                  double_bind=self.change_keybind,
                                                                  anchor=N,
                                                                  tag_dict=treeview_bind_tag_dict,
                                                                  fs_offset=10 + ((width * 0.25) * 0.5))

        # self.delete_button = Button(self.frame, text="Delete Key", command=self.delete_binding, width=8)
        # self.delete_button.place(x=20, y=height - 340, anchor=NW)
        #
        # self.add_button = Button(self.frame, text="Add Key", command=self.add_key_popup, width=9)
        # self.add_button.place(x=125, y=height - 340, anchor=N)
        #
        # self.save_button = Button(self.frame, text="Save File", command=self.save_binding, width=8)
        # self.save_button.place(x=230, y=height - 340, anchor=NE)

        self.tree_parents = []
        self.tags = ['odd', 'even', 'toggle']
        self.current_selection = "I000"

        dur_label = Label(self.frame, text="Duration Bindings", font=header_font)
        dur_label.place(x=width * 0.5, y=15, anchor=CENTER)

        dur_heading_dict = {"#0": ["Char", 'c', 1, YES, 'c']}
        dur_column_dict = {"1": ["Dur", 'c', 1, YES, 'c'],
                           "2": ["Total", 'c', 1, YES, 'c'],
                           "3": ["Tag", 'c', 1, YES, 'c']}
        self.dur_treeview, self.dur_filescroll = build_treeview(self.frame,
                                                                x=width * 0.5, y=30,
                                                                height=height - 100, width=width * 0.25,
                                                                column_dict=dur_column_dict,
                                                                heading_dict=dur_heading_dict,
                                                                button_1_bind=self.get_selection1,
                                                                double_bind=self.change_keybind1,
                                                                anchor=N,
                                                                tag_dict=treeview_bind_tag_dict,
                                                                fs_offset=10 + ((width * 0.25) * 0.5))

        self.tree_parents1 = []
        self.current_selection1 = "I000"

        # self.delete_button1 = Button(self.frame, text="Delete Key", command=self.delete_dur_binding, width=8)
        # self.delete_button1.place(x=250, y=height - 340)
        #
        # self.add_button1 = Button(self.frame, text="Add Key", command=self.add_dur_popup, width=9)
        # self.add_button1.place(x=355, y=height - 340, anchor=N)
        #
        # self.save_button1 = Button(self.frame, text="Save File", command=self.save_binding, width=8)
        # self.save_button1.place(x=460, y=height - 340, anchor=NE)

        sh_label = Label(self.frame, text="Session History", font=header_font)
        sh_label.place(x=(width * 0.75) + 30, y=15, anchor=CENTER)

        sh_heading_dict = {"#0": ["Event", 'c', 1, YES, 'c']}
        sh_column_dict = {"1": ["Time", 'c', 1, YES, 'c']}
        self.sh_treeview, self.sh_filescroll = build_treeview(self.frame,
                                                              x=(width * 0.75) + 30, y=30,
                                                              height=height - 100, width=width * 0.25,
                                                              column_dict=sh_column_dict,
                                                              heading_dict=sh_heading_dict,
                                                              double_bind=self.delete_event,
                                                              anchor=N,
                                                              tag_dict=treeview_bind_tag_dict,
                                                              fs_offset=10 + ((width * 0.25) * 0.5))

        self.tree_parents2 = []
        self.current_selection2 = "I000"

        self.key_explanation = Label(self.frame, font=field_font, text="Delete Last Event: Backspace"
                                                                       "\nDouble Click Any Event to Delete"
                                                                       "\nUndo Delete: +/= Button", justify=LEFT)
        self.key_explanation.place(x=((width * 0.75) + 30) - ((width * 0.25) * 0.5), y=height - 70, anchor=NW)

        # self.populate_bindings()
        # self.populate_bindings1()
        # self.populate_bindings2()

    def add_session_event(self, events):
        for event in events:
            if type(event[1]) is list:
                start_time = int(event[1][1]) - int(event[1][0])
            else:
                start_time = event[1]
            self.event_history.append(event)
            self.tree_parents2.append(self.treeview2.insert("", 'end', str(len(self.event_history)),
                                                            values=(self.event_history[-1][0], start_time),
                                                            tags=(self.tags[len(self.event_history) % 2])))
        self.treeview2.see(self.tree_parents2[-1])

    def delete_event(self, event):
        self.current_selection2 = self.treeview2.identify_row(event.y)
        if self.current_selection2:
            index = self.tree_parents2.index(str(self.current_selection2))
            self.treeview2.delete(self.tree_parents2[index])
            self.tree_parents2.pop(index)
            self.event_history.pop(index)

    def delete_last_event(self):
        if self.event_history:
            self.treeview2.delete(self.tree_parents2[len(self.event_history) - 1])
            self.tree_parents2.pop(len(self.event_history) - 1)
            self.event_history.pop(len(self.event_history) - 1)

    def delete_dur_binding(self):
        if self.current_selection1:
            self.dur_bindings.pop(int(self.current_selection1))
            self.clear_listbox1()
            self.populate_bindings1()

    def add_dur_popup(self):
        NewKeyPopup(self, self.frame, True)

    def check_key(self, key_char, start_time):
        return_bindings = []
        for i in range(0, len(self.bindings)):
            if self.bindings[i][1] == key_char:
                self.bindings_freq[i] += 1
                self.treeview.set(str(i), column="2", value=self.bindings_freq[i])
                return_bindings.append((self.bindings[i][0], start_time))
        for i in range(0, len(self.dur_bindings)):
            if self.dur_bindings[i][1] == key_char:
                if self.dur_sticky[i]:
                    self.treeview1.item(str(i), tags=self.tags[i % 2])
                    self.dur_sticky[i] = False
                    duration = [self.sticky_start[i], start_time]
                    return_bindings.append((self.dur_bindings[i][0], duration))
                    self.sticky_dur[i] += start_time - self.sticky_start[i]
                    self.sticky_start[i] = 0
                    self.treeview1.set(str(i), column="3", value=self.sticky_dur[i])
                else:
                    self.treeview1.item(str(i), tags=self.tags[2])
                    self.dur_sticky[i] = True
                    self.sticky_start[i] = start_time
        if return_bindings:
            self.add_session_event(return_bindings)
            return return_bindings

    def add_key_popup(self):
        NewKeyPopup(self, self.frame, False)

    def get_selection2(self, event):
        self.current_selection2 = self.treeview2.identify_row(event.y)

    def get_selection1(self, event):
        self.current_selection1 = self.treeview1.identify_row(event.y)

    def get_selection(self, event):
        self.current_selection = self.treeview.identify_row(event.y)

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

    def delete_binding(self):
        if self.current_selection:
            self.bindings.pop(int(self.current_selection))
            self.clear_listbox()
            self.populate_bindings()

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

    def change_keybind1(self, event):
        selection = self.treeview1.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), True)

    def change_keybind(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), False)

    def update_durbind(self, tag, key):
        self.dur_bindings[key] = (self.dur_bindings[key][0], tag)
        self.treeview1.set(str(key), column="1", value=tag)

    def update_keybind(self, tag, key):
        self.bindings[key] = (self.bindings[key][0], tag)
        self.treeview.set(str(key), column="1", value=tag)

    def add_keybind(self, tag, key):
        self.bindings.append((tag, key))
        self.bindings_freq.append(0)
        self.clear_listbox()
        self.populate_bindings()

    def add_durbind(self, tag, key):
        self.dur_bindings.append((tag, key))
        self.clear_listbox1()
        self.populate_bindings1()

    def clear_listbox2(self):
        for children in self.treeview2.get_children():
            self.treeview2.delete(children)

    def clear_listbox1(self):
        for children in self.treeview1.get_children():
            self.treeview1.delete(children)

    def clear_listbox(self):
        for children in self.treeview.get_children():
            self.treeview.delete(children)

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

    def populate_bindings(self):
        for i in range(0, len(self.bindings)):
            bind = self.bindings[i]
            self.tree_parents.append(self.treeview.insert("", 'end', str(i),
                                                          values=(bind[1], self.bindings_freq[i], bind[0]),
                                                          tags=(self.tags[i % 2])))

    def populate_bindings1(self):
        for i in range(0, len(self.dur_bindings)):
            bind = self.dur_bindings[i]
            self.dur_sticky.append(False)
            self.sticky_start.append(0)
            self.sticky_dur.append(0)
            self.tree_parents1.append(self.treeview1.insert("", 'end', str(i),
                                                            values=(bind[1], 0, 0, bind[0]),
                                                            tags=(self.tags[i % 2])))

    def populate_bindings2(self):
        if self.event_history:
            for i in range(0, len(self.event_history)):
                print(str(i))
                bind = self.event_history[i]
                self.tree_parents2.append(self.treeview2.insert("", 'end', str(i),
                                                                values=(bind[0], bind[1]),
                                                                tags=(self.tags[i % 2])))


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


class EmpaticaDataFields:
    def __init__(self, parent, output_view, height, width,
                 field_font, header_font, button_size):
        self.height, self.width = height, width
        self.ovu = output_view
        self.parent = parent
        self.frame = Frame(parent, width=250, height=(height - 280))
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
        self.treeview.place(x=20, y=65, height=(height - 450), width=210)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="E4 Name")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_selection)

        self.file_scroll = Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=65, height=(height - 450))

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.connect_button = Button(self.frame, text="Connect", command=self.connect_to_e4, width=12)
        self.connect_button.place(x=20, y=(height - 385))

        self.streaming_button = Button(self.frame, text="Stream", command=self.start_e4_streaming, width=12)
        self.streaming_button.place(x=230, y=(height - 385), anchor=NE)

        self.connected_label = Label(self.frame, text="CONNECTED", fg='green')
        self.streaming_label = Label(self.frame, text="STREAMING", fg='green')

        self.error_thread = None
        self.devices_thread = None

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
                    self.connected_label.place_forget()
                    self.streaming_label.place_forget()
                    self.e4_client = None
                else:
                    self.e4_client = EmpaticaE4(self.e4_address)
                    if self.e4_client.connected:
                        if self.error_thread is None:
                            self.error_thread = threading.Thread(target=self.check_e4_error)
                            self.error_thread.start()
                        for stream in EmpaticaDataStreams.ALL_STREAMS:
                            self.e4_client.subscribe_to_stream(stream)
                        self.connected_label.place(x=125, y=(self.height - 350), anchor=N)
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
                        self.ovu.e4_view.start_plot(self.e4_client)
                        self.streaming_label.place(x=125, y=(self.height - 320), anchor=N)
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


class ViewTactor:
    pass
