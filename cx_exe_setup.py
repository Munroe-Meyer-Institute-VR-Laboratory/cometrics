import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
from ui_params import cometrics_version

base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = dict(
    packages=["os", "sys", "tkinter", 'logger_util'],
    includes=['pynput', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'logger_util'],
    excludes=[],
    include_files=['external_bin', 'images', 'reference', 'config.yml'],
    # replace_paths=[("*", "")],
    path=sys.path + ["lib"],
)

bdist_msi_options = {
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % ("Name", "Product"),
                    }
executable = [Executable("cometrics.py",
                         targetName="cometrics.exe",
                         base=base,
                         icon=r'images\icon.ico')]

setup(name="cometrics",
      version=cometrics_version,
      description='Clinical tool for coregistration of frequency and duration based behavior, physiological signals, '
                  'and video data. Session tracking features streamline multi-session clinical data recording.',
      options={"bdist_msi": bdist_msi_options,
               "build_exe": build_exe_options},
      executables=executable)
