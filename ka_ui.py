import datetime
# Custom library imports
from experiment_select_ui import ExperimentSelectWindow
from patient_select_ui import PatientSelectWindow
from keystroke_file_ui import KeystrokeSelectWindow
from session_manager_ui import SessionManagerWindow
from logger_util import *


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    ExperimentSelection = ExperimentSelectWindow()
    if not ExperimentSelection.cancel:
        UserSelection = PatientSelectWindow(ExperimentSelection.experiment_dir)
        if not UserSelection.cancel:
            KeystrokeSelection = KeystrokeSelectWindow(ExperimentSelection.experiment_dir, UserSelection.patient_file)
            if not KeystrokeSelection.cancel:
                SessionManagerWindow(UserSelection.patient_file, KeystrokeSelection.keystroke_file)
