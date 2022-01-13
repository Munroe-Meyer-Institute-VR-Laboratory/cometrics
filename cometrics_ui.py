import datetime
# Custom library imports
from config_utils import ConfigUtils
import session_manager_ui
from logger_util import CreateLogger
from project_setup_ui import ProjectSetupWindow


def main(config_file, first_time_user):
    project_setup = ProjectSetupWindow(config_file, first_time_user)
    session_manager_ui.SessionManagerWindow(config_file, project_setup)
    return True


if __name__ == "__main__":
    CreateLogger()
    print("STARTUP:", datetime.datetime.now().strftime("%c"))
    config = ConfigUtils()
    first_time = config.get_first_time()
    ret = main(config, first_time)
    while not ret:
        ret = main(config, False)
