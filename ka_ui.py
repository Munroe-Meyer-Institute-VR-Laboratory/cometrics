from tkinter import *
from tkinter import filedialog, messagebox
from logger_util import *
import datetime


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    root = Tk()
    root.config(bg="white", bd=-2)
    pad = 3
    root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
    root.title("KSA - KeyStroke Annotator")
