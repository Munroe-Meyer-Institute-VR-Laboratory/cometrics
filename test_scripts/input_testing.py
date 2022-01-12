from pynput import keyboard


def on_press(key):
    try:
        key_char = key.char
        print(str(key_char).lower())
    except AttributeError:
        key_glob = key
        print(key_glob)


def on_release(key):
    print(key)


with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
