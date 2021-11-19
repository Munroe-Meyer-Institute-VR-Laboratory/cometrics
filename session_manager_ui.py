import os
import pathlib
import time
from os import walk
from tkinter import *
from tkinter import messagebox
import json
import datetime
from PIL import Image, ImageTk
import threading
from pynput import keyboard
import winsound
# Custom library imports
from logger_util import *
from output_view_ui import OutputViewPanel
from input_view_ui import EmpaticaDataFields
from menu_bar import MenuBar


class SessionTimeFields:
    def __init__(self, caller, parent, kdf=None):
        self.kdf = kdf
        self.caller = caller
        self.frame = Frame(parent, width=800, height=100, bg='white')
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

        self.interval_selection = BooleanVar()
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

        self.session_dur_selection = BooleanVar()
        self.session_dur_checkbutton = Checkbutton(self.frame, text="Session Duration (Seconds)",
                                                   variable=self.session_dur_selection, bg='white',
                                                   font=('Purisa', 14),
                                                   command=self.show_session_time)
        self.session_dur_checkbutton.place(x=250, y=34)

        self.session_toggle_button = Button(self.frame, text="Start Session", bg='#4abb5f',
                                            font=('Purisa', 11), width=15,
                                            command=self.caller.start_session)
        self.session_toggle_button.place(x=527, y=4)

        self.session_pause_button = Button(self.frame, text="Pause Session", width=15,
                                           font=('Purisa', 11), command=self.caller.pause_session)
        self.session_pause_button.place(x=527, y=36)

        self.key_explanation = Label(self.frame, text="Esc Key\n\nLeft Control", font=('Purisa', 11), bg='white',
                                     justify=LEFT)
        self.key_explanation.place(x=675, y=4)

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

    def lock_session_fields(self):
        self.interval_input.config(state='disabled')
        self.session_dur_input.config(state='disabled')

    def beep_interval_thread(self):
        interval = int(self.interval_input.get())
        while self.session_started:
            time.sleep(interval)
            if not self.session_paused and self.session_started:
                self.beep_th = threading.Thread(target=beep_thread)
                self.beep_th.start()

    def show_session_time(self):
        if self.session_dur_selection.get():
            self.session_dur_checkbutton.config(text="Session Duration")
            self.session_dur_input.place(x=430, y=38)
        else:
            self.session_dur_checkbutton.config(text="Session Duration (Seconds)")
            self.session_dur_input.place_forget()

    def show_beep_interval(self):
        if self.interval_selection.get():
            self.interval_checkbutton.config(text="Reminder Beep")
            self.interval_input.place(x=430, y=10)
        else:
            self.interval_checkbutton.config(text="Reminder Beep (Seconds)")
            self.interval_input.place_forget()

    def time_update_thread(self):
        while self.timer_running:
            time.sleep(1 - time.monotonic() % 1)
            if self.timer_running:
                if self.session_started and not self.session_paused:
                    self.session_time += 1
                    for i in range(0, len(self.kdf.dur_sticky)):
                        if self.kdf.dur_sticky[i]:
                            self.kdf.treeview1.set(str(i), column="2", value=self.session_time - self.kdf.sticky_start[i])
                    if self.session_duration:
                        if self.session_time >= self.session_duration:
                            self.stop_session()
                elif self.session_paused:
                    self.break_time += 1
                self.break_time_label['text'] = "Break Time:      " + str(datetime.timedelta(seconds=self.break_time))
                self.session_time_label['text'] = "Session Time:  " + str(datetime.timedelta(seconds=self.session_time))

    def start_session(self):
        self.session_started = True
        self.session_toggle_button['text'] = "Stop Session"
        self.session_toggle_button['bg'] = '#ea2128'
        self.session_toggle_button['command'] = self.caller.stop_session
        if self.session_dur_selection.get():
            self.session_duration = int(self.session_dur_input.get())
        if self.interval_selection.get():
            self.interval_thread = threading.Thread(target=self.beep_interval_thread)
            self.interval_thread.start()
        self.session_stopped_label.place_forget()
        self.session_start_label.place(x=20, y=66)

    def stop_session(self, caller_save=True):
        self.session_toggle_button['text'] = "Restart Session"
        self.session_toggle_button['bg'] = self.session_pause_button['bg']
        self.session_toggle_button['command'] = self.caller.menu.restart_program
        self.timer_running = False
        if self.session_paused:
            self.session_paused_label.place_forget()
        elif self.session_started:
            self.session_start_label.place_forget()
        self.session_stopped_label.place(x=20, y=66)
        self.session_started = False
        if caller_save:
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
    def __init__(self, parent, patient_file, session_number, session_date, session_time, conditions, debug=False):
        self.conditions = conditions
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
        self.assess_name_label = self.label_canvas.create_text(5, 165, text="Assessment Name", anchor=NW,
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
        self.sess_number_label = self.label_canvas.create_text(5, 540, text="Session Number: ",
                                                               anchor=NW,
                                                               font=('Purisa', 10))
        # Setup input variables
        self.session_number = session_number
        self.session_number_var = StringVar(self.frame, session_number)
        self.session_number_entry = Entry(self.frame, textvariable=self.session_number_var)
        self.session_number_entry.place(x=125, y=540, width=75)
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

        if self.conditions:
            self.cond_name_var = StringVar(self.frame)
            self.cond_name_entry = OptionMenu(self.frame, self.cond_name_var, *self.conditions)
            self.cond_name_entry.place(x=15, y=225, width=220, anchor=NW)
        else:
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

        self.prim_data_var = StringVar(self.frame, "Primary")
        self.prim_data_radio = Radiobutton(self.frame, text="Primary", value="Primary",
                                           variable=self.prim_data_var, command=self.check_radio)
        self.prim_data_radio.place(x=15, y=455)

        self.rel_data_radio = Radiobutton(self.frame, text="Reliability", value="Reliability",
                                          variable=self.prim_data_var, command=self.check_radio)
        self.rel_data_radio.place(x=125, y=455)

        self.label_canvas.place(x=0, y=0)

        if debug:
            self.sess_loc_var.set("Debug")
            self.assess_name_var.set("Debug")
            self.cond_name_var.set("Debug")
            self.case_mgr_var.set("Debug")
            self.sess_ther_var.set("Debug")
            self.data_rec_var.set("Debug")
            self.prim_ther_var.set("Debug")


    def check_radio(self):
        pass

    def save_patient_fields(self):
        self.patient.save_patient(self.patient_name_var.get(), self.mrn_var.get())

    def check_session_fields(self):
        if self.sess_loc_var.get() == "":
            return "Session location not set!"
        elif self.assess_name_var.get() == "":
            return "Assessment name not set!"
        elif self.cond_name_var.get() == "":
            return "Condition name not set!"
        elif self.prim_ther_var.get() == "":
            return "Primary therapist name not set!"
        elif self.case_mgr_var.get() == "":
            return "Case manager name not set!"
        elif self.sess_ther_var.get() == "":
            return "Session therapist name not set!"
        elif self.data_rec_var.get() == "":
            return "Data recorder not set!"
        elif self.prim_data_var.get() == "":
            return "Data type not set!"
        elif int(self.session_number_var.get()) < self.session_number and self.prim_data_var.get() == "Primary":
            return "Session number already exists!"
        else:
            return False

    def lock_session_fields(self):
        self.sess_entry.config(state='disabled')
        self.cond_name_entry.config(state='disabled')
        self.data_rec_entry.config(state='disabled')
        self.cond_name_entry.config(state='disabled')
        self.sess_ther_entry.config(state='disabled')
        self.case_mgr_entry.config(state='disabled')
        self.assess_name_entry.config(state='disabled')
        self.name_entry.config(state='disabled')
        self.mrn_entry.config(state='disabled')
        self.prim_ther_entry.config(state='disabled')

    def get_session_fields(self):
        return ([self.sess_loc_var.get(), self.assess_name_var.get(), self.cond_name_var.get(), self.prim_ther_var.get(),
                self.case_mgr_var.get(), self.sess_ther_var.get(), self.data_rec_var.get(), self.prim_data_var.get(),
                 self.session_number_var.get()],
                ["Session Location", "Assessment Name", "Condition Name", "Primary Therapist", "Case Manager",
                 "Session Therapist", "Data Recorder", "Primary Data", "Session Number"])


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
        self.patient_file = patient_file
        self.keystroke_file = keystroke_file
        self.global_commands = {
            "Toggle Session": keyboard.Key.esc,
            "Pause Session": keyboard.Key.ctrl_l,
            "Delete Last Event": keyboard.Key.backspace
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
        self.session_dir = path.join(*parts[0:-2], 'sessions')
        print(self.session_dir)

        self.close_program = False
        self.session_number = 1
        self.session_date = datetime.datetime.today().strftime("%B %d, %Y")
        self.session_time = datetime.datetime.now().strftime("%H:%M:%S")

        self.get_session_file(self.session_dir)
        root = self.root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(1250, 725))
        root.title("Experiment Collection & Logging v0.5.5")

        self.unmc_shield_canvas = Canvas(root, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('images/UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)

        self.menu = MenuBar(root, self)
        self.stf = SessionTimeFields(self, root)
        self.ovu = OutputViewPanel(root, keystroke_file)
        self.stf.kdf = self.ovu.key_view
        self.pdf = PatientDataFields(root, patient_file, self.session_number, self.session_date,
                                     self.session_time, self.ovu.key_view.conditions, debug=True)

        self.edf = EmpaticaDataFields(root, self.ovu)

        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.mainloop()

    def restart_program(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.edf.disconnect_e4()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()

    def on_closing(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.edf.disconnect_e4()
        self.listener.stop()
        self.root.quit()
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
                        response = self.pdf.check_session_fields()
                        if response is False:
                            self.start_session()
                        else:
                            messagebox.showwarning("Warning", response)
                elif key == "Pause Session":
                    self.pause_session()
                elif key == "Delete Last Event":
                    self.ovu.key_view.delete_last_event()

    def handle_key_press(self, key):
        try:
            if self.session_started:
                events = self.ovu.key_view.check_key(key, self.stf.session_time)
                for event in events:
                    if event[0] and event[1]:
                        self.tag_history.append(event)
        except TypeError as e:
            print(str(e))

    def save_session(self):
        self.pdf.save_patient_fields()
        dict_vals, dict_fields = self.pdf.get_session_fields()
        event_history = self.ovu.key_view.event_history
        if dict_vals[-1] != self.session_number:
            if dict_vals[-2] == "Reliability":
                self.session_file = path.join(pathlib.Path(self.session_file).parent, "session_" +
                                              str(dict_vals[-1]) + "_" + str(dict_vals[-2]) + ".json")
            else:
                self.session_file = path.join(pathlib.Path(self.session_file).parent, "session_" +
                                              str(dict_vals[-1]) + ".json")
        elif dict_vals[-2] == "Reliability":
            self.session_file = path.join(pathlib.Path(self.session_file).parent, "session_" +
                                          str(dict_vals[-1]) + "_" + str(dict_vals[-2]) + ".json")
        x = {
            "Session Date": self.session_date,
            "Session Start Time": self.session_time,
            "Session Time": self.stf.session_time,
            "Pause Time": self.stf.break_time
        }
        for val, field in zip(dict_vals, dict_fields):
            x[field] = val
        for i in range(0, len(event_history)):
            x[str(i)] = [event_history[i][0], event_history[i][1]]
        with open(self.session_file, 'w') as f:
            json.dump(x, f)
        self.ovu.save_session(path.join(self.session_dir, "session_" + str(self.session_number) + ".e4"), self.tag_history)

    def start_session(self):
        response = self.pdf.check_session_fields()
        if response is False:
            self.session_started = True
            self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.pdf.lock_session_fields()
            self.stf.lock_session_fields()
            self.ovu.start_session()
            self.stf.start_session()
        else:
            messagebox.showwarning("Warning", response)

    def stop_session(self):
        self.session_started = False
        # If being stopped by key press, otherwise don't go into an infinite loop
        if self.stf.session_started:
            self.stf.stop_session(False)
        self.ovu.stop_session()
        self.save_session()
        self.listener.stop()

    def pause_session(self):
        if self.session_started:
            if not self.session_paused:
                self.session_paused = True
                self.stf.pause_session()
            else:
                self.session_paused = False
                self.stf.pause_session()
