import datetime
# Custom library imports
from config_utils import ConfigUtils
from experiment_select_ui import ExperimentSelectWindow
import patient_select_ui
import keystroke_file_ui
import session_manager_ui
from logger_util import *
from project_setup_ui import ProjectSetupWindow


def main(config_file):
    project_setup = ProjectSetupWindow(config_file)
    session_manager_ui.SessionManagerWindow(project_setup)
    return True


if __name__ == "__main__":
    sys.stdout = Log()
    sys.stderr = sys.stdout
    print(datetime.datetime.now().strftime("%c"))
    config = ConfigUtils()
    ret = main(config)
    while not ret:
        ret = main(config)
