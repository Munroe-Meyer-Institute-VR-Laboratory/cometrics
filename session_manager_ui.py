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
import math


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

        self.key_explanation = Label(self.frame, text="Esc Key", font=('Purisa', 11), bg='white',
                                     justify=LEFT)
        self.key_explanation.place(x=675, y=8)

        self.key_explanation = Label(self.frame, text="Left Control", font=('Purisa', 11), bg='white',
                                     justify=LEFT)
        self.key_explanation.place(x=675, y=38)

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
    def __init__(self, parent, height, width, patient_file, session_number, session_date, session_time, conditions,
                 debug=False):
        self.conditions = conditions
        self.patient = PatientContainer(patient_file)
        self.patient_vars = [
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(),
            StringVar(value=session_number),
            StringVar(value="Primary")
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
        self.patient_frames = []
        self.next_button_image = PhotoImage(file='images/go-next.png')
        self.prev_button_image = PhotoImage(file='images/go-previous.png')
        field_count = int(((height - 355) - 30) / 45)
        frame_count = int(math.ceil(13 / field_count))
        print(f"Number of frames: {field_count}")
        for i in range(0, frame_count):
            self.patient_frames.append(Frame(parent, width=250, height=(height - 280)))
            patient_information = Label(self.patient_frames[-1], text="Patient Information", font=('Purisa', 12))
            patient_information.place(x=125, y=15, anchor=CENTER)
            if frame_count > 1:
                next_button = Button(self.patient_frames[-1], image=self.next_button_image, command=self.next_patient_field)
                prev_button = Button(self.patient_frames[-1], image=self.prev_button_image, command=self.prev_patient_field)
                next_button.place(x=250-15, y=(height - 280)*0.9, anchor=E)
                prev_button.place(x=15, y=(height - 280)*0.9, anchor=W)
                page_text = Label(self.patient_frames[-1], text=f"{i + 1}/{frame_count}", font=('Purisa', 12))
                page_text.place(x=250/2, y=(height-280)*0.9, anchor=CENTER)
        print(f"Number of frames: {frame_count}")
        patient_dict = [
            [Label, self.label_texts[PatientDataVar.PATIENT_NAME]],
            [Entry, self.label_texts[PatientDataVar.PATIENT_NAME]],
            [Label, self.label_texts[PatientDataVar.MRN]],
            [Entry, self.label_texts[PatientDataVar.MRN]],
            [Label, self.label_texts[PatientDataVar.SESS_LOC]],
            [Entry, self.label_texts[PatientDataVar.SESS_LOC]],
            [Label, self.label_texts[PatientDataVar.ASSESS_NAME]],
            [Entry, self.label_texts[PatientDataVar.ASSESS_NAME]],
            [Label, self.label_texts[PatientDataVar.COND_NAME]],
            [OptionMenu, self.label_texts[PatientDataVar.COND_NAME]],
            [Label, self.label_texts[PatientDataVar.PRIM_THER]],
            [Entry, self.label_texts[PatientDataVar.PRIM_THER]],
            [Label, self.label_texts[PatientDataVar.CASE_MGR]],
            [Entry, self.label_texts[PatientDataVar.CASE_MGR]],
            [Label, self.label_texts[PatientDataVar.SESS_THER]],
            [Entry, self.label_texts[PatientDataVar.SESS_THER]],
            [Label, self.label_texts[PatientDataVar.DATA_REC]],
            [Entry, self.label_texts[PatientDataVar.DATA_REC]],
            [Label, self.label_texts[PatientDataVar.SESS_NUM]],
            [Entry, self.label_texts[PatientDataVar.SESS_NUM]],
        ]
        info_count = 0
        frame_select = 0
        patient_y = 30
        for elem in range(0, len(patient_dict), 2):
            temp_label = patient_dict[elem][0](self.patient_frames[frame_select], text=patient_dict[elem][1], font=('Purisa', 10))
            temp_label.place(x=5, y=patient_y, anchor=NW)
            if patient_dict[elem + 1][0] is OptionMenu:
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select], patient_dict[elem][1], *self.conditions)
                temp_entry.place(x=15, y=patient_y + 20, anchor=NW, width=220)
            else:
                temp_entry = patient_dict[elem + 1][0](self.patient_frames[frame_select], textvariable=patient_dict[elem][1])
                temp_entry.place(x=15, y=patient_y+20, anchor=NW, width=220)
            info_count += 1
            if not info_count % field_count:
                frame_select += 1
                patient_y = 30
            else:
                if patient_dict[elem + 1][0] is OptionMenu:
                    patient_y += 55
                else:
                    patient_y += 45

        primary_data = Label(self.patient_frames[frame_select], text=self.label_texts[PatientDataVar.PRIM_DATA],
              font=('Purisa', 10))
        primary_data.place(x=5, y=patient_y, anchor=NW)
        self.prim_data_radio = Radiobutton(self.patient_frames[frame_select], text="Primary", value="Primary",
                                           variable=self.patient_vars[PatientDataVar.PRIM_DATA], command=self.check_radio)
        self.rel_data_radio = Radiobutton(self.patient_frames[frame_select], text="Reliability", value="Reliability",
                                          variable=self.patient_vars[PatientDataVar.PRIM_DATA], command=self.check_radio)
        self.prim_data_radio.place(x=15, y=patient_y+20)
        self.rel_data_radio.place(x=125, y=patient_y+20)
        info_count += 1
        if not info_count % field_count:
            frame_select += 1
            patient_y = 30
        else:
            patient_y += 45
        # Session date field
        date_label = Label(self.patient_frames[frame_select], text="Session Date: " + session_date, anchor=NW,
                                                        font=('Purisa', 10))
        date_label.place(x=5, y=patient_y, anchor=NW)
        info_count += 1
        info_count += 1
        if not info_count % field_count:
            frame_select += 1
            patient_y = 30
        else:
            patient_y += 20
        # Session start time field
        start_label = Label(self.patient_frames[frame_select], text="Session Start Time: " + session_time,
                            anchor=NW, font=('Purisa', 10))
        start_label.place(x=5, y=patient_y, anchor=NW)

        self.current_patient_field = 0
        self.patient_frames[self.current_patient_field].place(x=5, y=120)

        if debug:
            self.sess_loc_var.set("Debug")
            self.assess_name_var.set("Debug")
            self.cond_name_var.set("Debug")
            self.case_mgr_var.set("Debug")
            self.sess_ther_var.set("Debug")
            self.data_rec_var.set("Debug")
            self.prim_ther_var.set("Debug")

    def select_patient_fields(self, field):
        self.patient_frames[self.current_patient_field].place_forget()
        self.patient_frames[field].place(x=5, y=120)
        self.current_patient_field = field

    def next_patient_field(self):
        self.patient_frames[self.current_patient_field].place_forget()
        if self.current_patient_field + 1 >= len(self.patient_frames):
            self.current_patient_field = 0
        else:
            self.current_patient_field += 1
        self.patient_frames[self.current_patient_field].place(x=5, y=120)

    def prev_patient_field(self):
        self.patient_frames[self.current_patient_field].place_forget()
        if self.current_patient_field - 1 < 0:
            self.current_patient_field = len(self.patient_frames) - 1
        else:
            self.current_patient_field -= 1
        self.patient_frames[self.current_patient_field].place(x=5, y=120)

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
        self.session_number_entry.config(state='disabled')

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
    def __init__(self, config, project_setup):
        self.window_height, self.window_width = config.get_screen_size()[0], config.get_screen_size()[1]
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

        self.unmc_shield_canvas = Canvas(root, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('images/cometrics_logo.png').resize((250, int(250/5.7)), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 50, anchor=W, image=self.unmc_shield_img)

        self.menu = MenuBar(root, self)
        self.stf = SessionTimeFields(self, root)
        self.ovu = OutputViewPanel(root, self.keystroke_file, self.window_height, self.window_width)
        self.stf.kdf = self.ovu.key_view
        self.pdf = PatientDataFields(root, self.window_height, self.window_width,
                                     self.patient_file, self.session_number, self.session_date,
                                     self.session_time, self.ovu.key_view.conditions, debug=False)
        self.edf = EmpaticaDataFields(root, self.ovu, self.window_height, self.window_width)

        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.state('zoomed')
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
