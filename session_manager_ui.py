import os
import pathlib
import time
from os import walk
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style
import json
import datetime
from PIL import Image, ImageTk
import threading
from pynput import keyboard
import winsound
# Custom library imports
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams
from logger_util import *
from output_view_ui import OutputViewPanel
from input_view_ui import KeystrokeDataFields, EmpaticaDataFields


class SessionTimeFields:
    def __init__(self, caller, parent):
        self.caller = caller
        self.frame = Frame(parent, width=600, height=100, bg='white')
        self.frame.place(x=252, y=2)

        self.session_started = False
        self.session_paused = False
        self.timer_running = True
        self.ui_timer_running = True
        self.update_ui = False

        self.session_time = 0
        self.break_time = 0
        self.session_time_label = Label(self.frame, text="Session Time:  0:00:00", bg='white',
                                        font=('Purisa', 14))
        self.session_time_label.place(x=20, y=10)

        self.break_time_label = Label(self.frame, text="Break Time:      0:00:00", bg='white',
                                      font=('Purisa', 14))
        self.break_time_label.place(x=20, y=38)

        self.session_start_label = Label(self.frame, text="Session Started", bg='white', fg='green',
                                         font=('Purisa', 14))
        self.session_paused_label = Label(self.frame, text="Session Paused", bg='white', fg='yellow',
                                          font=('Purisa', 14))
        self.session_stopped_label = Label(self.frame, text="Session Stopped", bg='white', fg='red',
                                           font=('Purisa', 14))
        self.session_stopped_label.place(x=20, y=66)

        self.interval_selection = IntVar()
        self.interval_checkbutton = Checkbutton(self.frame, text="Reminder Beep (Seconds)",
                                                variable=self.interval_selection, bg='white',
                                                font=('Purisa', 14), command=self.show_beep_interval)
        self.interval_checkbutton.place(x=250, y=6)
        self.interval_input_var = StringVar()

        interval_cmd = self.frame.register(self.validate_number)
        self.interval_input = Entry(self.frame, validate='all', validatecommand=(interval_cmd, '%P'),
                                    font=('Purisa', 14), bg='white', width=6)

        session_cmd = self.frame.register(self.validate_number)
        self.session_dur_input = Entry(self.frame, validate='all', validatecommand=(session_cmd, '%P'),
                                       font=('Purisa', 14), bg='white', width=6)

        self.session_dur_selection = IntVar()
        self.session_dur_checkbutton = Checkbutton(self.frame, text="Session Duration (Seconds)",
                                                   variable=self.session_dur_selection, bg='white',
                                                   font=('Purisa', 14),
                                                   command=self.show_session_time)
        self.session_dur_checkbutton.place(x=250, y=34)

        self.session_duration = None
        self.beep_th = None
        self.interval_thread = None

        self.time_thread = threading.Thread(target=self.time_update_thread)
        self.time_thread.start()

    @staticmethod
    def validate_number(char):
        if str.isdigit(char) or char == "":
            return True
        return False

    def beep_interval_thread(self):
        interval = int(self.interval_input.get())
        while self.session_started:
            time.sleep(interval)
            if not self.session_paused and self.session_started:
                self.beep_th = threading.Thread(target=beep_thread)
                self.beep_th.start()

    def show_session_time(self):
        if self.session_dur_selection.get():
            self.session_dur_input.place(x=530, y=38)
        else:
            self.session_dur_input.place_forget()

    def show_beep_interval(self):
        if self.interval_selection.get():
            self.interval_input.place(x=530, y=10)
        else:
            self.interval_input.place_forget()

    def time_update_thread(self):
        while self.timer_running:
            time.sleep(1 - time.monotonic() % 1)
            if self.timer_running:
                if self.session_started and not self.session_paused:
                    if self.break_time > 0:
                        self.break_time = 0
                    self.session_time += 1
                    if self.session_duration:
                        if self.session_time >= self.session_duration:
                            self.stop_session()
                elif self.session_paused:
                    self.break_time += 1
                self.break_time_label['text'] = "Break Time:      " + str(datetime.timedelta(seconds=self.break_time))
                self.session_time_label['text'] = "Session Time:  " + str(datetime.timedelta(seconds=self.session_time))

    def start_session(self):
        self.session_started = True
        if self.session_dur_selection.get():
            self.session_duration = int(self.session_dur_input.get())
        if self.interval_selection.get():
            self.interval_thread = threading.Thread(target=self.beep_interval_thread)
            self.interval_thread.start()
        self.session_stopped_label.place_forget()
        self.session_start_label.place(x=20, y=66)

    def stop_session(self):
        self.timer_running = False
        if self.session_paused:
            self.session_paused_label.place_forget()
        elif self.session_started:
            self.session_start_label.place_forget()
        self.session_stopped_label.place(x=20, y=66)
        self.session_started = False
        self.caller.stop_session()

    def pause_session(self):
        if not self.session_paused:
            if self.session_started:
                self.session_start_label.place_forget()
            self.session_paused_label.place(x=20, y=66)
            self.session_paused = True
        else:
            self.session_start_label.place(x=20, y=66)
            self.session_paused_label.place_forget()
            self.session_paused = False

    def stop_timer(self):
        self.timer_running = False


class PatientDataFields:
    def __init__(self, parent, patient_file, session_number, session_date, session_time):
        self.patient = PatientContainer(patient_file)
        self.frame = Frame(parent, width=250, height=(parent.winfo_screenheight()-280))
        self.frame.place(x=5, y=120)
        # Create label canvas
        self.label_canvas = Canvas(self.frame, width=250, height=(parent.winfo_screenheight()-280))
        # Frame Information
        self.frame_info = self.label_canvas.create_text(125, 15, text="Patient Information", anchor=CENTER,
                                                        font=('Purisa', 12))
        # Patient name field
        self.name_label = self.label_canvas.create_text(5, 30, text="Name", anchor=NW,
                                                        font=('Purisa', 10))
        # Patient MRN field
        self.mrn_label = self.label_canvas.create_text(5, 75, text="Medical Record Number", anchor=NW,
                                                       font=('Purisa', 10))
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
        # Session date field
        self.date_label = self.label_canvas.create_text(5, 500, text="Session Date: " + session_date, anchor=NW,
                                                        font=('Purisa', 10))
        # Session start time field
        self.start_label = self.label_canvas.create_text(5, 520, text="Session Start Time: " + session_time, anchor=NW,
                                                         font=('Purisa', 10))
        # Session number field
        self.sess_number_label = self.label_canvas.create_text(5, 540, text="Session Number " + str(session_number),
                                                               anchor=NW,
                                                               font=('Purisa', 10))
        # Setup input variables
        self.patient_name_var = StringVar(self.frame)
        if self.patient.name:
            self.patient_name_var.set(self.patient.name)
        self.name_entry = Entry(self.frame, textvariable=self.patient_name_var)
        self.name_entry.place(x=15, y=50, width=220, anchor=NW)

        self.mrn_var = StringVar(self.frame)
        if self.patient.medical_record_number:
            self.mrn_var.set(self.patient.medical_record_number)
        self.mrn_entry = Entry(self.frame, textvariable=self.mrn_var)
        self.mrn_entry.place(x=15, y=95, width=220, anchor=NW)

        self.sess_loc_var = StringVar(self.frame)
        self.sess_entry = Entry(self.frame, textvariable=self.sess_loc_var)
        self.sess_entry.place(x=15, y=140, width=220, anchor=NW)

        self.assess_name_var = StringVar(self.frame)
        self.assess_name_entry = Entry(self.frame, textvariable=self.assess_name_var)
        self.assess_name_entry.place(x=15, y=180, width=220, anchor=NW)

        self.cond_name_var = StringVar(self.frame)
        self.cond_name_entry = Entry(self.frame, textvariable=self.cond_name_var)
        self.cond_name_entry.place(x=15, y=230, width=220, anchor=NW)

        self.prim_ther_var = StringVar(self.frame)
        self.prim_ther_entry = Entry(self.frame, textvariable=self.prim_ther_var)
        self.prim_ther_entry.place(x=15, y=275, width=220, anchor=NW)

        self.case_mgr_var = StringVar(self.frame)
        self.case_mgr_entry = Entry(self.frame, textvariable=self.case_mgr_var)
        self.case_mgr_entry.place(x=15, y=320, width=220, anchor=NW)

        self.sess_ther_var = StringVar(self.frame)
        self.sess_ther_entry = Entry(self.frame, textvariable=self.sess_ther_var)
        self.sess_ther_entry.place(x=15, y=365, width=220, anchor=NW)

        self.data_rec_var = StringVar(self.frame)
        self.data_rec_entry = Entry(self.frame, textvariable=self.data_rec_var)
        self.data_rec_entry.place(x=15, y=410, width=220, anchor=NW)

        self.prim_data_var = StringVar(self.frame)
        self.prim_data_entry = Entry(self.frame, textvariable=self.prim_data_var)
        self.prim_data_entry.place(x=15, y=455, width=220, anchor=NW)

        self.label_canvas.place(x=0, y=0)

    def save_patient_fields(self):
        self.patient.save_patient(self.patient_name_var.get(), self.mrn_var.get())

    def get_session_fields(self):
        return ([self.sess_loc_var.get(), self.assess_name_var.get(), self.cond_name_var.get(), self.prim_ther_var.get(),
                self.case_mgr_var.get(), self.sess_ther_var.get(), self.data_rec_var.get(), self.prim_data_var.get()],
                ["Session Location", "Assessment Name", "Condition Name", "Primary Therapist", "Case Manager",
                 "Session Therapist", "Data Recorder", "Primary Data"])


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


def beep_thread():
    winsound.PlaySound("SystemHand", winsound.SND_ALIAS)


class SessionManagerWindow:
    def __init__(self, patient_file, keystroke_file):
        self.global_commands = {
            "Toggle Session": keyboard.Key.esc,
            "Pause Session": keyboard.Key.ctrl_l
        }
        self.tag_history = []
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
        self.session_started = False
        self.session_paused = False
        parts = pathlib.Path(keystroke_file).parts
        self.session_files = []
        self.session_file = None
        self.session_dir = path.join(parts[0], parts[1], parts[2], parts[3], 'sessions')

        self.session_number = 1
        self.session_date = datetime.datetime.today().strftime("%B %d, %Y")
        self.session_time = datetime.datetime.now().strftime("%H:%M:%S")

        self.get_session_file(self.session_dir)
        root = self.root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
        root.title("KSA - KeyStroke Annotator")

        self.unmc_shield_canvas = Canvas(root, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('images/UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)

        self.pdf = PatientDataFields(root, patient_file, self.session_number, self.session_date, self.session_time)
        self.stf = SessionTimeFields(self, root)
        self.ovu = OutputViewPanel(root)
        self.edf = EmpaticaDataFields(root, self.ovu)
        self.kdf = KeystrokeDataFields(root, keystroke_file)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.mainloop()

    def on_closing(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.edf.disconnect_e4()
        self.root.destroy()
        sys.exit(0)

    def get_session_file(self, directory):
        if path.isdir(self.session_dir):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.session_number += 1
            self.session_file = path.join(directory, 'session_' + str(self.session_number) + '.json')
        else:
            os.mkdir(directory)
            self.session_file = path.join(directory, 'session_1.json')

    def on_press(self, key):
        try:
            self.handle_key_press(key.char)
        except AttributeError:
            self.handle_global_press(key)

    def on_release(self, key):
        pass

    def handle_global_press(self, key_char):
        for key in self.global_commands:
            if self.global_commands[key] == key_char:
                if key == "Toggle Session":
                    if self.session_started:
                        self.stop_session()
                    else:
                        self.start_session()
                elif key == "Pause Session":
                    self.pause_session()

    def handle_key_press(self, key):
        if self.session_started:
            event = self.kdf.check_key(key)
            self.tag_history.append((event, self.stf.session_time))

    def save_session(self):
        self.pdf.save_patient_fields()
        dict_vals, dict_fields = self.pdf.get_session_fields()
        x = {
            "Session Date": self.session_date,
            "Session Start Time": self.session_time,
            "Session Time": self.stf.session_time
        }
        for val, field in zip(dict_vals, dict_fields):
            x[field] = val
        for i in range(0, len(self.tag_history)):
            x[str(i)] = [self.tag_history[i][0], self.tag_history[i][1]]
        with open(self.session_file, 'w') as f:
            json.dump(x, f)
        self.edf.save_session(path.join(self.session_dir, "session_" + str(self.session_number) + "e4.json"))

    def start_session(self):
        self.session_started = True
        self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.stf.start_session()

    def stop_session(self):
        self.session_started = False
        # If being stopped by key press, otherwise don't go into an infinite loop
        if self.stf.session_started:
            self.stf.stop_session()
        self.save_session()

    def pause_session(self):
        if self.session_started:
            if not self.session_paused:
                self.session_paused = True
                self.stf.pause_session()
            else:
                self.session_paused = False
                self.stf.pause_session()
