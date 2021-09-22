import os
import pathlib
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
from logger_util import *
import openpyxl
from shutil import copy2


class KeystrokeSelectWindow:
    def __init__(self, experiment_dir, patient_file):
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
        self.treeview.bind("<Double-Button-1>", self.select_keystroke)
        self.treeview.bind("<Button-1>", self.get_keystroke)

        self.file_scroll = Scrollbar(self.main_root, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=5, height=406)

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.new_button = Button(self.main_root, text="New File", command=self.new_keystroke_popup, width=11)
        self.new_button.place(x=20, y=411, anchor=NW)

        self.select_button = Button(self.main_root, text="Select File", command=self.save_and_quit, width=12)
        self.select_button.place(x=155, y=411, anchor=N)

        self.cancel_button = Button(self.main_root, text="Cancel", command=self.quit_app, width=11)
        self.cancel_button.place(x=290, y=411, anchor=NE)

        # Configure keystroke file information
        self.experiment_dir = path.join(experiment_dir, 'data')
        self.patient_dir = path.join(self.experiment_dir, pathlib.Path(patient_file).stem)
        self.keystroke_directory = path.join(self.patient_dir, 'keystrokes')

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
            if not path.isdir(self.experiment_dir):
                os.mkdir(self.experiment_dir)
            if not path.isdir(self.patient_dir):
                os.mkdir(self.patient_dir)
            os.mkdir(self.keystroke_directory)

    def on_closing(self):
        self.new_keystroke, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

    def create_keystroke(self, name):
        with open(path.join(self.keystroke_directory, name + '.json'), 'w') as f:
            x = {
                "Name": name,
                "Frequency": [],
                "Duration": []
            }
            json.dump(x, f)
        self.keystroke_file = path.join(self.keystroke_directory, name + '.json')

    def new_keystroke_quit(self, name):
        if name and name != "":
            self.create_keystroke(name)
            self.main_root.destroy()

    def new_keystroke_popup(self):
        self.new_keystroke, self.cancel, self.selected = True, False, False
        Popup(self, self.main_root)

    def save_and_quit(self):
        if self.keystroke_file:
            self.new_keystroke, self.cancel, self.selected = False, False, True
            self.main_root.destroy()
        else:
            messagebox.showwarning("Warning", "Select protocol from list below first or click 'New File'")

    def quit_app(self):
        self.new_keystroke, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

    def select_keystroke(self, event):
        if self.treeview:
            selection = self.treeview.identify_row(event.y)
            if selection:
                if self.keystroke_file:
                    if self.keystroke_file == self.keystroke_files[int(selection)]:
                        self.save_and_quit()
                    else:
                        self.keystroke_file = self.keystroke_files[int(selection)]
                else:
                    self.keystroke_file = self.keystroke_files[int(selection)]

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


class Popup:
    def __init__(self, top, root):
        self.caller = top
        self.top_root = root
        self.entry, self.import_button = None, None
        self.keystroke_name_entry_pop_up(root)

    def keystroke_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x50")
        popup_root.title("Enter Protocol Name")

        # Create an Entry Widget in the Toplevel window
        self.entry = Entry(popup_root, bd=2, width=25)
        self.entry.pack()
        self.import_button = Button(popup_root, text="Import", command=self.import_ksf, width=8)
        self.import_button.place(x=145, y=22, anchor=NE)

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win, width=8)
        button.place(x=155, y=22, anchor=NW)

    def import_ksf(self):
        filename = filedialog.askopenfilename(filetypes=(("Excel Files", "*.xlsx"), ("All Files", "*.*")))
        if filename:
            wb = openpyxl.load_workbook(filename)
            data_wb = wb['Data']
            freq_cell, freq_coords, freq_keys = None, None, []
            dur_cell, dur_coords, dur_keys = None, None, []
            m_cells = data_wb.merged_cells
            for cell in m_cells:
                try:
                    if cell.start_cell.coordinate == 'J2' and cell.start_cell.value == "Frequency":
                        freq_cell = cell
                        coordinates = cell.coord.split(':')
                        freq_coords = [''.join([i for i in coordinates[0] if not i.isdigit()]),
                                       ''.join([i for i in coordinates[1] if not i.isdigit()])]
                        break
                except AttributeError:
                    continue
            for cell in m_cells:
                try:
                    if cell.min_col == freq_cell.max_col + 1 and cell.start_cell.value == "Duration":
                        coordinates = cell.coord.split(':')
                        dur_coords = [''.join([i for i in coordinates[0] if not i.isdigit()]),
                                      ''.join([i for i in coordinates[1] if not i.isdigit()])]
                        break
                except AttributeError:
                    continue
            freq_key_cells = data_wb[freq_coords[0] + str(3):freq_coords[1] + str(3)]
            freq_tag_cells = data_wb[freq_coords[0] + str(4):freq_coords[1] + str(4)]
            for key, tag in zip(freq_key_cells[0], freq_tag_cells[0]):
                freq_keys.append((tag.value, key.value))
            dur_key_cells = data_wb[dur_coords[0] + str(3):dur_coords[1] + str(3)]
            dur_tag_cells = data_wb[dur_coords[0] + str(4):dur_coords[1] + str(4)]
            for key, tag in zip(dur_key_cells[0], dur_tag_cells[0]):
                dur_keys.append((tag.value, key.value))
            name = pathlib.Path(filename).stem
            with open(path.join(self.caller.keystroke_directory, name + '.json'), 'w') as f:
                x = {
                    "Name": name,
                    "Frequency": freq_keys,
                    "Duration": dur_keys
                }
                json.dump(x, f)
            self.caller.keystroke_file = path.join(self.caller.keystroke_directory, name + '.json')
            copy2(filename, path.join(self.caller.experiment_dir, pathlib.Path(filename).name))
            self.close_win()
        else:
            messagebox.showwarning("Warning", "Select the protocol Excel tracker spreadsheet.")

    def close_win(self):
        if self.caller.keystroke_file:
            self.top_root.destroy()
        else:
            self.caller.new_keystroke_quit(self.entry.get())
