import json
import os
import pathlib
from os import walk, path
import openpyxl
import csv
import datetime
from tkinter import *
from tkinter import filedialog, messagebox
import traceback

from ksf_utils import cal_acc
from tkinter_utils import center


class PatientContainer:
    def __init__(self, patient_file):
        self.source_file = patient_file
        self.patient_json = None
        self.patient_path = None
        self.name = None
        self.medical_record_number = None
        if patient_file:
            self.update_fields(patient_file)

    def update_fields(self, filepath):
        f = open(filepath)
        self.patient_json = json.load(f)
        self.name = self.patient_json["Name"]
        self.medical_record_number = self.patient_json["MRN"]

    def save_patient(self, name, mrn):
        with open(self.source_file, 'w') as f:
            x = {
                "Name": name,
                "MRN": mrn
            }
            json.dump(x, f)


class AccuracyPopup:
    def __init__(self, root, ksf, caller):
        self.caller = caller
        self.ksf = ksf
        self.root = root
        self.window_entry, self.prim_browse, self.rel_browse, self.acc_report, self.acc_button = None, None, None, None, None
        self.window_label = None
        self.popup = None
        self.window_var = None
        self.prim_filename, self.rel_filename, self.ksf_filename = r"", r"", r""
        self.generate_accuracy(root)

    def generate_accuracy(self, root):
        # Create a Toplevel window
        self.popup = popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x200")
        popup_root.title("Generate Accuracy")

        # self.ksf_browse = Button(self.popup, text="Keystroke File", command=self.select_ksf_file, width=15, bd=2)
        # self.ksf_browse.place(x=145, y=10, anchor=NE)
        # self.ksf_file_var = StringVar(self.popup)
        # self.ksf_filename = self.ksf
        # self.ksf_file_var.set(pathlib.Path(self.ksf).stem)
        # self.ksf_file_label = Label(self.popup, textvariable=self.ksf_file_var, width=16, bg='white')
        # self.ksf_file_label.place(x=150, y=20, anchor=W)

        self.window_label = Label(self.popup, text="Window Size (s)", bg='white')
        self.window_label.place(x=145, y=20, anchor=NE)

        self.window_var = StringVar(self.popup)
        self.window_var.set(str(10))
        self.window_entry = Entry(self.popup, bd=2, width=10, textvariable=self.window_var)
        self.window_entry.place(x=150, y=20)

        self.prim_browse = Button(self.popup, text="Primary File", command=self.select_prim_file, width=15, bd=2)
        self.prim_browse.place(x=145, y=50, anchor=NE)
        self.prim_file_var = StringVar(self.popup)
        self.prim_file_var.set("No File Chosen")
        self.prim_file_label = Label(self.popup, textvariable=self.prim_file_var, width=16, bg='white')
        self.prim_file_label.place(x=145, y=80, anchor=NE)

        self.rel_browse = Button(self.popup, text="Reliability File", command=self.select_rel_file, width=15, bd=2)
        self.rel_browse.place(x=155, y=50, anchor=NW)
        self.rel_file_var = StringVar(self.popup)
        self.rel_file_var.set("No File Chosen")
        self.rel_file_label = Label(self.popup, textvariable=self.rel_file_var, width=16, bg='white')
        self.rel_file_label.place(x=155, y=80, anchor=NW)

        self.acc_button = Button(self.popup, text="Calculate Accuracy", width=15, bd=2, command=self.calculate_acc)
        self.acc_button.place(x=150, y=110, anchor=N)

        self.acc_var = StringVar(self.popup)
        self.acc_var.set("Not Calculated")
        self.acc_report = Label(self.popup, textvariable=self.acc_var, width=16, bg='white')
        self.acc_report.place(x=150, y=140, anchor=N)
        center(popup_root)
        popup_root.focus_force()

    def calculate_acc(self):
        output_file = cal_acc(self.prim_filename, self.reli_filename, self.window_var.get(), self.caller.graph_dir)
        if output_file:
            self.acc_var.set(str(pathlib.Path(output_file).stem))
        os.startfile(pathlib.Path(output_file).parent)
        self.popup.focus_force()

    def select_prim_file(self):
        self.prim_filename = filedialog.askopenfilename(filetypes=(("Session Files", "*.json"), ("All Files", "*.*")))
        self.prim_file_var.set(pathlib.Path(self.prim_filename).stem)
        self.popup.focus_force()

    # def select_ksf_file(self):
    #     self.ksf_filename = filedialog.askopenfilename(filetype=(("Keystroke Files", "*.json"), ("All Files", "*.*")))
    #     self.ksf_file_var.set(pathlib.Path(self.ksf_filename).stem)
    #     self.popup.focus_force()

    def select_rel_file(self):
        self.reli_filename = filedialog.askopenfilename(filetypes=(("Session Files", "*.json"), ("All Files", "*.*")))
        self.rel_file_var.set(pathlib.Path(self.reli_filename).stem)
        self.popup.focus_force()

    def close_window(self):
        self.popup.destroy()
