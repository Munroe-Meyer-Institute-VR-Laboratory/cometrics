import datetime
import json
import math
import os
import pathlib
import threading
import time
import winsound
from os import walk
from tkinter import *
from tkinter import messagebox

from PIL import Image, ImageTk
from pynput import keyboard
from ttk import Combobox

# Custom library imports
from logger_util import *
from menu_bar import MenuBar
from output_view_ui import OutputViewPanel
from tkinter_utils import get_treeview_style
from ui_params import large_header_font, large_field_font, large_field_offset, medium_header_font, medium_field_font, \
    medium_field_offset, small_header_font, small_field_font, small_field_offset, small_tab_size, medium_tab_size, \
    large_tab_size, ui_title


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
        session_time_label.place(x=width / 2, y=self.start_y, anchor=CENTER)

        self.session_time_label = Label(self.frame, text="0:00:00",
                                        font=header_font)
        self.session_time_label.place(x=width / 2, y=self.start_y + (field_offset / 2), anchor=CENTER)

        break_time_label = Label(self.frame, text='Break Time', font=(header_font[0], header_font[1], 'bold'))
        break_time_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 2), anchor=CENTER)

        self.break_time_label = Label(self.frame, text="0:00:00",
                                      font=header_font)
        self.break_time_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 3), anchor=CENTER)

        self.session_start_label = Label(self.frame, text="Session Started", fg='green',
                                         font=header_font)
        self.session_paused_label = Label(self.frame, text="Session Paused", fg='yellow',
                                          font=header_font)
        self.session_stopped_label = Label(self.frame, text="Session Stopped", fg='red',
                                           font=header_font)
        self.session_stopped_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 4), anchor=CENTER)

        self.interval_selection = BooleanVar()
        self.interval_checkbutton = Checkbutton(self.frame, text="Reminder Beep (Seconds)",
                                                variable=self.interval_selection,
                                                font=header_font, command=self.show_beep_interval)
        self.interval_checkbutton.place(x=10, y=self.start_y + ((field_offset / 2) * 6), anchor=W)
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
        self.session_dur_checkbutton.place(x=10, y=self.start_y + ((field_offset / 2) * 7), anchor=W)

        self.session_toggle_button = Button(self.frame, text="Start Session", bg='#4abb5f',
                                            font=field_font, width=13,
                                            command=self.caller.start_session)
        self.session_toggle_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 9), anchor=CENTER)
        self.key_explanation = Label(self.frame, text="Esc Key", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 9), anchor=W)

        self.session_pause_button = Button(self.frame, text="Pause Session", width=13,
                                           font=field_font, command=self.caller.pause_session)
        self.session_pause_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 10.5), anchor=CENTER)
        self.key_explanation = Label(self.frame, text="Left Ctrl", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 10.5), anchor=W)

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
            self.session_dur_input.place(x=self.width * 0.66, y=self.start_y + ((self.field_offset / 2) * 7), anchor=W)
        else:
            self.session_dur_checkbutton.config(text="Session Duration (Seconds)")
            self.session_dur_input.place_forget()

    def show_beep_interval(self):
        if self.interval_selection.get():
            self.interval_checkbutton.config(text="Reminder Beep")
            self.interval_input.place(x=self.width * 0.66, y=self.start_y + ((self.field_offset / 2) * 6), anchor=W)
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
                            self.kdf.dur_treeview.set(str(i), column="1",
                                                      value=self.session_time - self.kdf.sticky_start[i])
                    if self.session_duration:
                        if self.session_time >= self.session_duration:
                            self.caller.stop_session()
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
        self.video_playing = self.caller.ovu.video_view.toggle_video()
        self.session_stopped_label.place_forget()
        self.session_start_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4), anchor=CENTER)

    def stop_session(self):
        self.session_toggle_button['text'] = "Restart Session"
        self.session_toggle_button['bg'] = self.session_pause_button['bg']
        self.session_toggle_button['command'] = self.caller.menu.start_new_session
        self.timer_running = False
        if self.video_playing:
            self.video_playing = self.caller.ovu.video_view.toggle_video()
        if self.session_paused:
            self.session_paused_label.place_forget()
        elif self.session_started:
            self.session_start_label.place_forget()
        self.session_stopped_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                         anchor=CENTER)
        self.session_started = False

    def pause_session(self):
        if self.session_started:
            if not self.session_paused:
                self.video_playing = self.caller.ovu.video_view.toggle_video()
                self.session_start_label.place_forget()
                self.session_paused_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                                anchor=CENTER)
                self.session_paused = True
            else:
                self.video_playing = self.caller.ovu.video_view.toggle_video()
                self.session_start_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                               anchor=CENTER)
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
    def __init__(self, parent, x, y, height, width, patient_file, prim_session_number, reli_session_number,
                 session_date, session_time, conditions, field_offset=50,
                 header_font=('Purisa', 14), field_font=('Purisa', 12), debug=False):
        self.x, self.y = x, y
        self.conditions = conditions
        self.patient = PatientContainer(patient_file)
        self.prim_session_num, self.reli_session_num = prim_session_number, reli_session_number

        field_count = int(height / field_offset)
        if field_count < 13:
            field_count = int((height * 0.85) / field_offset)
        frame_count = int(math.ceil(13 / field_count))
        self.patient_frames = []
        self.next_button_image = PhotoImage(file='images/go_next.png')
        self.prev_button_image = PhotoImage(file='images/go_previous.png')
        print(f"INFO: Number of fields: {field_count}")
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
        print(f"INFO: Number of frames: {frame_count}")
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
            StringVar(self.patient_frames[math.ceil(10 / field_count) - 1], value=prim_session_number),
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
            self.patient_name = self.patient.name
        if self.patient.medical_record_number:
            self.patient_vars[PatientDataVar.MRN].set(self.patient.medical_record_number)
        self.session_number = prim_session_number
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
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select],
                                                       textvariable=patient_dict[elem][2], font=field_font)
                temp_entry['values'] = self.conditions
                temp_entry['state'] = 'readonly'
                temp_entry.config(font=field_font)
                temp_entry.place(x=15, y=patient_y + (field_offset / 2), anchor=NW, width=width * 0.88)
                self.patient_frames[frame_select].option_add('*TCombobox*Listbox.font', field_font)
            else:
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select], font=field_font,
                                                       textvariable=patient_dict[elem][2])
                temp_entry.place(x=15, y=patient_y + (field_offset / 2), anchor=NW, width=width * 0.88)
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
        self.start_label = Label(self.patient_frames[frame_select], text="Session Start Time: " + session_time,
                            anchor=NW, font=field_font)
        self.start_label.place(x=5, y=patient_y, anchor=NW)

        self.patient_vars[PatientDataVar.PATIENT_NAME].set(self.patient.name)
        if self.patient.medical_record_number:
            self.patient_vars[PatientDataVar.MRN].set(self.patient.medical_record_number)
        self.patient_vars[PatientDataVar.SESS_NUM].set(prim_session_number)

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
        if self.patient_vars[PatientDataVar.PRIM_DATA].get() == "Primary":
            self.patient_vars[PatientDataVar.SESS_NUM].set(self.prim_session_num)
            self.session_number = self.prim_session_num
        elif self.patient_vars[PatientDataVar.PRIM_DATA].get() == "Reliability":
            self.patient_vars[PatientDataVar.SESS_NUM].set(self.reli_session_num)
            self.session_number = self.reli_session_num
        else:
            print(f"ERROR: Something went wrong assigning the session type "
                  f"{self.patient_vars[PatientDataVar.PRIM_DATA].get()}")

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
        return {"Session Location": self.patient_vars[PatientDataVar.SESS_LOC].get(),
                "Assessment Name": self.patient_vars[PatientDataVar.ASSESS_NAME].get(),
                "Condition Name": self.patient_vars[PatientDataVar.COND_NAME].get(),
                "Primary Therapist": self.patient_vars[PatientDataVar.PRIM_THER].get(),
                "Case Manager": self.patient_vars[PatientDataVar.CASE_MGR].get(),
                "Session Therapist": self.patient_vars[PatientDataVar.SESS_THER].get(),
                "Data Recorder": self.patient_vars[PatientDataVar.DATA_REC].get(),
                "Primary Data": self.patient_vars[PatientDataVar.PRIM_DATA].get(),
                "Session Number": self.patient_vars[PatientDataVar.SESS_NUM].get()
                }


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
        # region Project File Setup
        # Get the project files
        self.config = config
        self.patient_file = project_setup.patient_data_file
        self.keystroke_file = project_setup.ksf_file
        self.session_dir = project_setup.phase_dir
        self.tracker_file = project_setup.tracker_file
        self.graph_dir = path.join(self.session_dir, config.get_data_folders()[0])
        self.export_dir = path.join(self.session_dir, config.get_data_folders()[3])
        self.data_dir = path.join(self.session_dir, config.get_data_folders()[1])
        self.prim_dir = path.join(self.data_dir, "Primary")
        if not os.path.exists(self.prim_dir):
            os.mkdir(self.prim_dir)
        self.reli_dir = path.join(self.data_dir, "Reliability")
        if not os.path.exists(self.reli_dir):
            os.mkdir(self.reli_dir)
        # Log this for debugging
        print("INFO:", self.patient_file, self.keystroke_file, self.session_dir, self.prim_dir, self.reli_dir)
        # Generate session date and time
        now = datetime.datetime.today()
        self.session_date = now.strftime("%B %d, %Y")
        self.session_file_date = now.strftime("%B")[:3] + now.strftime("%d") + now.strftime("%Y")
        self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
        # Get the number of primary and reliability sessions collected so far
        self.prim_session_number = 1
        self.reli_session_number = 1
        self.get_prim_session(self.prim_dir)
        self.get_reli_session(self.reli_dir)
        # endregion

        # region User Interface Setup
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
        print("INFO:", self.header_font, self.field_font, self.field_offset)

        root = self.root = Tk()
        root.config(bg="white", bd=-2)
        root.title(ui_title)

        self.field_width = int(self.window_width * 0.2)
        self.output_width = int(self.window_width * 0.58)

        self.logo_width = self.field_width
        self.logo_height = int(self.logo_width / 5.7)
        self.patient_field_height = int((self.window_height - self.logo_height - 10) * 0.85)

        self.logo_canvas = Canvas(root, width=self.logo_width, height=self.logo_height, bg="white", bd=-2)
        self.logo_canvas.place(x=2, y=2)
        self.logo_img = ImageTk.PhotoImage(
            Image.open('images/cometrics_logo.png').resize((self.logo_width, self.logo_height), Image.ANTIALIAS))
        self.logo_canvas.create_image(0, 0, anchor=NW, image=self.logo_img)

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
                                   x=(self.logo_width * 2) + 20,
                                   y=(self.logo_height + 10) - self.button_size[1],
                                   height=self.patient_field_height,
                                   width=self.output_width,
                                   button_size=self.button_size,
                                   ksf=self.keystroke_file,
                                   field_font=self.field_font,
                                   header_font=self.header_font)
        self.stf.kdf = self.ovu.key_view
        self.pdf = PatientDataFields(root,
                                     x=5,
                                     y=self.logo_height + 10,
                                     height=self.patient_field_height,
                                     width=self.field_width,
                                     patient_file=self.patient_file,
                                     prim_session_number=self.prim_session_number,
                                     reli_session_number=self.reli_session_number,
                                     session_date=self.session_date,
                                     session_time=self.session_time,
                                     conditions=project_setup.conditions,
                                     header_font=self.header_font,
                                     field_font=self.field_font,
                                     field_offset=self.field_offset, debug=True)
        self.patient_name = self.pdf.patient_name
        # endregion

        # Setup key listener
        self.global_commands = {
            "Toggle Session": keyboard.Key.esc,
            "Pause Session": keyboard.Key.ctrl_l,
            "Delete Last Event": keyboard.Key.backspace,
            "Undo Last Delete": keyboard.Key.ctrl_r
        }
        self.tag_history = []
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
        # Configure window close override
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.restart = False
        self.setup_again = False
        self.close_program = False
        # Start the window in fullscreen
        root.state('zoomed')
        # Start the UI loop
        root.mainloop()

    def restart_program(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.setup_again = True

    def create_new_session(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.restart = True

    def on_closing(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.close_program = True

    def get_reli_session(self, directory):
        if path.isdir(directory):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.reli_session_number += 1
        else:
            messagebox.showerror("Error", "Reliability session folder could not be found!")
            print("ERROR: Reliability session folder could not be found")

    def get_prim_session(self, directory):
        if path.isdir(directory):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.prim_session_number += 1
        else:
            messagebox.showerror("Error", "Primary session folder could not be found!")
            print("ERROR: Primary session folder could not be found")

    def on_press(self, key):
        try:
            key_char = key.char
            # Only process key input if session has started
            if self.stf.session_started:
                # Only process key input if the main window has focus, otherwise ignore
                if self.root.focus_get():
                    # Enforce lower case for all inputs that are characters
                    key_char = str(key_char).lower()
                    self.handle_key_press(key_char)
                else:
                    print("INFO: Typing outside window")
        except AttributeError:
            self.handle_global_press(key)

    def on_release(self, key):
        pass

    def handle_global_press(self, key_char):
        for key in self.global_commands:
            if self.global_commands[key] == key_char:
                if key == "Toggle Session":
                    if self.stf.session_started:
                        self.stop_session()
                    else:
                        response = self.pdf.check_session_fields()
                        if response is False:
                            self.start_session()
                        else:
                            messagebox.showwarning("Warning", response)
                            print("WARNING:", response)
                elif key == "Pause Session":
                    self.pause_session()
                elif key == "Delete Last Event":
                    self.ovu.key_view.delete_last_event()
                elif key == "Undo Last Delete":
                    self.ovu.key_view.undo_last_delete()

    def handle_key_press(self, key):
        try:
            if self.stf.session_started:
                self.ovu.check_event(key, self.stf.session_time)
        except TypeError as e:
            print(f"ERROR: Exception encountered when handling key press:\n{str(e)}")

    def save_session(self):
        session_fields = self.pdf.get_session_fields()
        session_data, e4_data = self.ovu.get_session_data()
        x = {
            "Session Date": self.session_date,
            "Session Start Time": self.session_time,
            "Session Time": self.stf.session_time,
            "Pause Time": self.stf.break_time,
            "Keystroke File": pathlib.Path(self.keystroke_file).stem
        }
        session_fields.update(x)
        session_fields["Event History"] = session_data
        session_fields["E4 Data"] = e4_data
        session_fields["KSF"] = self.ovu.key_view.keystroke_json
        reli = '_R' if session_fields["Primary Data"] == "Reliability" else ''
        output_session_file = path.join(self.session_dir,
                                        self.config.get_data_folders()[1],
                                        session_fields["Primary Data"],
                                        f"{session_fields['Session Number']}"
                                        f"{session_fields['Assessment Name'][:2]}"
                                        f"{session_fields['Condition Name'][:2]}"
                                        f"{self.session_file_date}{reli}.json")
        with open(output_session_file, 'w') as f:
            json.dump(session_fields, f)
        print(f"INFO: Saved session file to: {output_session_file}")

    def start_session(self):
        response = self.pdf.check_session_fields()
        if response is False:
            self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.pdf.start_label['text'] = "Session Start Time: " + self.session_time
            self.pdf.save_patient_fields()
            self.pdf.lock_session_fields()
            self.stf.lock_session_fields()
            self.ovu.start_session()
            self.stf.start_session()
        else:
            messagebox.showwarning("Warning", response)
            print("WARNING:", response)

    def stop_session(self):
        self.stf.stop_session()
        self.ovu.stop_session()
        self.save_session()
        self.listener.stop()

    def pause_session(self):
        if self.stf.session_started:
            self.stf.pause_session()
