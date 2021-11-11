import datetime
# Custom library imports
from experiment_select_ui import ExperimentSelectWindow
import patient_select_ui
import keystroke_file_ui
import session_manager_ui
from logger_util import *


def main():
    ExperimentSelection = ExperimentSelectWindow()
    if not ExperimentSelection.cancel:
        print(ExperimentSelection.experiment_dir)
        UserSelection = patient_select_ui.PatientSelectWindow(ExperimentSelection.experiment_dir)
        if not UserSelection.cancel:
            print(UserSelection.patient_file)
            KeystrokeSelection = keystroke_file_ui.KeystrokeSelectWindow(ExperimentSelection.experiment_dir, UserSelection.patient_file)
            if not KeystrokeSelection.cancel:
                print(KeystrokeSelection.keystroke_file)
                SessionManager = session_manager_ui.SessionManagerWindow(UserSelection.patient_file, KeystrokeSelection.keystroke_file)
                return SessionManager.close_program
            else:
                return KeystrokeSelection.cancel
        else:
            return UserSelection.cancel
    else:
        return ExperimentSelection.cancel


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    ret = main()
    while not ret:
        ret = main()
