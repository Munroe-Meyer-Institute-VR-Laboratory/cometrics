""" tkVideo: Python module for playing videos (without sound) inside tkinter Label widget using Pillow and imageio

Copyright © 2020 Xenofon Konitsas <konitsasx@gmail.com>
Released under the terms of the MIT license (https://opensource.org/licenses/MIT) as described in LICENSE.md

"""
import time
try:
    import Tkinter as tk  # for Python2 (although it has already reached EOL)
except ImportError:
    import tkinter as tk  # for Python3
import threading
import imageio
from PIL import Image, ImageTk


class tkvideo():
    """
        Main class of tkVideo. Handles loading and playing
        the video inside the selected label.

        :keyword path:
            Path of video file
        :keyword label:
            Name of label that will house the player
        :param loop:
            If equal to 0, the video only plays once,
            if not it plays in an infinite loop (default 0)
        :param size:
            Changes the video's dimensions (2-tuple,
            default is 640x360)
    """

    def __init__(self, path, label, loop=False, size=(640, 360), slider=None, keep_ratio=False):
        self.path = path
        self.label = label
        self.loop = loop
        self.playing = False
        self.frame_data = imageio.get_reader(path)
        self.meta_data = self.frame_data.get_meta_data()
        self.fps = self.meta_data['fps']
        self.nframes = self.frame_data.count_frames()
        if self.nframes == float("inf"):
            self.nframes = int(float(self.fps) * float(self.meta_data['duration']))
        self.current_frame = 0
        if keep_ratio:
            temp = self.frame_data._get_data(0)[0].shape
            self.aspect_ratio = float(temp[1]) / float(temp[0])
            self.size = (size[0], int(size[0] / self.aspect_ratio))
        else:
            self.size = size
        self.slider = slider
        if self.slider:
            self.slider.config(from_=1, to=self.nframes)
            self.slider.set(1)

    def load_frame(self, frame):
        image, met = self.frame_data._get_data(int(frame))
        frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize(self.size))
        self.label.config(image=frame_image)
        self.label.image = frame_image
        self.current_frame = int(frame)

    def load(self, path, label, loop):
        """
            Loads the video's frames recursively onto the selected label widget's image parameter.
            Loop parameter controls whether the function will run in an infinite loop
            or once.
        """
        frame_data = imageio.get_reader(path)

        if loop:
            while True:
                for image in frame_data.iter_data():
                    frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize(self.size))
                    label.config(image=frame_image)
                    label.image = frame_image
        else:
            for image in frame_data.iter_data():
                frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize(self.size))
                label.config(image=frame_image)
                label.image = frame_image

    def stop_playing(self):
        if self.playing:
            self.playing = False

    def iter_data_index(self, path, label, frame, fps, slider):
        """ iter_data()
        Iterate over all images in the series. (Note: you can also
        iterate over the reader object.)
        """
        frame_data = imageio.get_reader(path)
        frame_data._checkClosed()
        n = frame_data.get_length()
        i = int(frame)
        self.playing = True
        while i < n:
            try:
                im, meta = frame_data._get_data(i)
                self.current_frame = i
            except StopIteration as e:
                print(str(e))
                self.playing = False
                return
            except IndexError as e:
                print(str(e))
                self.playing = False
                if n == float("inf"):
                    return
                raise
            frame_image = ImageTk.PhotoImage(Image.fromarray(im).resize(self.size))
            label.config(image=frame_image)
            # label.image = frame_image
            i += 1
            if slider:
                slider.set(i)
            if not self.playing:
                break
        self.playing = False

    def play(self):
        """
            Creates and starts a thread as a daemon that plays the video by rapidly going through
            the video's frames.
        """
        if self.current_frame == self.nframes - 1:
            self.current_frame = 0
        thread = threading.Thread(target=self.iter_data_index,
                                  args=(self.path, self.label, self.current_frame, self.fps, self.slider))
        thread.daemon = 1
        thread.start()
