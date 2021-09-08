import json
import pathlib
from os import walk, path
import openpyxl


class PatientContainer:
    def __init__(self, patient_file):
        self.source_file = patient_file
        self.patient_json = None
        self.patient_path = None
        self.name = None
        self.medical_record_number = None
        if patient_file:
            self.update_fields(patient_file)

    def update_fields(self, filepath):
        f = open(filepath)
        self.patient_json = json.load(f)
        self.name = self.patient_json["Name"]
        self.medical_record_number = self.patient_json["MRN"]

    def save_patient(self, name, mrn):
        with open(self.source_file, 'w') as f:
            x = {
                "Name": name,
                "MRN": mrn
            }
            json.dump(x, f)

# class SessionStatisticsPopup:
#     def __init__(self, parent):
#         popup_root = self.popup_root = Toplevel(parent)
#         popup_root.config(bg="white", bd=-2)
#         popup_root.geometry("800x500")
#         popup_root.title("Session Statistics")
#
#         style = Style()
#         style.configure("mystyle.Treeview", highlightthickness=0, bd=0,
#                         font=('Calibri', 10))  # Modify the font of the body
#         style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'))  # Modify the font of the headings
#         style.map('Treeview', foreground=self.fixed_map('foreground'),
#                   background=self.fixed_map('background'))
#         # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
#         self.treeview = Treeview(popup_root, style="mystyle.Treeview", height=18, selectmode='browse')
#         self.treeview.place(x=20, y=30, height=386, width=300)
#
#         self.treeview.heading("#0", text="#", anchor='c')
#         self.treeview["columns"] = ["1", "2", "3"]
#         self.treeview.column("#0", width=40, stretch=NO, anchor='c')
#         self.treeview.heading("1", text="Condition")
#         self.treeview.column("1", width=40, stretch=YES, anchor='c')
#         self.treeview.heading("2", text="Reliability")
#         self.treeview.column("2", width=65, stretch=YES, anchor='c')
#         self.treeview.heading("3", text="Dur")
#         self.treeview.column("3", width=65, stretch=NO, anchor='c')
#
#         self.treeview.tag_configure('odd', background='#E8E8E8')
#         self.treeview.tag_configure('even', background='#DFDFDF')
#         self.treeview.tag_configure('toggle', background='red')
#         #
#         # self.treeview.bind("<Button-1>", self.get_selection)
#         # self.treeview.bind("<Double-Button-1>", self.change_keybind)
#
#         # style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])  # Remove the borders
#         self.treeview1 = Treeview(popup_root, style="mystyle.Treeview", height=18, selectmode='browse')
#         self.treeview1.place(x=320, y=30, height=386, width=460)
#
#         self.treeview1.heading("#0", text="#", anchor='c')
#         self.treeview1["columns"] = ["1", "2", "3", "4", "5", "6"]
#         self.treeview1.column("#0", width=40, stretch=NO, anchor='c')
#         self.treeview1.heading("1", text="Condition")
#         self.treeview1.column("1", width=40, stretch=NO, anchor='c')
#         self.treeview1.heading("2", text="Reliability")
#         self.treeview1.column("2", width=65, stretch=YES, anchor='c')
#         self.treeview1.heading("3", text="Dur")
#         self.treeview1.column("3", width=65, stretch=NO, anchor='c')
#         self.treeview1.heading("4", text="Dur")
#         self.treeview1.column("4", width=65, stretch=NO, anchor='c')
#         self.treeview1.heading("5", text="Dur")
#         self.treeview1.column("5", width=65, stretch=NO, anchor='c')
#         self.treeview1.heading("6", text="Dur")
#         self.treeview1.column("6", width=65, stretch=NO, anchor='c')
#
#         self.treeview1.tag_configure('odd', background='#E8E8E8')
#         self.treeview1.tag_configure('even', background='#DFDFDF')
#         self.treeview1.tag_configure('toggle', background='red')
#
#         self.file_scroll = Scrollbar(popup_root, orient="vertical", command=self.scroll_control)
#         self.file_scroll.place(x=2, y=30, height=386)
#
#         self.file_scroll1 = Scrollbar(popup_root, orient="horizontal", command=self.treeview1.xview)
#         self.file_scroll1.place(x=320, y=416, width=460, anchor=NW)
#
#         self.treeview.configure(yscrollcommand=self.file_scroll.set)
#         self.treeview1.configure(yscrollcommand=self.file_scroll.set, xscrollcommand=self.file_scroll1.set)
#
#         self.treeview.bind("<MouseWheel>", self.scroll_together)
#         self.treeview1.bind("<MouseWheel>", self.scroll_together)
#
#         self.tree_parents = []
#         self.tree1_parents = []
#         self.tags = ['odd', 'even', 'toggle']
#         self.current_selection = "I000"
#
#         self.populate_treeview()
#
#     def scroll_control(self, *args):
#         self.treeview.yview(*args)
#         self.treeview1.yview(*args)
#
#     def scroll_together(self, event):
#         self.treeview.yview("scroll", int(-1*(event.delta/120)), "units")
#         self.treeview1.yview("scroll", int(-1*(event.delta/120)), "units")
#         return "break"
#
#     def populate_treeview(self):
#         for i in range(0, 50):
#             self.tree_parents.append(self.treeview.insert("", 'end', str(i), text=str(i),
#                                                           values=(str(i), str(i),),
#                                                           tags=(self.tags[i % 2])))
#             self.tree1_parents.append(self.treeview1.insert("", 'end', str(i), text=str(i),
#                                                             values=(str(i), str(i), str(i), str(i), str(i)),
#                                                             tags=(self.tags[i % 2])))
#
#     def fixed_map(self, option):
#         # https://stackoverflow.com/a/62011081
#         # Fix for setting text colour for Tkinter 8.6.9
#         # From: https://core.tcl.tk/tk/info/509cafafae
#         #
#         # Returns the style map for 'option' with any styles starting with
#         # ('!disabled', '!selected', ...) filtered out.
#
#         # style.map() returns an empty list for missing options, so this
#         # should be future-safe.
#         style = Style()
#         return [elm for elm in style.map('Treeview', query_opt=option) if
#                 elm[:2] != ('!disabled', '!selected')]


def populate_spreadsheet(patient_file, ksf, session_dir):
    wb = openpyxl.load_workbook('reference/New Template Graphing Practice.xlsx')
    data_wb = wb['Data']
    bindings = open_keystroke_file(ksf)
    sessions = get_session_files(session_dir)
    patient = PatientContainer(patient_file)
    row = 5
    data_wb['A1'].value = "Assessment: " + sessions[0]['Assessment Name']
    data_wb['A2'].value = "Client: " + patient.name
    for session in sessions:
        d = data_wb['B' + str(row):'AL' + str(row)]
        d[0][0].value = session['Condition Name']
        d[0][1].value = session['Session Date']
        d[0][2].value = session['Session Therapist']
        d[0][3].value = session['Primary Therapist']
        d[0][4].value = session['Primary Data']
        d[0][6].value = int(session['Session Time'])/60
        row += 1
    wb.save('test.xlsx')


def get_session_files(session_dir):
    session_files = []
    sessions = []
    if path.isdir(session_dir):
        _, _, files = next(walk(session_dir))
        for file in files:
            if pathlib.Path(file).suffix == ".json":
                session_files.append(file)
    for file in session_files:
        with open(path.join(session_dir, file), 'r') as f:
            sessions.append(json.load(f))
    return sessions


def open_keystroke_file(key_file):
    bindings = []
    with open(key_file) as f:
        keystroke_json = json.load(f)
    for key in keystroke_json:
        if key != "Name":
            bindings.append((key, keystroke_json[key]))
    return bindings
