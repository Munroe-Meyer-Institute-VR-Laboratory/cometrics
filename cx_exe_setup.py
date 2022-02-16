import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
from ui_params import cometrics_version

buildOptions = dict(
    packages=["os", "sys", "tkinter", 'logger_util'],
    includes=['pynput', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'logger_util'],
    excludes=[],
    include_files=['external_bin', 'images', 'reference', 'config.yml'],
    # replace_paths=[("*", "")],
    path=sys.path + ["lib"],
)

# GUI applications require a different base on Windows (the default is for
# a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(name="cometrics",
      version=cometrics_version,
      description='Clinical tool for coregistration of frequency and duration based behavior, physiological signals, '
                  'and video data. Session tracking features streamline multi-session clinical data recording.',
      options={"build_exe": buildOptions},
      executables=[Executable("cometrics_ui.py", base=base, icon=r'images\icon.ico')])
