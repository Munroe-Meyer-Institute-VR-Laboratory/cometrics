import json
import threading
import time
import traceback
from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Treeview, Style

# Custom library imports
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4, EmpaticaDataStreams

from tkinter_utils import build_treeview
from ui_params import treeview_tags


class KeystrokeDataFields:
    def __init__(self, parent, keystroke_file, height, width):
        self.frame = Frame(parent, width=250, height=(height - 280))
        self.frame.place(x=520, y=120)
        self.keystroke_json = None
        self.new_keystroke = False
        self.bindings = []
        self.dur_bindings = []
        self.bindings_freq = []
        self.key_file = keystroke_file
        self.conditions = []
        self.open_keystroke_file()
        self.freq_strings = []
        self.freq_key_strings = []

        self.dur_sticky = []
        self.sticky_start = []
        self.sticky_dur = []

        keystroke_label = Label(self.frame, text="Key Bindings", font=('Purisa', 12))
        keystroke_label.place(x=125, y=15, anchor=CENTER)

        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 10))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.frame, style="mystyle.Treeview", height=18, selectmode='browse', show="headings")
        self.treeview.place(x=20, y=30, height=(height / 2 - 200), width=210)

        self.treeview["columns"] = ["1", "2", "3"]
        self.treeview.heading("1", text="Char", anchor='c')
        self.treeview.column("1", width=40, stretch=NO, anchor='c')
        self.treeview.heading("2", text="Freq")
        self.treeview.column("2", width=40, stretch=NO, anchor='c')
        self.treeview.heading("3", text="Tag")
        self.treeview.column("3", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.tag_configure('toggle', background='red')

        self.treeview.bind("<Button-1>", self.get_selection)
        self.treeview.bind("<Double-Button-1>", self.change_keybind)

        self.delete_button = Button(self.frame, text="Delete Key", command=self.delete_binding, width=8)
        self.delete_button.place(x=20, y=height / 2 - 170, anchor=NW)

        self.add_button = Button(self.frame, text="Add Key", command=self.add_key_popup, width=9)
        self.add_button.place(x=125, y=height / 2 - 170, anchor=N)

        self.save_button = Button(self.frame, text="Save File", command=self.save_binding, width=8)
        self.save_button.place(x=230, y=height / 2 - 170, anchor=NE)

        self.file_scroll = Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=30, height=(height / 2 - 200))

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even', 'toggle']
        self.current_selection = "I000"

        self.treeview1 = Treeview(self.frame, style="mystyle.Treeview", height=18, selectmode='browse', show="headings")
        self.treeview1.place(x=20, y=(height / 2 - 175) + 50,
                             height=(height / 2 - 200), width=210)

        self.treeview1["columns"] = ["1", "2", "3", "4"]
        self.treeview1.heading("1", text="Char", anchor='c')
        self.treeview1.column("1", width=40, stretch=NO, anchor='c')
        self.treeview1.heading("2", text="Dur")
        self.treeview1.column("2", width=40, stretch=NO, anchor='c')
        self.treeview1.heading("3", text="Total")
        self.treeview1.column("3", width=45, stretch=NO, anchor='c')
        self.treeview1.heading("4", text="Tag")
        self.treeview1.column("4", width=65, stretch=YES, anchor='c')

        self.treeview1.tag_configure('odd', background='#E8E8E8')
        self.treeview1.tag_configure('even', background='#DFDFDF')
        self.treeview1.tag_configure('toggle', background='red')

        self.treeview1.bind("<Button-1>", self.get_selection1)
        self.treeview1.bind("<Double-Button-1>", self.change_keybind1)

        self.file_scroll1 = Scrollbar(self.frame, orient="vertical", command=self.treeview1.yview)
        self.file_scroll1.place(x=2, y=(height / 2 - 175) + 50,
                                height=(height / 2 - 200))

        self.treeview1.configure(yscrollcommand=self.file_scroll1.set)
        self.tree_parents1 = []
        self.current_selection1 = "I000"

        self.populate_bindings()
        self.populate_bindings1()

        self.delete_button1 = Button(self.frame, text="Delete Key", command=self.delete_dur_binding, width=8)
        self.delete_button1.place(x=20, y=height - 325)

        self.add_button1 = Button(self.frame, text="Add Key", command=self.add_dur_popup, width=9)
        self.add_button1.place(x=125, y=height - 325, anchor=N)

        self.save_button1 = Button(self.frame, text="Save File", command=self.save_binding, width=8)
        self.save_button1.place(x=230, y=height - 325, anchor=NE)

    def delete_dur_binding(self):
        if self.current_selection1:
            self.dur_bindings.pop(int(self.current_selection1))
            self.clear_listbox1()
            self.populate_bindings1()

    def add_dur_popup(self):
        NewKeyPopup(self, self.frame, True)

    def check_key(self, key_char, start_time):
        return_bindings = []
        key_type = False
        duration = None
        for i in range(0, len(self.bindings)):
            if self.bindings[i][1] == key_char:
                self.bindings_freq[i] += 1
                self.treeview.set(str(i), column="2", value=self.bindings_freq[i])
                return_bindings.append(self.bindings[i][0])
                key_type = False
        for i in range(0, len(self.dur_bindings)):
            if self.dur_bindings[i][1] == key_char:
                return_bindings.append(self.dur_bindings[i][0])
                if self.dur_sticky[i]:
                    self.treeview1.item(str(i), tags=self.tags[i % 2])
                    self.dur_sticky[i] = False
                    duration = (self.sticky_start[i], start_time)
                    self.sticky_dur[i] += start_time - self.sticky_start[i]
                    self.sticky_start[i] = 0
                    self.treeview1.set(str(i), column="3", value=self.sticky_dur[i])
                else:
                    self.treeview1.item(str(i), tags=self.tags[2])
                    self.dur_sticky[i] = True
                    self.sticky_start[i] = start_time
                key_type = True
        if return_bindings:
            return return_bindings, key_type, duration

    def add_key_popup(self):
        NewKeyPopup(self, self.frame, False)

    def get_selection1(self, event):
        self.current_selection1 = self.treeview1.identify_row(event.y)

    def get_selection(self, event):
        self.current_selection = self.treeview.identify_row(event.y)

    def import_binding(self):
        pass

    def save_binding(self):
        x = {
            "Name": self.keystroke_json["Name"],
            "Frequency": self.bindings,
            "Duration": self.dur_bindings
        }
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

    def change_keybind1(self, event):
        selection = self.treeview1.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), True)

    def change_keybind(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            Popup(self, self.frame, int(selection), False)

    def update_durbind(self, tag, key):
        self.dur_bindings[key] = (self.dur_bindings[key][0], tag)
        self.treeview1.set(str(key), column="1", value=tag)

    def update_keybind(self, tag, key):
        self.bindings[key] = (self.bindings[key][0], tag)
        self.treeview.set(str(key), column="1", value=tag)

    def add_keybind(self, tag, key):
        self.bindings.append((tag, key))
        self.bindings_freq.append(0)
        self.clear_listbox()
        self.populate_bindings()

    def add_durbind(self, tag, key):
        self.dur_bindings.append((tag, key))
        self.clear_listbox1()
        self.populate_bindings1()

    def clear_listbox1(self):
        for children in self.treeview1.get_children():
            self.treeview1.delete(children)

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
                if key == "Frequency":
                    for binding in self.keystroke_json[key]:
                        self.bindings.append(binding)
                        self.bindings_freq.append(0)
                elif key == "Duration":
                    for binding in self.keystroke_json[key]:
                        self.dur_bindings.append(binding)
                elif key == "Conditions":
                    for binding in self.keystroke_json[key]:
                        self.conditions.append(binding)

    def populate_bindings(self):
        for i in range(0, len(self.bindings)):
            bind = self.bindings[i]
            self.tree_parents.append(self.treeview.insert("", 'end', str(i),
                                                          values=(bind[1], self.bindings_freq[i], bind[0]),
                                                          tags=(self.tags[i % 2])))

    def populate_bindings1(self):
        for i in range(0, len(self.dur_bindings)):
            bind = self.dur_bindings[i]
            self.dur_sticky.append(False)
            self.sticky_start.append(0)
            self.sticky_dur.append(0)
            self.tree_parents1.append(self.treeview1.insert("", 'end', str(i),
                                                            values=(bind[1], 0, 0, bind[0]),
                                                            tags=(self.tags[i % 2])))


class NewKeyPopup:
    def __init__(self, top, root, dur_freq):
        self.caller = top
        self.dur_freq = dur_freq
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
            if not self.dur_freq:
                self.caller.add_keybind(self.tag_entry.get(), self.key_entry.get())
            else:
                self.caller.add_durbind(self.tag_entry.get(), self.key_entry.get())
            self.popup_root.destroy()


class Popup:
    def __init__(self, top, root, tag, dur_key):
        self.caller = top
        self.dur_key = dur_key
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
            if not self.dur_key:
                self.caller.update_keybind(self.entry.get(), self.tag)
            else:
                self.caller.update_durbind(self.entry.get(), self.tag)
            self.popup_root.destroy()


class EmpaticaDataFields:
    def __init__(self, parent, output_view, height, width):
        self.height, self.width = height, width
        self.ovu = output_view
        self.parent = parent
        self.frame = Frame(parent, width=250, height=(height - 280))
        self.frame.place(x=265, y=120)

        self.emp_client = None
        self.e4_client = None
        self.e4_address = None

        empatica_label = Label(self.frame, text="Empatica E4", font=('Purisa', 12))
        empatica_label.place(x=125, y=15, anchor=CENTER)

        self.empatica_button = Button(self.frame, text="Start Server", command=self.start_e4_server)
        self.empatica_button.place(x=125, y=30, anchor=N)

        e4_heading_dict = {"#0": ["E4 Device Name", 'c', 1, YES, 'c']}
        self.e4_treeview_parents = []
        self.e4_treeview, self.e4_filescroll = build_treeview(self.frame, x=20, y=65, height=(height - 450), width=210,
                                                              heading_dict=e4_heading_dict,
                                                              button_1_bind=self.get_selection)

        self.connect_button = Button(self.frame, text="Connect", command=self.connect_to_e4, width=12)
        self.connect_button.place(x=20, y=(height - 385))

        self.streaming_button = Button(self.frame, text="Stream", command=self.start_e4_streaming, width=12)
        self.streaming_button.place(x=230, y=(height - 385), anchor=NE)

        self.disconnected_image = PhotoImage(file='images/disconnected.png')
        self.connected_image = PhotoImage(file='images/connected.png')
        self.connected_label = Label(self.frame, image=self.disconnected_image)
        self.connected_label.place(x=250*0.25, y=height - 330, anchor=CENTER)

        self.streaming_image = PhotoImage(file='images/streaming.png')
        self.nostreaming_image = PhotoImage(file='images/nostreaming.png')
        self.streaming_label = Label(self.frame, image=self.nostreaming_image)
        self.streaming_label.place(x=250*0.75, y=height - 330, anchor=CENTER)

        self.error_thread = None
        self.devices_thread = None

    def check_e4_error(self):
        while self.e4_client:
            if self.e4_client.client.last_error:
                messagebox.showerror("E4 Error", "Encountered error from E4!\n" + self.e4_client.client.last_error)
                self.connect_to_e4()
            time.sleep(0.5)

    def disconnect_e4(self):
        if self.emp_client:
            self.emp_client.close()
        if self.e4_client:
            if self.e4_client.connected:
                self.e4_client.close()

    def connect_to_e4(self):
        if self.emp_client:
            try:
                if self.e4_client:
                    self.e4_client.disconnect()
                    self.connect_button.config(text="Connect")
                    self.connected_label.config(image=self.disconnected_image)
                    self.streaming_label.config(image=self.nostreaming_image)
                    self.e4_client = None
                else:
                    self.e4_client = EmpaticaE4(self.e4_address)
                    if self.e4_client.connected:
                        if self.error_thread is None:
                            self.error_thread = threading.Thread(target=self.check_e4_error)
                            self.error_thread.start()
                        for stream in EmpaticaDataStreams.ALL_STREAMS:
                            self.e4_client.subscribe_to_stream(stream)
                        self.connected_label.config(image=self.connected_image)
                        self.connect_button.config(text="Disconnect")
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
                print(traceback.print_exc())
        else:
            messagebox.showwarning("Warning", "Connect to server first!")

    def start_e4_streaming(self):
        if self.emp_client:
            if self.e4_client:
                if self.e4_client.connected:
                    try:
                        self.e4_client.start_streaming()
                        self.ovu.e4_view.start_plot(self.e4_client)
                        self.streaming_label.config(image=self.streaming_image)
                    except Exception as e:
                        messagebox.showerror("Exception Encountered",
                                             "Encountered an error when connecting to E4:\n" + str(e))
                        print(traceback.print_exc())
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
                print(traceback.print_exc())
        else:
            try:
                self.devices_thread = threading.Thread(target=self.list_devices_thread)
                self.devices_thread.start()
            except Exception as e:
                messagebox.showerror("Exception Encountered", "Encountered an error when connecting to E4:\n" + str(e))
                print(traceback.print_exc())

    def list_devices_thread(self):
        self.emp_client.list_connected_devices()
        time.sleep(1)
        self.clear_device_list()
        self.populate_device_list()

    def clear_device_list(self):
        for children in self.e4_treeview.get_children():
            self.e4_treeview.delete(children)
        self.e4_treeview_parents = []

    def populate_device_list(self):
        for i in range(0, len(self.emp_client.device_list)):
            self.e4_treeview_parents.append(
                self.e4_treeview.insert("", 'end', str(i),
                                        text=str(self.emp_client.device_list[i].decode("utf-8")),
                                        tags=(treeview_tags[i % 2])))

    def get_selection(self, event):
        self.current_selection = self.e4_treeview.identify_row(event.y)
        if self.current_selection:
            if self.emp_client:
                if len(self.emp_client.device_list) != 0:
                    self.e4_address = self.emp_client.device_list[int(self.current_selection)]
                else:
                    messagebox.showerror("Error", "No connected E4s!")
            else:
                messagebox.showwarning("Warning", "Connect to server first!")

    def save_session(self, filename):
        if self.e4_client:
            if self.e4_client.connected:
                self.e4_client.save_readings(filename)
