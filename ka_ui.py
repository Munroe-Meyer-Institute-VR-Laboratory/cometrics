import os
import pathlib
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
from logger_util import *
import datetime
from PIL import Image, ImageTk
from patient_select_ui import PatientSelectWindow
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4


class StaticImages(Frame):
    def __init__(self, parent, **kw):
        super().__init__(**kw)
        self.unmc_shield_canvas = Canvas(parent, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)


class SessionTimeFields:
    def __init__(self, parent):
        pass


class PatientDataFields:
    def __init__(self, parent):
        pass


class EmpaticaDataFields:
    def __init__(self, parent):
        pass


class KeystrokeDataFields:
    def __init__(self, parent):
        pass


class PatientContainer:
    def __init__(self):
        self.patient_path = None
        self.patient_name = None
        self.medical_record_number = None

    def update_fields(self, filepath):
        self.patient_path = filepath


class Annotator:
    def __init__(self, patient_file):
        root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
        root.title("KSA - KeyStroke Annotator")
        StaticImages(root)
        root.mainloop()


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    # Get the patient
    UserSelection = PatientSelectWindow()
    # Check what the result was
    if not UserSelection.cancel:
        Annotator(UserSelection.patient_file)
