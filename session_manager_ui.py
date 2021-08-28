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
    def __init__(self, parent, patient_file):
        self.patient = PatientContainer(patient_file)
        self.frame = Frame(parent, width=250, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)
        # Create label canvas
        self.label_canvas = Canvas(self.frame, width=250, height=500)
        # Frame Information
        self.frame_info = self.label_canvas.create_text(125, 10, text="Patient Information", anchor=CENTER,
                                                        font=('Purisa', 12))
        # Patient name field
        self.name_label = self.label_canvas.create_text(5, 30, text="Name", anchor=NW,
                                                        font=('Purisa', 10))
        # Patient MRN field
        self.mrn_label = self.label_canvas.create_text(5, 75, text="Medical Record Number", anchor=NW,
                                                       font=('Purisa', 10))
        # Session date field
        # self.date_label = self.label_canvas.create_text(5, 120, text="Session Date",
        #                                                 font=('Purisa', 10))
        # Session start time field
        # self.start_label = self.label_canvas.create_text(5, 165, text="Session Start Time", anchor=NW,
        #                                                  font=('Purisa', 10))
        # Session number field
        # self.sess_number_label = self.label_canvas.create_text(5, 210, text="Session Number", anchor=NW,
        #                                                        font=('Purisa', 10))
        # Session location field
        self.sess_loc_label = self.label_canvas.create_text(5, 120, text="Session Location", anchor=NW,
                                                            font=('Purisa', 10))
        # Assessment name field
        self.assess_name_label = self.label_canvas.create_text(5, 165, text="Assessement Name", anchor=NW,
                                                               font=('Purisa', 10))
        # Condition name field
        self.cond_name_label = self.label_canvas.create_text(5, 210, text="Condition Name", anchor=NW,
                                                             font=('Purisa', 10))
        # Primary therapist field
        self.prim_ther_label = self.label_canvas.create_text(5, 255, text="Primary Therapist Name", anchor=NW,
                                                             font=('Purisa', 10))
        # Case manager field
        self.case_mgr_label = self.label_canvas.create_text(5, 300, text="Case Manager Name", anchor=NW,
                                                            font=('Purisa', 10))
        # Session therapist field
        self.sess_ther_label = self.label_canvas.create_text(5, 345, text="Session Therapist Name", anchor=NW,
                                                             font=('Purisa', 10))
        # Data recorder name
        self.data_rec_label = self.label_canvas.create_text(5, 390, text="Data Recorder Name", anchor=NW,
                                                            font=('Purisa', 10))
        # Primary data field
        self.prim_data_label = self.label_canvas.create_text(5, 435, text="Primary or Reliability Data", anchor=NW,
                                                             font=('Purisa', 10))
        # Setup input variables
        self.patient_name_var = StringVar(self.frame)
        if self.patient.name:
            self.patient_name_var.set(self.patient.name)
        self.name_field = Entry(self.frame, textvariable=self.patient_name_var)
        self.name_field.place(x=15, y=50, width=220, anchor=NW)
        self.label_canvas.pack()


class EmpaticaDataFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)


class KeystrokeDataFields:
    def __init__(self, parent, keystroke_file):
        self.frame = Frame(parent, width=350, height=500)
        self.frame.pack(side=LEFT, padx=5, pady=5)


class PatientContainer:
    def __init__(self, patient_file):
        self.patient_json = None
        self.patient_path = None
        self.name = None
        self.medical_record_number = None
        self.age = None
        if patient_file:
            self.update_fields(patient_file)

    def update_fields(self, filepath):
        f = open(filepath)
        self.patient_json = json.load(f)
        self.name = self.patient_json["Name"]
        self.medical_record_number = self.patient_json["MRN"]
        self.age = self.patient_json["Age"]


class SessionManagerWindow:
    def __init__(self, patient_file, keystroke_file):
        parts = keystroke_file.split('/')[:-2]
        self.session_files = []
        self.session_file = None
        self.session_dir = path.join(parts[0], parts[1], parts[2], 'sessions')
        self.session_number = 1
        self.get_session_file(self.session_dir)
        root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
        root.title("KSA - KeyStroke Annotator")
        StaticImages(root)
        PatientDataFields(root, patient_file)
        EmpaticaDataFields(root)
        KeystrokeDataFields(root, keystroke_file)
        # SessionTimeFields(root)
        root.mainloop()

    def get_session_file(self, directory):
        if path.isdir(self.session_dir):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.session_number += 1
            self.session_file = open(path.join(directory, 'session_' + str(self.session_number) + '.json'))
        else:
            os.mkdir(directory)
