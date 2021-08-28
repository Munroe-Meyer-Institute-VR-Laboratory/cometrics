import os
import pathlib
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
import datetime
from PIL import Image, ImageTk
import pynput
# Custom library imports
from patient_select_ui import PatientSelectWindow
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4
from logger_util import *
from keystroke_file_ui import KeystrokeSelectWindow


class StaticImages(Frame):
    def __init__(self, parent, **kw):
        super().__init__(**kw)
        self.unmc_shield_canvas = Canvas(parent, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)


class SessionTimeFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=TOP, padx=5, pady=5)


class PatientDataFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)
        self.name_label = Label(self.frame, text="Patient Name")
        self.name_label.pack(side=TOP, padx=5, pady=5)


class EmpaticaDataFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)


class KeystrokeDataFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)


class PatientContainer:
    def __init__(self, patient_file):
        self.patient_json = None
        self.patient_path = None
        self.name = None
        self.medical_record_number = None
        self.age = None
        self.update_fields(patient_file)

    def update_fields(self, filepath):
        f = open(filepath)
        self.patient_json = json.load(f)
        self.name = self.patient_json["Name"]
        self.medical_record_number = self.patient_json["MRN"]
        self.age = self.patient_json["Age"]


class SessionManagerWindow:
    def __init__(self, patient_file, keystroke_file):
        root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
        root.title("KSA - KeyStroke Annotator")
        StaticImages(root)
        PatientDataFields(root)
        EmpaticaDataFields(root)
        KeystrokeDataFields(root)
        SessionTimeFields(root)
        root.mainloop()