import tkinter as tk
import cv2
import PIL.Image
import PIL.ImageTk
import time
import numpy as np
from tkinter import ttk
from threading import Thread
from queue import Queue

# Class that creates the App Window


class App:
    def __init__(self, window, window_title):

        # initial window
        self.window = window
        self.window_width = 1280
        self.window_height = 720
        self.window.geometry('{:d}x{:d}'.format(self.window_width, self.window_height))
        self.window.title(window_title)
        self.window.configure(background="teal")
        self.window.resizable(0, 0)

        # Labels and fields for video URL
        tk.Label(self.window, text="Enter a path to the video:", foreground="white", background="coral",
                  font="none 12 bold", bd=2, relief="groove").place(x=20, y=20)
        self.video_entry = tk.Entry(window, width=27, foreground="white", background="coral",
                  font="none 12 bold", bd=2, relief="groove")
        self.video_entry.place(x=20, y=50)
        tk.Button(self.window, text="OPEN", width=8, foreground="black", background="white",
                  font="none 14 bold", command=self.open_video).place(x=20, y=80)

        # key-binds
        self.window.bind("s", self.snapshot)
        self.window.bind("q", self.quit)

        # creating canvas proper for a video size
        self.video_height = round(self.window_height*0.75)
        self.video_width = round(self.window_width*0.75)
        self.canvas = tk.Canvas(window,
                                width=self.video_width,
                                height=self.video_height,
                                relief='sunken')
        self.turtle_bg = PIL.Image.open("Turtle.jpg")
        self.turtle_bg = self.turtle_bg.resize((self.video_width, self.video_height), PIL.Image.ANTIALIAS)
        self.photo = PIL.ImageTk.PhotoImage(self.turtle_bg)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.canvas.place(x=self.window_width-self.video_width-5, y=0)

        # opening the video
        self.video_source = None
        self.vid = None
        # while True:
        #     if self.video_source != None:
        #         break
        # Update & delay
        self.delay = 1
        self.update()

        self.window.mainloop()


    def open_video(self):
        video_source = self.video_entry.get()
        try:
            self.video_source = video_source
            self.vid = VideoCap(str(video_source)).start()
        except:
            "Sorry, there must have been a mistake. Please, try again later"

    def update(self):

        if self.video_source != None:
            frame = self.vid.read()
            frame = resize(frame, width=self.video_width, height=self.video_height)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

            if not self.vid.more():
                self.quit(True)

        self.window.after(self.delay, self.update)

    # Snapshot method
    def snapshot(self, whatever):
        # \whatever\ - never used, somehow needed...
        frame = self.vid.read()
        time3 = ms2time(self.vid.timestamps[0])
        cv2.imwrite("Frame-" + time3 + ".jpg", frame)

    def quit(self, whatever):
        if whatever:
            self.canvas.destroy()
            self.vid.stop()
            self.window.quit()


# Class that captures a video
class VideoCap:

    def __init__(self, video_source=0, qsize=128):
        # Opening the video
        self.vid = cv2.VideoCapture(video_source)

        if not self.vid.isOpened():
            raise ValueError("Unable to open the video", video_source)

        self.stopped = False

        # Getting video's width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Bufferization
        self.Q = Queue(maxsize=qsize)
        self.thread = Thread(target=self.get_frame, args=())
        self.thread.daemon = True
        self.timestamps = np.empty(qsize)
        self.position_in_Q = 0

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        while self.vid.isOpened():
            if self.stopped:
                break

            if not self.Q.full():
                grabbed, frame = self.vid.read()
                if self.position_in_Q < len(self.timestamps):
                    self.timestamps[self.position_in_Q] = self.vid.get(cv2.CAP_PROP_POS_MSEC)
                    self.position_in_Q += 1
                else:
                    self.timestamps[:-1] = self.timestamps[1:]
                    self.timestamps[-1] = self.vid.get(cv2.CAP_PROP_POS_MSEC)

                if not grabbed:
                    self.stop()
                    break

                # cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.Q.put(frame)

            else:
                time.sleep(0.05)

        # Releasing the video source when the object is destroyed
        self.vid.release()

    def start(self):
        # start a thread to read frames from the file video stream
        self.thread.start()
        return self

    def read(self):
        # return next frame in the queue
        return self.Q.get()

    def more(self):
        # return True if there are still frames in the queue. If stream is not stopped, try to wait a moment
        tries = 0
        while self.Q.qsize() == 0 and not self.stopped and tries < 5:
            time.sleep(0.05)
            tries += 1

        return self.Q.qsize() > 0

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True


def resize(image, width=None, height=None, inter=cv2.INTER_AREA):
    # initialize the dimensions of the image to be resized and grab the image size
    (h, w) = image.shape[:2]

    # if both the width and height are None, then return the original image
    if width is None and height is None:
        return image

    # check to see if the width is None
    if width is None:
        # calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)

    # otherwise, the height may be None or not - does not matter
    else:
        # calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # resize the image
    resized = cv2.resize(image, dim, interpolation=inter)

    return resized


def seconds2time(input):
    m, s = divmod(input, 60)
    s, ms = divmod(s, 1)
    h, m = divmod(m, 60)
    return "{:.0f}h_{:.0f}m_{:.0f}s_{:.0f}ms".format(h, m, s, ms*100)


def ms2time(input):
    s, ms = divmod(input, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return "{:.0f}h_{:.0f}m_{:.0f}s_{:.0f}ms".format(h, m, s, ms)


def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])


# Create a window and pass it to the Application object
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/MountainTest.MOV"

App(tk.Tk(), window_title='MountainTest')