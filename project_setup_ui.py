import json
import os
import pathlib
from tkinter import *
from tkinter import messagebox, filedialog
import yaml
from config_utils import ConfigUtils
from ksf_utils import import_ksf
from logger_util import *
from tkinter_utils import center, get_display_size, get_treeview_style, build_treeview, EntryPopup, select_focus, \
    NewKeyPopup
from ui_params import project_treeview_params as ptp, treeview_tags, ksf_distance, window_ratio


class ProjectSetupWindow:
    def __init__(self, config):
        self.config = config
        # region Window setup
        if len(config.get_screen_size()) == 2:
            self.main_root = Tk()
            self.window_height = int(config.get_screen_size()[0] * window_ratio)
            self.window_width = int(config.get_screen_size()[1] * window_ratio)
        else:
            self.main_root, self.window_height, self.window_width = get_display_size()
            config.set_screen_size(self.window_height, self.window_width)
            self.window_width = int(self.window_width * window_ratio)
            self.window_height = int(self.window_height * window_ratio)
        # endregion
        # Create Project Setup label
        self.project_setup_label = Label(self.main_root, text="Project Setup", font=('Purisa', 15, 'bold'))
        self.project_setup_label.place(x=ptp[0], y=ptp[1] / 2, anchor=W)
        # Create global style
        _ = get_treeview_style()
        # Define heading dicts
        project_heading_dict = {"#0": ["Recent Projects", 'w', 1, YES, 'w']}
        patient_heading_dict = {"#0": ["Existing Patients", 'w', 1, YES, 'w']}
        concern_heading_dict = {"#0": ["Presenting Concerns", 'w', 1, YES, 'w']}
        # Build treeviews
        self.project_treeview_parents, self.patient_treeview_parents, self.concern_treeview_parents = [], [], []
        project_treeview_height = int(self.window_height * 0.3)
        treeview_width = int(self.window_width * 0.45)
        self.project_treeview, self.project_filescroll = build_treeview(self.main_root, ptp[0], ptp[1],
                                                                        project_treeview_height,
                                                                        treeview_width,
                                                                        project_heading_dict,
                                                                        double_bind=self.select_project)
        self.recent_projects = config.get_recent_projects()
        self.populate_recent_projects()
        patient_treeview_height = int(self.window_height * 0.2)
        self.patient_treeview, self.patient_filescroll = build_treeview(self.main_root, ptp[0],
                                                                        ptp[1] + int(self.window_height * 0.35),
                                                                        patient_treeview_height,
                                                                        treeview_width,
                                                                        patient_heading_dict,
                                                                        double_bind=self.select_patient)

        self.concern_treeview, self.concern_filescroll = build_treeview(self.main_root, ptp[0],
                                                                        ptp[1] + int(self.window_height * 0.35) + int(
                                                                            self.window_height * 0.25),
                                                                        patient_treeview_height,
                                                                        treeview_width,
                                                                        concern_heading_dict,
                                                                        double_bind=self.select_concern)
        # Get phases and create dropbox
        self.phases = config.get_phases()
        if self.phases:
            self.phases_var = StringVar(self.main_root)
            self.phases_var.set("Select a Phase")
            self.phases_var.trace("w", self.phase_callback)
            self.phases_menu = OptionMenu(self.main_root, self.phases_var, *self.phases)
            self.phases_menu.place(x=ptp[0],
                                   y=ptp[1] + int(self.window_height * 0.35) + int(self.window_height * 0.25) + int(
                                       self.window_height * 0.21),
                                   width=int(self.window_width * 0.2))
            self.phases_menu.config(state='disabled')
        # Create KSF label
        self.ksf_setup_label = Label(self.main_root, text="Keystroke File Setup", font=('Purisa', 15, 'bold'))
        self.ksf_setup_label.place(x=10 + self.window_width / 2, y=ptp[1] / 2, anchor=W)
        self.ksf_path = Label(self.main_root, text="Select Condition and Phase to Load", font=('Purisa', 11, 'italic'),
                              bg='white', width=30, anchor='w')
        self.ksf_path.place(x=10 + self.window_width / 2, y=ptp[1])
        self.ksf_import = Button(self.main_root, text="Import", font=('Purisa', 11), width=10,
                                 command=self.import_concern_ksf)
        self.ksf_import.place(x=300 + 10 + self.window_width / 2, y=ptp[1] - 4)
        self.ksf_import.config(state='disabled')
        # Define frequency and duration key headers
        freq_heading_dict = {"#0": ["Frequency Key", 'w', 1, YES, 'w']}
        dur_heading_dict = {"#0": ["Duration Key", 'w', 1, YES, 'w']}
        key_column_dict = {"1": ["Tag", 'w', 1, YES, 'w']}
        key_treeview_height = int(self.window_height * 0.2)
        self.frequency_treeview_parents = []
        self.frequency_key_treeview, self.frequency_key_filescroll = build_treeview(self.main_root,
                                                                                    20 + self.window_width / 2,
                                                                                    ptp[1] + (self.window_height * 0.1),
                                                                                    key_treeview_height,
                                                                                    treeview_width,
                                                                                    freq_heading_dict,
                                                                                    key_column_dict)
                                                                                    # double_bind=self.select_frequency_key)
        self.duration_treeview_parents = []
        self.duration_key_treeview, self.duration_key_filescroll = build_treeview(self.main_root,
                                                                                  20 + self.window_width / 2,
                                                                                  ptp[1] + (
                                                                                          self.window_height * 0.15) + (
                                                                                          self.window_height * 0.2),
                                                                                  key_treeview_height,
                                                                                  treeview_width,
                                                                                  dur_heading_dict,
                                                                                  key_column_dict)
                                                                                  # double_bind=self.select_duration_key)

        self.continue_button = Button(self.main_root, text='Continue', width=12, command=self.continue_project)
        self.continue_button.place(x=self.window_width*0.78, y=ptp[1] + int(self.window_height * 0.35) + int(self.window_height * 0.25) + int(
                                       self.window_height * 0.21))
        self.continue_button.config(state='disabled')
        self.cancel_button = Button(self.main_root, text='Cancel', width=12, command=self.cancel_project)
        self.cancel_button.place(x=self.window_width*0.78+100, y=ptp[1] + int(self.window_height * 0.35) + int(self.window_height * 0.25) + int(
                                       self.window_height * 0.21))
        # Create window geometry, center, and display
        self.main_root.geometry("{0}x{1}+0+0".format(self.window_width, self.window_height))
        center(self.main_root)
        self.main_root.title("cometrics v0.8.0")
        self.icon = PhotoImage(file=r'images/cometrics_icon.png')
        self.main_root.iconphoto(True, self.icon)
        self.main_root.resizable(width=False, height=False)
        self.main_root.mainloop()

    # region External Data Entry
    def popup_return(self, data, caller):
        print(data, caller)
        if not data:
            messagebox.showwarning("Warning", "No project name entered! Please try again.")
            return
        if caller == 0:
            # Update path to project and create if it doesn't exist
            self.project_dir = os.path.join(self.top_dir, data)
            if not os.path.exists(self.project_dir):
                os.mkdir(self.project_dir)
            # Add to treeview
            self.project_treeview_parents.append(
                self.project_treeview.insert("", 'end', str((len(self.project_treeview_parents) + 1)), text=data,
                                             tags=treeview_tags[(len(self.project_treeview_parents) + 1) % 2]))
            select_focus(self.project_treeview, len(self.project_treeview_parents))
            # Save recent path to config
            if not self.recent_projects:
                self.recent_projects = []
            self.recent_projects.append(self.project_dir)
            self.config.set_recent_projects(self.recent_projects)
            # Load the project
            self.load_project(self.project_dir)
        elif caller == 1:
            self.patient_dir = os.path.join(self.project_dir, data)
            if not os.path.exists(self.patient_dir):
                os.mkdir(self.patient_dir)
            self.patient_treeview_parents.append(
                self.patient_treeview.insert("", 'end', str((len(self.patient_treeview_parents) + 1)), text=data,
                                             tags=treeview_tags[(len(self.patient_treeview_parents) + 1) % 2]))
            select_focus(self.patient_treeview, len(self.patient_treeview_parents))
            self.load_patient(self.patient_dir)
        elif caller == 2:
            self.concerns.append(data)
            self.write_concern_file()
            self.concern_treeview_parents.append(
                self.concern_treeview.insert("", 'end', str((len(self.concern_treeview_parents) + 1)), text=data,
                                             tags=treeview_tags[(len(self.concern_treeview_parents) + 1) % 2]))
            select_focus(self.concern_treeview, len(self.concern_treeview_parents))

    # endregion

    # region Project UI Controls
    def select_project(self, event):
        selection = self.project_treeview.identify_row(event.y)
        if selection:
            if selection == '0':
                self.create_new_project()
            else:
                self.load_project(self.recent_projects[int(selection) - 1])

    def create_new_project(self):
        self.top_dir = filedialog.askdirectory(title='Select root directory to save files')
        print(self.top_dir)
        if not self.top_dir:
            messagebox.showwarning("Warning", "No root filepath chosen! Please try again.")
            return
        else:
            self.top_dir = path.normpath(self.top_dir)
        EntryPopup(self, self.main_root, "Enter New Project Name", 0)

    def populate_recent_projects(self):
        self.project_treeview_parents.append(
            self.project_treeview.insert("", 'end', str(0), text="Create or Import New Project",
                                         tags=treeview_tags[2]))
        if self.recent_projects:
            for i in range(0, len(self.recent_projects)):
                self.project_treeview_parents.append(
                    self.project_treeview.insert("", 'end', str(i + 1), text=str(pathlib.Path(
                        self.recent_projects[i]).stem),
                                                 tags=(treeview_tags[(i + 1) % 2])))

    def load_project(self, directory):
        self.project_dir = directory
        try:
            _, self.patients, _ = next(os.walk(directory))
        except StopIteration:
            messagebox.showerror("Error", "Selected project cannot be found!")
            return
        self.populate_patients()

    # endregion

    # region Patient UI Controls
    def populate_patients(self):
        self.patient_treeview_parents.append(self.patient_treeview.insert("", 'end', str(0), text="Create New Patient",
                                                                          tags=treeview_tags[2]))
        if self.patients:
            for i in range(0, len(self.patients)):
                self.patient_treeview_parents.append(
                    self.patient_treeview.insert("", 'end', str(i + 1), text=str(self.patients[i]),
                                                 tags=(treeview_tags[(i + 1) % 2])))

    def create_new_patient(self):
        EntryPopup(self, self.main_root, "Enter New Patient Name", 1)

    def select_patient(self, event):
        selection = self.patient_treeview.identify_row(event.y)
        if selection:
            if selection == '0':
                self.create_new_patient()
            else:
                self.patient_dir = os.path.join(self.project_dir, self.patients[int(selection) - 1])
                self.load_patient(self.patients[int(selection) - 1])

    def patient_creation_check(self):
        if self.config.get_default_dirs():
            for directory in self.config.get_default_dirs():
                if not os.path.exists(os.path.join(self.patient_dir, directory)):
                    os.mkdir(os.path.join(self.patient_dir, directory))
                for data_dir in self.config.get_data_folders():
                    if not os.path.exists(os.path.join(self.patient_dir, directory, data_dir)):
                        os.mkdir(os.path.join(self.patient_dir, directory, data_dir))

    def load_patient(self, directory):
        if self.config.get_patient_concerns():
            _concern_file = self.config.get_patient_concerns()
            self.concern_file = os.path.join(self.project_dir, directory, _concern_file)
            self.populate_patient_concerns()
            self.patient_data_file = os.path.normpath(
                os.path.join(self.patient_dir, pathlib.Path(self.patient_dir).stem + '.json'))
            if not os.path.exists(self.patient_data_file):
                with open(self.patient_data_file, 'w') as f:
                    x = {
                        "Name": pathlib.Path(self.patient_dir).stem,
                        "MRN": ""
                    }
                    json.dump(x, f)

    # endregion

    # region Concern UI Controls
    def populate_patient_concerns(self):
        self.read_concern_file()
        self.concern_treeview_parents.append(self.concern_treeview.insert("", 'end', str(0), text="Create New Concern",
                                                                          tags=treeview_tags[2]))
        if self.concerns:
            for i in range(0, len(self.concerns)):
                self.concern_treeview_parents.append(
                    self.concern_treeview.insert("", 'end', str(i + 1), text=str(self.concerns[i]),
                                                 tags=(treeview_tags[(i + 1) % 2])))

    def select_concern(self, event):
        selection = self.concern_treeview.identify_row(event.y)
        if selection:
            if selection == '0':
                self.create_new_concern()
            else:
                self.selected_concern = self.concerns[int(selection) - 1]
                self.phases_menu.config(state='active')

    def create_new_concern(self):
        EntryPopup(self, self.main_root, "Enter New Concern", 2)

    def read_concern_file(self):
        if os.path.exists(self.concern_file):
            with open(self.concern_file, 'r') as file:
                self.concerns = yaml.safe_load(file)
        else:
            self.concerns = []

    def write_concern_file(self):
        with open(self.concern_file, 'w') as file:
            yaml.dump(self.concerns, file)
        self.read_concern_file()

    # endregion

    # region Phase UI Controls
    def phase_callback(self, *args):
        phase_dir = os.path.join(self.patient_dir, self.selected_concern + " " + self.phases_var.get())
        if not os.path.exists(phase_dir):
            os.mkdir(phase_dir)
        self.ksf_dir = os.path.join(self.patient_dir, self.selected_concern + " " + self.phases_var.get(),
                                    self.config.get_data_folders()[2])
        if os.path.exists(self.ksf_dir):
            ksf_dir = pathlib.Path(self.ksf_dir)
            ksf_pattern = r'*.json'
            try:
                self.ksf_file = max(ksf_dir.glob(ksf_pattern), key=lambda f: f.stat().st_ctime)
                self.ksf_path['text'] = pathlib.Path(self.ksf_file).stem
                self.load_concern_ksf()
            except ValueError:
                self.ksf_file = None
                self.ksf_path['text'] = f"No KSF in {self.selected_concern} {self.phases_var.get()}"
                self.ksf_import.config(state='active')
                self.clear_duration_treeview()
                self.clear_frequency_treeview()
        else:
            os.mkdir(self.ksf_dir)
            self.ksf_path['text'] = f"No KSF in {self.selected_concern} {self.phases_var.get()}"
            self.ksf_import.config(state='active')
            self.clear_duration_treeview()
            self.clear_frequency_treeview()
    # endregion

    # region KSF UI Controls
    def key_popup_return(self, tag, key, caller):
        print(tag, key, caller)
        if not tag or not key:
            messagebox.showwarning("Warning", "Invalid key entered! Please try again.")
        if caller == 1:
            self.create_frequency_key()
        elif caller == 2:
            self.create_duration_key()

    def load_concern_ksf(self):
        with open(self.ksf_file) as f:
            self._ksf = json.load(f)
        self.frequency_keys = self._ksf["Frequency"]
        self.duration_keys = self._ksf["Duration"]
        self.populate_frequency_treeview()
        self.populate_duration_treeview()
        self.continue_button.config(state='active')

    def import_concern_ksf(self):
        tracker_file = filedialog.askopenfilename(filetypes=(("Excel Files", "*.xlsx"),))
        if tracker_file:
            self.ksf_file, self._ksf = import_ksf(tracker_file, self.ksf_dir)
            self.ksf_path['text'] = pathlib.Path(self.ksf_file).stem
            self.frequency_keys = self._ksf["Frequency"]
            self.duration_keys = self._ksf["Duration"]
            self.populate_frequency_treeview()
            self.populate_duration_treeview()
            self.continue_button.config(state='active')
        else:
            messagebox.showwarning("Warning", "No tracker file selected! Please try again.")

    def populate_frequency_treeview(self):
        # self.frequency_treeview_parents.append(
        #     self.frequency_key_treeview.insert("", 'end', str(0), text="Create New Frequency Key",
        #                                        tags=treeview_tags[2]))
        if self.frequency_keys:
            for i in range(0, len(self.frequency_keys)):
                self.frequency_treeview_parents.append(
                    self.frequency_key_treeview.insert("", 'end', str(i), text=str(self.frequency_keys[i][1]),
                                                       values=str(self.frequency_keys[i][0]),
                                                       tags=(treeview_tags[(i) % 2])))

    def clear_frequency_treeview(self):
        for parent in self.frequency_treeview_parents:
            self.frequency_key_treeview.delete(parent)
        self.frequency_treeview_parents = []

    def clear_duration_treeview(self):
        for parent in self.duration_treeview_parents:
            self.duration_key_treeview.delete(parent)
        self.duration_treeview_parents = []

    def populate_duration_treeview(self):
        # self.duration_treeview_parents.append(
        #     self.duration_key_treeview.insert("", 'end', str(0), text="Create New Duration Key",
        #                                       tags=treeview_tags[2]))
        if self.duration_keys:
            for i in range(0, len(self.duration_keys)):
                self.duration_treeview_parents.append(
                    self.duration_key_treeview.insert("", 'end', str(i), text=str(self.duration_keys[i][1]),
                                                      values=(self.duration_keys[i][0]),
                                                      tags=(treeview_tags[(i) % 2])))

    def select_frequency_key(self, event):
        selection = self.frequency_key_treeview.identify_row(event.y)
        if selection:
            if selection == '0':
                NewKeyPopup(self, self.main_root, 1)
            else:
                self.delete_frequency_key()

    def select_duration_key(self, event):
        selection = self.duration_key_treeview.identify_row(event.y)
        if selection:
            if selection == '0':
                NewKeyPopup(self, self.main_root, 2)
            else:
                self.delete_duration_key()

    def create_frequency_key(self):
        print()

    def create_duration_key(self):
        print()

    def delete_frequency_key(self):
        print()

    def delete_duration_key(self):
        print()
    # endregion

    # region Exit UI Controls
    def continue_project(self):
        self.main_root.destroy()

    def cancel_project(self):
        sys.exit(1)
    # endregion
