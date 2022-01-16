import datetime
import wmi
# Custom library imports
from config_utils import ConfigUtils
import session_manager_ui
from logger_util import CreateLogger
from project_setup_ui import ProjectSetupWindow


def main(config_file, first_time_user):
    project_setup = ProjectSetupWindow(config_file, first_time_user)
    return session_manager_ui.SessionManagerWindow(config_file, project_setup)


def log_startup():
    print("STARTUP:", datetime.datetime.now().strftime("%c"))
    c = wmi.WMI()
    my_system = c.Win32_ComputerSystem()[0]
    print(f"STARTUP: Manufacturer - {my_system.Manufacturer}")
    print(f"STARTUP: Model - {my_system.Model}")
    print(f"STARTUP: Name - {my_system.Name}")
    print(f"STARTUP: NumberOfProcessors - {my_system.NumberOfProcessors}")
    print(f"STARTUP: SystemType - {my_system.SystemType}")
    print(f"STARTUP: SystemFamily - {my_system.SystemFamily}")


if __name__ == "__main__":
    CreateLogger()
    log_startup()
    config = ConfigUtils()
    first_time = config.get_first_time()
    while main(config, first_time):
        pass
