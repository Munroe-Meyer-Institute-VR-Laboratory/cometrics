import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
from ui_params import cometrics_version

base = None
if sys.platform == "win32":
    base = "Win32GUI"

directory_table = [
    (
        "ProgramMenuFolder",
        "TARGETDIR",
        ".",
    ),
    (
        "MyProgramMenu",
        "ProgramMenuFolder",
        "MYPROG~1|cometrics",
    ),
]

shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "cometrics",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]cometrics.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

msi_data = {
    "Directory": directory_table,
    "Shortcut": shortcut_table,
    "ProgId": [
        ("Prog.Id", None, None, "cometrics", "IconId", None),
    ],
    "Icon": [
        ("IconId", r'images\icon.ico'),
    ],
}


build_exe_options = dict(
    packages=["os", "sys", "tkinter", 'logger_util', 'scipy'],
    includes=['pynput', 'pynput.keyboard._win32', 'pynput.mouse._win32', 'logger_util', 'scipy._lib.deprecation'],
    excludes=[],
    include_files=['external_bin', 'images', 'reference', 'config.yml', 'LICENSE',
                   (r'venv\Lib\site-packages\imageio', r'lib\imageio')],
)

bdist_msi_options = {
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % ("cometrics", cometrics_version),
    'data': msi_data,
    'upgrade_code': '{9DD1C082-2D1D-4AC5-9150-22CA5DF3D780}'
}

executable = [Executable("cometrics.py",
                         targetName="cometrics.exe",
                         base=base,
                         icon=r'images\icon.ico',
                         shortcutName="cometrics",
                         shortcutDir="MyProgramMenu",
                         copyright="Copyright (C) 2022 Walker Arce",
                         ),]

setup(name="cometrics",
      version=cometrics_version,
      description=f'cometrics v{cometrics_version}',
      options={"bdist_msi": bdist_msi_options,
               "build_exe": build_exe_options},
      executables=executable)
