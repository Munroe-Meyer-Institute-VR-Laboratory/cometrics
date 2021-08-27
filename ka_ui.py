from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style

from logger_util import *
import datetime
from PIL import Image, ImageTk


class StaticImages(Frame):
    def __init__(self, parent, **kw):
        super().__init__(**kw)
        self.unmc_shield_canvas = Canvas(parent, width=250, height=100, bg="white", bd=-2)
        self.unmc_shield_canvas.place(x=2, y=2)
        self.unmc_shield_img = ImageTk.PhotoImage(Image.open('UNMCLogo.jpg').resize((250, 100), Image.ANTIALIAS))
        self.unmc_shield_canvas.create_image(0, 0, anchor=NW, image=self.unmc_shield_img)


class PatientSelectWindow:
    def __init__(self):
        self.main_root = Tk()
        self.main_root.config(bg="white", bd=-2)
        self.main_root.geometry("{0}x{1}+0+0".format(300, 700))
        self.main_root.title("KSA - KeyStroke Annotator")
        style = Style()
        style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
                        font=('Calibri', 11))  # Modify the font of the body
        style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
        style.map('Treeview', foreground=self.fixed_map('foreground'),
                  background=self.fixed_map('background'))
        # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
        self.treeview = Treeview(self.main_root, style="mystyle.Treeview", height=18, selectmode='browse')
        self.treeview.place(x=5, y=5)

        self.treeview.heading("#0", text="#", anchor='c')
        self.treeview["columns"] = ["1"]
        self.treeview.column("#0", width=65, stretch=NO, anchor='c')
        self.treeview.heading("1", text="Patient")
        self.treeview.column("1", width=65, stretch=NO, anchor='c')

        self.treeview.tag_configure('odd', background='#E8E8E8')
        self.treeview.tag_configure('even', background='#DFDFDF')
        self.treeview.bind("<Button-1>", self.get_patient)

        self.file_scroll = Scrollbar(self.main_root, orient="vertical", command=self.treeview.yview)
        self.file_scroll.place(x=0, y=0, height=385)

        self.treeview.configure(yscrollcommand=self.file_scroll.set)
        self.tree_parents = []
        self.tags = ['odd', 'even']
        self.current_selection = "I000"
        self.patient_file = None

        self.new_button = Button(self.main_root, text="New Patient", command=self.new_patient_quit)
        self.new_button.place(x=20, y=620)

        self.select_button = Button(self.main_root, text="Select Patient", command=self.save_and_quit)
        self.select_button.place(x=120, y=620)

        self.cancel_button = Button(self.main_root, text="Cancel", command=self.quit_app)
        self.cancel_button.place(x=220, y=620)

        self.patient_files = []
        self.new_patient, self.cancel, self.selected = False, False, False
        # https://stackoverflow.com/a/111160
        self.main_root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main_root.mainloop()

    def on_closing(self):
        self.new_patient, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

    def new_patient_quit(self):
        self.new_patient, self.cancel, self.selected = True, False, False
        self.main_root.destroy()

    def save_and_quit(self):
        self.new_patient, self.cancel, self.selected = False, False, True
        self.main_root.destroy()

    def quit_app(self):
        self.new_patient, self.cancel, self.selected = False, True, False
        self.main_root.destroy()

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

    def get_patient(self, event):
        selection = self.treeview.identify_row(event.y)
        if selection:
            Patient.update_fields(self.patient_files[selection])


class PatientContainer:
    def __init__(self):
        self.patient_path = None

    def update_fields(self, filepath):
        self.patient_path = filepath


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))

    Patient = PatientContainer()
    UserSelection = PatientSelectWindow()

    if not UserSelection.cancel:
        root = Tk()
        root.config(bg="white", bd=-2)
        pad = 3
        root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth() - pad, root.winfo_screenheight() - pad))
        root.title("KSA - KeyStroke Annotator")

        StaticImages(root)
        root.mainloop()
