import tkinter as tk
import cv2
import PIL.Image
import PIL.ImageTk
import time
import numpy as np
from threading import Thread
from queue import Queue
import csv
import os

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

        # managing behaviors
        self.behaviors = [('Behavior', 'Started', 'Ended')]
        self.behavior_types = []
        self.current_behavior = ""
        self.current_behavior_start = None
        self.behaviors_buttons = {}

        # Labels and fields for video URL
        self.video_entry = None
        self.csv_entry = None
        self.GUI()

        # creating canvas proper for a video size
        self.video_height = round(self.window_height*0.75)
        self.video_width = round(self.window_width*0.75)
        self.canvas = tk.Canvas(self.window,
                                width=self.video_width,
                                height=self.video_height,
                                relief='sunken')
        self.turtle_bg = PIL.Image.open("Turtle.jpg")
        self.turtle_bg = self.turtle_bg.resize((self.video_width, self.video_height), PIL.Image.ANTIALIAS)
        self.photo = PIL.ImageTk.PhotoImage(self.turtle_bg)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.canvas.place(x=self.window_width-self.video_width-5, y=0)

        # snapnote
        self.snap_canvas = None
        self.snap = None

        # opening the video
        self.video_source = None
        self.vid = None

        # Update & delay
        self.delay = 1
        self.update()

        self.window.mainloop()

    def GUI(self):
        x_indent = 15
        # video
        tk.Label(self.window, text="Enter a path to the video:", foreground="white", background="coral",
                font="none 12 bold", bd=2, relief="groove").place(x=x_indent, y=20)
        self.video_entry = tk.Entry(self.window, width=27, foreground="white", background="coral",
                font="none 12 bold", bd=2, relief="groove", disabledforeground="coral")
        self.video_entry.place(x=x_indent, y=50)

        # csv behaviors
        tk.Label(self.window, text="Enter a path to behaviors CSV:", foreground="white",
                 background="coral", font="none 12 bold", bd=2, relief="groove").place(x=x_indent, y=90)
        self.csv_entry = tk.Entry(self.window, width=27, foreground="white", background="coral",
                font="none 12 bold", bd=2, relief="groove", disabledforeground="coral")
        self.csv_entry.place(x=x_indent, y=120)

        # open
        tk.Button(self.window, text="OPEN", width=8, foreground="black", background="white",
                  font="none 14 bold", command=self.open_video).place(x=x_indent, y=150)

    def open_video(self):
        # departure point for the work with video;
        # starts video, reads csv with behavior, binds buttons and creates a folder for snapshots
        video_source = self.video_entry.get()
        csv_source = self.csv_entry.get()
        self.video_entry.config(state='disabled')
        self.csv_entry.config(state='disabled')
        try:
            with open(str(csv_source), 'r') as readFile:
                reader = csv.reader(readFile)
                dummy = list(reader)
            flatten = lambda l: [item for sublist in l for item in sublist]
            self.behavior_types = flatten(dummy)

            self.video_source = video_source
            self.vid = VideoCap(str(video_source)).start()

            # key-binds
            self.window.bind("<Escape>", self.quit)
            self.BBB()
            create_folder("BehaviorStarts")
        except:
            "Sorry, there must have been a mistake. Please, try again later"

    def update(self):

        if self.video_source != None:
            frame = self.vid.read()
            frame = resize(frame, width=self.video_width, height=self.video_height)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.canvas.itemconfig(item, tags="Video")

            with open('output.csv', 'w') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerows(self.behaviors)

            if not self.vid.more():
                self.quit(True)

        self.window.after(self.delay, self.update)

    def BBB(self):
        # Behavior-Button Binding
        buttons = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
                   "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

        for i, b in enumerate(self.behavior_types):
            self.behaviors_buttons[buttons[i]] = b
            self.window.bind(buttons[i], self.startBehavior, add="+")
            # self.window.bind(buttons[i], self.endBehavior, add="+")
            self.window.bind("<Control-" + buttons[i] + ">", self.endBehavior)

    # Snapshot method
    def startBehavior(self, event):

        frame = self.vid.read()
        time_start = ms2time(self.vid.timestamps[0])
        self.current_behavior = self.behaviors_buttons[event.keysym]

        if self.current_behavior_start is not  None:
            self.current_behavior_start += (time_start,)
            self.behaviors.append(self.current_behavior_start)
            self.current_behavior_start = None

        self.current_behavior_start = (self.current_behavior, time_start)
        cv2.imwrite("BehaviorStarts/" + self.current_behavior + " " + time_start + ".jpg", frame)

        # Lower left corner note that behavior is on
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = resize(frame, width=256, height=148)
        self.snap = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        tk.Label(self.window, text="Behavior started", foreground="white", background="coral",
                font="none 12 bold", bd=2, relief="groove", height=1).place(x=10, y=360)
        tk.Label(self.window, text=self.current_behavior, foreground="coral", background="white",
                font="none 12 bold italic", bd=2, relief="sunken", height=1, width=15).place(x=130, y=360)

        self.snap_canvas = tk.Canvas(self.window, width=256, height=148, relief='sunken')
        self.snap_canvas.create_image(3, 5, image=self.snap, anchor=tk.NW)
        self.snap_canvas.place(x=10, y=395)

    def endBehavior(self, event):
        # waiting for the second press

        time_end = ms2time(self.vid.timestamps[0])
        self.current_behavior_start += (time_end,)
        self.behaviors.append(self.current_behavior_start)


    def quit(self, whatever):
        # writing last behavior
        if self.current_behavior_start is not None:
            if len(self.current_behavior_start) != 3:
                time_start = ms2time(self.vid.timestamps[0])
                self.current_behavior_start += (time_start,)
                self.behaviors.append(self.current_behavior_start)
                with open('output.csv', 'w') as writeFile:
                    writer = csv.writer(writeFile)
                    writer.writerows(self.behaviors)

        if whatever:
            self.canvas.destroy()
            if self.vid is not None:
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
    return "{:.0f}:{:.0f}:{:.0f}:{:.0f}".format(h, m, s, ms*100)


def ms2time(input):
    s, ms = divmod(input, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    # "{:.0f}h_{:.0f}m_{:.0f}s_{:.0f}ms"
    return "{:.0f}:{:.0f}:{:.0f}:{:.0f}".format(h, m, s, ms)


def create_folder(folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print("System error. Could not create " + folder + ".")



# Create a window and pass it to the Application object
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/MountainTest.MOV"
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/TurtleMartinique.mov"
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/turtle2.avi"
# csv = /Users/thewaveorthemountain/Formation/S2/Project/behaviors_test.csv

App(tk.Tk(), window_title='TurtleCap')