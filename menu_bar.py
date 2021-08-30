from tkinter import *


class MenuBar(Frame):
    def __init__(self, parent, *args, **kwargs):
        Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.retrain_thread = None
        menu = Menu(self.parent)
        self.parent.config(menu=menu)
        self.preload_thread = None

        fileMenu = Menu(menu)
        # fileMenu.add_command(label="Preload Videos", command=self.preload_videos)
        # fileMenu.add_command(label="Exit", command=self.exit_program)
        menu.add_cascade(label="File", menu=fileMenu)

        editMenu = Menu(menu)
        # editMenu.add_command(label="Load Violence Model", command=self.load_violence_model)
        # editMenu.add_command(label="Train Selected Model", command=self.retrain_model)
        # editMenu.add_command(label="Convert Model to TFLite", command=self.convert_model_to_tflite)
        menu.add_cascade(label="ML", menu=editMenu)
