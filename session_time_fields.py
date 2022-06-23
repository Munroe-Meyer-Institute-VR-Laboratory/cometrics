import datetime
import math
import threading
import time
import winsound
from tkinter import *

from tkinter_utils import set_entry_text
from ui_params import treeview_bind_tags


# TODO: Create a wrapper on this like the output view ui to create the 'Session' mode and 'Review' mode
# TODO: Either the panel is switched by clicking a tab or it can be automatically created when a session with existing data is loaded?
# TODO: It would seem potentially confusing to not have some kind of obvious UI change, so maybe some kind of header tab?
# TODO: No, because you need to be able to switch back and forth, if you're reviewing a session and need to change something,
# TODO: the 'Session' mode can be used to do that
class SessionTimeFields:
    def __init__(self, caller, parent, x, y, height, width, button_size,
                 header_font=('Purisa', 14), field_font=('Purisa', 11),
                 field_offset=60, ovu=None):
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
        session_time_label = Label(self.session_frame, text="Session Time", font=(header_font[0], header_font[1], 'bold'))
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
        self.session_toggle_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 9), anchor=CENTER)
        self.key_explanation = Label(self.session_frame, text="Esc Key", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 9), anchor=W)

        self.session_pause_button = Button(self.session_frame, text="Pause Session", width=13,
                                           font=field_font, command=self.caller.pause_session)
        self.session_pause_button.place(x=width / 2, y=self.start_y + ((field_offset / 2) * 10.5), anchor=CENTER)
        self.key_explanation = Label(self.session_frame, text="Left Ctrl", font=field_font,
                                     justify=LEFT)
        self.key_explanation.place(x=width * 0.75, y=self.start_y + ((field_offset / 2) * 10.5), anchor=W)

        self.play_image = PhotoImage(file='images/video-start.png')
        self.pause_image = PhotoImage(file='images/video-pause.png')
        self.forward_image = PhotoImage(file='images/skip_forward.png')
        self.backward_image = PhotoImage(file='images/skip_backward.png')
        #
        self.play_button = Button(self.session_frame, image=self.play_image,
                                  command=self.caller.start_session)
        self.forward_button = Button(self.session_frame, image=self.forward_image)
        self.backward_button = Button(self.session_frame, image=self.backward_image)

        self.session_duration = None
        self.beep_th = None
        self.interval_thread = None

        # session_button = Button(self.frame, text="Session", command=self.switch_session_frame, width=12,
        #                         font=field_font)
        # self.view_buttons.append(session_button)
        # self.SESSION_VIEW = len(self.view_buttons) - 1
        # self.view_buttons[self.SESSION_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
        #                                            width=button_size[0], height=button_size[1])
        # self.view_buttons[self.SESSION_VIEW].config(relief=SUNKEN)

        # review_button = Button(self.frame, text="Review", command=self.switch_review_frame, width=12,
        #                        font=field_font)
        # self.view_buttons.append(review_button)
        # self.REVIEW_VIEW = len(self.view_buttons) - 1
        # self.view_buttons[self.REVIEW_VIEW].place(x=(len(self.view_buttons) - 1) * button_size[0], y=0,
        #                                           width=button_size[0], height=button_size[1])

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
        self.play_button.place(x=self.width / 2,
                               y=self.start_y + ((self.field_offset / 2) * 12.0), anchor=N)
        self.forward_button.place(x=(self.width / 2) + 60,
                                  y=self.start_y + ((self.field_offset / 2) * 12.0), anchor=N)
        self.backward_button.place(x=(self.width / 2) - 60,
                                   y=self.start_y + ((self.field_offset / 2) * 12.0), anchor=N)
        self.forward_button.config(state='disabled')
        self.backward_button.config(state='disabled')
        self.session_dur_selection.set(True)
        self.show_session_time()
        set_entry_text(self.session_dur_input, str(int(math.ceil(nframes))))
        self.session_dur_input.config(state='disabled')
        self.session_dur_checkbutton.config(state='disabled')
        # TODO: This feels like a lot of dependency on structure
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
        # TODO: Tie in Woodway and BLE protocol access
        while self.timer_running:
            time.sleep(1 - time.monotonic() % 1)
            if self.timer_running:
                if self.session_started and not self.session_paused:
                    self.session_time += 1
                    for i in range(0, len(self.ovu.key_view.dur_sticky)):
                        if self.ovu.key_view.dur_sticky[i]:
                            self.ovu.key_view.dur_treeview.set(str(i), column="1",
                                                      value=self.session_time - self.ovu.key_view.sticky_start[i])
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
                if self.session_time < self.ovu.key_view.sticky_start[i]:
                    self.ovu.key_view.dur_sticky[i] = False
                    self.ovu.key_view.dur_treeview.item(str(i), tags=treeview_bind_tags[i % 2])
                else:
                    self.ovu.key_view.dur_treeview.set(str(i), column="1",
                                              value=self.session_time - self.ovu.key_view.sticky_start[i])

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
    def __init__(self, caller, parent, x, y, height, width, button_size,
                 header_font=('Purisa', 14), field_font=('Purisa', 11),
                 field_offset=60, ovu=None):
        pass
