import datetime
import os
import pathlib
import traceback
from os import walk
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Treeview, Style
import json
from logger_util import *
import openpyxl
from shutil import copy2


def import_ksf(filename, ksf_dir):
    if filename:
        try:
            wb = openpyxl.load_workbook(filename)
            data_wb = None
            try:
                data_wb = wb['Data']
            except KeyError as e:
                messagebox.showerror("Error", "Sheet 'Data' not found!\n"
                                              "This is required for importing the keystrokes!\n" + str(e))
            if data_wb is not None:
                freq_cell, freq_coords, freq_keys = None, None, []
                dur_cell, dur_coords, dur_keys = None, None, []
                m_cells = data_wb.merged_cells
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
                            coordinates = cell.coord.split(':')
                            dur_coords = [''.join([i for i in coordinates[0] if not i.isdigit()]),
                                          ''.join([i for i in coordinates[1] if not i.isdigit()])]
                            break
                    except AttributeError:
                        continue
                if freq_coords is None:
                    messagebox.showerror("Error", "Frequency bindings were not found, make sure they start at cell J2!")
                elif dur_coords is None:
                    messagebox.showerror("Error", "Duration bindings were not found, make sure they start in the cell "
                                                  "after 'Frequency' header!\nIf the 'Frequency' header ends at column "
                                                  "5, then 'Duration' should start at column 6!")
                else:
                    freq_key_cells = data_wb[freq_coords[0] + str(3):freq_coords[1] + str(3)]
                    freq_tag_cells = data_wb[freq_coords[0] + str(4):freq_coords[1] + str(4)]
                    for key, tag in zip(freq_key_cells[0], freq_tag_cells[0]):
                        freq_keys.append((str(tag.value), str(key.value)))
                    dur_key_cells = data_wb[dur_coords[0] + str(3):dur_coords[1] + str(3)]
                    dur_tag_cells = data_wb[dur_coords[0] + str(4):dur_coords[1] + str(4)]
                    for key, tag in zip(dur_key_cells[0], dur_tag_cells[0]):
                        dur_keys.append((str(tag.value), str(key.value)))
                    conditions = []
                    try:
                        cond_wb = wb['Conditions']
                        for i in range(1, 20):
                            if cond_wb['A' + str(i)].value is None:
                                break
                            else:
                                conditions.append(str(cond_wb['A' + str(i)].value))
                    except KeyError as e:
                        print("No conditions in the workbook!", str(e))
                        messagebox.showwarning("Warning", "Conditions not found in selected spreadsheet!\n"
                                                          "Add sheet called 'Conditions' for this feature!")
                    name = pathlib.Path(filename).stem
                    x = {
                        "Name": name,
                        "Frequency": freq_keys,
                        "Duration": dur_keys,
                        "Conditions": conditions
                    }
                    with open(path.normpath(path.join(ksf_dir, name + '.json')), 'w') as f:
                        json.dump(x, f)
                    keystroke_file = path.join(ksf_dir, name + '.json')
                    copy2(filename, path.join(ksf_dir, pathlib.Path(filename).name))
                    return keystroke_file, x
        except Exception as e:
            messagebox.showwarning("Warning", "Excel format is not correct!\n" + str(e))
            print(traceback.print_exc())
    else:
        messagebox.showwarning("Warning", "Select the protocol Excel tracker spreadsheet.")


def cal_acc(self):
    if path.isfile(self.rel_filename) and path.isfile(self.prim_filename) and path.isfile(self.ksf_filename):
        try:
            with open(self.ksf_filename) as f:
                keystroke_json = json.load(f)
            freq_bindings = []
            dur_bindings = []
            for key in keystroke_json:
                if key == "Frequency":
                    for bindings in keystroke_json[key]:
                        freq_bindings.append(bindings[0])
                if key == "Duration":
                    for bindings in keystroke_json[key]:
                        dur_bindings.append(bindings[0])
            with open(self.prim_filename, 'r') as f:
                prim_session = json.load(f)
            with open(self.rel_filename, 'r') as f:
                rel_session = json.load(f)
            prim_ksf, rel_ksf, rel_type = prim_session["Keystroke File"], rel_session["Keystroke File"], rel_session["Primary Data"]
            # Perform error checking before causing errors
            if not os.path.samefile(prim_ksf, self.ksf_filename):
                messagebox.showerror("Error", "Primary session does not use the selected KSF!")
                return
            elif not os.path.samefile(rel_ksf, self.ksf_filename):
                messagebox.showerror("Error", "Reliability session does not use the selected KSF!")
                return
            elif rel_type == "Primary":
                messagebox.showerror("Error", "Selected reliability file is not a reliability collection!")
                return
            prim_window_freq, prim_window_dur = get_keystroke_window(self.ksf, prim_session, int(self.window_var.get()))
            rel_window_freq, rel_window_dur = get_keystroke_window(self.ksf, rel_session, int(self.window_var.get()))

            if len(prim_window_freq) > len(rel_window_freq):
                for i in range(0, len(prim_window_freq) - len(rel_window_freq)):
                    rel_window_freq.append([0] * len(freq_bindings))
            elif len(prim_window_freq) < len(rel_window_freq):
                for i in range(0, len(rel_window_freq) - len(prim_window_freq)):
                    prim_window_freq.append([0] * len(freq_bindings))
            if len(prim_window_dur) > len(rel_window_dur):
                for i in range(0, len(prim_window_dur) - len(rel_window_dur)):
                    rel_window_dur.append([0] * len(dur_bindings))
            elif len(prim_window_dur) < len(rel_window_dur):
                for i in range(0, len(rel_window_dur) - len(prim_window_dur)):
                    prim_window_dur.append([0] * len(dur_bindings))
            freq_pia = [0] * len(freq_bindings)
            freq_oia_agree, freq_oia_disagree = [0] * len(freq_bindings), [0] * len(freq_bindings)
            freq_nia_agree, freq_nia_disagree = [0] * len(freq_bindings), [0] * len(freq_bindings)
            freq_eia_agree = [0] * len(freq_bindings)
            freq_tia_agree = [0] * len(freq_bindings)
            freq_intervals, dur_intervals = [0] * len(freq_bindings), [0] * len(dur_bindings)
            dur_pia = [0] * len(dur_bindings)
            dur_eia_agree = [0] * len(dur_bindings)
            for row in range(0, len(prim_window_freq)):
                for cell in range(0, len(prim_window_freq[row])):
                    if prim_window_freq[row][cell] > rel_window_freq[row][cell]:
                        larger = prim_window_freq[row][cell]
                        smaller = rel_window_freq[row][cell]
                    else:
                        smaller = prim_window_freq[row][cell]
                        larger = rel_window_freq[row][cell]
                    if smaller == larger:
                        x = 1
                    else:
                        x = smaller / larger
                    freq_pia[cell] += x
                    if larger == 0 and smaller == 0 or larger >= 1 and smaller >= 1:
                        freq_tia_agree[cell] += 1
                    if larger == smaller:
                        freq_eia_agree[cell] += 1

                    if larger == 0 and smaller == 0:
                        freq_nia_agree[cell] += 1
                    elif larger >= 1 and smaller == 0:
                        freq_nia_disagree[cell] += 1

                    if larger >= 1 and smaller >= 1:
                        freq_oia_agree[cell] += 1
                    elif larger >= 1 and smaller == 0:
                        freq_oia_disagree[cell] += 1

                    freq_intervals[cell] += 1
            for row in range(0, len(prim_window_dur)):
                for cell in range(0, len(prim_window_dur[row])):
                    if prim_window_dur[row][cell] > rel_window_dur[row][cell]:
                        larger = prim_window_dur[row][cell]
                        smaller = rel_window_dur[row][cell]
                    else:
                        smaller = prim_window_dur[row][cell]
                        larger = rel_window_dur[row][cell]
                    if smaller == larger:
                        x = 1
                        dur_eia_agree[cell] += 1
                    else:
                        x = smaller / larger
                    dur_pia[cell] += x
                    dur_intervals[cell] += 1
            headers = {
                "Generation Date": datetime.datetime.today().strftime
                                   ("%B %d, %Y") + " " + datetime.datetime.now().strftime("%H:%M:%S"),
                "Primary Session Date": prim_session["Session Date"] + " " + prim_session["Session Start Time"],
                "Primary Therapist": prim_session["Primary Therapist"],
                "Primary Case Manager": prim_session["Case Manager"],
                "Primary Session Therapist": prim_session["Session Therapist"],
                "Reliability Session Date": rel_session["Session Date"] + " " + rel_session["Session Start Time"],
                "Reliability Therapist": rel_session["Primary Therapist"],
                "Reliability Case Manager": rel_session["Case Manager"],
                "Reliability Session Therapist": rel_session["Session Therapist"],
                "Window Size (seconds)": str(self.window_entry.get()) + " seconds"
            }
            path_to_file = filedialog.asksaveasfilename(
                defaultextension='.xlsx', filetypes=[("Excel files", '*.xlsx')],
                title="Choose output filename")
            wb = openpyxl.Workbook()
            ws = wb.active
            wb.create_sheet("Primary Data")
            wb.create_sheet("Reliability Data")
            ws.title = "Interval Measures"
            for x, header in zip(range(1, 10), headers):
                ws.cell(row=x, column=1).value = header
                ws.cell(row=x, column=2).value = headers[header]

            row = 11
            for col, val in enumerate(freq_bindings, start=2):
                ws.cell(row=row, column=col).value = val
            row += 1
            ws.cell(row=row, column=1).value = "Freq PIA"
            for col, val in enumerate(freq_pia, start=2):
                ws.cell(row=row, column=col).value = str(
                    int((val / freq_intervals[freq_pia.index(val)]) * 100)) + "%"
            row += 1
            ws.cell(row=row, column=1).value = "Freq NIA"
            for col, val in enumerate(freq_nia_agree, start=2):
                # This protects from when there are no occurrences at all in the session
                if val == 0 and freq_nia_disagree[freq_nia_agree.index(val)] == 0:
                    ws.cell(row=row, column=col).value = "N/A"
                else:
                    ws.cell(row=row, column=col).value = str(int((val / (val + freq_nia_disagree[
                                                                 freq_nia_agree.index(val)])) * 100)) + "%"
            row += 1
            ws.cell(row=row, column=1).value = "Freq TIA"
            for col, val in enumerate(freq_tia_agree, start=2):
                ws.cell(row=row, column=col).value = str(int((val / freq_intervals[
                                                             freq_tia_agree.index(val)]) * 100)) + "%"
            row += 1
            ws.cell(row=row, column=1).value = "Freq EIA"
            for col, val in enumerate(freq_eia_agree, start=2):
                ws.cell(row=row, column=col).value = str(int((val / freq_intervals[
                                                             freq_eia_agree.index(val)]) * 100)) + "%"
            row += 1
            ws.cell(row=row, column=1).value = "Freq OIA"
            for col, val in enumerate(freq_oia_agree, start=2):
                # This protects from when there are no occurrences at all in the session
                if val == 0 and freq_oia_disagree[freq_oia_agree.index(val)] == 0:
                    ws.cell(row=row, column=col).value = "N/A"
                else:
                    ws.cell(row=row, column=col).value = str(int((val / (val + freq_oia_disagree[
                                                                 freq_oia_agree.index(val)])) * 100)) + "%"
            row += 2
            for col, val in enumerate(dur_bindings, start=2):
                ws.cell(row=row, column=col).value = val
            row += 1
            ws.cell(row=row, column=1).value = "Dur PIA"
            for col, val in enumerate(dur_pia, start=2):
                ws.cell(row=row, column=col).value = str(int((val / dur_intervals[dur_pia.index(val)]) * 100)) + "%"
            row += 1
            ws.cell(row=row, column=1).value = "Dur EIA"
            for col, val in enumerate(dur_eia_agree, start=2):
                ws.cell(row=row, column=col).value = str(int((val / dur_intervals[
                                                             dur_eia_agree.index(val)]) * 100)) + "%"
            row += 1

            ws = wb["Primary Data"]
            row = 1
            for col, val in enumerate(freq_bindings, start=1):
                ws.cell(row=row, column=col).value = val
            row += 1
            for window in prim_window_freq:
                for col, val in enumerate(window, start=1):
                    ws.cell(row=row, column=col).value = val
                row += 1
            row += 1
            for col, val in enumerate(dur_bindings, start=1):
                ws.cell(row=row, column=col).value = val
            row += 1
            for window in prim_window_dur:
                for col, val in enumerate(window, start=1):
                    ws.cell(row=row, column=col).value = val
                row += 1

            ws = wb["Reliability Data"]
            row = 1
            for col, val in enumerate(freq_bindings, start=1):
                ws.cell(row=row, column=col).value = val
            row += 1
            for window in rel_window_freq:
                for col, val in enumerate(window, start=1):
                    ws.cell(row=row, column=col).value = val
                row += 1
            row += 1
            for col, val in enumerate(dur_bindings, start=1):
                ws.cell(row=row, column=col).value = val
            row += 1
            for window in rel_window_dur:
                for col, val in enumerate(window, start=1):
                    ws.cell(row=row, column=col).value = val
                row += 1

            wb.save(path_to_file)
            os.startfile(pathlib.Path(path_to_file).parent)
            self.root.iconify()
        except Exception as e:
            messagebox.showerror("Error", "Error encountered!\n" + str(e))
            print(traceback.print_exc())
    else:
        messagebox.showwarning("Warning", "Please choose valid files!")


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
    template = path.join(*parts[0:-2], "data", pathlib.Path(ksf).stem + ".xlsx")
    wb = openpyxl.load_workbook(template)
    data_wb = wb['Data']
    sessions = get_sessions(session_dir)
    sess_parts = pathlib.Path(session_dir).parts
    analysis_dir = path.join(*sess_parts[0:-1], 'analysis')
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
    row, col, sess = 5, 7, 1
    for session in sessions:
        st_cell = data_wb[''.join([i for i in st_cell.coordinate if not i.isdigit()]) + str(row)]
        pt_cell = data_wb[''.join([i for i in pt_cell.coordinate if not i.isdigit()]) + str(row)]
        key_freq, key_dur = get_keystroke_info(ksf, session)
        d = data_wb['A' + str(row):'H' + str(row)]
        freq_d = data_wb[freq_coords[0] + str(row):freq_coords[1] + str(row)]
        dur_d = data_wb[dur_coords[0] + str(row):dur_coords[1] + str(row)]
        d[0][0].value = sess
        d[0][1].value = session['Condition Name']
        d[0][2].value = session['Session Date']
        d[0][3].value = session['Session Therapist']
        d[0][4].value = session['Primary Therapist']
        d[0][5].value = session['Primary Data']
        d[0][7].value = int(session['Session Time'])/60
        data_wb[st_cell.coordinate].value = session['Session Time']
        data_wb[pt_cell.coordinate].value = session['Pause Time']
        # Populate frequency and duration keys
        for freq, col in zip(key_freq, range(0, len(key_freq))):
            freq_d[0][col].value = freq
        for dur, col in zip(key_dur, range(0, len(key_dur))):
            dur_d[0][col].value = dur
        row += 1
        sess += 1
    wb.save(path.join(analysis_dir, sess_parts[-2] + "_analysis.xlsx"))
    os.startfile(analysis_dir)
    root.root.iconify()


def get_keystroke_window(key_file, session_file, window_size):
    session_time = int(session_file["Session Time"])
    with open(key_file) as f:
        keystroke_json = json.load(f)
    freq_bindings = []
    dur_bindings = []
    for key in keystroke_json:
        if key == "Frequency":
            for bindings in keystroke_json[key]:
                freq_bindings.append(bindings[0])
        if key == "Duration":
            for bindings in keystroke_json[key]:
                dur_bindings.append(bindings[0])
    if session_time % window_size != 0:
        session_time += window_size - (session_time % window_size)
    freq_windows = [[0] * len(freq_bindings) for i in range(int(session_time / window_size))]
    dur_windows = [[0] * len(dur_bindings) for i in range(int(session_time / window_size))]
    keys = list(session_file.keys())[14:]
    dur_keys, freq_keys = [], []
    for key in keys:
        if type(session_file[key][1]) is list:
            dur_keys.append(key)
        else:
            freq_keys.append(key)
    for i in range(0, session_time, window_size):
        for key in freq_keys[:]:
            if i <= session_file[key][1] < (i + window_size):
                freq_windows[int(i / window_size)][freq_bindings.index(session_file[key][0])] += 1
                freq_keys.remove(key)
            else:
                break
    for i in range(0, session_time, window_size):
        for key in dur_keys[:]:
            if i <= session_file[key][1][0] < (i + window_size):
                dur_windows[int(i / window_size)][dur_bindings.index(session_file[key][0])] += 1
                if i <= session_file[key][1][1] < (i + window_size):
                    dur_keys.remove(key)
            elif i <= session_file[key][1][1] < (i + window_size):
                dur_windows[int(i / window_size)][dur_bindings.index(session_file[key][0])] += 1
                dur_keys.remove(key)
            else:
                break
    return freq_windows, dur_windows


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
            print(str(e))
            print(traceback.print_exc())
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
            data = json.load(f)
            if data['Primary Data'] == "Primary":
                sessions.append(data)
    return sessions


def open_keystroke_file(key_file):
    bindings = []
    with open(key_file) as f:
        keystroke_json = json.load(f)
    for key in keystroke_json:
        if key != "Name":
            bindings.append((key, keystroke_json[key]))
    return bindings
