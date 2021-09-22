import datetime
# Custom library imports
from experiment_select_ui import ExperimentSelectWindow
import patient_select_ui
import keystroke_file_ui
import session_manager_ui
from logger_util import *


def main():
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    ExperimentSelection = ExperimentSelectWindow()
    if not ExperimentSelection.cancel:
        UserSelection = patient_select_ui.PatientSelectWindow(ExperimentSelection.experiment_dir)
        if not UserSelection.cancel:
            KeystrokeSelection = keystroke_file_ui.KeystrokeSelectWindow(ExperimentSelection.experiment_dir, UserSelection.patient_file)
            if not KeystrokeSelection.cancel:
                session_manager_ui.SessionManagerWindow(UserSelection.patient_file, KeystrokeSelection.keystroke_file)


if __name__ == "__main__":
    main()
