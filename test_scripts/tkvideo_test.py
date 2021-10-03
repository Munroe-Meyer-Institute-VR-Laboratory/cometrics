from tkinter import *
from tkvideo import tkvideo
from tkinter import filedialog, messagebox
import random


def play_video():
    frames = [20, 50, 110, 440, 230]
    player.play(random.choice(frames))


frame_number = 0
# create instance of window
root = Tk()
# set window title
root.title('Video Player')
# create label
button = Button(root, text="Play Video", command=play_video)
button.pack()
video_label = Label(root)
video_label.pack()
video_path = filedialog.askopenfilename()
if video_path:
    # read video to display on label
    player = tkvideo(video_path, video_label,
                     loop=False, size=(700, 500))
else:
    messagebox.showwarning("Select Video File", "Please retry and select a video file.")
root.mainloop()