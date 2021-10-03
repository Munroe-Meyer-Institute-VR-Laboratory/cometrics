import datetime
import threading
import time
from tkinter import *
from tkinter import filedialog

from tkvideo import tkvideo
from video_loader import VideoLoader
import cv2
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure

from gif_player import ImageLabel


# Custom library imports


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

        # video_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        # test_label = Label(video_frame, text="Video Frame")
        # test_label.place(x=200, y=200)
        # self.view_frames.append(video_frame)
        #
        # camera_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        # test_label = Label(camera_frame, text="Camera Frame")
        # test_label.place(x=200, y=200)
        # self.view_frames.append(camera_frame)

        # tactor_frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 280))
        # test_label = Label(tactor_frame, text="Tactor Frame")
        # test_label.place(x=200, y=200)
        # self.view_frames.append(tactor_frame)

        e4_output_button = Button(self.frame, text="E4 Streams", command=self.switch_e4_frame, width=12)
        self.view_buttons.append(e4_output_button)
        self.view_buttons[0].place(x=0, y=0)
        self.view_buttons[0].config(relief=SUNKEN)

        # video_view_button = Button(self.frame, text="Annotate Video", command=self.switch_video_frame, width=12)
        # self.view_buttons.append(video_view_button)
        # self.view_buttons[1].place(x=92, y=0)

        # camera_view_button = Button(self.frame, text="Video Capture", command=self.switch_camera_frame, width=12)
        # self.view_buttons.append(camera_view_button)
        # self.view_buttons[2].place(x=184, y=0)

        # tactor_view_button = Button(self.frame, text="Tactor View", command=self.switch_tactor_frame, width=12)
        # self.view_buttons.append(tactor_view_button)
        # self.view_buttons[3].place(x=276, y=0)

        clean_view = Frame(self.frame, width=(700-(92*len(self.view_buttons))+2), height=25, bg='white')
        clean_view.place(x=(92*len(self.view_buttons))+2, y=0)

        self.e4_view = ViewE4(self.view_frames[OutputViews.E4_VIEW])
        # self.video_view = ViewVideo(self.view_frames[OutputViews.VIDEO_VIEW])

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

    def stop_plot(self):
        self.streaming = False
        self.kill = True

    def start_plot(self, e4):
        self.e4 = e4
        self.streaming = True
        self.update_thread.start()

    def update_labels_thread(self):
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


class ViewTactor:
    pass


class ViewVideo:
    def __init__(self, parent):
        fig_color = '#%02x%02x%02x' % (240, 240, 237)
        self.parent = parent
        self.current_frame = None

        self.new_video_button = Button(self.parent, text="Select Video", font=('Purisa', 11),
                                       command=self.open_video)
        self.new_video_button.place(x=50, y=50, anchor=W)

        self.play_image = ImageTk.PhotoImage(Image.open(r'images/play.jpg').resize((30, 30), Image.ANTIALIAS))
        self.pause_image = ImageTk.PhotoImage(Image.open(r'images/pause.jpg').resize((30, 30), Image.ANTIALIAS))

        self.play_button = Button(self.parent, width=30, height=30, image=self.play_image, command=self.toggle_video)
        self.play_button.place(x=350, y=540, anchor=N)

        # self.pause_button = Button(self.parent, width=30, height=30, image=self.pause_image, command=self.toggle_video)
        # self.pause_button.place(x=350, y=540, anchor=N)
        self.frame_img = ImageTk.PhotoImage(Image.open('images/mmi_logo.jpg'), Image.ANTIALIAS)
        self.video_label = Label(self.parent, width=600, height=400, bg="white", bd=-2, image=self.frame_img)
        self.video_label.place(x=350, y=100, anchor=N)

        self.slider = Scale(parent, from_=0, to=0, orient=HORIZONTAL, bg=fig_color, length=600,
                            command=self.update_frame)
        self.slider.place(x=350, y=500, anchor=N)

        self.frame_title = Label(self.parent, text="Current Video: ", bg=fig_color,
                                 font=('Purisa', 11))
        self.frame_title.place(x=50, y=100, anchor=SW)

        self.loading_screen = ImageLabel(self.video_label)

        self.video_playing = False
        self.frame_number = 0
        self.fps = 0
        self.frame_delay = 0
        self.frame_imgs = []
        self.loaded_video = None
        self.video_thread, self.load_thread = None, None

    def toggle_video(self):
        if not self.video_playing:
            self.video_playing = True
            self.play_button['image'] = self.pause_image
            self.play_video()
        else:
            self.video_playing = False
            self.loaded_video.stop_playing()
            self.play_button['image'] = self.play_image

    def open_video(self):
        video_path = filedialog.askopenfilename(filetypes=(("Video Files", (".avi", ".mov", ".mpg", ".mpeg", ".mp4", ".mkv", ".wmv")), ("All Files", "*.*")))
        if video_path:
            self.video_label.config(image='')
            self.load_loading()
            self.frame_title['text'] = "Current Video: " + video_path
            self.loaded_video = tkvideo(video_path, self.video_label, slider=self.slider, size=(600, 400), keep_ratio=True)
            self.update_frame(0)
            self.unload_loading()

    def unload_loading(self):
        self.loading_screen.unload()
        self.loading_screen.place_forget()

    def load_loading(self):
        self.loading_screen.place(x=100, y=0, anchor=NW)
        self.loading_screen.load(r'images\loading.gif', (400, 400))

    def update_frame_slider(self):
        self.slider.config(from_=1, to=self.frame_number)
        self.slider.set(1)

    def set_frame_slider(self, frame):
        self.slider.set(frame)

    def play_video(self):
        self.loaded_video.play()

    # def play_video_thread(self, start_frame):
    #     for i in range(start_frame, self.frame_number + 1):
    #         self.update_frame(i)
    #         self.sleep(self.frame_delay)
    #         if not self.video_playing:
    #             break
    #     if self.video_playing:
    #         self.toggle_video()

    def update_frame(self, frame):
        self.loaded_video.load_frame(frame)

    # def get_frame(self, frame):
    #     temp_frame = self.loaded_video.read()
    #     if temp_frame is not None:
    #         temp_frame = cv2.cvtColor(temp_frame, cv2.COLOR_BGR2RGB)
    #         temp_frame = Image.fromarray(temp_frame)
    #         self.frame_img = temp_frame.resize((800, 600), Image.ANTIALIAS)
    #         self.frame_img = ImageTk.PhotoImage(self.frame_img)
    #         self.frame_canvas.itemconfig(self.video_frame, image=self.frame_img)
    #     else:
    #         print(datetime.datetime.now().strftime("%c:"), "Invalid frame index chosen:", frame)
    #
    # def load_frames(self, video_path):
    #     loaded_video = cv2.VideoCapture(video_path)
    #     success, frame = loaded_video.read()
    #     self.fps, self.frame_delay, self.frame_number = 0, 0, 0
    #     self.frame_imgs = []
    #     while success:
    #         self.frame_number += 1
    #         temp_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         temp_frame = Image.fromarray(temp_frame)
    #         temp_frame = temp_frame.resize((800, 600), Image.ANTIALIAS)
    #         temp_frame = ImageTk.PhotoImage(temp_frame)
    #         self.frame_imgs.append(temp_frame)
    #         success, frame = loaded_video.read()
    #     self.fps = loaded_video.get(cv2.CAP_PROP_FPS)
    #     self.frame_delay = 1.0 / float(self.fps)
    #     self.update_frame(0)
    #     self.update_frame_slider()
    #     self.unload_loading()
    #     print("Video Params | Frame Count:", len(self.frame_imgs), "| FPS:", self.fps,
    #           "| Frame Delay:", self.frame_delay)


class ViewCamera:
    pass
