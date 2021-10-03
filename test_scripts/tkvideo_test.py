from tkinter import *
from tkvideo import tkvideo
import time
import random
playing = False


def play_video():
    frames = [20, 50, 110, 440, 230]
    player.play(random.choice(frames))


frame_number = 0
# create instance fo window
root = Tk()
# set window title
root.title('Video Player')
# create label
button = Button(root, text="Play Video", command=play_video)
button.pack()
video_label = Label(root)
video_label.pack()
# read video to display on label
player = tkvideo(r"C:\Users\wsarc\Videos\test.mp4", video_label,
                 loop = 1, size = (700, 500))
root.mainloop()