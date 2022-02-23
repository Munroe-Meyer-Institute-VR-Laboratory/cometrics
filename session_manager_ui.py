import datetime
import json
import math
import os
import pathlib
from os import walk, path
from tkinter import *
from tkinter import messagebox

from PIL import Image, ImageTk
from pynput import keyboard

# Custom library imports
from tkvideoutils import cp_rename
from menu_bar import MenuBar
from output_view_ui import OutputViewPanel
from patient_data_fields import PatientDataFields
from session_time_fields import SessionTimeFields
from tkinter_utils import get_treeview_style
from ui_params import large_header_font, large_field_font, large_field_offset, medium_header_font, medium_field_font, \
    medium_field_offset, small_header_font, small_field_font, small_field_offset, small_tab_size, medium_tab_size, \
    large_tab_size, ui_title


class SessionManagerWindow:
    def __init__(self, config, project_setup):
        # region Project File Setup
        # Get the project files
        self.config = config
        self.patient_file = project_setup.patient_data_file
        self.keystroke_file = project_setup.ksf_file
        self.session_dir = project_setup.phase_dir
        self.tracker_file = project_setup.tracker_file
        self.graph_dir = path.join(self.session_dir, config.get_data_folders()[0])
        self.export_dir = path.join(self.session_dir, config.get_data_folders()[3])
        self.data_dir = path.join(self.session_dir, config.get_data_folders()[1])
        self.prim_dir = path.join(self.data_dir, "Primary")
        if not os.path.exists(self.prim_dir):
            os.mkdir(self.prim_dir)
        self.reli_dir = path.join(self.data_dir, "Reliability")
        if not os.path.exists(self.reli_dir):
            os.mkdir(self.reli_dir)
        # Log this for debugging
        print("INFO:", self.patient_file, self.keystroke_file, self.session_dir, self.prim_dir, self.reli_dir)
        # Generate session date and time
        now = datetime.datetime.today()
        self.session_date = now.strftime("%B %d, %Y")
        self.session_file_date = now.strftime("%B")[:3] + now.strftime("%d") + now.strftime("%Y")
        self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
        # Get the number of primary and reliability sessions collected so far
        self.prim_session_number = 1
        self.reli_session_number = 1
        self.get_prim_session(self.prim_dir)
        self.get_reli_session(self.reli_dir)
        # endregion

        # region User Interface Setup
        self.window_height, self.window_width = config.get_screen_size()[0], config.get_screen_size()[1]
        if self.window_width == 1920:
            self.header_font = large_header_font
            self.field_font = large_field_font
            self.field_offset = large_field_offset
            self.button_size = large_tab_size
        elif 1920 > self.window_width > 1280:
            self.header_font = medium_header_font
            self.field_font = medium_field_font
            self.field_offset = medium_field_offset
            self.button_size = medium_tab_size
        else:
            self.header_font = small_header_font
            self.field_font = small_field_font
            self.field_offset = small_field_offset
            self.button_size = small_tab_size
        print("INFO:", self.header_font, self.field_font, self.field_offset, self.window_width, self.window_height)

        root = self.root = Tk()
        root.config(bg="white", bd=-2)
        root.title(ui_title)

        self.field_width = int(self.window_width * 0.2)
        self.output_width = int(self.window_width * 0.58)

        self.logo_width = self.field_width
        self.logo_height = int(self.logo_width / 5.7)
        self.patient_field_height = int((self.window_height - self.logo_height - 10) * 0.85)

        self.logo_canvas = Canvas(root, width=self.logo_width, height=self.logo_height, bg="white", bd=-2)
        self.logo_canvas.place(x=2, y=2)
        self.logo_img = ImageTk.PhotoImage(
            Image.open('images/cometrics_logo.png').resize((self.logo_width, self.logo_height), Image.ANTIALIAS))
        self.logo_canvas.create_image(0, 0, anchor=NW, image=self.logo_img)

        _ = get_treeview_style()

        self.menu = MenuBar(root, self)
        self.stf = SessionTimeFields(self, root,
                                     x=self.logo_width + 10,
                                     y=self.logo_height + 10,
                                     height=self.patient_field_height,
                                     width=self.field_width,
                                     header_font=self.header_font,
                                     field_font=self.field_font,
                                     field_offset=self.field_offset)
        self.ovu = OutputViewPanel(root,
                                   x=(self.logo_width * 2) + 20,
                                   y=(self.logo_height + 10) - self.button_size[1],
                                   height=self.patient_field_height,
                                   width=self.output_width,
                                   button_size=self.button_size,
                                   ksf=self.keystroke_file,
                                   field_font=self.field_font,
                                   header_font=self.header_font,
                                   video_import_cb=self.start_video_control,
                                   slider_change_cb=self.change_time,
                                   fps=self.config.get_fps())
        self.stf.kdf = self.ovu.key_view
        self.pdf = PatientDataFields(root,
                                     x=5,
                                     y=self.logo_height + 10,
                                     height=self.patient_field_height,
                                     width=self.field_width,
                                     patient_file=self.patient_file,
                                     prim_session_number=self.prim_session_number,
                                     reli_session_number=self.reli_session_number,
                                     session_date=self.session_date,
                                     session_time=self.session_time,
                                     conditions=project_setup.conditions,
                                     header_font=self.header_font,
                                     field_font=self.field_font,
                                     field_offset=self.field_offset,
                                     ksf=self.keystroke_file)
        self.patient_name = self.pdf.patient_name
        # endregion

        # Setup key listener
        self.global_commands = {
            "Toggle Session": keyboard.Key.esc,
            "Pause Session": keyboard.Key.ctrl_l,
            "Delete Last Event": keyboard.Key.backspace,
            "Undo Last Delete": keyboard.Key.ctrl_r
        }
        self.tag_history = []
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener.start()
        # Configure window close override
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.restart = False
        self.setup_again = False
        self.close_program = False
        # Start the window in fullscreen
        root.state('zoomed')
        # Start the UI loop
        root.mainloop()

    def change_time(self, frame):
        if self.ovu.video_view.player:
            if not self.ovu.video_view.player.playing:
                self.ovu.video_view.player.load_frame(int(frame))
        self.stf.change_time(int((float(frame) / self.ovu.video_view.player.fps) + 0.5))

    def start_video_control(self):
        self.ovu.video_view.load_video()
        if self.ovu.video_view.video_loaded:
            video_length = self.ovu.video_view.player.nframes / self.ovu.video_view.player.fps
            self.stf.video_control(video_length)

    def restart_program(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.setup_again = True

    def create_new_session(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.restart = True

    def on_closing(self):
        self.stf.stop_timer()
        self.ovu.close()
        self.listener.stop()
        self.root.quit()
        self.root.destroy()
        self.close_program = True

    def get_reli_session(self, directory):
        if path.isdir(directory):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.reli_session_number += 1
        else:
            messagebox.showerror("Error", "Reliability session folder could not be found!")
            print("ERROR: Reliability session folder could not be found")

    def get_prim_session(self, directory):
        if path.isdir(directory):
            _, _, files = next(walk(directory))
            for file in files:
                if pathlib.Path(file).suffix == ".json":
                    self.prim_session_number += 1
        else:
            messagebox.showerror("Error", "Primary session folder could not be found!")
            print("ERROR: Primary session folder could not be found")

    def on_press(self, key):
        try:
            key_char = key.char
            # Only process key input if session has started
            if self.stf.session_started:
                # Only process key input if the main window has focus, otherwise ignore
                if self.root.focus_get():
                    # Enforce lower case for all inputs that are characters
                    key_char = str(key_char).lower()
                    self.handle_key_press(key_char)
                else:
                    print("INFO: Typing outside window")
        except AttributeError:
            self.handle_global_press(key)

    def on_release(self, key):
        pass

    def handle_global_press(self, key_char):
        for key in self.global_commands:
            if self.global_commands[key] == key_char:
                if key == "Toggle Session":
                    if self.stf.session_started:
                        self.stop_session()
                    else:
                        response = self.pdf.check_session_fields()
                        if response is False:
                            self.start_session()
                        else:
                            messagebox.showwarning("Warning", response)
                            print("WARNING:", response)
                elif key == "Pause Session":
                    self.pause_session()
                elif key == "Delete Last Event":
                    self.ovu.delete_last_event()
                elif key == "Undo Last Delete":
                    self.ovu.undo_last_delete()

    def handle_key_press(self, key):
        try:
            if self.stf.session_started:
                self.ovu.check_event(key, self.stf.session_time)
        except TypeError as e:
            print(f"ERROR: Exception encountered when handling key press:\n{str(e)}")

    def save_session(self):
        session_fields = self.pdf.get_session_fields()
        session_data, e4_data, video_file = self.ovu.get_session_data()
        # If no session data is recorded, ask before saving it
        if not session_data:
            response = messagebox.askyesno("Session Data Empty", "There was no session data recorded, "
                                                                 "do you want to save an empty session?")
            if not response:
                return
        x = {
            "Session Date": self.session_date,
            "Session Start Time": self.session_time,
            "Session Time": self.stf.session_time,
            "Pause Time": self.stf.break_time,
            "Keystroke File": pathlib.Path(self.keystroke_file).stem,
            "Video File": pathlib.Path(video_file).name if video_file else ''
        }
        session_fields.update(x)
        session_fields["Event History"] = session_data
        session_fields["E4 Data"] = e4_data
        session_fields["KSF"] = self.ovu.key_view.keystroke_json
        reli = '_R' if session_fields["Primary Data"] == "Reliability" else ''
        output_session_file = path.join(self.session_dir,
                                        self.config.get_data_folders()[1],
                                        session_fields["Primary Data"],
                                        f"{session_fields['Session Number']}"
                                        f"{session_fields['Assessment Name'][:2]}"
                                        f"{session_fields['Condition Name'][:2]}"
                                        f"{self.session_file_date}{reli}.json")
        if self.ovu.video_view.video_file:
            cp_rename(src=self.ovu.video_view.video_file,
                      dst=path.join(self.session_dir,
                                    self.config.get_data_folders()[1],
                                    session_fields["Primary Data"]),
                      name=f"{session_fields['Session Number']}"
                           f"{session_fields['Assessment Name'][:2]}"
                           f"{session_fields['Condition Name'][:2]}"
                           f"{self.session_file_date}{reli}")
        with open(output_session_file, 'w') as f:
            json.dump(session_fields, f)
        print(f"INFO: Saved session file to: {output_session_file}")

    def start_session(self):
        response = self.pdf.check_session_fields()
        if response is False:
            self.session_time = datetime.datetime.now().strftime("%H:%M:%S")
            self.pdf.start_label['text'] = "Session Start Time: " + self.session_time
            self.pdf.save_patient_fields()
            self.pdf.lock_session_fields()
            self.stf.lock_session_fields()
            # Start the session
            session_fields = self.pdf.get_session_fields()
            reli = '_R' if session_fields["Primary Data"] == "Reliability" else ''
            self.ovu.start_session(recording_path=path.join(self.session_dir,
                                                            self.config.get_data_folders()[1],
                                                            session_fields["Primary Data"],
                                                            f"{session_fields['Session Number']}"
                                                            f"{session_fields['Assessment Name'][:2]}"
                                                            f"{session_fields['Condition Name'][:2]}"
                                                            f"{self.session_file_date}{reli}.mp4"))
            self.stf.start_session()
        else:
            messagebox.showwarning("Warning", response)
            print("WARNING:", response)

    def stop_session(self):
        self.stf.stop_session()
        self.ovu.stop_session()
        self.save_session()
        self.listener.stop()

    def pause_session(self):
        if self.stf.session_started:
            self.stf.pause_session()

