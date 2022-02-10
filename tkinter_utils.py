import tkinter
from tkinter import TOP, W, N, NW, CENTER, messagebox
from tkinter.ttk import Style
from tkinter.ttk import Treeview

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


def get_treeview_style(name="mystyle.Treeview", font=('Calibri', 13), heading_font=('Calibri', 13, 'bold'),
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
        file_scroll.place(x=(x-fs_offset), y=y, height=height, anchor=anchor)
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
