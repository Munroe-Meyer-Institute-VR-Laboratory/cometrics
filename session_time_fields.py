import datetime
import json
import math
import os
import pathlib
import threading
import time
import winsound
from tkinter import messagebox, Frame, Label, CENTER, BooleanVar, Checkbutton, StringVar, Entry, W, Button, LEFT, \
    PhotoImage, SUNKEN, RAISED, N, Radiobutton, NE, NW
from tkinter.ttk import Combobox

from tkinter_utils import set_entry_text
from ui_params import treeview_bind_tags, crossmark, checkmark


class SessionTimeFields:
    def __init__(self, caller, parent, x, y, height, width, button_size,
                 header_font=('Purisa', 14), field_font=('Purisa', 11),
                 field_offset=60, ovu=None, review_mode=False):
        self.SESSION_VIEW, self.REVIEW_VIEW = 0, 1
        self.x, self.y = x, y
        self.button_size = button_size
        self.width, self.height = width, height
        self.field_offset = field_offset
        self.ovu = ovu
        self.caller = caller

        self.frame = Frame(parent, width=width, height=height)
        self.frame.place(x=x, y=y)

        clean_view = Frame(self.frame, width=width,
                           height=button_size[1], bg='white')
        clean_view.place(x=0, y=0)

        self.session_frame = Frame(parent, width=width, height=height)
        self.session_frame.place(x=x, y=y + self.button_size[1])

        self.review_frame = Frame(parent, width=width, height=height)
        self.view_frames = [self.session_frame, self.review_frame]
        self.view_buttons = []

        self.video_playing = False
        self.session_started = False
        self.session_paused = False
        self.timer_running = True
        self.ui_timer_running = True
        self.update_ui = False
        self.start_y = 15
        self.session_time = 0
        self.break_time = 0

        self.current_button = 0
        session_time_label = Label(self.session_frame, text="Session Time",
                                   font=(header_font[0], header_font[1], 'bold'))
        session_time_label.place(x=width / 2, y=self.start_y, anchor=CENTER)

        self.session_time_label = Label(self.session_frame, text="0:00:00",
                                        font=header_font)
        self.session_time_label.place(x=width / 2, y=self.start_y + (field_offset / 2), anchor=CENTER)

        break_time_label = Label(self.session_frame, text='Break Time', font=(header_font[0], header_font[1], 'bold'))
        break_time_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 2), anchor=CENTER)

        self.break_time_label = Label(self.session_frame, text="0:00:00",
                                      font=header_font)
        self.break_time_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 3), anchor=CENTER)

        self.session_start_label = Label(self.session_frame, text="Session Started", fg='green',
                                         font=header_font)
        self.session_paused_label = Label(self.session_frame, text="Session Paused", fg='yellow',
                                          font=header_font)
        self.session_stopped_label = Label(self.session_frame, text="Session Stopped", fg='red',
                                           font=header_font)
        self.session_stopped_label.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 4), anchor=CENTER)

        self.interval_selection = BooleanVar()
        self.interval_checkbutton = Checkbutton(self.session_frame, text="Reminder Beep (Seconds)",
                                                variable=self.interval_selection,
                                                font=header_font, command=self.show_beep_interval)
        self.interval_checkbutton.place(x=10, y=self.start_y + ((field_offset / 2) * 6), anchor=W)
        self.interval_input_var = StringVar()

        interval_cmd = self.session_frame.register(self.validate_number)
        self.interval_input = Entry(self.session_frame, validate='all', validatecommand=(interval_cmd, '%P'),
                                    font=header_font, width=6)

        session_cmd = self.session_frame.register(self.validate_number)
        self.session_dur_input = Entry(self.session_frame, validate='all', validatecommand=(session_cmd, '%P'),
                                       font=header_font, width=6)

        self.session_dur_selection = BooleanVar()
        self.session_dur_checkbutton = Checkbutton(self.session_frame, text="Session Duration (Seconds)",
                                                   variable=self.session_dur_selection,
                                                   font=header_font,
                                                   command=self.show_session_time)
        self.session_dur_checkbutton.place(x=10, y=self.start_y + ((field_offset / 2) * 7), anchor=W)

        self.session_toggle_button = Button(self.session_frame, text="Start Session", bg='#4abb5f',
                                            font=field_font, width=13,
                                            command=self.caller.start_session)
        self.session_toggle_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 10.5), anchor=CENTER)

        self.double_speed_selection = BooleanVar()
        self.double_speed_checkbutton = Checkbutton(self.session_frame, text="Double Speed Playback",
                                                    variable=self.double_speed_selection,
                                                    font=header_font,
                                                    command=self.double_speed_toggle)
        self.double_speed_checkbutton.place(x=10, y=self.start_y + ((field_offset / 2) * 8), anchor=W)

        self.key_explanation = Label(self.session_frame, text="Esc Key", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 10.5), anchor=W)

        self.session_pause_button = Button(self.session_frame, text="Pause Session", width=13,
                                           font=field_font, command=self.caller.pause_session)
        self.session_pause_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 12), anchor=CENTER)
        self.key_explanation = Label(self.session_frame, text="Left Ctrl", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 12), anchor=W)

        self.play_image = PhotoImage(file='images/video-start.png')
        self.pause_image = PhotoImage(file='images/video-pause.png')
        self.forward_image = PhotoImage(file='images/skip_forward.png')
        self.backward_image = PhotoImage(file='images/skip_backward.png')

        self.play_button = Button(self.session_frame, image=self.play_image,
                                  command=self.caller.start_session)
        self.forward_button = Button(self.session_frame, image=self.forward_image)
        self.backward_button = Button(self.session_frame, image=self.backward_image)
        self.play_button.place(x=self.width / 2,
                               y=self.start_y + ((self.field_offset / 2) * 14), anchor=N)
        self.forward_button.place(x=(self.width / 2) + 60,
                                  y=self.start_y + ((self.field_offset / 2) * 14), anchor=N)
        self.backward_button.place(x=(self.width / 2) - 60,
                                   y=self.start_y + ((self.field_offset / 2) * 14), anchor=N)
        self.forward_button.config(state='disabled')
        self.backward_button.config(state='disabled')
        self.play_button.config(state='disabled')

        self.session_duration = None
        self.beep_th = None
        self.interval_thread = None

        if review_mode:
            session_button = Button(self.frame, text="Session", command=self.switch_session_frame, width=12,
                                    font=field_font)
            self.view_buttons.append(session_button)
            self.SESSION_VIEW = len(self.view_buttons) - 1
            self.view_buttons[self.SESSION_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
                                                       width=button_size[0], height=button_size[1])
            self.view_buttons[self.SESSION_VIEW].config(relief=SUNKEN)

            review_button = Button(self.frame, text="Review", command=self.switch_review_frame, width=12,
                                   font=field_font)
            self.view_buttons.append(review_button)
            self.REVIEW_VIEW = len(self.view_buttons) - 1
            self.view_buttons[self.REVIEW_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
                                                      width=button_size[0], height=button_size[1])

            self.rm = ReviewMode(caller, self.view_frames[self.REVIEW_VIEW], width=width, height=height,
                                 button_size=button_size, field_font=field_font, header_font=header_font)

        self.time_thread = threading.Thread(target=self.time_update_thread)

    def switch_session_frame(self):
        self.switch_frame(self.SESSION_VIEW)

    def switch_frame(self, view):
        self.view_buttons[self.current_button].config(relief=RAISED)
        self.view_frames[self.current_button].place_forget()
        self.current_button = view
        self.view_buttons[view].config(relief=SUNKEN)
        self.view_frames[view].place(x=self.x, y=self.y + self.button_size[1])

    def switch_review_frame(self):
        self.switch_frame(self.REVIEW_VIEW)

    def video_control(self, nframes):
        self.play_button.config(state='active')
        self.session_dur_selection.set(True)
        self.show_session_time()
        set_entry_text(self.session_dur_input, str(int(math.ceil(nframes))))
        self.session_dur_input.config(state='disabled')
        self.session_dur_checkbutton.config(state='disabled')
        self.forward_button.config(command=self.caller.ovu.video_view.player.skip_video_forward)
        self.backward_button.config(command=self.caller.ovu.video_view.player.skip_video_backward)

    @staticmethod
    def validate_number(char):
        if str.isdigit(char) or char == "":
            return True
        return False

    def lock_session_fields(self):
        self.interval_input.config(state='disabled')
        self.session_dur_input.config(state='disabled')

    def beep_interval_thread(self):
        interval = int(self.interval_input.get())
        while self.session_started:
            time.sleep(interval)
            if not self.session_paused and self.session_started:
                self.beep_th = threading.Thread(target=self.beep_thread)
                self.beep_th.start()

    def double_speed_toggle(self):
        if self.double_speed_selection.get():
            if not self.ovu.video_view.double_speed_on():
                messagebox.showwarning("Warning", "Video needs to be loaded first!")
                print("WARNING: Video needs to be loaded first")
                self.double_speed_selection.set(False)
        else:
            if not self.ovu.video_view.double_speed_off():
                messagebox.showwarning("Warning", "Video needs to be loaded first!")
                print("WARNING: Video needs to be loaded first")
                self.double_speed_selection.set(True)

    def show_session_time(self):
        if self.session_dur_selection.get():
            self.session_dur_checkbutton.config(text="Session Duration")
            self.session_dur_input.place(x=self.width * 0.66, y=self.start_y + ((self.field_offset / 2) * 7), anchor=W)
        else:
            self.session_dur_checkbutton.config(text="Session Duration (Seconds)")
            self.session_dur_input.place_forget()

    def show_beep_interval(self):
        if self.interval_selection.get():
            self.interval_checkbutton.config(text="Reminder Beep")
            self.interval_input.place(x=self.width * 0.66, y=self.start_y + ((self.field_offset / 2) * 6), anchor=W)
        else:
            self.interval_checkbutton.config(text="Reminder Beep (Seconds)")
            self.interval_input.place_forget()

    def time_update_thread(self):
        while self.timer_running:
            time.sleep(1 - time.monotonic() % 1)
            if self.timer_running:
                if self.session_started and not self.session_paused:
                    self.session_time += 1
                    for i in range(0, len(self.ovu.key_view.dur_sticky)):
                        if self.ovu.key_view.dur_sticky[i]:
                            self.ovu.key_view.dur_treeview.set(str(i), column="1",
                                                               value=self.session_time - self.ovu.key_view.sticky_start[
                                                                   i][0])
                    if self.session_duration:
                        if self.session_time >= self.session_duration:
                            self.caller.stop_session()
                    if self.ovu.woodway_view:
                        self.ovu.woodway_view.next_protocol_step(self.session_time)
                    if self.ovu.ble_view:
                        self.ovu.ble_view.next_protocol_step(self.session_time)
                elif self.session_paused:
                    if not self.caller.ovu.video_view.player:
                        self.break_time += 1
                self.break_time_label['text'] = str(datetime.timedelta(seconds=self.break_time))
                self.session_time_label['text'] = str(datetime.timedelta(seconds=self.session_time))

    def change_time(self, current_seconds):
        self.session_time = current_seconds
        self.session_time_label['text'] = str(datetime.timedelta(seconds=self.session_time))
        for i in range(0, len(self.ovu.key_view.dur_sticky)):
            if self.ovu.key_view.dur_sticky[i]:
                if self.session_time < self.ovu.key_view.sticky_start[i][0]:
                    self.ovu.key_view.dur_sticky[i] = False
                    self.ovu.key_view.dur_treeview.item(str(i), tags=treeview_bind_tags[i % 2])
                else:
                    self.ovu.key_view.dur_treeview.set(str(i), column="1",
                                                       value=self.session_time - self.ovu.key_view.sticky_start[i][0])

    def start_session(self):
        self.session_started = True
        self.session_toggle_button['text'] = "Stop Session"
        self.session_toggle_button['bg'] = '#ea2128'
        self.session_toggle_button.config(command=self.caller.stop_session)
        self.play_button.config(command=self.caller.pause_session)
        self.play_button.config(image=self.pause_image)
        if self.session_dur_selection.get():
            self.session_duration = int(self.session_dur_input.get())
        if self.interval_selection.get():
            self.interval_thread = threading.Thread(target=self.beep_interval_thread)
            self.interval_thread.start()
        if self.caller.ovu.video_view.player:
            self.video_playing = self.caller.ovu.video_view.play_video()
            self.forward_button.config(state='active')
            self.backward_button.config(state='active')
        else:
            self.time_thread.start()
        self.session_stopped_label.place_forget()
        self.session_start_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4), anchor=CENTER)

    def stop_session(self):
        self.session_toggle_button['text'] = "Restart Session"
        self.session_toggle_button['bg'] = self.session_pause_button['bg']
        self.session_toggle_button['command'] = self.caller.menu.start_new_session
        self.play_button.config(state='disabled')
        self.forward_button.config(state='disabled')
        self.backward_button.config(state='disabled')
        self.timer_running = False
        if self.video_playing:
            self.video_playing = self.caller.ovu.video_view.pause_video()
        if self.session_paused:
            self.session_paused_label.place_forget()
        elif self.session_started:
            self.session_start_label.place_forget()
        self.session_stopped_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                         anchor=CENTER)
        self.session_started = False

    def pause_session(self):
        if self.session_started:
            if not self.session_paused:
                if self.caller.ovu.video_view.player:
                    self.video_playing = self.caller.ovu.video_view.pause_video()
                    self.play_button.config(image=self.play_image)
                self.session_start_label.place_forget()
                self.session_paused_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                                anchor=CENTER)
                self.session_paused = True
            else:
                if self.caller.ovu.video_view.player:
                    self.video_playing = self.caller.ovu.video_view.play_video()
                    self.play_button.config(image=self.pause_image)
                self.session_start_label.place(x=self.width / 2, y=self.start_y + ((self.field_offset / 2) * 4),
                                               anchor=CENTER)
                self.session_paused_label.place_forget()
                self.session_paused = False

    def stop_timer(self):
        self.timer_running = False

    def beep_thread(self):
        winsound.PlaySound("SystemHand", winsound.SND_ALIAS)


class ReviewMode:
    def __init__(self, caller, parent, height, width, button_size,
                 header_font=('Purisa', 14), field_font=('Purisa', 11)):
        self.caller = caller
        self.parent = parent

        # region Session Load
        self.review_name_label = Label(parent, text="Reviewer Name", font=field_font)
        self.review_name_label.place(x=int(width / 2), y=5, anchor=N)
        widget_offset = height * 0.05

        self.review_name_var = StringVar(parent)

        self.review_name_entry = Entry(parent, textvariable=self.review_name_var, font=field_font)
        self.review_name_entry.place(x=int(width / 2), y=widget_offset, anchor=N, width=button_size[0] * 2)

        self.prim_session_number = caller.prim_session_number - 1
        self.reli_session_number = caller.reli_session_number - 1

        self.session_number = self.prim_session_number
        self.prim_var = StringVar(parent, value="Primary")
        self.sess_num = StringVar(parent, value=self.prim_session_number)
        primary_data = Label(parent, text="Primary or Reliability Review", font=field_font)
        primary_data.place(x=int(width / 2), y=widget_offset * 2, anchor=N)
        self.prim_data_radio = Radiobutton(parent, text="Primary", value="Primary",
                                           variable=self.prim_var, command=self.check_radio,
                                           font=field_font, width=12)
        self.rel_data_radio = Radiobutton(parent, text="Reliability", value="Reliability",
                                          variable=self.prim_var, command=self.check_radio,
                                          font=field_font, width=12)
        self.prim_data_radio.place(x=(width / 2), y=widget_offset * 3, anchor=NE)
        self.rel_data_radio.place(x=(width / 2), y=widget_offset * 3, anchor=NW)

        self.check_session_var = StringVar(parent)
        self.check_session_label = Label(parent, textvariable=self.check_session_var, font=header_font)
        self.check_session_label.place(x=(width / 2), y=widget_offset * 4, anchor=N)

        self.selected_session = 1
        self.forward_image = PhotoImage(file='images/go_next.png')
        self.backward_image = PhotoImage(file='images/go_previous.png')
        self.forward_session_button = Button(parent, image=self.forward_image, command=self.next_session)
        self.backward_session_button = Button(parent, image=self.backward_image, command=self.prev_session)
        self.forward_session_button.place(x=(width / 2) + 70, y=widget_offset * 5, anchor=N)
        self.backward_session_button.place(x=(width / 2) - 70, y=widget_offset * 5, anchor=N)

        self.loaded_session_var = StringVar(parent, value=f"Session\n{self.selected_session} / {self.session_number}")
        self.loaded_session = Label(parent, textvariable=self.loaded_session_var, font=header_font)
        self.loaded_session.place(x=int(width / 2), y=(widget_offset * 5) + 20, anchor=CENTER)

        self.load_session_button = Button(parent, text="Load Session", font=field_font, command=self.load_session)
        self.load_session_button.place(x=int(width / 2), y=widget_offset * 7, width=button_size[0] * 2,
                                       height=button_size[1],
                                       anchor=N)
        # endregion

        # region Event Review
        self.event_number = 1
        self.selected_event = 1
        self.forward_event_button = Button(parent, image=self.forward_image, command=self.next_event)
        self.backward_event_button = Button(parent, image=self.backward_image, command=self.prev_event)
        self.forward_event_button.place(x=(width / 2) + 70, y=widget_offset * 8 + (button_size[1] / 2), anchor=N)
        self.backward_event_button.place(x=(width / 2) - 70, y=widget_offset * 8 + (button_size[1] / 2), anchor=N)

        self.loaded_event_var = StringVar(parent, value=f"Event\n0 / 0")
        self.loaded_event = Label(parent, textvariable=self.loaded_event_var, font=header_font)
        self.loaded_event.place(x=int(width / 2), y=(widget_offset * 8 + (button_size[1] / 2)) + 20, anchor=CENTER)

        freq_label = Label(parent, font=field_font, text="Frequency Key Association")
        freq_label.place(x=int(width / 2), y=(widget_offset * 10 + (button_size[1] / 2)), anchor=N)

        self.freq_var = StringVar(parent)
        self.freq_box = Combobox(parent, textvariable=self.freq_var, font=field_font)
        self.freq_box['values'] = ['None'] + caller.ovu.key_view.bindings
        self.freq_box.config(font=field_font)
        self.freq_box.place(x=int(width / 2), y=(widget_offset * 11 + (button_size[1] / 2)), anchor=N, width=200)
        self.freq_box.option_add('*TCombobox*Listbox.font', field_font)

        dur_label = Label(parent, font=field_font, text="Duration Key Association")
        dur_label.place(x=int(width / 2), y=(widget_offset * 12 + (button_size[1] / 2)), anchor=N)

        self.dur_var = StringVar(parent)
        self.dur_box = Combobox(parent, textvariable=self.dur_var, font=field_font)
        self.dur_box['values'] = ['None'] + caller.ovu.key_view.dur_bindings
        self.dur_box.config(font=field_font)
        self.dur_box.place(x=int(width / 2), y=(widget_offset * 13 + (button_size[1] / 2)), anchor=N, width=200)
        self.dur_box.option_add('*TCombobox*Listbox.font', field_font)

        self.start_clip_button = Button(parent, text='Play Clip', font=field_font, command=self.play_clip)
        self.start_clip_button.place(x=int(width / 2), y=(widget_offset * 14 + (button_size[1] / 2)),
                                     width=button_size[0] * 2, height=button_size[1], anchor=N)

        self.to_frame = StringVar(parent)
        self.to_frame_entry = Entry(parent, textvariable=self.to_frame, font=field_font)
        self.to_frame_entry.place(x=int(width / 2) - 10, y=(widget_offset * 15 + (button_size[1] / 2)),
                                  width=button_size[0] - 20, height=button_size[1], anchor=NE)

        self.from_frame = StringVar(parent)
        self.from_frame_entry = Entry(parent, textvariable=self.from_frame, font=field_font)
        self.from_frame_entry.place(x=int(width / 2) + 10, y=(widget_offset * 15 + (button_size[1] / 2)),
                                    width=button_size[0] - 20, height=button_size[1], anchor=NW)

        self.accept_button = Button(parent, text="Accept", bg='green', font=field_font, fg='white',
                                    command=self.accept_changes)
        self.accept_button.place(x=int(width / 2), y=(widget_offset * 16 + (button_size[1] / 2)),
                                 width=button_size[0], height=button_size[1] * 2, anchor=NE)

        self.reject_button = Button(parent, text="Reject", bg='red', font=field_font, fg='white',
                                    command=self.reject_changes)
        self.reject_button.place(x=int(width / 2), y=(widget_offset * 16 + (button_size[1] / 2)),
                                 width=button_size[0], height=button_size[1] * 2, anchor=NW)

        self.save_session_button = Button(parent, text="Approve Session", font=field_font, command=self.approve_changes)
        self.save_session_button.place(x=int(width / 2), y=(widget_offset * 18 + (button_size[1] / 2)),
                                       width=button_size[0] * 2, height=button_size[1], anchor=N)
        self.disable_event_review()
        # endregion

        self.session_events = []
        self.selected_event_json = None
        self.session_json = dict()
        self.session_file = None
        self.session_video_file = None
        self.load_session_json()

    def enable_session_select(self):
        self.load_session_button['text'] = 'Load Session'
        self.load_session_button['command'] = self.load_session
        self.review_name_entry['state'] = 'normal'
        self.forward_session_button['state'] = 'normal'
        self.backward_session_button['state'] = 'normal'
        self.prim_data_radio['state'] = 'normal'
        self.rel_data_radio['state'] = 'normal'

    def disable_session_select(self):
        self.load_session_button['text'] = 'Close Session'
        self.load_session_button['command'] = self.reset_session
        self.review_name_entry['state'] = 'disabled'
        self.forward_session_button['state'] = 'disabled'
        self.backward_session_button['state'] = 'disabled'
        self.prim_data_radio['state'] = 'disabled'
        self.rel_data_radio['state'] = 'disabled'

    def disable_event_review(self):
        self.dur_box['state'] = 'disabled'
        self.freq_box['state'] = 'disabled'
        self.accept_button['state'] = 'disabled'
        self.reject_button['state'] = 'disabled'
        self.save_session_button['state'] = 'disabled'
        self.forward_event_button['state'] = 'disabled'
        self.backward_event_button['state'] = 'disabled'
        self.start_clip_button['state'] = 'disabled'
        self.to_frame_entry['state'] = 'disabled'
        self.from_frame_entry['state'] = 'disabled'

    def enable_event_review(self):
        self.dur_box['state'] = 'readonly'
        self.freq_box['state'] = 'readonly'
        self.accept_button.config(state='active', bg='green')
        self.reject_button.config(state='active', bg='red')
        self.save_session_button['state'] = 'active'
        self.forward_event_button['state'] = 'active'
        self.backward_event_button['state'] = 'active'
        self.start_clip_button['state'] = 'active'
        self.to_frame_entry['state'] = 'normal'
        self.from_frame_entry['state'] = 'normal'

    def next_session(self):
        self.session_json = dict()
        if self.selected_session + 1 > self.session_number:
            self.selected_session = 1
        else:
            self.selected_session += 1
        self.load_session_json()
        self.loaded_session_var.set(f"Session\n{self.selected_session} / {self.session_number}")

    def prev_session(self):
        self.session_json = dict()
        if self.selected_session - 1 < 1:
            self.selected_session = self.session_number
        else:
            self.selected_session -= 1
        self.load_session_json()
        self.loaded_session_var.set(f"Session\n{self.selected_session} / {self.session_number}")

    def next_event(self):
        if self.selected_event + 1 > self.event_number:
            self.selected_event = 1
        else:
            self.selected_event += 1
        self.loaded_event_var.set(f"Event\n{self.selected_event} / {self.event_number}")
        self.load_event()

    def prev_event(self):
        if self.selected_event - 1 < 1:
            self.selected_event = self.event_number
        else:
            self.selected_event -= 1
        self.loaded_event_var.set(f"Event\n{self.selected_event} / {self.event_number}")
        self.load_event()

    def check_radio(self):
        if self.prim_var.get() == "Primary":
            self.sess_num.set(self.prim_session_number)
            self.session_number = self.prim_session_number
        elif self.prim_var.get() == "Reliability":
            self.sess_num.set(self.reli_session_number)
            self.session_number = self.reli_session_number
        else:
            print(f"ERROR: Something went wrong assigning the session type "
                  f"{self.prim_var.get()}")
        if self.session_number == 0:
            self.forward_session_button['state'] = 'disabled'
            self.backward_session_button['state'] = 'disabled'
            self.load_session_button['state'] = 'disabled'
            self.no_sessions_found()
            self.loaded_session_var.set(f"Session\n0 / 0")
        else:
            self.forward_session_button['state'] = 'active'
            self.backward_session_button['state'] = 'active'
            self.load_session_button['state'] = 'active'
            self.selected_session = 1
            self.load_session_json()
            self.loaded_session_var.set(f"Session\n{self.selected_session} / {self.session_number}")

    def play_clip(self):
        if not self.caller.ovu.video_view.player.playing:
            self.caller.ovu.video_view.play_video()
        else:
            self.caller.ovu.video_view.pause_video()

    def load_session_json(self):
        try:
            if self.prim_var.get() == "Primary":
                self.session_file = self.caller.prim_files[int(self.selected_session) - 1]
                with open(self.session_file, 'r') as f:
                    self.session_json = json.load(f)
            elif self.prim_var.get() == "Reliability":
                self.session_file = self.caller.reli_files[int(self.selected_session) - 1]
                with open(self.session_file, 'r') as f:
                    self.session_json = json.load(f)
            else:
                messagebox.showerror("Error", "Something went wrong loading the session JSON file!")
                return False
            self.check_session()
            return True
        except IndexError:
            self.check_session()
            return False

    def load_session(self):
        if self.review_name_var.get() == "":
            messagebox.showwarning("Review Name Empty", "Fill out reviewer name before starting!")
        else:
            if self.load_session_json():
                self.session_video_file = os.path.join(pathlib.Path(self.session_file).parent,
                                                       pathlib.Path(self.session_file).stem + ".mp4")
                if os.path.exists(self.session_video_file):
                    self.session_events = self.session_json["Event History"]
                    if len(self.session_events):
                        self.selected_event = 1
                        self.event_number = len(self.session_events)
                        self.loaded_event_var.set(f"Event\n{self.selected_event} / {len(self.session_events)}")
                        self.caller.ovu.video_view.load_video(ask=False, video_filepath=self.session_video_file)
                        self.caller.ovu.video_view.add_event_history(self.session_events)
                        self.caller.ovu.video_view.populate_event_treeview_review()
                        self.enable_event_review()
                        self.disable_session_select()
                        self.load_event()
                    else:
                        messagebox.showinfo("No Session Events", "No session events found in this session!")
                else:
                    messagebox.showerror("No Video Found", "Annotations cannot be checked without an associated video!")

    def load_event(self):
        if self.session_events:
            self.selected_event_json = self.session_events[int(self.selected_event) - 1]
            if type(self.selected_event_json[1]) is list:
                self.caller.ovu.video_view.focus_on_event(int(self.selected_event) - 1)
                self.caller.ovu.video_view.set_clip(self.selected_event_json[2][0], self.selected_event_json[2][1])
                freq_val, dur_val = self.get_key_binding(self.selected_event_json)
                self.freq_var.set(freq_val)
                self.dur_var.set(str(dur_val[0]) + " {" + str(dur_val[1]) + "}")
                self.to_frame.set(self.selected_event_json[2][0])
                self.from_frame_entry['state'] = 'normal'
                self.from_frame.set(self.selected_event_json[2][1])
            else:
                self.caller.ovu.video_view.focus_on_event(int(self.selected_event) - 1)
                self.caller.ovu.video_view.set_clip(self.selected_event_json[2] - 8, self.selected_event_json[2] + 7)
                freq_val, dur_val = self.get_key_binding(self.selected_event_json)
                self.freq_var.set(str(freq_val[0]) + " {" + str(freq_val[1]) + "}")
                self.dur_var.set(dur_val)
                self.to_frame.set(self.selected_event_json[2])
                self.from_frame_entry['state'] = 'disabled'
                self.from_frame.set("")
        else:
            self.disable_event_review()
            self.save_session_button['state'] = 'normal'
            self.loaded_event_var.set(f"Event\n0 / 0")

    def get_key_binding(self, event):
        if type(event[1]) is list:
            for bind in self.caller.ovu.key_view.dur_bindings:
                if event[0] == bind[1]:
                    return 'None', bind
        else:
            for bind in self.caller.ovu.key_view.bindings:
                if event[0] == bind[1]:
                    return bind, 'None'
        messagebox.showerror("Error", f"Something was wrong with selected event!\n{event}")
        return 'None', 'None'

    def check_session(self):
        try:
            if self.session_json['Reviewed']:
                self.session_reviewed()
                return True
            self.session_needs_review()
            return False
        except KeyError:
            self.session_needs_review()
            return False

    def session_reviewed(self):
        self.check_session_var.set(f"{self.session_json['Reviewer']}: {checkmark}")
        self.check_session_label.config(fg='green')

    def session_needs_review(self):
        self.check_session_var.set(f"Session Review: {crossmark}")
        self.check_session_label.config(fg='red')

    def no_sessions_found(self):
        self.check_session_var.set("No sessions found!")
        self.check_session_label.config(fg='red')

    def accept_changes(self):
        if self.dur_var.get() != 'None' and self.freq_var.get() != 'None':
            messagebox.showerror("Error",
                                 "Only one tag per event is allowed, set either frequency or duration dropdown to None!")
            print("ERROR: Only one tag per event is allowed, set either frequency or duration dropdown to None")
        elif self.dur_var.get() == 'None' and self.freq_var.get() == 'None':
            messagebox.showerror("Error", "Event must have a tag, reject the event to delete it!")
            print("ERROR: Event must have a tag, reject the event to delete it")
        elif self.dur_var.get() != 'None':
            new_event_tag = ' '.join(self.dur_var.get().split(' ')[1:]).replace('{', '').replace('}', '')
            start_frame, end_frame = int(self.to_frame.get()), int(self.from_frame.get())
            start_time, end_time = int((float(start_frame) / self.caller.ovu.video_view.player.fps)), \
                                   int((float(end_frame) / self.caller.ovu.video_view.player.fps))
            if self.caller.ovu.video_view.player.audio_loaded:
                start_audio, end_audio = int((
                                                         len(self.caller.ovu.video_view.player.audio_data) * start_frame) / self.caller.ovu.video_view.player.nframes), \
                                         int((
                                                         len(self.caller.ovu.video_view.player.audio_data) * end_frame) / self.caller.ovu.video_view.player.nframes)
            else:
                start_audio, end_audio = None, None
            start_e4, end_e4 = None, None
            self.session_events[int(self.selected_event) - 1] = (new_event_tag, [start_time, end_time],
                                                                 [start_frame, end_frame], [start_e4, end_e4],
                                                                 [start_audio, end_audio])
            self.caller.ovu.video_view.add_event_history(self.session_events)
            self.caller.ovu.video_view.populate_event_treeview_review()
            self.caller.ovu.video_view.focus_on_event(int(self.selected_event) - 1)
            self.load_event()
            self.next_event()
        elif self.freq_var.get() != 'None':
            new_event_tag = ' '.join(self.freq_var.get().split(' ')[1:]).replace('{', '').replace('}', '')
            start_frame = int(self.to_frame.get())
            start_time = int((float(start_frame) / self.caller.ovu.video_view.player.fps))
            if self.caller.ovu.video_view.player.audio_loaded:
                start_audio = int((
                                              len(self.caller.ovu.video_view.player.audio_data) * start_frame) / self.caller.ovu.video_view.player.nframes)
            else:
                start_audio = None
            start_e4 = None
            self.session_events[int(self.selected_event) - 1] = (
            new_event_tag, start_time, start_frame, start_e4, start_audio)

            self.caller.ovu.video_view.add_event_history(self.session_events)
            self.caller.ovu.video_view.populate_event_treeview_review()
            self.caller.ovu.video_view.focus_on_event(int(self.selected_event) - 1)
            self.load_event()
            self.next_event()
        else:
            messagebox.showerror("Error",
                                 f"Something went wrong accepting changes!\n{self.dur_var.get()}\n{self.freq_var.get()}")
            print("ERROR: Something went wrong accepting changes!")

    def reject_changes(self):
        self.session_events.pop(int(self.selected_event) - 1)
        self.event_number = len(self.session_events)
        self.selected_event = 1
        self.loaded_event_var.set(f"Event\n{self.selected_event} / {self.event_number}")
        self.caller.ovu.video_view.clear_clip()
        self.caller.ovu.video_view.add_event_history(self.session_events)
        self.caller.ovu.video_view.populate_event_treeview_review()
        self.load_event()
        self.next_event()

    def reset_session(self):
        self.enable_session_select()
        self.disable_event_review()
        self.caller.ovu.video_view.player.close()
        self.load_session_json()

    def approve_changes(self):
        self.session_json['Reviewer'] = self.review_name_var.get()
        self.session_json['Reviewed'] = True
        with open(self.session_file, 'w') as f:
            json.dump(self.session_json, f)
        messagebox.showinfo("Success", "Changes have been saved!")
        self.enable_session_select()
        self.disable_event_review()
        self.caller.ovu.video_view.player.close()
        self.load_session_json()
