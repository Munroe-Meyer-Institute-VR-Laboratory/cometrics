import os
import pathlib
import sys
from os import walk
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview, Style
from logger_util import *


class ExperimentSelectWindow:
    def __init__(self):
        self.main_root = Tk()
        self.main_root.config(bg="white", bd=-2)
        self.main_root.geometry("{0}x{1}+0+0".format(300, 460))
        self.main_root.title("Select Experiment")
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
        self.treeview.heading("1", text="Experiment")
        self.treeview.column("1", width=65, stretch=YES, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_experiment)
        # self.treeview.bind("<Double-Button-1>", self.select_experiment)

        self.file_scroll = Scrollbar(self.main_root, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=5, height=406)

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"

        self.new_button = Button(self.main_root, text="New", command=self.new_experiment_popup, width=11)
        self.new_button.place(x=20, y=411, anchor=NW)

        self.select_button = Button(self.main_root, text="Select", command=self.save_and_quit, width=12)
        self.select_button.place(x=155, y=411, anchor=N)

        self.cancel_button = Button(self.main_root, text="Cancel", command=self.quit_app, width=11)
        self.cancel_button.place(x=290, y=411, anchor=NE)

        self.top_dir = None
        self.experiment_dirs = []
        self.experiment_dir = None
        self.load_experiments()
        self.populate_experiments()
        self.new_experiment, self.cancel, self.selected = False, False, False
        # https://stackoverflow.com/a/111160
        self.main_root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_root.mainloop()

    def populate_experiments(self):
        for i in range(0, len(self.experiment_dirs)):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
                                                          values=(pathlib.Path(self.experiment_dirs[i]).stem,),
                                                          tags=(self.tags[i % 2])))

    def load_experiments(self):
        self.top_dir = None
        while not self.top_dir:
            self.top_dir = filedialog.askdirectory(title='Select root directory to save files')
            print(self.top_dir)
            if not self.top_dir:
                if not messagebox.askokcancel("Exit", "Press cancel to close program"):
                    sys.exit()
            else:
                self.top_dir = path.normpath(self.top_dir)
        if path.isdir(self.top_dir):
            _, dirs, _ = next(walk(self.top_dir))
            for dir in dirs:
                self.experiment_dirs.append(path.normpath(path.join(self.top_dir, dir)))
        else:
            os.mkdir(path.join(self.top_dir, 'experiments'))

    def on_closing(self):
        if self.main_root:
            self.new_experiment, self.cancel, self.selected = False, True, False
            self.main_root.quit()
            self.main_root.destroy()

    def new_experiment_popup(self):
        self.new_experiment, self.cancel, self.selected = False, False, True
        Popup(self, self.main_root)

    def new_experiment_quit(self, name):
        if name and name != "":
            self.create_experiment(name)
            self.main_root.quit()
            self.main_root.destroy()

    def save_and_quit(self):
        if self.experiment_dir:
            self.new_experiment, self.cancel, self.selected = False, False, True
            self.main_root.quit()
            self.main_root.destroy()
        else:
            messagebox.showwarning("Warning", "Select experiment from list below first or click 'New'")

    def quit_app(self):
        self.new_experiment, self.cancel, self.selected = False, True, False
        self.main_root.quit()
        self.main_root.destroy()

    def create_experiment(self, experiment_name):
        os.mkdir(path.join(self.top_dir, experiment_name))
        self.experiment_dir = path.normpath(path.join(self.top_dir, experiment_name))

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

    def select_experiment(self, event):
        if self.treeview:
            selection = self.treeview.identify_row(event.y)
            if selection:
                if self.experiment_dir:
                    if self.experiment_dir == self.experiment_dirs[int(selection)]:
                        self.save_and_quit()
                    else:
                        self.experiment_dir = self.experiment_dirs[int(selection)]
                else:
                    self.experiment_dir = self.experiment_dirs[int(selection)]

    def get_experiment(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            if self.experiment_dir:
                if self.experiment_dir == self.experiment_dirs[int(selection)]:
                    self.save_and_quit()
                else:
                    self.experiment_dir = self.experiment_dirs[int(selection)]
            else:
                self.experiment_dir = self.experiment_dirs[int(selection)]


class Popup:
    def __init__(self, top, root):
        self.caller = top
        self.entry = None
        self.patient_name_entry_pop_up(root)

    def patient_name_entry_pop_up(self, root):
        # Create a Toplevel window
        popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x50")
        popup_root.title("Enter Experiment Name")

        # Create an Entry Widget in the Toplevel window
        self.entry = Entry(popup_root, bd=2, width=25)
        self.entry.pack()

        # Create a Button Widget in the Toplevel Window
        button = Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)

    def close_win(self):
        self.caller.new_experiment_quit(self.entry.get())
