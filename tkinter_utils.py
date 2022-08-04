import _tkinter
import gc
import os.path
import pathlib
import threading
import time
import tkinter
import traceback
from tkinter import TOP, W, N, NW, messagebox, END, ttk, filedialog, INSERT
from tkinter.ttk import Style, Combobox
from tkinter.ttk import Treeview
import numpy as np
from PIL import ImageTk as itk
from github import Github
from logger_util import parse_log
from tkvideoutils import ImageLabel
from ui_params import treeview_default_tag_dict, cometrics_ver_root


def center(toplevel, y_offset=-20):
    toplevel.update_idletasks()

    # Tkinter way to find the screen resolution
    screen_width = toplevel.winfo_screenwidth()
    screen_height = toplevel.winfo_screenheight()

    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = screen_width / 2 - size[0] / 2
    y = screen_height / 2 - size[1] / 2
    y += y_offset
    toplevel.geometry("+%d+%d" % (x, y))


def get_display_size():
    root = tkinter.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    height = root.winfo_screenheight()
    width = root.winfo_screenwidth()
    root.attributes('-fullscreen', False)
    root.deiconify()
    root.focus_force()
    return root, height, width


def get_slider_style(root):
    fig_color = '#%02x%02x%02x' % (240, 240, 237)
    style = ttk.Style(root)
    style.theme_use('clam')
    # self.style.element_create('Horizontal.Scale.trough', 'image', self.trough_img)
    # create custom layout
    style.layout('custom.Horizontal.TScale',
                 [('Horizontal.Scale.trough',
                   {'sticky': 'nswe',
                    'children': [('custom.Horizontal.Scale.slider',
                                  {'side': 'left', 'sticky': ''})]})])
    style.configure('custom.Horizontal.TScale', background=fig_color)
    return 'custom.Horizontal.TScale', style


def get_treeview_style(name="mystyle.Treeview", font=('Purisa', 12), heading_font=('Purisa', 12, 'bold'),
                       rowheight=25, h_thickness=0, bd=0):
    style = Style()
    style.configure(name, highlightthickness=h_thickness, bd=bd, font=font)  # Modify the font of the body
    style.configure("mystyle.Treeview.Heading", font=heading_font)  # Modify the font of the headings
    style.configure('Treeview', rowheight=rowheight)
    style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))
    return style


def build_treeview(root, x, y, height, width, heading_dict, column_dict=None, selectmode='browse', t_height=18,
                   filescroll=True, button_1_bind=None, double_bind=None, button_3_bind=None, style="mystyle.Treeview",
                   anchor=NW, tag_dict=treeview_default_tag_dict, fs_offset=18):
    treeview = Treeview(root, style=style, height=t_height, selectmode=selectmode)
    treeview.place(x=x, y=y, height=height, width=width, anchor=anchor)
    # Define header
    heading = heading_dict["#0"]
    treeview.heading("#0", text=heading[0], anchor=heading[1])
    treeview.column("#0", width=heading[2], stretch=heading[3], anchor=heading[4])
    # Define columns
    if column_dict:
        treeview["columns"] = list(column_dict.keys())
        for col in column_dict:
            treeview.heading(col, text=column_dict[col][0], anchor=column_dict[col][1])
            treeview.column(col, width=column_dict[col][2], stretch=column_dict[col][3], anchor=column_dict[col][4])
    for tag in tag_dict:
        treeview.tag_configure(tag, background=tag_dict[tag])
    if button_1_bind:
        treeview.bind("<ButtonRelease-1>", button_1_bind)
    if double_bind:
        treeview.bind("<Double-Button-1>", double_bind)
    if button_3_bind:
        treeview.bind("<ButtonRelease-3>", button_3_bind)
    if filescroll:
        file_scroll = tkinter.Scrollbar(root, orient="vertical", command=treeview.yview)
        file_scroll.place(x=(x - fs_offset), y=y, height=height, anchor=anchor)
        treeview.configure(yscrollcommand=file_scroll.set)
    else:
        file_scroll = None
    return treeview, file_scroll


def clear_treeview(widget: Treeview):
    for children in widget.get_children():
        widget.delete(children)


def scroll_to(widget: Treeview, selection):
    widget.yview_moveto(int(selection) / (len(widget.get_children())))


def select_focus(widget: Treeview, selection):
    selection = str(selection)
    widget.selection_set(selection)
    widget.focus(selection)


def fixed_map(option):
    # https://stackoverflow.com/a/62011081
    # Fix for setting text colour for Tkinter 8.6.9
    # From: https://core.tcl.tk/tk/info/509cafafae
    #
    # Returns the style map for 'option' with any styles starting with
    # ('!disabled', '!selected', ...) filtered out.

    # style.map() returns an empty list for missing options, so this
    # should be future-safe.
    style = Style()
    return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]


class LoadingWindow:
    def __init__(self, objects):
        self.objects = objects
        self.root = root = tkinter.Tk()
        root.config(bd=-2)
        root.overrideredirect(True)
        root.geometry("250x100")
        center(self.root, y_offset=0)
        self.checkmark_img = tkinter.PhotoImage(file=os.path.join(os.getcwd(), r'images/checkmark.png'))
        self.label_var = tkinter.StringVar(root, value='Cleaning up resources')
        self.text_label = tkinter.Label(root, textvariable=self.label_var, font=('Purisa', 11))
        self.label = tkinter.Label(root)
        self.label.place(x=10, y=50, anchor=tkinter.W)
        self.text_label.place(x=70, y=50, anchor=tkinter.W)
        self.image_label = ImageLabel(os.path.join(os.getcwd(), r'images\loading.gif'), self.label, (100, 100))
        root.after(500, self.update_text)
        self.dots = 0
        self.done = False
        gc_thread = threading.Thread(target=self.perform_gc)
        gc_thread.daemon = True
        gc_thread.start()
        root.mainloop()

    def perform_gc(self):
        del self.objects
        gc.collect()
        time.sleep(1)
        self.image_label.unload()
        self.image_label.label.config(image=self.checkmark_img)
        time.sleep(1)
        self.done = True

    def update_text(self):
        try:
            self.dots += 1
            if self.dots > 3:
                self.dots = 0
            self.label_var.set(f"Cleaning up resources{'.' * self.dots}")
            if self.done:
                self.close()
            else:
                self.root.after(500, self.update_text)
        except _tkinter.TclError:
            pass

    def close(self):
        self.image_label.unload()
        self.label.destroy()
        self.root.quit()
        self.root.destroy()


class ExternalButtonPopup:
    def __init__(self, root, caller, field_font=('Purisa', 12)):
        self.caller = caller
        self.key = None
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x200")
        popup_root.title("External Button Setup")
        key_tag = tkinter.Label(popup_root, text="Key", bg='white', font=('Purisa', 12))
        key_tag.place(x=50, y=20)
        self.key_entry = tkinter.Entry(popup_root, bd=2, width=17, font=('Purisa', 12))
        self.key_entry.place(x=90, y=20)

        freq_label = tkinter.Label(popup_root, font=field_font, text="Frequency Key Association", bg='white')
        freq_label.place(x=50, y=50)
        self.freq_var = tkinter.StringVar(popup_root)
        freq_box = Combobox(popup_root, textvariable=self.freq_var, font=field_font)
        freq_box['values'] = ['None'] + self.caller.ovu.key_view.bindings
        freq_box['state'] = 'readonly'
        freq_box.config(font=field_font)
        freq_box.place(x=50, y=75, width=200)
        freq_box.option_add('*TCombobox*Listbox.font', field_font)

        dur_label = tkinter.Label(popup_root, font=field_font, text="Duration Key Association", bg='white')
        dur_label.place(x=50, y=100)
        self.dur_var = tkinter.StringVar(popup_root)
        dur_box = Combobox(popup_root, textvariable=self.dur_var, font=field_font)
        dur_box['values'] = ['None'] + self.caller.ovu.key_view.dur_bindings
        dur_box['state'] = 'readonly'
        dur_box.config(font=field_font)
        dur_box.place(x=50, y=125, width=200)
        dur_box.option_add('*TCombobox*Listbox.font', field_font)

        ok_button = tkinter.Button(popup_root, text="OK", command=self.on_closing, font=('Purisa', 12))
        ok_button.place(x=150, y=160, anchor=N)

    def set_value(self, key):
        self.key = key
        self.key_entry.delete(0, END)
        self.key_entry.insert(0, str(key))

    def on_closing(self):
        if self.key:
            self.caller.ext_raw = self.key
            if self.dur_var.get():
                if self.dur_var.get() != 'None':
                    self.caller.ext_dur_val = self.dur_var.get()[0]
            if self.freq_var.get():
                if self.freq_var.get() != 'None':
                    self.caller.ext_freq_val = self.freq_var.get()[0]
        self.caller.button_input_handler = None
        self.popup_root.destroy()


class EditEventPopup:
    def __init__(self, root, caller, dur_bindings, freq_bindings, selected_event, selection,
                 field_font=('Purisa', 12)):
        self.caller = caller
        self.selection = selection
        self.selected_event = selected_event
        self.dur_bindings, self.freq_bindings = dur_bindings, freq_bindings
        self.key = None
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x200")
        popup_root.title("Edit Event")
        center(popup_root)

        freq_label = tkinter.Label(popup_root, font=field_font, text="Frequency Key Association", bg='white')
        freq_label.place(x=50, y=20)
        self.freq_var = tkinter.StringVar(popup_root)
        freq_box = Combobox(popup_root, textvariable=self.freq_var, font=field_font)
        freq_box['values'] = ['None'] + freq_bindings
        freq_box['state'] = 'readonly'
        freq_box.config(font=field_font)
        freq_box.place(x=50, y=45, width=200)
        freq_box.option_add('*TCombobox*Listbox.font', field_font)

        dur_label = tkinter.Label(popup_root, font=field_font, text="Duration Key Association", bg='white')
        dur_label.place(x=50, y=70)
        self.dur_var = tkinter.StringVar(popup_root)
        dur_box = Combobox(popup_root, textvariable=self.dur_var, font=field_font)
        dur_box['values'] = ['None'] + dur_bindings
        dur_box['state'] = 'readonly'
        dur_box.config(font=field_font)
        dur_box.place(x=50, y=95, width=200)
        dur_box.option_add('*TCombobox*Listbox.font', field_font)

        if type(selected_event[1]) is list:
            freq_val, dur_val = self.get_key_binding(selected_event)
            self.freq_var.set(freq_val)
            self.dur_var.set(str(dur_val[0]) + " {" + str(dur_val[1]) + "}")
            freq_box['state'] = 'disabled'
        else:
            freq_val, dur_val = self.get_key_binding(selected_event)
            self.freq_var.set(str(freq_val[0]) + " {" + str(freq_val[1]) + "}")
            self.dur_var.set(dur_val)
            dur_box['state'] = 'disabled'

        ok_button = tkinter.Button(popup_root, text="OK", command=self.on_closing, font=field_font)
        ok_button.place(x=150, y=130, anchor=N)

    def get_key_binding(self, event):
        if type(event[1]) is list:
            for bind in self.dur_bindings:
                if event[0] == bind[1]:
                    return 'None', bind
        else:
            for bind in self.freq_bindings:
                if event[0] == bind[1]:
                    return bind, 'None'
        messagebox.showerror("Error", f"Something was wrong with selected event!\n{event}")
        return 'None', 'None'

    def on_closing(self):
        if self.dur_var.get() != 'None' and self.freq_var.get() != 'None':
            messagebox.showerror("Error", "Event cannot have two tags! Set either duration or frequency to 'None'!")
            self.popup_root.focus_force()
            return
        elif self.dur_var.get() == 'None' and self.freq_var.get() == 'None':
            messagebox.showerror("Error", "Event must have a value! Set either duration or frequency to an event!")
            self.popup_root.focus_force()
            return
        elif self.dur_var.get() != 'None':
            self.selected_event[0] = ' '.join(self.dur_var.get().split(' ')[1:]).replace('{', '').replace('}', '')
        elif self.freq_var.get() != 'None':
            self.selected_event[0] = ' '.join(self.freq_var.get().split(' ')[1:]).replace('{', '').replace('}', '')
        self.caller.popup_return(self.selection, self.selected_event)
        self.popup_root.destroy()


class ConfigPopup:
    def __init__(self, root, config):
        self.config = config
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x380")
        popup_root.title("Configuration Settings")
        fps_tag = tkinter.Label(popup_root, text="FPS", bg='white', font=('Purisa', 12))
        fps_tag.place(x=10, y=10)
        self.fps_entry = tkinter.Entry(popup_root, bd=2, width=5, font=('Purisa', 12))
        self.fps_entry.insert(0, int(self.config.get_fps()))
        self.fps_entry.place(x=60, y=10)
        self.e4_var = tkinter.BooleanVar(popup_root, value=self.config.get_e4())
        e4_checkbutton = tkinter.Checkbutton(popup_root, text="E4 Enabled", bg='white', variable=self.e4_var,
                                             font=('Purisa', 12))
        e4_checkbutton.place(x=10, y=50)
        self.woodway_var = tkinter.BooleanVar(popup_root, value=self.config.get_woodway())
        woodway_checkbutton = tkinter.Checkbutton(popup_root, text="Woodway Enabled", bg='white',
                                                  variable=self.woodway_var, font=('Purisa', 12))
        woodway_checkbutton.place(x=10, y=90)
        self.ble_var = tkinter.BooleanVar(popup_root, value=self.config.get_ble())
        ble_checkbutton = tkinter.Checkbutton(popup_root, text="BLE Enabled", bg='white',
                                              variable=self.ble_var, font=('Purisa', 12))
        ble_checkbutton.place(x=10, y=130)

        a_tag = tkinter.Label(popup_root, text="A", bg='white', font=('Purisa', 12))
        a_tag.place(x=10, y=170)

        self.a_entry = tkinter.Entry(popup_root, bd=2, width=12, font=('Purisa', 12))
        self.a_entry.insert(0, str(self.config.get_woodway_a()))
        self.a_entry.place(x=60, y=170)

        b_tag = tkinter.Label(popup_root, text="B", bg='white', font=('Purisa', 12))
        b_tag.place(x=10, y=210)

        self.b_entry = tkinter.Entry(popup_root, bd=2, width=12, font=('Purisa', 12))
        self.b_entry.insert(0, str(self.config.get_woodway_b()))
        self.b_entry.place(x=60, y=210)

        self.review_var = tkinter.BooleanVar(popup_root, value=self.config.get_review())
        review_checkbutton = tkinter.Checkbutton(popup_root, text="Review Mode Enabled", bg='white',
                                                 variable=self.review_var, font=('Purisa', 12))
        review_checkbutton.place(x=10, y=250)

        clear_projects = tkinter.Button(popup_root, text="Clear Recent Projects",
                                        font=('Purisa', 12), command=self.clear_projects)
        clear_projects.place(x=10, y=290)
        ok_button = tkinter.Button(popup_root, text="OK", command=self.on_closing, font=('Purisa', 12))
        ok_button.place(x=150, y=330, anchor=N)

    def on_closing(self):
        self.update_fps()
        self.update_e4()
        self.update_woodway()
        self.update_ble()
        self.update_review()
        self.popup_root.destroy()

    def update_fps(self):
        self.config.set_fps(int(self.fps_entry.get()))

    def update_e4(self):
        self.config.set_e4(self.e4_var.get())

    def update_ble(self):
        self.config.set_ble(self.ble_var.get())

    def update_woodway(self):
        self.config.set_woodway(self.woodway_var.get())

    def update_review(self):
        self.config.set_review(self.review_var.get())

    def clear_projects(self):
        self.config.set_recent_projects([])


class ProjectPopup:
    def __init__(self, top, root, name, popup_call):
        assert top.popup_return
        self.popup_call = popup_call
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = name
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("400x100")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        project_name_text = tkinter.Label(popup_root, text="Project Name", font=('Purisa', 10), bg='white')
        project_name_text.place(x=10, y=10, anchor=NW)
        self.project_name_var = tkinter.StringVar(popup_root)
        self.entry = tkinter.Entry(popup_root, bd=2, width=35, textvariable=self.project_name_var)
        self.entry.place(x=110, y=11, anchor=NW)

        project_dir_text = tkinter.Label(popup_root, text="Project Folder", font=('Purisa', 10), bg='white')
        project_dir_text.place(x=10, y=40, anchor=NW)
        self.dir_entry_var = tkinter.StringVar(popup_root, value=rf'{cometrics_ver_root}\Projects')
        self.dir_entry = tkinter.Entry(popup_root, bd=2, width=35, textvariable=self.dir_entry_var)
        self.dir_entry.place(x=110, y=41, anchor=NW)

        self.folder_img = itk.PhotoImage(file='images/folder.png')
        dir_button = tkinter.Button(popup_root, image=self.folder_img, command=self.select_dir)
        dir_button.place(x=330, y=40, anchor=NW)

        # Create a Button Widget in the Toplevel Window
        import_button = tkinter.Button(popup_root, text="Import", command=self.import_project)
        import_button.place(x=195, y=95, anchor=tkinter.SE, width=50)
        button = tkinter.Button(popup_root, text="OK", command=self.close_win)
        button.place(x=205, y=95, anchor=tkinter.SW, width=50)
        center(popup_root)
        popup_root.focus_force()
        self.entry.focus()

    def import_project(self):
        chosen_project = filedialog.askdirectory(initialdir=rf'{cometrics_ver_root}\Projects',
                                                 title='Select project folder')
        if chosen_project:
            if os.path.isdir(chosen_project):
                if not os.path.exists(os.path.join(chosen_project, '.cometrics')):
                    response = messagebox.askyesno("Invalid Project", "Project is not a valid cometrics project, "
                                                                      "this could happen if importing a legacy project "
                                                                      "(legacy projects will be updated in that case), "
                                                                      "continue?")
                    if not response:
                        self.popup_root.focus_force()
                        return
                self.dir_entry_var.set(pathlib.Path(chosen_project).parent)
                self.project_name_var.set(pathlib.Path(chosen_project).name)
                self.close_win()
            else:
                messagebox.showerror("Project Error", "Projects must be folders!")

    def select_dir(self):
        chosen_dir = filedialog.askdirectory(title='Select root directory to save files')
        if chosen_dir:
            self.dir_entry_var.set(chosen_dir)
        self.popup_root.focus_force()

    def close_win(self):
        self.caller.popup_return((self.entry.get(), self.dir_entry.get()), self.popup_call)
        self.popup_root.destroy()


class EntryPopup:
    def __init__(self, top, root, name, popup_call):
        assert top.popup_return
        self.popup_call = popup_call
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = name
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x50")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        self.entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.entry.pack()

        # Create a Button Widget in the Toplevel Window
        button = tkinter.Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)
        center(popup_root)
        popup_root.focus_force()
        self.entry.focus()

    def close_win(self):
        try:
            self.caller.popup_return(self.entry.get(), self.popup_call)
            self.popup_root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Exception encountered:\n{str(e)}\n{traceback.print_exc()}")


class NewKeyPopup:
    def __init__(self, top, root, dur_freq):
        assert top.key_popup_return
        self.caller = top
        self.dur_freq = dur_freq
        self.tag_entry = None
        self.key_entry = None
        self.popup_root = None
        self.new_key_name_entry(root)

    def new_key_name_entry(self, root):
        # Create a Toplevel window
        popup_root = self.popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x100")
        popup_root.title("Enter New Binding")

        # Create an Entry Widget in the Toplevel window
        self.tag_label = tkinter.Label(popup_root, text="Key Tag", bg='white')
        self.tag_label.place(x=30, y=20, anchor=W)
        self.tag_entry = tkinter.Entry(popup_root, bd=2, width=25, bg='white')
        self.tag_entry.place(x=90, y=20, anchor=W)

        self.key_label = tkinter.Label(popup_root, text="Key", bg='white')
        self.key_label.place(x=30, y=50, anchor=W)
        self.key_entry = tkinter.Entry(popup_root, bd=2, width=25, bg='white')
        self.key_entry.place(x=90, y=50, anchor=W)

        # Create a Button Widget in the Toplevel Window
        button = tkinter.Button(popup_root, text="OK", command=self.close_win)
        button.place(x=150, y=70, anchor=N)
        center(popup_root)
        popup_root.focus_force()
        self.tag_entry.focus()

    def close_win(self):
        if len(self.key_entry.get()) == 1:
            self.caller.key_popup_return(self.tag_entry.get(), self.key_entry.get(), self.dur_freq)
            self.popup_root.destroy()
        else:
            messagebox.showwarning("Warning", 'New key binding can only be one character!')
            print("WARNING: New key binding can only be one character!")
            self.popup_root.focus_force()
            self.tag_entry.focus()


def set_entry_text(widget: tkinter.Entry, text):
    widget.delete(0, END)
    widget.insert(0, text)


class AddWoodwayProtocolStep:
    def __init__(self, top, root, edit=False, dur=None, rs=None, ls=None, incl=None):
        assert top.popup_return
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = "Add Woodway Step"
        self.dur, self.rs, self.ls, self.incl = dur, rs, ls, incl
        self.edit = edit
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x250")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        label = tkinter.Label(popup_root, text="Step Duration", font=('Purisa', 12), bg='white')
        label.pack()
        self.duration_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.duration_entry.pack()
        if self.dur is not None:
            set_entry_text(self.duration_entry, self.dur)
        label = tkinter.Label(popup_root, text="Left Side Speed", font=('Purisa', 12), bg='white')
        label.pack()
        self.ls_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.ls_entry.pack()
        if self.ls is not None:
            set_entry_text(self.ls_entry, self.ls)
        label = tkinter.Label(popup_root, text="Right Side Speed", font=('Purisa', 12), bg='white')
        label.pack()
        self.rs_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.rs_entry.pack()
        if self.rs is not None:
            set_entry_text(self.rs_entry, self.rs)
        label = tkinter.Label(popup_root, text="Incline", font=('Purisa', 12), bg='white')
        label.pack()
        self.incline_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.incline_entry.pack()
        if self.incl is not None:
            set_entry_text(self.incline_entry, self.incl)

        # Create a Button Widget in the Toplevel Window
        button = tkinter.Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)
        center(popup_root)
        popup_root.focus_force()
        self.duration_entry.focus()

    def close_win(self):
        try:
            new_step = [float(self.duration_entry.get()), float(self.ls_entry.get()),
                        float(self.rs_entry.get()), float(self.incline_entry.get())]
            self.caller.popup_return(new_step, self.edit)
            self.popup_root.destroy()
        except ValueError:
            messagebox.showerror("Error", "All values input must be numbers! Check Woodway documentation or\n"
                                          "User Guide for valid values!")


class AddBleProtocolStep:
    def __init__(self, top, root, edit=False, dur=None, motor_1=None, motor_2=None):
        assert top.popup_return
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = "Add BLE Step"
        self.edit = edit
        self.dur, self.motor_1, self.motor_2 = dur, motor_1, motor_2
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x175")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        label = tkinter.Label(popup_root, text="Step Duration", font=('Purisa', 12), bg='white')
        label.pack()
        self.duration_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.duration_entry.pack()
        if self.dur is not None:
            set_entry_text(self.duration_entry, self.dur)
        label = tkinter.Label(popup_root, text="Left Motor Level", font=('Purisa', 12), bg='white')
        label.pack()
        self.motor_1_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.motor_1_entry.pack()
        if self.motor_1 is not None:
            set_entry_text(self.motor_1_entry, self.motor_1)
        label = tkinter.Label(popup_root, text="Right Motor Level", font=('Purisa', 12), bg='white')
        label.pack()
        self.motor_2_entry = tkinter.Entry(popup_root, bd=2, width=25)
        self.motor_2_entry.pack()
        if self.motor_2 is not None:
            set_entry_text(self.motor_2_entry, self.motor_2)

        # Create a Button Widget in the Toplevel Window
        button = tkinter.Button(popup_root, text="OK", command=self.close_win)
        button.pack(pady=5, side=TOP)
        center(popup_root)
        popup_root.focus_force()
        self.duration_entry.focus()

    def close_win(self):
        try:
            new_step = [float(self.duration_entry.get()), float(self.motor_1_entry.get()),
                        float(self.motor_2_entry.get())]
            self.caller.popup_return(new_step, edit=self.edit)
            self.popup_root.destroy()
        except ValueError:
            messagebox.showerror("Error", "All values input must be numbers! Check Woodway documentation or\n"
                                          "User Guide for valid values!")


class CalibrateWoodway:
    def __init__(self, top, root, woodway):
        assert top.calibrate_return
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = "Calibrate Woodway"
        self.woodway = woodway
        self.calibrating = False
        self.calibrated_speed_increasing = None
        self.calibrated_speed_decreasing = None
        self.calibrated_speed = None
        self.calibration_step = 0
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("800x300")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        label = tkinter.Label(popup_root, text="1. Press the 'Calibrate' button,\n"
                                               "2. The Woodway will increase speed by 0.1 MPH from zero every five seconds,\n"
                                               "3. Prompt the subject to alert operator when walking feels comfortable,\n"
                                               "4. When subject alerts operator, press the 'Stop' button,\n"
                                               "5. The speed when stopped will be recorded, \n"
                                               "6. Press 'Calibrate' button again to decrease speed from 150% of previous recorded speed,\n"
                                               "7. Prompt the subject to alert operator when walking feel comfortable,\n"
                                               "8. When subject alerts operator, press the 'Stop' button,\n"
                                               "9. The speed when stopped will be recorded,\n"
                                               "10. The two recorded speeds will be averaged and saved as the Preferred Walking Speed,\n"
                                               "11. Double check the final speed and press 'Save' to save the speed.",
                              font=('Purisa', 12), bg='white', justify=tkinter.LEFT)
        label.pack()

        # Create a Button Widget in the Toplevel Window
        label.place(x=10, y=10)

        # Create a Button Widget in the Toplevel Window
        self.cal_button = tkinter.Button(popup_root, text="Calibrate", command=self.start_calibration_step,
                                         font=('Purisa', 12))
        self.cal_button.place(x=400, y=280, anchor=tkinter.SE, width=150, height=30)
        self.stop_button = tkinter.Button(popup_root, text="Stop", command=self.stop_calibration_step,
                                          font=('Purisa', 12))
        self.stop_button.place(x=400, y=280, anchor=tkinter.SW, width=150, height=30)
        self.stop_button["state"] = 'disabled'
        self.calibration_text_var = tkinter.StringVar(popup_root, value=f"Calibration Value: 0.0 MPH")
        text = tkinter.Label(popup_root, textvariable=self.calibration_text_var, font=('Purisa', 12), bg='white')
        text.place(x=400, y=240, anchor=tkinter.S)
        center(popup_root)
        popup_root.focus_force()

    def start_calibration_step(self):
        if self.calibration_step == 0:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread, args=(0.1, True))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        elif self.calibration_step == 1:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread,
                                          args=(self.calibrated_speed_increasing * 1.5, False))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        self.stop_button["state"] = 'active'
        self.cal_button["state"] = 'disabled'

    def calibration_thread(self, start_value, increasing):
        while self.calibrating:
            if increasing:
                for speed in np.arange(start_value, 20.0, 0.1):
                    self.calibrated_speed_increasing = speed
                    self.woodway.set_speed(float(speed), float(speed))
                    self.calibration_text_var.set(f"Calibration Value: {self.calibrated_speed_increasing:.1f} MPH")
                    for i in range(0, 4):
                        time.sleep(0.25)
                        if not self.calibrating:
                            self.calibrated_speed_increasing = np.average(self.woodway.get_speeds())
                            self.woodway.set_speed(float(0.0), float(0.0))
                            return
            else:
                for speed in np.arange(start_value, 0.0, -0.1):
                    self.calibrated_speed_decreasing = speed
                    self.woodway.set_speed(float(speed), float(speed))
                    self.calibration_text_var.set(f"Calibration Value: {self.calibrated_speed_decreasing:.1f} MPH")
                    for i in range(0, 4):
                        time.sleep(0.25)
                        if not self.calibrating:
                            self.calibrated_speed_decreasing = np.average(self.woodway.get_speeds())
                            self.woodway.set_speed(float(0.0), float(0.0))
                            if self.calibrated_speed_increasing and self.calibrated_speed_decreasing:
                                self.calibrated_speed = np.average([self.calibrated_speed_increasing,
                                                                    self.calibrated_speed_decreasing])
                                self.calibration_text_var.set(f"Calibration Value: {self.calibrated_speed:.1f} MPH")
                                self.stop_button.config(text="Save", command=self.close_win)
                            return

    def stop_calibration_step(self):
        self.calibrating = False
        if self.calibration_step == 2:
            self.stop_button["state"] = 'active'
            self.cal_button["state"] = 'disabled'
        else:
            self.stop_button["state"] = 'disabled'
            self.cal_button["state"] = 'active'

    def close_win(self):
        if self.calibrated_speed:
            self.caller.calibrate_return(self.calibrated_speed)
        self.calibrating = False
        self.popup_root.destroy()


class CalibrateVibrotactors:
    def __init__(self, top, root, left_vta, right_vta):
        assert top.calibrate_return
        self.caller = top
        self.entry = None
        self.popup_root = None
        self.name = "Calibrate Vibrotactors"
        self.left_vta, self.right_vta = left_vta, right_vta
        self.calibrating = False
        self.calibrated_left_increasing = None
        self.calibrated_right_increasing = None
        self.calibrated_left_decreasing = None
        self.calibrated_right_decreasing = None
        self.calibrated_left = None
        self.calibrated_right = None
        self.calibration_step = 0
        self.popup_entry(root)

    def popup_entry(self, root):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("800x350")
        popup_root.title(self.name)

        # Create an Entry Widget in the Toplevel window
        label = tkinter.Label(popup_root, text="1. Press the 'Calibrate Left' button,\n"
                                               "2. The vibrotactors will increase intensity by one from zero each second,\n"
                                               "3. Prompt the subject to alert operator when vibrotactors are perceptible,\n"
                                               "4. When subject alerts operator, press the 'Stop' button,\n"
                                               "5. The intensity level when stopped will be recorded, \n"
                                               "6. Press 'Calibrate Left' button again to decrease intensity from 150% of previous recorded intensity level,\n"
                                               "7. Prompt the subject to alert operator when vibrotactors are perceptible,\n"
                                               "8. When subject alerts operator, press the 'Stop' button,\n"
                                               "9. The intensity level when stopped will be recorded,\n"
                                               "10. The two recorded levels will be averaged and saved as the Left Sensory Perception Threshold,\n"
                                               "11. Notice 'Calibrate Right' button, repeat procedure for left vibrotactor,\n"
                                               "12. Double check the final values and press 'Save' to save the thresholds.",
                              font=('Purisa', 12), bg='white', justify=tkinter.LEFT)
        label.place(x=10, y=10)

        # Create a Button Widget in the Toplevel Window
        self.cal_button = tkinter.Button(popup_root, text="Calibrate Left", command=self.start_calibration_step,
                                         font=('Purisa', 12))
        self.cal_button.place(x=400, y=330, anchor=tkinter.SE, width=150, height=30)
        self.stop_button = tkinter.Button(popup_root, text="Stop", command=self.stop_calibration_step,
                                          font=('Purisa', 12))
        self.stop_button.place(x=400, y=330, anchor=tkinter.SW, width=150, height=30)
        self.stop_button["state"] = 'disabled'
        self.calibration_text_var = tkinter.StringVar(popup_root, value=f"Calibration Left: 0\tCalibration Right: 0")
        text = tkinter.Label(popup_root, textvariable=self.calibration_text_var, font=('Purisa', 12), bg='white')
        text.place(x=400, y=290, anchor=tkinter.S)
        center(popup_root)
        popup_root.focus_force()

    def start_calibration_step(self):
        if self.calibration_step == 0:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread, args=(self.left_vta, 0, True, True))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        elif self.calibration_step == 1:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread,
                                          args=(self.left_vta, int(self.calibrated_left_increasing * 1.5),
                                                False, True))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        elif self.calibration_step == 2:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread,
                                          args=(self.right_vta, 0, True, False))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        elif self.calibration_step == 3:
            self.calibrating = True
            cal_thread = threading.Thread(target=self.calibration_thread,
                                          args=(self.right_vta, int(self.calibrated_right_increasing * 1.5),
                                                False, False))
            cal_thread.daemon = True
            cal_thread.start()
            self.calibration_step += 1
        self.stop_button["state"] = 'active'
        self.cal_button["state"] = 'disabled'

    def calibration_thread(self, vta, start_value, increasing, side):
        while self.calibrating:
            if side:
                if increasing:
                    for speed in np.arange(start_value, 255, 1):
                        self.calibrated_left_increasing = speed
                        vta.write_all_motors(speed)
                        self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left_increasing}"
                                                      f"\tCalibration Right: 0")
                        for i in range(0, 4):
                            time.sleep(0.25)
                            if not self.calibrating:
                                vta.write_all_motors(0)
                                return
                else:
                    for speed in np.arange(start_value, 0, -1):
                        self.calibrated_left_decreasing = speed
                        vta.write_all_motors(speed)
                        self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left_decreasing}"
                                                      f"\tCalibration Right: 0")
                        for i in range(0, 4):
                            time.sleep(0.25)
                            if not self.calibrating:
                                vta.write_all_motors(0)
                                if self.calibrated_left_decreasing and self.calibrated_left_increasing:
                                    self.calibrated_left = int(np.average([self.calibrated_left_increasing,
                                                                           self.calibrated_left_decreasing]))
                                    self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left}"
                                                                  f"\tCalibration Right: 0")
                                self.cal_button.config(text="Calibrate Right")
                                return
            else:
                if increasing:
                    for speed in np.arange(start_value, 255, 1):
                        self.calibrated_right_increasing = speed
                        vta.write_all_motors(speed)
                        self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left}"
                                                      f"\tCalibration Right: {self.calibrated_right_increasing}")
                        for i in range(0, 4):
                            time.sleep(0.25)
                            if not self.calibrating:
                                vta.write_all_motors(0)
                                return
                else:
                    for speed in np.arange(start_value, 0, -1):
                        self.calibrated_right_decreasing = speed
                        vta.write_all_motors(speed)
                        self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left}"
                                                      f"\tCalibration Right: {self.calibrated_right_decreasing}")
                        for i in range(0, 4):
                            time.sleep(0.25)
                            if not self.calibrating:
                                vta.write_all_motors(0)
                                if self.calibrated_right_decreasing and self.calibrated_right_increasing:
                                    self.calibrated_right = int(np.average([self.calibrated_right_decreasing,
                                                                            self.calibrated_right_increasing]))
                                    self.calibration_text_var.set(f"Calibration Left: {self.calibrated_left}"
                                                                  f"\tCalibration Right: {self.calibrated_right}")
                                    self.stop_button.config(text="Save", command=self.close_win)
                                return

    def stop_calibration_step(self):
        self.calibrating = False
        if self.calibration_step == 4:
            self.cal_button["state"] = 'disabled'
            self.stop_button["state"] = 'active'
        else:
            self.stop_button["state"] = 'disabled'
            self.cal_button["state"] = 'active'

    def close_win(self):
        if self.calibrated_left and self.calibrated_right:
            self.caller.calibrate_return(self.calibrated_left, self.calibrated_right)
        self.calibrating = False
        self.popup_root.destroy()


class GitHubIssue:
    def __init__(self, root, token, current_log_file):
        self.log_file = parse_log(current_log_file)
        self.token = token
        self.entry = None
        self.popup_root = None
        self.label_options = [
            'Bug',
            'Enhancement',
            'Documentation'
        ]
        self.name = "Submit Feedback to Developer"
        self.popup_entry(root)

    def popup_entry(self, root, field_font=('Purisa', 12)):
        # Create a Toplevel window
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("800x350")
        popup_root.title(self.name)

        self.title_var = tkinter.StringVar(popup_root, value='Feedback Title')
        self.title_entry = tkinter.Entry(popup_root, textvariable=self.title_var, font=field_font, bd=2, fg='grey')
        self.title_entry.bind("<FocusIn>", self.title_handle_focus_in)
        self.title_entry.bind("<FocusOut>", self.title_handle_focus_out)
        self.title_entry.place(x=10, y=10)

        self.label_var = tkinter.StringVar(popup_root, value='Select a Label')
        dropdown_box = Combobox(popup_root, textvariable=self.label_var, font=field_font)
        dropdown_box['values'] = self.label_options
        dropdown_box['state'] = 'readonly'
        dropdown_box.config(font=field_font)
        dropdown_box.option_add('*TCombobox*Listbox.font', field_font)
        dropdown_box.place(x=10, y=40)

        self.default_desc_text = "Enter a description of the problem you encountered.\n"\
                                 "Please be descriptive!\n"\
                                 "If possible, include steps to recreate the problem and contact "\
                                 "information if you would like the developer to reach out for more "\
                                 "information and updates."
        self.desc_var = tkinter.StringVar(popup_root)
        self.description_entry = tkinter.Text(popup_root, bg="white", fg='grey',
                                              cursor="arrow",
                                              exportselection=0,
                                              highlightcolor="black",
                                              width=10,
                                              xscrollcommand="scrollbar")
        self.description_entry.bind("<FocusIn>", self.handle_focus_in)
        self.description_entry.bind("<FocusOut>", self.handle_focus_out)
        self.description_entry.insert(INSERT, self.default_desc_text)
        self.description_entry.place(x=10, y=70, height=210, width=780)

        cancel_button = tkinter.Button(popup_root, text='Cancel', command=self.cancel, font=field_font)
        cancel_button.place(x=790, y=300, width=120, anchor=tkinter.NE)

        submit_button = tkinter.Button(popup_root, text='Submit', command=self.submit_issue, font=field_font)
        submit_button.place(x=660, y=300, width=120, anchor=tkinter.NE)

        center(popup_root)
        popup_root.focus_force()

    def title_handle_focus_in(self, _):
        title = self.title_var.get()
        if title == "Feedback Title":
            self.title_entry.delete(0, END)
            self.title_entry.config(fg='black')

    def title_handle_focus_out(self, _):
        title = self.title_var.get()
        if not title:
            self.title_entry.delete(0, END)
            self.title_entry.config(fg='grey')
            self.title_entry.insert(0, "Feedback Title")

    def handle_focus_in(self, _):
        desc = self.description_entry.get('1.0', END)
        if desc == self.default_desc_text + '\n':
            self.description_entry.delete('1.0', END)
            self.description_entry.config(fg='black')

    def handle_focus_out(self, _):
        desc = self.description_entry.get('1.0', END)
        if desc == '\n':
            self.description_entry.insert(INSERT, self.default_desc_text)
            self.description_entry.config(fg='grey')

    def cancel(self):
        self.popup_root.destroy()

    def submit_issue(self):
        desc = self.description_entry.get('1.0', END)
        if desc == '\n' or desc == self.default_desc_text + '\n':
            messagebox.showerror("Error", "Enter a description of the issue encountered!")
            return
        label_set = self.label_var.get()
        if label_set == "Select a Label":
            messagebox.showerror("Error", "Select a label for the issue encountered!")
            return
        title = self.title_var.get()
        if not title or title == 'Feedback Title':
            messagebox.showerror("Error", "Enter a title for the issue encountered!")
            return

        response = messagebox.askyesno("Submit?", "You are submitting a feedback ticket to the developer.\n"
                                                  "The feedback provided in the textbox will be posted to a public"
                                                  "repository.\n"
                                                  "Details of this feedback collection can be found in our Privacy Policy.\n"
                                                  "Continue?")
        if response:
            try:
                g = Github(self.token)
                repo = g.get_repo('Munroe-Meyer-Institute-VR-Laboratory/cometrics')

                repo.create_issue(
                    title=title,
                    body=desc,
                    labels=[
                        repo.get_label(label_set.lower())
                    ]
                )
                messagebox.showinfo("Success!", "Feedback has been submitted!")
            except Exception as e:
                messagebox.showerror("Error", f"An exception was encountered!\n{str(e)}")
                print(f"ERROR: An exception was encountered!\n{str(e)}")
        self.popup_root.destroy()
