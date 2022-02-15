import datetime
import os
import sys
# Custom library imports
import imageio_ffmpeg

from config_utils import ConfigUtils
from session_manager_ui import SessionManagerWindow
from logger_util import CreateLogger, log_startup
from project_setup_ui import ProjectSetupWindow
from ui_params import cometrics_data_root


def main(config_file, first_time_user):
    project_setup = ProjectSetupWindow(config_file, first_time_user)
    return SessionManagerWindow(config_file, project_setup)


if __name__ == "__main__":
    # Check root dir
    if not os.path.exists(cometrics_data_root):
        os.mkdir(cometrics_data_root)
    # Reroute stdout and stderr
    CreateLogger(os.path.join(cometrics_data_root, 'logs'))
    # Log computer information
    log_startup()
    # Setup environment variables
    cwd = os.getcwd()
    ffmpeg_path = os.path.join(cwd, r'external_bin\ffmpeg\ffmpeg-win64-v4.2.2.exe')
    if os.path.exists(ffmpeg_path):
        os.environ['IMAGEIO_FFMPEG_EXE'] = os.path.join(cwd, r'external_bin\ffmpeg\ffmpeg-win64-v4.2.2.exe')
    print(f"STARTUP: {cwd}")
    print(f"INFO: imageio_ffmpeg exe location - {imageio_ffmpeg.get_ffmpeg_exe()}")
    # Load our configuration
    config = ConfigUtils()
    config.set_logs_dir(os.path.join(cometrics_data_root, 'logs'))
    first_time = config.get_first_time()
    while True:
        setup = ProjectSetupWindow(config, first_time)
        if setup.setup_complete:
            while True:
                manager = SessionManagerWindow(config, setup)
                if manager.setup_again:
                    break
                elif manager.close_program:
                    break
            if manager.close_program:
                break
        else:
            break
    sys.exit(0)
