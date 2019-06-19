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
        self.window.configure(background="#32515a")
        self.window.resizable(0, 0)

        # managing behaviors
        self.behaviors = [('Behavior', 'Started', 'Ended')]
        self.behavior_types = []
        self.current_behavior = ""
        self.current_behavior_start = None
        self.behaviors_buttons = {}
        self.behaviors_window = None

        # creating canvas proper for a video size
        self.video_height = round(self.window_height*0.75)
        self.video_width = round(self.window_width*0.75)
        self.canvas = tk.Canvas(self.window,
                                width=self.video_width,
                                height=self.video_height,
                                relief='sunken', borderwidth=1, highlightthickness=1)
        self.turtle_bg = PIL.Image.open("Turtle.jpg")
        self.turtle_bg = self.turtle_bg.resize((self.video_width, self.video_height), PIL.Image.ANTIALIAS)
        self.photo = PIL.ImageTk.PhotoImage(self.turtle_bg)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.canvas.place(x=self.window_width-self.video_width-5, y=0)

        # Labels and fields for video URL
        self.video_entry = None
        self.csv_entry = None
        self.play_stop_button = None
        self.flash_forward_button = None
        self.flash_backward_button = None
        self.play_img = None
        self.stop_img = None
        self.flash_forward_img = None
        self.flash_backward_img = None
        # time labels
        self.current_timestamp = tk.StringVar()
        self.current_timestamp_value = 0
        self.total_time = tk.StringVar()
        self.GUI()

        # snapnote
        self.snap_canvas = None
        self.snap = None

        # opening the video
        self.video_source = None
        self.vid = None

        # Update & delay
        self.delay = 1
        self.playing = 0
        self.update()

        self.window.mainloop()

    def GUI(self):
        x_indent = 15
        # video
        tk.Label(self.window, text="Enter a path to the video:", foreground="white", background="#e8a502",
                font="none 12 bold", bd=2, relief="groove", borderwidth=0, highlightthickness=0).place(x=x_indent, y=20)
        self.video_entry = tk.Entry(self.window, width=27, foreground="white", background="#e8a502",
                font="none 12 bold", bd=2, relief="groove", disabledforeground="#e8a502",
                                    borderwidth=0, highlightthickness=0)
        self.video_entry.place(x=x_indent, y=50)

        # csv behaviors
        tk.Label(self.window, text="Enter a path to behaviors CSV:", foreground="white",
                 background="#e8a502", font="none 12 bold", bd=2, relief="groove",
                 borderwidth=0, highlightthickness=0).place(x=x_indent, y=90)
        self.csv_entry = tk.Entry(self.window, width=27, foreground="white", background="#e8a502",
                font="none 12 bold", bd=2, relief="groove", disabledforeground="#e8a502",
                                  borderwidth=0, highlightthickness=0)
        self.csv_entry.place(x=x_indent, y=120)

        # open
        tk.Button(self.window, text="OPEN", width=8, foreground="black", background="white",
                  font="none 14 bold", command=self.open_video).place(x=x_indent, y=150)

        # current time and total time labels
        tk.Label(self.window, textvariable=self.current_timestamp, foreground="white",
                 background="#e8a502", font="none 12 bold", bd=2, height=2, width=20,
                 relief="groove").place(x=self.window_width-(self.video_width/2)-340, y=self.video_height+40)
        self.current_timestamp.set("Current timestamp")
        tk.Label(self.window, textvariable=self.total_time, foreground="white",
                 background="#e8a502", font="none 12 bold", bd=2, height=2, width=20,
                 relief="groove").place(x=self.window_width-(self.video_width/2)+140, y=self.video_height+40)
        self.total_time.set("Total time")

        # play/stop button
        im_play = PIL.Image.open("turtle_play.png")
        im_play = im_play.resize((50, 50), PIL.Image.ANTIALIAS)
        self.play_img = PIL.ImageTk.PhotoImage(im_play)
        im_play = PIL.Image.open("turtle_stop.png")
        im_play = im_play.resize((50, 50), PIL.Image.ANTIALIAS)
        self.stop_img = PIL.ImageTk.PhotoImage(im_play)

        self.play_stop_button = tk.Button(self.window, image=self.play_img, command=self.play_and_stop,
                                   relief="groove", state='disabled', borderwidth=0, highlightthickness=0)
        self.play_stop_button.place(x=self.window_width-(self.video_width/2)-35, y=self.video_height+30)

        # flash forward & backward button
        im_play = PIL.Image.open("turtle_right.png")
        im_play = im_play.resize((50, 50), PIL.Image.ANTIALIAS)
        self.flash_forward_img = PIL.ImageTk.PhotoImage(im_play)
        self.flash_forward_button = tk.Button(self.window, image=self.flash_forward_img, command=self.flash_forward,
                                   relief="groove", state='disabled', borderwidth=0, highlightthickness=0)
        self.flash_forward_button.place(x=self.window_width-(self.video_width/2)+50, y=self.video_height+30)

        im_play = PIL.Image.open("turtle_left.png")
        im_play = im_play.resize((50, 50), PIL.Image.ANTIALIAS)
        self.flash_backward_img = PIL.ImageTk.PhotoImage(im_play)
        self.flash_backward_button = tk.Button(self.window, image=self.flash_backward_img, command=self.flash_backward,
                                   relief="groove", state='disabled', borderwidth=0, highlightthickness=0)
        self.flash_backward_button.place(x=self.window_width-(self.video_width/2)-120, y=self.video_height+30)

    def flash_forward(self, event=None):
        if event:
            time.sleep(0.05)

        self.vid.OnHold = True

        self.flash_forward_button.configure(state='disabled')
        self.delay = 1000*60*60*24
        plus30sec = min(round(self.vid.vid.get(cv2.CAP_PROP_POS_FRAMES) + 5.0*self.vid.vid.get(cv2.CAP_PROP_FPS)),
                        self.vid.length)
        self.vid.vid.set(cv2.CAP_PROP_POS_FRAMES, plus30sec)
        # emptying the queue
        for i in range(int(self.vid.Q.qsize())):
            self.vid.read()
        self.vid.position_in_Q = 0
        self.vid.timestamps = np.empty(self.vid.Qsize)

        self.vid.OnHold = False
        self.delay = 1
        time.sleep(0.3)
        self.flash_forward_button.configure(state='normal')
        print("VIDEO IS ON:", ms2time(self.current_timestamp_value))

    def flash_backward(self, event=None):
        if event:
            time.sleep(0.05)

        self.vid.OnHold = True
        # changing current position in the video
        self.flash_backward_button.configure(state='disabled')
        self.delay = 1000*60*60*24
        minus30sec = max(1.0,
                         round(self.vid.vid.get(cv2.CAP_PROP_POS_FRAMES) - 10.0*self.vid.vid.get(cv2.CAP_PROP_FPS)))
        self.vid.vid.set(cv2.CAP_PROP_POS_FRAMES, minus30sec)
        # emptying the queue
        for i in range(int(self.vid.Q.qsize())):
            self.vid.read()
        self.vid.timestamps = np.empty(self.vid.Qsize)
        self.vid.position_in_Q = 0

        # taking care of behavior that possibly started in the future;
        # the last behavior that was tracked before current timestamp is prolongated

        # if self.behaviors[-1][0] != 'Behavior':
        #     self.current_behavior = self.behaviors[-1][0]
        #     time_start = ms2time(self.current_timestamp_value)
        #     self.current_behavior_start = (self.current_behavior, time_start)

        self.vid.OnHold = False
        self.delay = 1
        time.sleep(0.3)
        self.flash_backward_button.configure(state='normal')
        # erasing unnecessary behaviors
        while len(self.behaviors) > 1:
            if (time2ms(self.behaviors[-1][2]) >= self.current_timestamp_value or
             time2ms(self.behaviors[-1][1]) >= self.current_timestamp_value):
                self.behaviors.pop()
            else:
                break
        self.current_behavior_start = None
        print("VIDEO IS ON:", ms2time(self.current_timestamp_value))


    def play_and_stop(self, event=None):
        if event:
            time.sleep(0.05)

        time.sleep(0.1)
        if self.playing:
            self.playing = 0
            self.play_stop_button.configure(image=self.play_img)
            frame = self.vid.read()
            frame = resize(frame, width=self.video_width, height=self.video_height)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.delay = 1000*60*60*24
            self.window.after(self.delay, self.update)

        else:
            self.playing = 1
            self.play_stop_button.configure(image=self.stop_img)
            self.delay = 1
            self.window.after(self.delay, self.update)


    def open_video(self):
        # departure point for the work with video;
        # starts video, reads csv with behaviors, binds buttons and creates a folder for snapshots
        video_source = self.video_entry.get()
        csv_source = self.csv_entry.get()

        # enabling and disabling buttons, entries
        self.video_entry.config(state='disabled')
        self.csv_entry.config(state='disabled')
        self.play_stop_button.configure(state='normal')
        self.flash_forward_button.configure(state='normal')
        self.flash_backward_button.configure(state='normal')
        self.play_stop_button.configure(image=self.stop_img)

        try:
            with open(str(csv_source), 'r') as readFile:
                reader = csv.reader(readFile)
                dummy = list(reader)
            self.behavior_types = dummy
            print(self.behavior_types)

            self.video_source = video_source
            self.vid = VideoCap(str(video_source)).start()
            self.playing = 1
            print("CODEC-CODEC: ", decode_fourcc(self.vid.vid.get(cv2.CAP_PROP_FOURCC)))

            # key-binds
            self.window.bind("<Escape>", self.quit)
            self.window.bind("<space>", self.play_and_stop)
            self.window.bind("<Left>", self.flash_backward)
            self.window.bind("<Right>", self.flash_forward)
            self.BBB()
            create_folder("BehaviorStarts")
            self.total_time.set(seconds2time(self.vid.length/self.vid.vid.get(cv2.CAP_PROP_FPS)))
        except:
            "Sorry, there must have been a mistake. Please, try again later"

    def update(self):

        if self.video_source is not None:
            while self.vid.OnHold:
                continue

            frame = self.vid.read()
            frame = resize(frame, width=self.video_width, height=self.video_height)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            item = self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            self.canvas.itemconfig(item, tags="Video")
            self.current_timestamp.set(ms2time(self.vid.timestamps[0]))
            self.current_timestamp_value = time2ms(self.current_timestamp.get())

            with open('output.csv', 'w') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerows(self.behaviors)

            if not self.vid.more():
                self.quit(True)

        self.window.after(self.delay, self.update)

    def BBB(self):

        # Creating separate window to show the dictionary
        self.behaviors_window = tk.Toplevel()
        self.behaviors_window.geometry('{:d}x{:d}'.format(200, self.window_height))
        self.behaviors_window.title("Behaviors dictionary")
        self.behaviors_window.configure(background="#32515a")
        self.behaviors_window.resizable(0, 0)
        scrollbar = tk.Scrollbar(self.behaviors_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        aux_list = tk.Listbox(self.behaviors_window, yscrollcommand=scrollbar.set,
                              foreground="white", background="#e8a502",
                              font="none 12 bold", bd=2, relief="groove"
                              )

        # Behavior-Button Binding
        for i, pair in enumerate(self.behavior_types):
            print("Pair is ", pair)
            print("Behavior is ", pair[0])
            print("Button is ", pair[1])
            self.behaviors_buttons[pair[1]] = pair[0]
            self.window.bind(pair[1], self.startBehavior, add="+")
            aux_list.insert(tk.END, pair[0] + " - " + pair[1])

        aux_list.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=aux_list.yview)

        self.window.bind("<Control-s>", self.check)
        self.window.bind("<Shift-f>", self.check)


    # Snapshot method
    def startBehavior(self, event):

        frame = self.vid.read()
        time_start = ms2time(self.vid.timestamps[0])
        self.current_behavior = self.behaviors_buttons[event.keysym]

        if self.current_behavior_start is not None:
            self.current_behavior_start += (time_start,)
            self.behaviors.append(self.current_behavior_start)
            self.current_behavior_start = None

        self.current_behavior_start = (self.current_behavior, time_start)
        cv2.imwrite("BehaviorStarts/" + self.current_behavior + " " + time_start + ".jpg", frame)

        # Lower left corner note that behavior is on
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = resize(frame, width=256, height=148)
        self.snap = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        tk.Label(self.window, text="Behavior started", foreground="white", background="#e8a502",
                font="none 12 bold", bd=2, relief="groove", height=1).place(x=10, y=360)
        tk.Label(self.window, text=self.current_behavior, foreground="#e8a502", background="white",
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
                # Releasing the video source when the object is destroyed
                self.vid.__del__()
            self.window.quit()


# Class that captures a video
class VideoCap:

    def __init__(self, video_source=0, qsize=512):
        # Opening the video
        self.vid = cv2.VideoCapture(video_source)

        if not self.vid.isOpened():
            raise ValueError("Unable to open the video", video_source)

        self.stopped = False
        self.OnHold = False
        self.Qsize = qsize
        # callback variable; needed when moving forward or backwards in the video
        self.CallBack = 0

        # Getting video's width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Bufferization
        self.Q = Queue(maxsize=qsize)
        self.thread = Thread(target=self.get_frame, args=())
        self.thread.daemon = True
        self.timestamps = np.empty(qsize)
        self.position_in_Q = 0

        # video length & trackbar
        self.length = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))


    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        while self.vid.isOpened():
            self.CallBack = 0
            if self.stopped:
                break

            while self.OnHold:
                pass

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
                time.sleep(0.1)
            self.CallBack = 1

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

def time2ms(input):
    h,m,s,ms = input.split(":")
    result = int(ms) + int(s)*1000 + int(m)*1000*60 + int(h)*1000*60*60
    return result


def create_folder(folder):
    try:
        if not os.path.exists(folder):
            os.makedirs(folder)
    except OSError:
        print("System error. Could not create " + folder + ".")

def decode_fourcc(cc):
    return "".join([chr((int(cc) >> 8 * i) & 0xFF) for i in range(4)])


# Create a window and pass it to the Application object
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/MountainTest.MOV"
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/TurtleMartinique.mov"
# video_source= /Users/thewaveorthemountain/Formation/S2/Project/Turtles/turtle2.avi
# csv = /Users/thewaveorthemountain/Formation/S2/Project/Turtles/behaviors_new.csv
# csv = /Users/thewaveorthemountain/Formation/S2/Project/Turtles/behaviors.csv

App(tk.Tk(), window_title='TurtleCap')