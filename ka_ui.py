import os
import pathlib
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
import datetime
from PIL import Image, ImageTk
import pynput
# Custom library imports
from patient_select_ui import PatientSelectWindow
from keystroke_file_ui import KeystrokeSelectWindow
from session_manager_ui import SessionManagerWindow
from logger_util import *
from pyempatica.empaticae4 import EmpaticaClient, EmpaticaE4


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    # Get the patient
    UserSelection = PatientSelectWindow()
    # Check what the result was
    if not UserSelection.cancel:
        KeystrokeSelection = KeystrokeSelectWindow(UserSelection.patient_file)
        if not KeystrokeSelection.cancel:
            SessionManagerWindow(UserSelection.patient_file, KeystrokeSelection.keystroke_file)
