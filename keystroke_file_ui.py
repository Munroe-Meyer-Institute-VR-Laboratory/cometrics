import os
import pathlib
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
from logger_util import *


class KeystrokeSelectWindow:
    def __init__(self, patient_file):
        self.main_root = Tk()
        self.main_root.config(bg="white", bd=-2)
        self.main_root.geometry("{0}x{1}+0+0".format(300, 460))
        self.main_root.title("Select Keystroke")
        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.main_root, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=20, y=5, height=406, width=270)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="Keystroke File")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_keystroke)

        self.file_scroll = Scrollbar(self.main_root, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=5, height=406)

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.new_button = Button(self.main_root, text="New File", command=self.new_patient_quit)
        self.new_button.place(x=20, y=420)

        self.select_button = Button(self.main_root, text="Select File", command=self.save_and_quit)
        self.select_button.place(x=120, y=420)

        self.cancel_button = Button(self.main_root, text="Cancel", command=self.quit_app)
        self.cancel_button.place(x=220, y=420)

        # Configure keystroke file information
        self.patient_dir = './data/' + pathlib.Path(patient_file).stem + '/'
        self.keystroke_directory = self.patient_dir + 'keystrokes/'
        self.keystroke_file = None
        self.keystroke_files = []
        self.load_keystrokes(self.keystroke_directory)
        self.populate_keystrokes()
        self.new_keystroke, self.cancel, self.selected = False, False, False
        # https://stackoverflow.com/a/111160
        self.main_root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_root.mainloop()

    def populate_keystrokes(self):
        for i in range(0, len(self.keystroke_files)):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
                                                          values=(pathlib.Path(self.keystroke_files[i]).stem,),
                                                          tags=(self.tags[i % 2])))

    def load_keystrokes(self, directory):
        if path.isdir(directory):
            valid_dir = False
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    if not valid_dir:
                        valid_dir = True
                    self.keystroke_files.append(path.join(directory, file))
        else:
            if not path.isdir('./data/'):
                os.mkdir('./data/')
            if not path.isdir(self.patient_dir):
                os.mkdir(self.patient_dir)
            os.mkdir(self.keystroke_directory)

    def on_closing(self):
        self.new_keystroke, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

    def new_patient_quit(self):
        self.new_keystroke, self.cancel, self.selected = True, False, False
        self.main_root.destroy()

    def save_and_quit(self):
        if self.keystroke_file:
            self.new_keystroke, self.cancel, self.selected = False, False, True
            self.main_root.destroy()
        else:
            messagebox.showwarning("Warning", "Select patient from list below first or click 'New Patient'")

    def quit_app(self):
        self.new_keystroke, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

    def get_keystroke(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            self.keystroke_file = self.keystroke_files[int(selection)]

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