import json
import os
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


def export_columnwise_csv(session_dir):
    sessions = get_session_files(session_dir)
    sess_parts = session_dir.split('\\')
    export_dir = path.join(sess_parts[0], sess_parts[1], sess_parts[2], sess_parts[3], 'export')
    export_files = []
    if not path.exists(export_dir):
        os.mkdir(export_dir)
    else:
        get_export_files(export_dir)


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
        try:
            if session_file[session_info][0] in freq_bindings:
                key_freq[freq_bindings.index(session_file[session_info][0])] += 1
            elif session_file[session_info][0] in dur_bindings:
                i = dur_bindings.index(session_file[session_info][0])
                key_dur[i] += int(session_file[session_info][1][1]) - int(session_file[session_info][1][0])
        except Exception as e:
            continue
    return key_freq, key_dur


def get_export_files(export_dir):
    export_files = []
    if path.isdir(export_dir):
        _, _, files = next(walk(export_dir))
        for file in files:
            if pathlib.Path(file).suffix == ".xlsx":
                export_files.append(file)
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
