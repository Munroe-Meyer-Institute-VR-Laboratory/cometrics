""" tkVideo: Python module for playing videos (without sound) inside tkinter Label widget using Pillow and imageio

Copyright © 2020 Xenofon Konitsas <konitsasx@gmail.com>
Released under the terms of the MIT license (https://opensource.org/licenses/MIT) as described in LICENSE.md

"""
import time
import moviepy.editor as mp
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
        self.frame_data = imageio.get_reader(path)
        if keep_ratio:
            temp = self.frame_data._get_data(0)[0].shape
            self.aspect_ratio = float(temp[1]) / float(temp[0])
            self.size = (size[0], int(size[0] * self.aspect_ratio))
        else:
            self.size = size
        self.slider = slider

    def load_frame(self, frame):
        image, met = self.frame_data._get_data(int(frame))
        frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize(self.size))
        self.label.config(image=frame_image)
        self.label.image = frame_image
        if self.slider:
            self.slider.set(frame)

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

    def iter_data_index(self, path, label, frame, slider):
        """ iter_data()
        Iterate over all images in the series. (Note: you can also
        iterate over the reader object.)
        """
        frame_data = imageio.get_reader(path)
        delay = float(1 / frame_data.get_meta_data()['fps'])
        frame_data._checkClosed()
        n = frame_data.get_length()
        i = frame
        while i < n:
            try:
                im, meta = frame_data._get_data(i)
            except StopIteration:
                return
            except IndexError:
                if n == float("inf"):
                    return
                raise
            frame_image = ImageTk.PhotoImage(Image.fromarray(im).resize(self.size))
            label.config(image=frame_image)
            label.image = frame_image
            if slider:
                slider.set(i)
            i += 1
            time.sleep(delay)

    def play(self, start_frame=None):
        """
            Creates and starts a thread as a daemon that plays the video by rapidly going through
            the video's frames.
        """
        if not start_frame:
            thread = threading.Thread(target=self.iter_data_index, args=(self.path, self.label, start_frame))
        else:
            thread = threading.Thread(target=self.load, args=(self.path, self.label, self.loop))
        thread.daemon = 1
        thread.start()
