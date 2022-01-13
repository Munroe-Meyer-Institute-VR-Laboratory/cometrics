from pynput import keyboard
from tkinter import *


def on_press(key):
    try:
        key_char = key.char
        focus = root.focus_get()
        if focus:
            print("Pressed key:", key_char)
    except AttributeError:
        key_glob = key
        focus = root.focus_get()
        if focus:
            print("Pressed key:", key_glob)


def on_release(key):
    print(key)


# ...or, in a non-blocking fashion:
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

root = Tk()
root.geometry("600x600")
root.title("Root")
root.mainloop()
