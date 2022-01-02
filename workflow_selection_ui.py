import os
import pathlib
import sys
from os import walk
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import Treeview, Style

from logger_util import *


class WorkflowSelectionWindow:
    def __init__(self):
        self.main_root = Tk()
        self.main_root.config(bg="white", bd=-2)
        self.main_root.geometry("{0}x{1}+0+0".format(400, 200))
        self.main_root.title("ECL")
        new_project_label = Label(self.main_root, text="New Project", bg='white',
                                  font=('Purisa', 14))
        new_project_label.place(anchor=CENTER, x=100, y=150)
        click_btn = PhotoImage(file='images/newproject.png')
        img_label = Label(image=click_btn)
        button = Button(self.main_root, image=click_btn, command=self.new_project_clicked,
                        borderwidth=0, highlightthickness=0)
        button.place(anchor=CENTER, x=100, y=75)
        click_btn2 = PhotoImage(file='images/openproject.png')
        img_label2 = Label(image=click_btn2)
        button2 = Button(self.main_root, image=click_btn2, command=self.open_project_clicked,
                         borderwidth=0, highlightthickness=0)
        button2.place(anchor=CENTER, x=300, y=75)
        open_project_label = Label(self.main_root, text="Open Project", bg='white',
                                  font=('Purisa', 14))
        open_project_label.place(anchor=CENTER, x=300, y=150)
        self.new_project_button = Button()
        self.center(self.main_root)
        self.main_root.resizable(width=False, height=False)
        self.main_root.mainloop()

    def new_project_clicked(self):
        print("Clicked new project")

    def open_project_clicked(self):
        print("Clicked open project")

    @staticmethod
    def center(toplevel):
        toplevel.update_idletasks()

        # Tkinter way to find the screen resolution
        screen_width = toplevel.winfo_screenwidth()
        screen_height = toplevel.winfo_screenheight()

        size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
        x = screen_width / 2 - size[0] / 2
        y = screen_height / 2 - size[1] / 2

        toplevel.geometry("+%d+%d" % (x, y))


if __name__ == '__main__':
    WorkflowSelectionWindow()
