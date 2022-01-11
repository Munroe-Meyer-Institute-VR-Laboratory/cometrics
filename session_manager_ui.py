import os
import pathlib
import time
from os import walk
from tkinter import *
from tkinter import messagebox
from ttk import Combobox
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
import math

from tkinter_utils import get_treeview_style
from ui_params import large_header_font, large_field_font, large_field_offset, medium_header_font, medium_field_font, \
    medium_field_offset, small_header_font, small_field_font, small_field_offset, large_button_size, medium_button_size, \
    small_button_size, small_tab_size, medium_tab_size, large_tab_size


class SessionTimeFields:
    def __init__(self, caller, parent, x, y, height, width,
                 header_font=('Purisa', 14), field_font=('Purisa', 11),
                 field_offset=60, kdf=None):
        self.width, self.height = width, height
        self.field_offset = field_offset
        self.kdf = kdf
        self.caller = caller
        self.frame = Frame(parent, width=width, height=height)
        self.frame.place(x=x, y=y)

        self.session_started = False
        self.session_paused = False
        self.timer_running = True
        self.ui_timer_running = True
        self.update_ui = False
        self.start_y = 15
        self.session_time = 0
        self.break_time = 0
        session_time_label = Label(self.frame, text="Session Time", font=(header_font[0], header_font[1], 'bold'))
        session_time_label.place(x=width/2, y=self.start_y, anchor=CENTER)

        self.session_time_label = Label(self.frame, text="0:00:00",
                                        font=header_font)
        self.session_time_label.place(x=width/2, y=self.start_y+(field_offset / 2), anchor=CENTER)

        break_time_label = Label(self.frame, text='Break Time', font=(header_font[0], header_font[1], 'bold'))
        break_time_label.place(x=width/2, y=self.start_y+((field_offset / 2) * 2), anchor=CENTER)

        self.break_time_label = Label(self.frame, text="0:00:00",
                                      font=header_font)
        self.break_time_label.place(x=width/2, y=self.start_y+((field_offset / 2) * 3), anchor=CENTER)

        self.session_start_label = Label(self.frame, text="Session Started", fg='green',
                                         font=header_font)
        self.session_paused_label = Label(self.frame, text="Session Paused", fg='yellow',
                                          font=header_font)
        self.session_stopped_label = Label(self.frame, text="Session Stopped", fg='red',
                                           font=header_font)
        self.session_stopped_label.place(x=width/2, y=self.start_y+((field_offset / 2) * 4), anchor=CENTER)

        self.interval_selection = BooleanVar()
        self.interval_checkbutton = Checkbutton(self.frame, text="Reminder Beep (Seconds)",
                                                variable=self.interval_selection,
                                                font=header_font, command=self.show_beep_interval)
        self.interval_checkbutton.place(x=10, y=self.start_y+((field_offset / 2) * 6), anchor=W)
        self.interval_input_var = StringVar()

        interval_cmd = self.frame.register(self.validate_number)
        self.interval_input = Entry(self.frame, validate='all', validatecommand=(interval_cmd, '%P'),
                                    font=header_font, width=6)

        session_cmd = self.frame.register(self.validate_number)
        self.session_dur_input = Entry(self.frame, validate='all', validatecommand=(session_cmd, '%P'),
                                       font=header_font, width=6)

        self.session_dur_selection = BooleanVar()
        self.session_dur_checkbutton = Checkbutton(self.frame, text="Session Duration (Seconds)",
                                                   variable=self.session_dur_selection,
                                                   font=header_font,
                                                   command=self.show_session_time)
        self.session_dur_checkbutton.place(x=10, y=self.start_y+((field_offset / 2) * 7), anchor=W)

        self.session_toggle_button = Button(self.frame, text="Start Session", bg='#4abb5f',
                                            font=field_font, width=13,
                                            command=self.caller.start_session)
        self.session_toggle_button.place(x=width/2, y=self.start_y+((field_offset / 2) * 9), anchor=CENTER)
        self.key_explanation = Label(self.frame, text="Esc Key", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 9), anchor=W)

        self.session_pause_button = Button(self.frame, text="Pause Session", width=13,
                                           font=field_font, command=self.caller.pause_session)
        self.session_pause_button.place(x=width/2, y=self.start_y+((field_offset / 2) * 10.5), anchor=CENTER)
        self.key_explanation = Label(self.frame, text="Left Ctrl", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width*0.75, y=self.start_y+((field_offset / 2) * 10.5), anchor=W)

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
            self.session_dur_input.place(x=self.width*0.66, y=self.start_y+((self.field_offset / 2) * 7), anchor=W)
        else:
            self.session_dur_checkbutton.config(text="Session Duration (Seconds)")
            self.session_dur_input.place_forget()

    def show_beep_interval(self):
        if self.interval_selection.get():
            self.interval_checkbutton.config(text="Reminder Beep")
            self.interval_input.place(x=self.width*0.66, y=self.start_y+((self.field_offset / 2) * 6), anchor=W)
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
                            self.kdf.treeview1.set(str(i), column="2",
                                                   value=self.session_time - self.kdf.sticky_start[i])
                    if self.session_duration:
                        if self.session_time >= self.session_duration:
                            self.stop_session()
                elif self.session_paused:
                    self.break_time += 1
                self.break_time_label['text'] = str(datetime.timedelta(seconds=self.break_time))
                self.session_time_label['text'] = str(datetime.timedelta(seconds=self.session_time))

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


class PatientDataVar:
    PATIENT_NAME = 0
    MRN = 1
    SESS_LOC = 2
    ASSESS_NAME = 3
    COND_NAME = 4
    PRIM_THER = 5
    CASE_MGR = 6
    SESS_THER = 7
    DATA_REC = 8
    SESS_NUM = 9
    PRIM_DATA = 10


class PatientDataFields:
    def __init__(self, parent, x, y, height, width, patient_file, session_number,
                 session_date, session_time, conditions, field_offset=50,
                 header_font=('Purisa', 14), field_font=('Purisa', 12), debug=False):
        self.x, self.y = x, y
        self.conditions = conditions
        self.patient = PatientContainer(patient_file)

        field_count = int(height / field_offset)
        if field_count < 13:
            field_count = int((height * 0.85) / field_offset)
        frame_count = int(math.ceil(13 / field_count))
        self.patient_frames = []
        self.next_button_image = PhotoImage(file='images/go_next.png')
        self.prev_button_image = PhotoImage(file='images/go_previous.png')
        print(f"Number of fields: {field_count}")
        for i in range(0, frame_count):
            self.patient_frames.append(Frame(parent, width=width, height=height))
            patient_information = Label(self.patient_frames[-1], text="Patient Information", font=header_font)
            patient_information.place(x=width / 2, y=15, anchor=CENTER)
            if frame_count > 1:
                next_button = Button(self.patient_frames[-1], image=self.next_button_image,
                                     command=self.next_patient_field)
                prev_button = Button(self.patient_frames[-1], image=self.prev_button_image,
                                     command=self.prev_patient_field)
                next_button.place(x=width - 15, y=height * 0.9, anchor=E)
                prev_button.place(x=15, y=height * 0.9, anchor=W)
                page_text = Label(self.patient_frames[-1], text=f"{i + 1}/{frame_count}", font=header_font)
                page_text.place(x=width / 2, y=height * 0.9, anchor=CENTER)
        print(f"Number of frames: {frame_count}")
        self.patient_vars = [
            StringVar(self.patient_frames[math.ceil(1 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(2 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(3 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(4 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(5 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(6 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(7 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(8 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(9 / field_count) - 1]),
            StringVar(self.patient_frames[math.ceil(10 / field_count) - 1], value=session_number),
            StringVar(self.patient_frames[math.ceil(11 / field_count) - 1], value="Primary")
        ]
        self.label_texts = [
            "Name",
            "Medical Record Number",
            "Session Location",
            "Assessment Name",
            "Condition Name",
            "Primary Therapist",
            "Case Manager",
            "Session Therapist",
            "Data Recorder",
            "Session Number",
            "Primary or Reliability Session"
        ]
        if self.patient.name:
            self.patient_vars[PatientDataVar.PATIENT_NAME].set(self.patient.name)
        if self.patient.medical_record_number:
            self.patient_vars[PatientDataVar.MRN].set(self.patient.medical_record_number)
        self.session_number = session_number
        self.patient_entries, self.patient_labels = [], []

        patient_dict = [
            [Label, self.label_texts[PatientDataVar.PATIENT_NAME], self.patient_vars[PatientDataVar.PATIENT_NAME]],
            [Entry, self.label_texts[PatientDataVar.PATIENT_NAME], self.patient_vars[PatientDataVar.PATIENT_NAME]],
            [Label, self.label_texts[PatientDataVar.MRN], self.patient_vars[PatientDataVar.MRN]],
            [Entry, self.label_texts[PatientDataVar.MRN], self.patient_vars[PatientDataVar.MRN]],
            [Label, self.label_texts[PatientDataVar.SESS_LOC], self.patient_vars[PatientDataVar.SESS_LOC]],
            [Entry, self.label_texts[PatientDataVar.SESS_LOC], self.patient_vars[PatientDataVar.SESS_LOC]],
            [Label, self.label_texts[PatientDataVar.ASSESS_NAME], self.patient_vars[PatientDataVar.ASSESS_NAME]],
            [Entry, self.label_texts[PatientDataVar.ASSESS_NAME], self.patient_vars[PatientDataVar.ASSESS_NAME]],
            [Label, self.label_texts[PatientDataVar.COND_NAME], self.patient_vars[PatientDataVar.COND_NAME]],
            [Combobox, self.label_texts[PatientDataVar.COND_NAME], self.patient_vars[PatientDataVar.COND_NAME]],
            [Label, self.label_texts[PatientDataVar.PRIM_THER], self.patient_vars[PatientDataVar.PRIM_THER]],
            [Entry, self.label_texts[PatientDataVar.PRIM_THER], self.patient_vars[PatientDataVar.PRIM_THER]],
            [Label, self.label_texts[PatientDataVar.CASE_MGR], self.patient_vars[PatientDataVar.CASE_MGR]],
            [Entry, self.label_texts[PatientDataVar.CASE_MGR], self.patient_vars[PatientDataVar.CASE_MGR]],
            [Label, self.label_texts[PatientDataVar.SESS_THER], self.patient_vars[PatientDataVar.SESS_THER]],
            [Entry, self.label_texts[PatientDataVar.SESS_THER], self.patient_vars[PatientDataVar.SESS_THER]],
            [Label, self.label_texts[PatientDataVar.DATA_REC], self.patient_vars[PatientDataVar.DATA_REC]],
            [Entry, self.label_texts[PatientDataVar.DATA_REC], self.patient_vars[PatientDataVar.DATA_REC]],
            [Label, self.label_texts[PatientDataVar.SESS_NUM], self.patient_vars[PatientDataVar.SESS_NUM]],
            [Entry, self.label_texts[PatientDataVar.SESS_NUM], self.patient_vars[PatientDataVar.SESS_NUM]],
        ]

        info_count = 0
        frame_select = 0
        patient_y = 30
        for elem in range(0, len(patient_dict), 2):
            temp_label = patient_dict[elem][0](self.patient_frames[frame_select], text=patient_dict[elem][1],
                                               font=field_font)
            self.patient_labels.append(temp_label)
            temp_label.place(x=5, y=patient_y, anchor=NW)
            if patient_dict[elem + 1][0] is Combobox:
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select], textvariable=patient_dict[elem][2], font=field_font)
                temp_entry['values'] = self.conditions
                temp_entry['state'] = 'readonly'
                temp_entry.config(font=field_font)
                temp_entry.place(x=15, y=patient_y + (field_offset / 2), anchor=NW, width=width*0.88)
                self.patient_frames[frame_select].option_add('*TCombobox*Listbox.font', field_font)
            else:
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select], font=field_font,
                                                       textvariable=patient_dict[elem][2])
                temp_entry.place(x=15, y=patient_y + (field_offset / 2), anchor=NW, width=width*0.88)
            self.patient_entries.append(temp_entry)
            info_count += 1
            if not info_count % field_count and frame_count != 1:
                frame_select += 1
                patient_y = 30
            else:
                if patient_dict[elem + 1][0] is OptionMenu:
                    patient_y += field_offset
                else:
                    patient_y += field_offset

        primary_data = Label(self.patient_frames[frame_select], text=self.label_texts[PatientDataVar.PRIM_DATA],
                             font=field_font)
        primary_data.place(x=5, y=patient_y, anchor=NW)
        prim_data_radio = Radiobutton(self.patient_frames[frame_select], text="Primary", value="Primary",
                                      variable=self.patient_vars[PatientDataVar.PRIM_DATA], command=self.check_radio,
                                      font=field_font, width=12)
        rel_data_radio = Radiobutton(self.patient_frames[frame_select], text="Reliability", value="Reliability",
                                     variable=self.patient_vars[PatientDataVar.PRIM_DATA], command=self.check_radio,
                                     font=field_font, width=12)
        prim_data_radio.place(x=(width / 2), y=patient_y + (field_offset / 2), anchor=NE)
        rel_data_radio.place(x=(width / 2), y=patient_y + (field_offset / 2), anchor=NW)
        self.patient_entries.append(prim_data_radio)
        self.patient_entries.append(rel_data_radio)
        info_count += 1
        if not info_count % field_count and frame_count != 1:
            frame_select += 1
            patient_y = 30
        else:
            patient_y += field_offset
        # Session date field
        date_label = Label(self.patient_frames[frame_select], text="Session Date: " + session_date, anchor=NW,
                           font=field_font)
        date_label.place(x=5, y=patient_y, anchor=NW)
        info_count += 1
        info_count += 1
        if not info_count % field_count and frame_count != 1:
            frame_select += 1
            patient_y = 30
        else:
            patient_y += field_offset / 2
        # Session start time field
        start_label = Label(self.patient_frames[frame_select], text="Session Start Time: " + session_time,
                            anchor=NW, font=field_font)
        start_label.place(x=5, y=patient_y, anchor=NW)

        self.patient_vars[PatientDataVar.PATIENT_NAME].set(self.patient.name)
        if self.patient.medical_record_number:
            self.patient_vars[PatientDataVar.MRN].set(self.patient.medical_record_number)
        self.patient_vars[PatientDataVar.SESS_NUM].set(session_number)

        self.current_patient_field = 0
        self.patient_frames[self.current_patient_field].place(x=self.x, y=self.y)
        self.patient_entries[0].focus()

        if debug:
            self.patient_vars[PatientDataVar.SESS_LOC].set("Debug")
            self.patient_vars[PatientDataVar.ASSESS_NAME].set("Debug")
            self.patient_vars[PatientDataVar.COND_NAME].set("Debug")
            self.patient_vars[PatientDataVar.CASE_MGR].set("Debug")
            self.patient_vars[PatientDataVar.SESS_THER].set("Debug")
            self.patient_vars[PatientDataVar.DATA_REC].set("Debug")
            self.patient_vars[PatientDataVar.PRIM_THER].set("Debug")

    def select_patient_fields(self, field):
        self.patient_frames[self.current_patient_field].place_forget()
        self.patient_frames[field].place(x=self.x, y=self.y)
        self.current_patient_field = field

    def next_patient_field(self):
        self.patient_frames[self.current_patient_field].place_forget()
        if self.current_patient_field + 1 >= len(self.patient_frames):
            self.current_patient_field = 0
        else:
            self.current_patient_field += 1
        self.patient_frames[self.current_patient_field].place(x=self.x, y=self.y)

    def prev_patient_field(self):
        self.patient_frames[self.current_patient_field].place_forget()
        if self.current_patient_field - 1 < 0:
            self.current_patient_field = len(self.patient_frames) - 1
        else:
            self.current_patient_field -= 1
        self.patient_frames[self.current_patient_field].place(x=self.x, y=self.y)

    def check_radio(self):
        pass

    def save_patient_fields(self):
        self.patient.save_patient(self.patient_vars[PatientDataVar.PATIENT_NAME].get(),
                                  self.patient_vars[PatientDataVar.MRN].get())

    def check_session_fields(self):
        if self.patient_vars[PatientDataVar.SESS_LOC].get() == "":
            return "Session location not set!"
        elif self.patient_vars[PatientDataVar.ASSESS_NAME].get() == "":
            return "Assessment name not set!"
        elif self.patient_vars[PatientDataVar.COND_NAME].get() == "":
            return "Condition name not set!"
        elif self.patient_vars[PatientDataVar.PRIM_THER].get() == "":
            return "Primary therapist name not set!"
        elif self.patient_vars[PatientDataVar.CASE_MGR].get() == "":
            return "Case manager name not set!"
        elif self.patient_vars[PatientDataVar.SESS_THER].get() == "":
            return "Session therapist name not set!"
        elif self.patient_vars[PatientDataVar.DATA_REC].get() == "":
            return "Data recorder not set!"
        elif self.patient_vars[PatientDataVar.PRIM_DATA].get() == "":
            return "Data type not set!"
        elif int(self.patient_vars[PatientDataVar.SESS_NUM].get()) < self.session_number and self.patient_vars[
            PatientDataVar.PRIM_DATA].get() == "Primary":
            return "Session number already exists!"
        else:
            return False

    def lock_session_fields(self):
        for entry in self.patient_entries:
            entry.config(state='disabled')

    def get_session_fields(self):
        return ([self.patient_vars[PatientDataVar.SESS_LOC].get(), self.patient_vars[PatientDataVar.ASSESS_NAME].get(),
                 self.patient_vars[PatientDataVar.COND_NAME].get(), self.patient_vars[PatientDataVar.PRIM_THER].get(),
                 self.patient_vars[PatientDataVar.CASE_MGR].get(), self.patient_vars[PatientDataVar.SESS_THER].get(),
                 self.patient_vars[PatientDataVar.DATA_REC].get(), self.patient_vars[PatientDataVar.PRIM_DATA].get(),
                 self.patient_vars[PatientDataVar.SESS_NUM].get()],
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
    def __init__(self, config, project_setup):
        self.window_height, self.window_width = config.get_screen_size()[0], config.get_screen_size()[1]
        if self.window_width == 1920:
            self.header_font = large_header_font
            self.field_font = large_field_font
            self.field_offset = large_field_offset
            self.button_size = large_tab_size
        elif 1920 > self.window_width > 1280:
            self.header_font = medium_header_font
            self.field_font = medium_field_font
            self.field_offset = medium_field_offset
            self.button_size = medium_tab_size
        else:
            self.header_font = small_header_font
            self.field_font = small_field_font
            self.field_offset = small_field_offset
            self.button_size = small_tab_size
        print(self.header_font, self.field_font, self.field_offset)
        self.patient_file = project_setup.patient_data_file
        self.keystroke_file = project_setup.ksf_file
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
        parts = pathlib.Path(self.keystroke_file).parts
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
        root.title("cometrics v0.8.0")

        self.field_width = int(self.window_width * 0.2)
        self.output_width = int(self.window_width * 0.58)

        self.logo_width = self.field_width
        self.logo_height = int(self.logo_width / 5.7)
        self.patient_field_height = int((self.window_height - self.logo_height - 10) * 0.85)
        print(self.patient_field_height)

        self.unmc_shield_canvas = Canvas(root, width=self.logo_width, height=self.logo_height, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(
            Image.open('images/cometrics_logo.png').resize((self.logo_width, self.logo_height), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)

        _ = get_treeview_style()

        self.menu = MenuBar(root, self)
        self.stf = SessionTimeFields(self, root,
                                     x=self.logo_width + 10,
                                     y=self.logo_height + 10,
                                     height=self.patient_field_height,
                                     width=self.field_width,
                                     header_font=self.header_font,
                                     field_font=self.field_font,
                                     field_offset=self.field_offset)
        self.ovu = OutputViewPanel(root,
                                   x=(self.logo_width*2)+20,
                                   y=(self.logo_height + 10)-self.button_size[1],
                                   height=self.patient_field_height,
                                   width=self.output_width,
                                   button_size=self.button_size,
                                   ksf=self.keystroke_file,
                                   field_font=self.field_font,
                                   header_font=self.header_font)
        # self.stf.kdf = self.ovu.key_view
        self.pdf = PatientDataFields(root, 5, self.logo_height + 10, self.patient_field_height, self.field_width,
                                     self.patient_file, self.session_number, self.session_date,
                                     self.session_time, ['Shine', 'On'],
                                     header_font=self.header_font,
                                     field_font=self.field_font,
                                     field_offset=self.field_offset, debug=False)
        # self.session_time, self.ovu.key_view.conditions, debug=False)
        # self.edf = EmpaticaDataFields(root, self.ovu, self.window_height, self.window_width)

        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.state('zoomed')
        root.mainloop()

    def restart_program(self):
        # self.stf.stop_timer()
        # self.ovu.close()
        # self.edf.disconnect_e4()
        # self.listener.stop()
        self.root.quit()
        self.root.destroy()

    def on_closing(self):
        # self.stf.stop_timer()
        # self.ovu.close()
        # self.edf.disconnect_e4()
        # self.listener.stop()
        # self.root.quit()
        # self.root.destroy()
        sys.exit(0)

    def get_session_file(self, directory):
        if path.isdir(self.session_dir):
            _, _, files = next(walk(directory))
            for file in files:
                if len(pathlib.Path(file).stem.split('_')) == 3:
                    continue
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
            "Pause Time": self.stf.break_time,
            "Keystroke File": self.keystroke_file
        }
        for val, field in zip(dict_vals, dict_fields):
            x[field] = val
        for i in range(0, len(event_history)):
            x[str(i)] = [event_history[i][0], event_history[i][1]]
        with open(self.session_file, 'w') as f:
            json.dump(x, f)
        self.ovu.save_session(path.join(self.session_dir, "session_" + str(self.session_number) + ".e4"),
                              self.tag_history)

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
