from tkinter import *


class HistoryViewPanel:
    def __init__(self, parent):
        self.frame = Frame(parent, width=700, height=(parent.winfo_screenheight() - 255))
        self.frame.place(x=780, y=95)
