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
# Custom library imports
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams
from logger_util import *


class StaticImages(Frame):
    def __init__(self, parent, **kw):
        super().__init__(**kw)
        self.unmc_shield_canvas = Canvas(parent, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)


class SessionTimeFields:
    def __init__(self, parent):
        self.frame = Frame(parent, width=500, height=100, bg='white')
        self.frame.place(x=252, y=2)

        self.session_started = False
        self.session_paused = False
        self.timer_running = True
        self.ui_timer_running = True
        self.update_ui = False

        self.session_time = 0
        self.break_time = 0
        self.session_time_label = Label(self.frame, text="Session Time: 00:00:00", bg='white',
                                        font=('Purisa', 14))
        self.session_time_label.place(x=20, y=10)

        self.break_time_label = Label(self.frame, text="Break Time:     00:00:00", bg='white',
                                      font=('Purisa', 14))
        self.break_time_label.place(x=20, y=38)

        self.session_start_label = Label(self.frame, text="Session Started", bg='white', fg='green',
                                         font=('Purisa', 14))
        self.session_paused_label = Label(self.frame, text="Session Paused", bg='white', fg='yellow',
                                          font=('Purisa', 14))
        self.session_stopped_label = Label(self.frame, text="Session Stopped", bg='white', fg='red',
                                           font=('Purisa', 14))
        self.session_stopped_label.place(x=20, y=66)

        self.time_thread = threading.Thread(target=self.time_update_thread)
        self.time_thread.start()

    def time_update_thread(self):
        while self.timer_running:
            time.sleep(1 - time.monotonic() % 1)
            if self.timer_running:
                if self.session_started and not self.session_paused:
                    if self.break_time > 0:
                        self.break_time = 0
                    self.session_time += 1
                elif self.session_paused:
                    self.break_time += 1
                self.break_time_label['text'] = "Break Time:      " + str(datetime.timedelta(seconds=self.break_time))
                self.session_time_label['text'] = "Session Time:  " + str(datetime.timedelta(seconds=self.session_time))

    def start_session(self):
        self.session_stopped_label.place_forget()
        self.session_start_label.place(x=20, y=66)
        self.session_started = True

    def stop_session(self):
        if self.session_paused:
            self.session_paused_label.place_forget()
        elif self.session_started:
            self.session_start_label.place_forget()
        self.session_stopped_label.place(x=20, y=66)
        self.session_started = False

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

        self.label_canvas.pack()


class EmpaticaDataFields:
    def __init__(self, parent):
        self.parent = parent
        self.frame = Frame(parent, width=250, height=(parent.winfo_screenheight() - 280))
        self.frame.place(x=265, y=120)

        self.emp_client = None
        self.e4_client = None
        self.e4_address = None

        empatica_label = Label(self.frame, text="Empatica E4", font=('Purisa', 12))
        empatica_label.place(x=125, y=15, anchor=CENTER)

        self.empatica_button = Button(self.frame, text="Start Server", command=self.start_e4_server)
        self.empatica_button.place(x=125, y=30, anchor=N)

        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 10))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.frame, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=20, y=65, height=(parent.winfo_screenheight() - 450), width=210)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="E4 Name")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_selection)

        self.file_scroll = Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=65, height=(parent.winfo_screenheight() - 450))

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.connect_button = Button(self.frame, text="Connect", command=self.connect_to_e4, width=12)
        self.connect_button.place(x=20, y=(parent.winfo_screenheight() - 385))

        self.streaming_button = Button(self.frame, text="Stream", command=self.start_e4_streaming, width=12)
        self.streaming_button.place(x=230, y=(parent.winfo_screenheight() - 385), anchor=NE)

        self.connected_label = Label(self.frame, text="CONNECTED", fg='green')
        self.streaming_label = Label(self.frame, text="STREAMING", fg='green')

        self.devices_thread = None

    def connect_to_e4(self):
        if self.emp_client:
            try:
                self.e4_client = EmpaticaE4(self.e4_address)
                if self.e4_client.connected:
                    for stream in EmpaticaDataStreams.ALL_STREAMS:
                        self.e4_client.subscribe_to_stream(stream)
                    self.connected_label.place(x=125, y=(self.parent.winfo_screenheight() - 350), anchor=N)
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_streaming(self):
        if self.emp_client:
            if self.e4_client:
                if self.e4_client.connected:
                    try:
                        self.e4_client.start_streaming()
                        self.streaming_label.place(x=125, y=(self.parent.winfo_screenheight() - 320), anchor=N)
                    except Exception as e:
                        messagebox.showerror("Exception Encountered",
                                             "Encountered an error when connecting to E4:\n" + str(e))
                else:
                    messagebox.showwarning("Warning", "Device is not connected!")
            else:
                messagebox.showwarning("Warning", "Connect to device first!")
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_server(self):
        if not self.emp_client:
            try:
                self.emp_client = EmpaticaClient()
                self.empatica_button['text'] = "List Devices"
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
        else:
            try:
                self.devices_thread = threading.Thread(target=self.list_devices_thread)
                self.devices_thread.start()
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))

    def list_devices_thread(self):
        if not self.emp_client:
            self.emp_client.list_connected_devices()
            time.sleep(1)
            self.clear_device_list()
            self.populate_device_list()

    def clear_device_list(self):
        for children in self.treeview.get_children():
            self.treeview.delete(children)

    def populate_device_list(self):
        for i in range(0, len(self.emp_client.device_list)):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
                                                          values=(self.emp_client.device_list[i],),
                                                          tags=(self.tags[i % 2])))

    def get_selection(self, event):
        self.current_selection = self.treeview.identify_row(event.y)
        if self.current_selection:
            if self.emp_client:
                if len(self.emp_client.device_list) != 0:
                    self.e4_address = self.emp_client.device_list(int(self.current_selection))
                else:
                    messagebox.showerror("Error", "No connected E4s!")
            else:
                messagebox.showwarning("Warning", "Connect to server first!")

    def fixed_map(self, option):
        # https://stackoverflow.com/a/62011081
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        style = Style()
        return [elm for elm in style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]


class KeystrokeDataFields:
    def __init__(self, parent, keystroke_file):
        self.frame = Frame(parent, width=250, height=(parent.winfo_screenheight() - 280))
        self.frame.place(x=520, y=120)
        self.keystroke_json = None
        self.new_keystroke = False
        self.bindings = []
        self.key_file = keystroke_file
        self.open_keystroke_file()

        keystroke_label = Label(self.frame, text="Key Bindings", font=('Purisa', 12))
        keystroke_label.place(x=125, y=15, anchor=CENTER)

        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 10))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.frame, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=20, y=30, height=(parent.winfo_screenheight() - 350), width=210)

        self.treeview.heading("#0", text="Char", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="Tag")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_selection)
        self.treeview.bind("<Double-Button-1>", self.change_keybind)

        self.file_scroll = Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=30, height=(parent.winfo_screenheight() - 350))

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.populate_bindings()

        self.delete_button = Button(self.frame, text="Delete Key", command=self.delete_binding, width=8)
        self.delete_button.place(x=20, y=parent.winfo_screenheight() - 320)

        self.add_button = Button(self.frame, text="Add Key", command=self.add_key_popup, width=9)
        self.add_button.place(x=125, y=parent.winfo_screenheight() - 320, anchor=N)

        self.save_button = Button(self.frame, text="Save File", command=self.save_binding, width=8)
        self.save_button.place(x=230, y=parent.winfo_screenheight() - 320, anchor=NE)

    def check_key(self, key_char):
        for key in self.bindings:
            if key[1] == key_char:
                return key[0]
        return None

    def add_key_popup(self):
        NewKeyPopup(self, self.frame)

    def get_selection(self, event):
        self.current_selection = self.treeview.identify_row(event.y)

    def save_binding(self):
        x = {"Name": self.keystroke_json["Name"]}
        for binding in self.bindings:
            x.update({str(binding[0]): str(binding[1])})
        with open(self.key_file, 'w') as f:
            json.dump(x, f)

    def delete_binding(self):
        if self.current_selection:
            self.bindings.pop(int(self.current_selection))
            self.clear_listbox()
            self.populate_bindings()

    def fixed_map(self, option):
        # https://stackoverflow.com/a/62011081
        # Fix for setting text colour for Tkinter 8.6.9
        # From: https://core.tcl.tk/tk/info/509cafafae
        #
        # Returns the style map for 'option' with any styles starting with
        # ('!disabled', '!selected', ...) filtered out.

        # style.map() returns an empty list for missing options, so this
        # should be future-safe.
        style = Style()
        return [elm for elm in style.map('Treeview', query_opt=option) if
                elm[:2] != ('!disabled', '!selected')]

    def change_keybind(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection))

    def update_keybind(self, tag, key):
        self.bindings[key] = (self.bindings[key][0], tag)
        self.clear_listbox()
        self.populate_bindings()

    def add_keybind(self, tag, key):
        self.bindings.append((tag, key))
        self.clear_listbox()
        self.populate_bindings()

    def clear_listbox(self):
        for children in self.treeview.get_children():
            self.treeview.delete(children)

    def open_keystroke_file(self):
        with open(self.key_file) as f:
            self.keystroke_json = json.load(f)
        if len(self.keystroke_json) == 1:
            self.new_keystroke = True
        else:
            for key in self.keystroke_json:
                if key != "Name":
                    self.bindings.append((key, self.keystroke_json[key]))

    def populate_bindings(self):
        for i in range(0, len(self.bindings)):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=self.bindings[i][1],
                                                          values=(self.bindings[i][0],),
                                                          tags=(self.tags[i % 2])))


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


class NewKeyPopup:
    def __init__(self, top, root):
        self.caller = top
        self.tag_entry = None
        self.key_entry = None
        self.popup_root = None
        self.patient_name_entry_pop_up(root)

    def patient_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = self.popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x100")
        popup_root.title("Enter New Binding")

        # Create an Entry Widget in the Toplevel window
        self.tag_label = Label(popup_root, text="Key Tag", bg='white')
        self.tag_label.place(x=30, y=20, anchor=W)
        self.tag_entry = Entry(popup_root, bd=2, width=25, bg='white')
        self.tag_entry.place(x=90, y=20, anchor=W)

        self.key_label = Label(popup_root, text="Key", bg='white')
        self.key_label.place(x=30, y=50, anchor=W)
        self.key_entry = Entry(popup_root, bd=2, width=25, bg='white')
        self.key_entry.place(x=90, y=50, anchor=W)

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win)
        button.place(x=150, y=70, anchor=N)

    def close_win(self):
        if len(self.key_entry.get()) == 1:
            self.caller.add_keybind(self.tag_entry.get(), self.key_entry.get())
            self.popup_root.destroy()


class Popup:
    def __init__(self, top, root, tag):
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.tag = tag
        self.patient_name_entry_pop_up(root)

    def patient_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = self.popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x50")
        popup_root.title("Enter New Key Bind")

        # Create an Entry Widget in the Toplevel window
        self.entry = Entry(popup_root, bd=2, width=25)
        self.entry.pack()

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)

    def close_win(self):
        if len(self.entry.get()) == 1:
            self.caller.update_keybind(self.entry.get(), self.tag)
            self.popup_root.destroy()


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
        StaticImages(root)
        self.pdf = PatientDataFields(root, patient_file, self.session_number, self.session_date, self.session_time)
        self.edf = EmpaticaDataFields(root)
        self.kdf = KeystrokeDataFields(root, keystroke_file)
        self.stf = SessionTimeFields(root)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        root.mainloop()
        print(self.tag_history)

    def on_closing(self):
        if self.root:
            self.stf.stop_timer()
            self.root.destroy()

    def get_session_file(self, directory):
        if path.isdir(self.session_dir):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.session_number += 1
            self.session_file = open(path.join(directory, 'session_' + str(self.session_number) + '.json'), 'w')
        else:
            os.mkdir(directory)

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
        event = self.kdf.check_key(key)
        self.tag_history.append((event, self.stf.session_time))

    def start_session(self):
        self.session_started = True
        self.stf.start_session()

    def stop_session(self):
        self.session_started = False
        self.stf.stop_session()

    def pause_session(self):
        if self.session_started:
            if not self.session_paused:
                self.session_paused = True
                self.stf.pause_session()
            else:
                self.session_paused = False
                self.stf.pause_session()
