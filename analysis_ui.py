import json
import os
import pathlib
from os import walk, path
import openpyxl
import csv
import datetime
from tkinter import *
from tkinter import filedialog, messagebox


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


class AccuracyPopup:
    def __init__(self, root):
        self.window_entry, self.prim_browse, self.rel_browse, self.acc_report, self.acc_button = None, None, None, None, None
        self.window_label = None
        self.popup = None
        self.window_var = None
        self.prim_filename, self.rel_filename = None, None
        self.generate_accuracy(root)

    def generate_accuracy(self, root):
        # Create a Toplevel window
        self.popup = popup_root = Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x175")
        popup_root.title("Generate Accuracy")

        self.window_label = Label(self.popup, text="Window Size (s)", bg='white')
        self.window_label.place(x=100, y=10, anchor=NE)

        self.window_var = StringVar(self.popup)
        self.window_var.set(str(10))
        self.window_entry = Entry(self.popup, bd=2, width=25, textvariable=self.window_var)
        self.window_entry.place(x=105, y=10)

        self.prim_browse = Button(self.popup, text="Primary File", command=self.select_prim_file, width=15, bd=2)
        self.prim_browse.place(x=145, y=40, anchor=NE)
        self.prim_file_var = StringVar(self.popup)
        self.prim_file_var.set("No File Chosen")
        self.prim_file_label = Label(self.popup, textvariable=self.prim_file_var, width=16, bg='white')
        self.prim_file_label.place(x=145, y=70, anchor=NE)

        self.rel_browse = Button(self.popup, text="Reliability File", command=self.select_rel_file, width=15, bd=2)
        self.rel_browse.place(x=155, y=40, anchor=NW)
        self.rel_file_var = StringVar(self.popup)
        self.rel_file_var.set("No File Chosen")
        self.rel_file_label = Label(self.popup, textvariable=self.rel_file_var, width=16, bg='white')
        self.rel_file_label.place(x=155, y=70, anchor=NW)

        self.acc_button = Button(self.popup, text="Calculate Accuracy", width=15, bd=2, command=self.cal_acc)
        self.acc_button.place(x=150, y=100, anchor=N)

        self.acc_var = StringVar(self.popup)
        self.acc_var.set("Not Calculated")
        self.acc_report = Label(self.popup, textvariable=self.acc_var, width=16, bg='white')
        self.acc_report.place(x=150, y=130, anchor=N)

    def cal_acc(self):
        if path.isfile(self.rel_file_var.get()) and path.isfile(self.prim_file_var.get()):
            pass
        else:
            messagebox.showwarning("Warning", "Please choose valid files!")

    def select_prim_file(self):
        self.prim_filename = filedialog.askopenfilename(filetypes=(("Session Files", "*.json"), ("All Files", "*.*")))
        self.prim_file_var.set(pathlib.Path(self.prim_filename).name)

    def select_rel_file(self):
        self.rel_filename = filedialog.askopenfilename(filetypes=(("Session Files", "*.json"), ("All Files", "*.*")))
        self.rel_file_var.set(pathlib.Path(self.rel_filename).name)

    def close_window(self):
        self.popup.destroy()


def export_columnwise_csv(root, session_dir):
    sessions = get_session_files(session_dir)
    sess_parts = session_dir.split('\\')
    export_dir = path.join(sess_parts[0], sess_parts[1], sess_parts[2], sess_parts[3], 'export')
    export_files = []
    date = datetime.datetime.today().strftime("%B %d, %Y")
    time = datetime.datetime.now().strftime("%H:%M:%S")
    if not path.exists(export_dir):
        os.mkdir(export_dir)
    else:
        export_files = get_export_files(export_dir)
    for file in sessions:
        name = pathlib.Path(file).stem
        if name in export_files:
            continue
        with open(path.join(session_dir, file), 'r') as f:
            session = json.load(f)
        with open(path.join(export_dir, name + ".csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, 'Generated on', date, time])
            writer.writerow(['Event', 'Tag', 'Onset', 'Offset'])
            for key in session:
                # Event
                if type(session[key]) is list:
                    row = [key, session[key][0]]
                    # Duration event
                    if type(session[key][1]) is list:
                        row.append(session[key][1][0])
                        row.append(session[key][1][1])
                    # Frequency event
                    else:
                        row.append(session[key][1])
                # Data Field
                else:
                    row = ['', key, session[key]]
                writer.writerow(row)
    os.startfile(export_dir)
    root.root.iconify()


def populate_spreadsheet(root, patient_file, ksf, session_dir):
    parts = pathlib.Path(patient_file).parts
    template = path.join(parts[0], parts[1], "data", pathlib.Path(ksf).stem + ".xlsx")
    wb = openpyxl.load_workbook(template)
    data_wb = wb['Data']
    sessions = get_sessions(session_dir)
    sess_parts = session_dir.split('\\')
    analysis_dir = path.join(sess_parts[0], sess_parts[1], sess_parts[2], sess_parts[3], 'analysis')
    if not path.exists(analysis_dir):
        os.mkdir(analysis_dir)
    patient = PatientContainer(patient_file)
    m_cells = data_wb.merged_cells
    freq_cell, freq_coords = None, None
    dur_cell, dur_coords = None, None
    st_cell, pt_cell = None, None
    for row in data_wb.iter_rows(3, 3):
        for cell in row:
            if cell.value == 'ST':
                st_cell = cell
            if cell.value == 'PT':
                pt_cell = cell
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
                dur_cell = cell
                coordinates = cell.coord.split(':')
                dur_coords = [''.join([i for i in coordinates[0] if not i.isdigit()]),
                              ''.join([i for i in coordinates[1] if not i.isdigit()])]
                break
        except AttributeError:
            continue
    data_wb['A1'].value = "Assessment: " + sessions[0]['Assessment Name']
    data_wb['A2'].value = "Client: " + patient.name
    row, col = 5, 7
    for session in sessions:
        st_cell = data_wb[''.join([i for i in st_cell.coordinate if not i.isdigit()]) + str(row)]
        pt_cell = data_wb[''.join([i for i in pt_cell.coordinate if not i.isdigit()]) + str(row)]
        key_freq, key_dur = get_keystroke_info(ksf, session)
        d = data_wb['B' + str(row):'H' + str(row)]
        freq_d = data_wb[freq_coords[0] + str(row):freq_coords[1] + str(row)]
        dur_d = data_wb[dur_coords[0] + str(row):dur_coords[1] + str(row)]
        d[0][0].value = session['Condition Name']
        d[0][1].value = session['Session Date']
        d[0][2].value = session['Session Therapist']
        d[0][3].value = session['Primary Therapist']
        d[0][4].value = session['Primary Data']
        d[0][6].value = int(session['Session Time'])/60
        data_wb[st_cell.coordinate].value = session['Session Time']
        data_wb[pt_cell.coordinate].value = session['Pause Time']
        # Populate frequency and duration keys
        for freq, col in zip(key_freq, range(0, len(key_freq))):
            freq_d[0][col].value = freq
        for dur, col in zip(key_dur, range(0, len(key_dur))):
            dur_d[0][col].value = dur
        row += 1
    wb.save(path.join(analysis_dir, sess_parts[3] + "_analysis.xlsx"))
    os.startfile(analysis_dir)
    root.root.iconify()


def get_keystroke_info(key_file, session_file):
    freq_bindings = []
    dur_bindings = []
    key_freq = []
    key_dur = []
    with open(key_file) as f:
        keystroke_json = json.load(f)
    for key in keystroke_json:
        if key == "Frequency":
            for bindings in keystroke_json[key]:
                freq_bindings.append(bindings[0])
            key_freq = [0]*len(freq_bindings)
        if key == "Duration":
            for bindings in keystroke_json[key]:
                dur_bindings.append(bindings[0])
            key_dur = [0]*len(dur_bindings)
    for session_info in session_file:
        session_param = session_file[session_info]
        try:
            if session_param[0] in freq_bindings:
                key_freq[freq_bindings.index(session_param[0])] += 1
            elif session_param[0] in dur_bindings:
                i = dur_bindings.index(session_param[0])
                key_dur[i] += int(session_param[1][1]) - int(session_param[1][0])
        except Exception as e:
            continue
    return key_freq, key_dur


def get_export_files(export_dir):
    export_files = []
    if path.isdir(export_dir):
        _, _, files = next(walk(export_dir))
        for file in files:
            if pathlib.Path(file).suffix == ".csv":
                export_files.append(pathlib.Path(file).stem)
    return export_files


def get_session_files(session_dir):
    session_files = []
    if path.isdir(session_dir):
        _, _, files = next(walk(session_dir))
        for file in files:
            if pathlib.Path(file).suffix == ".json":
                session_files.append(file)
    return session_files


def get_sessions(session_dir):
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
