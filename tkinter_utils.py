import tkinter
from tkinter import TOP, W, N, NW, CENTER, messagebox, END, ttk
from tkinter.ttk import Style, Combobox
from tkinter.ttk import Treeview, Entry

from ui_params import treeview_default_tag_dict


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
                   filescroll=True, button_1_bind=None, double_bind=None, style="mystyle.Treeview", anchor=NW,
                   tag_dict=treeview_default_tag_dict, fs_offset=18):
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


class ConfigPopup:
    def __init__(self, root, config):
        self.config = config
        self.popup_root = popup_root = tkinter.Toplevel(root)
        popup_root.config(bg="white", bd=-2)
        popup_root.geometry("300x250")
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
        clear_projects = tkinter.Button(popup_root, text="Clear Recent Projects",
                                        font=('Purisa', 12), command=self.clear_projects)
        clear_projects.place(x=10, y=170)
        ok_button = tkinter.Button(popup_root, text="OK", command=self.on_closing, font=('Purisa', 12))
        ok_button.place(x=150, y=210, anchor=N)

    def on_closing(self):
        self.update_fps()
        self.update_e4()
        self.update_woodway()
        self.update_ble()
        self.popup_root.destroy()

    def update_fps(self):
        self.config.set_fps(int(self.fps_entry.get()))

    def update_e4(self):
        self.config.set_e4(self.e4_var.get())

    def update_ble(self):
        self.config.set_ble(self.ble_var.get())

    def update_woodway(self):
        self.config.set_woodway(self.woodway_var.get())

    def clear_projects(self):
        self.config.set_recent_projects([])


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
        self.caller.popup_return(self.entry.get(), self.popup_call)
        self.popup_root.destroy()


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
