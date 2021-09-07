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


class SessionStatisticsPopup:
    def __init__(self, parent):
        popup_root = self.popup_root = Toplevel(parent)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("800x500")
        popup_root.title("Session Statistics")

        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 10))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(popup_root, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=20, y=30, height=400, width=300)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1", "2", "3"]
        self.treeview.column("#0", width=40, stretch=NO, anchor='c')
        self.treeview.heading("1", text="Condition")
        self.treeview.column("1", width=40, stretch=NO, anchor='c')
        self.treeview.heading("2", text="Reliability")
        self.treeview.column("2", width=65, stretch=YES, anchor='c')
        self.treeview.heading("3", text="Dur")
        self.treeview.column("3", width=65, stretch=NO, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.tag_configure('toggle', background='red')
        #
        # self.treeview.bind("<Button-1>", self.get_selection)
        # self.treeview.bind("<Double-Button-1>", self.change_keybind)

        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview1 = Treeview(popup_root, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview1.place(x=320, y=30, height=400, width=300)

        self.treeview1.heading("#0", text="#", anchor='c')
        self.treeview1["columns"] = ["1", "2", "3"]
        self.treeview1.column("#0", width=40, stretch=NO, anchor='c')
        self.treeview1.heading("1", text="Condition")
        self.treeview1.column("1", width=40, stretch=NO, anchor='c')
        self.treeview1.heading("2", text="Reliability")
        self.treeview1.column("2", width=65, stretch=YES, anchor='c')
        self.treeview1.heading("3", text="Dur")
        self.treeview1.column("3", width=65, stretch=NO, anchor='c')

        self.treeview1.tag_configure('odd', background='#E8E8E8')
        self.treeview1.tag_configure('even', background='#DFDFDF')
        self.treeview1.tag_configure('toggle', background='red')

        self.treeview.yview = (self.treeview.yview, self.treeview1.yview)


        self.file_scroll = Scrollbar(popup_root, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=2, y=30, height=400)

        self.file_scroll1 = Scrollbar(popup_root, orient="horizontal", command=self.treeview1.xview)
        self.file_scroll1.place(x=320, y=420, width=300)

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.treeview1.configure(yscrollcommand=self.file_scroll.set, xscrollcommand=self.file_scroll1.set)


        self.tree_parents = []
        self.tree1_parents = []
        self.tags = ['odd', 'even', 'toggle']
        self.current_selection = "I000"

        self.populate_treeview()

    def populate_treeview(self):
        for i in range(0, 50):
            self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
                                                          values=(str(i), str(i),),
                                                          tags=(self.tags[i % 2])))
            self.tree1_parents.append(self.treeview1.insert("", 'end', str(i), text=str(i),
                                                          values=(str(i), str(i),),
                                                          tags=(self.tags[i % 2])))

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
