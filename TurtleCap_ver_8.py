import tkinter as tk
import tkinter.ttk as ttk
import cv2
import PIL.Image
import PIL.ImageTk
import time
import numpy as np
import threading
from queue import Queue
import queue as queue
import csv
import os

# Class that creates the App Window


class App:
    def __init__(self, window, window_title):

        # initial window
        self.window = window
        self.window_width = 1400
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
        # last 10 behaviors table
        self.last_10_behaviors = []
        self.last_10_starts = []
        self.last_10_ends = []
        self.last_10_create()

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
        self.jump_entry = None
        self.error_window = None


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

        # "jump to" button
        tk.Label(self.window, text="Move to:", foreground="white", width=10, height=2,
                 background="#e8a502", font="none 12 bold", bd=2, relief="groove",
                 highlightthickness=0).place(x=self.window_width-(self.video_width/2)-260,
                                                            y=self.video_height+100)
        self.jump_entry = tk.Entry(self.window, width=24, foreground="white", background="#e8a502",
                                   font="none 12 bold", bd=2, relief="groove", disabledforeground="#e8a502",
                                   borderwidth=0, highlightthickness=0)
        self.jump_entry.place(x=self.window_width-(self.video_width/2)-118,
                                                            y=self.video_height+110)
        tk.Button(self.window, text="JUMP", width=8, foreground="black", background="white",
                  font="none 14 bold", command=self.jump).place(x=self.window_width-(self.video_width/2)+140,
                                                            y=self.video_height+107)
    def error_box(self, message):

        def close():
            self.error_window.destroy()

        self.error_window = tk.Toplevel()
        self.error_window.geometry('{:d}x{:d}+{:d}+{:d}'.format(256, 121,
                                                                self.window_width//2-128, self.window_height//2-60))
        self.error_window.title("Error!")
        self.error_window.configure(background="#e8a502")
        self.error_window.resizable(0, 0)

        text = tk.Text(self.error_window, background="#e8a502", height=4, font="none 14 bold", foreground="black",
                       borderwidth=0, wrap=tk.WORD, relief="flat", highlightthickness=0)
        text.tag_configure("center", justify='center')
        text.pack(fill=tk.BOTH)
        text.insert(tk.END, message)
        text.tag_add("center", "1.0", "end")
        text.config(state="disabled")

        tk.Button(self.error_window, text="Splendid!", width=8, foreground="black", background="white",
                  font="none 14 bold", command=close).pack(anchor=tk.S)

    def last_10_create(self):
        last_10_table = tk.Frame(self.window, background="#32515a", width=200, height=300)
        last_10_table.place(x=10, y=240)

        tk.Label(self.window, text="Last 10 registered behaviors", foreground="white", background="#e8a502",
                 font="none 16 bold", bd=2, relief="groove", height=1, width=22).place(x=30, y=200)

        for i in range(10):
            # behavior
            self.last_10_behaviors.append(tk.StringVar())
            self.last_10_behaviors[i].set("-")
            tk.Label(last_10_table, textvariable=self.last_10_behaviors[i],  foreground="#e8a502", background="white",
                font="none 12 bold italic", bd=2, relief="sunken", height=1, width=16).grid(row=i, column=0)
            # start
            self.last_10_starts.append(tk.StringVar())
            self.last_10_starts[i].set("-")
            tk.Label(last_10_table, textvariable=self.last_10_starts[i],  foreground="#e8a502", background="white",
                font="none 12 bold italic", bd=2, relief="sunken", height=1, width=8).grid(row=i, column=1)
            # end
            self.last_10_ends.append(tk.StringVar())
            self.last_10_ends[i].set("-")
            tk.Label(last_10_table, textvariable=self.last_10_ends[i],  foreground="#e8a502", background="white",
                font="none 12 bold italic", bd=2, relief="sunken", height=1, width=8).grid(row=i, column=2)

    def update_last_10(self):
        if len(self.behaviors) > 1:
            if len(self.behaviors) <= 11:
                for i in range(len(self.behaviors)-1):
                    self.last_10_behaviors[i].set(self.behaviors[i + 1][0])
                    self.last_10_starts[i].set(self.behaviors[i + 1][1])
                    self.last_10_ends[i].set(self.behaviors[i + 1][2])
                for i in range(len(self.behaviors), 10):
                    self.last_10_behaviors[i].set('-')
                    self.last_10_starts[i].set('-')
                    self.last_10_ends[i].set('-')
            else:
                for i in range(10):
                    self.last_10_behaviors[i].set(self.behaviors[i - 10][0])
                    self.last_10_starts[i].set(self.behaviors[i - 10][1])
                    self.last_10_ends[i].set(self.behaviors[i - 10][2])
        else:
            for i in range(10):
                self.last_10_behaviors[i].set('-')
                self.last_10_starts[i].set('-')
                self.last_10_ends[i].set('-')


    def jump(self):

        self.vid.pause()
        jump_to = self.current_timestamp_value
        try:
            jump_to = time2ms(self.jump_entry.get())
        except Exception:
            self.error_box("Given timestamp does not exist.\n "
                           "Please, follow the 'h:m:s:ms' format.")
        self.jump_entry.config(state='disabled')
        self.delay = 1000 * 60 * 60 * 24
        self.current_behavior_start = None

        # emptying the queue
        with self.vid.Q.mutex:
            self.vid.Q.queue.clear()
        self.vid.timestamps = np.empty(self.vid.Qsize)
        self.vid.position_in_Q = 0

        # changing current position in the video
        self.vid.vid.set(cv2.CAP_PROP_POS_MSEC, jump_to)

        self.vid.resume()
        time.sleep(0.4)
        self.delay = 1
        self.jump_entry.config(state='normal')
        self.window.focus_set()

    def flash_forward(self, event=None):
        if event:
            time.sleep(0.05)

        self.vid.pause()
        self.flash_forward_button.configure(state='disabled')
        self.delay = 1000*60*60*24

        # emptying the queue
        with self.vid.Q.mutex:
            self.vid.Q.queue.clear()
        self.vid.timestamps = np.empty(self.vid.Qsize)
        self.vid.position_in_Q = 0

        # changing current position in the video
        plus30sec = min(int(self.vid.vid.get(cv2.CAP_PROP_POS_FRAMES) + 10*self.vid.vid.get(cv2.CAP_PROP_FPS) -
                            self.vid.Qsize),
                        self.vid.length)
        self.vid.vid.set(cv2.CAP_PROP_POS_FRAMES, plus30sec)


        self.vid.resume()
        self.delay = 1
        time.sleep(0.4)
        self.flash_forward_button.configure(state='normal')

    def flash_backward(self, event=None):
        if event:
            time.sleep(0.05)

        self.vid.pause()
        self.flash_backward_button.configure(state='disabled')
        self.delay = 1000 * 60 * 60 * 24

        # emptying the queue
        with self.vid.Q.mutex:
            self.vid.Q.queue.clear()
        self.vid.timestamps = np.empty(self.vid.Qsize)
        self.vid.position_in_Q = 0

        # changing current position in the video
        minus30sec = max(1.0,
                         int(self.vid.vid.get(cv2.CAP_PROP_POS_FRAMES) - 5*self.vid.vid.get(cv2.CAP_PROP_FPS) -
                             self.vid.Qsize))
        self.vid.vid.set(cv2.CAP_PROP_POS_FRAMES, minus30sec)

        self.vid.resume()
        time.sleep(0.2)
        self.delay = 1

        # erasing unnecessary behaviors
        while len(self.behaviors) > 1:
            if (time2ms(self.behaviors[-1][2]) >= self.current_timestamp_value or
             time2ms(self.behaviors[-1][1]) >= self.current_timestamp_value):
                self.behaviors.pop()
            else:
                break
        self.current_behavior_start = None
        time.sleep(0.2)
        self.flash_backward_button.configure(state='normal')

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

            # key-binds
            self.window.bind("<Escape>", self.quit)
            self.window.bind("<space>", self.play_and_stop)
            self.window.bind("<Left>", self.flash_backward)
            self.window.bind("<Right>", self.flash_forward)
            self.BBB()
            create_folder("BehaviorStarts")
            self.total_time.set(seconds2time(self.vid.length/self.vid.vid.get(cv2.CAP_PROP_FPS)))
        except Exception:
            self.error_box("Sorry, there must have been a mistake. Please, check if the path is correct.")
            self.video_entry.config(state='normal')
            self.csv_entry.config(state='normal')

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
            self.update_last_10()

            with open('output.csv', 'w') as writeFile:
                writer = csv.writer(writeFile)
                writer.writerows(self.behaviors)

            if not self.vid.more():
                self.quit(True)

        self.window.after(self.delay, self.update)

    def BBB(self):

        # Creating separate window to show the dictionary
        self.behaviors_window = tk.Toplevel()
        self.behaviors_window.geometry('{:d}x{:d}+{:d}+{:d}'.format(250, self.window_height,
                                                                    self.window_width-250, 20))
        self.behaviors_window.title("Behaviors dictionary")
        self.behaviors_window.configure(background="#32515a")
        self.behaviors_window.resizable(0, 0)

        # Table interface
        ttk.Style().configure('.',
                              relief='flat',
                              borderwidth=1
                              )
        table = ttk.Treeview(self.behaviors_window, selectmode='browse')
        table.pack(side="left")
        table["columns"] = ("1", "2")
        table.column("1", width=200)
        table.column("2", width=40)
        table.heading("1", text="Behavior")
        table.heading("2", text="Button")
        table['show'] = 'headings'

        scrollbar = ttk.Scrollbar(self.behaviors_window, orient="vertical", command=table.yview)
        scrollbar.pack(side='right', fill='y')
        table.configure(yscrollcommand=scrollbar.set)

        # Behavior-Button Binding
        for i, pair in enumerate(self.behavior_types):
            self.behaviors_buttons[pair[1]] = pair[0]
            self.window.bind(pair[1], self.startBehavior, add="+")
            table.insert("", 'end', text="L1", values=(pair[0], pair[1]))

        table.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=table.yview)


    # Snapshot method
    def startBehavior(self, event):

        frame = self.vid.read()
        time_start = ms2time(self.current_timestamp_value)
        self.current_behavior = self.behaviors_buttons[event.keysym]

        # ending previous behavior
        if self.current_behavior_start is not None:
            self.current_behavior_start += (time_start,)
            self.behaviors.append(self.current_behavior_start)
            self.current_behavior_start = None

        # double-check - erasing unnecessary behaviors
        while len(self.behaviors) > 1:
            if time2ms(self.behaviors[-1][1]) >= self.current_timestamp_value:
                self.behaviors.pop()
            else:
                break

        # fixing behavior that started in the past and ended in the future
        # as a result of flashing backwards
        if self.behaviors[-1][2] != time_start and len(self.behaviors) > 1:
            self.behaviors[-1] = (self.behaviors[-1][0], self.behaviors[-1][1], time_start)

        self.current_behavior_start = (self.current_behavior, time_start)
        cv2.imwrite("BehaviorStarts/" + self.current_behavior + " " + time_start + ".jpg", frame)

        # Lower left corner note that behavior is on
        SnapNote = tk.Frame(self.window, background="#32515a", width=280, height=200)
        SnapNote.place(x=20, y=500)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = resize(frame, width=256, height=148)
        self.snap = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))

        tk.Label(SnapNote, text="Behavior started", foreground="white", background="#e8a502",
                font="none 12 bold", bd=2, relief="groove", height=1).place(x=0, y=0)
        tk.Label(SnapNote, text=self.current_behavior, foreground="#e8a502", background="white",
                font="none 12 bold italic", bd=2, relief="sunken", height=1, width=15).place(x=120, y=0)

        self.snap_canvas = tk.Canvas(SnapNote, width=256, height=148, relief='sunken')
        self.snap_canvas.create_image(3, 5, image=self.snap, anchor=tk.NW)
        self.snap_canvas.place(x=0, y=35)

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

        # Getting video's width and height
        self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Bufferization
        self.Q = Queue(maxsize=qsize)
        self.thread = threading.Thread(target=self.get_frame, args=())
        self.thread.daemon = True
        self.timestamps = np.empty(qsize)
        self.position_in_Q = 0
        self.state = threading.Condition()

        # video length
        self.length = int(self.vid.get(cv2.CAP_PROP_FRAME_COUNT))


    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        while self.vid.isOpened():
            if self.stopped:
                break

            with self.state:
                if self.OnHold:
                    self.position_in_Q = 0
                    self.state.wait()

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

                self.Q.put(frame)

            else:
                time.sleep(0.1)

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

    def resume(self):
        # resuming a thread
        with self.state:
            self.OnHold = False
            self.state.notify()

    def pause(self):
        # blocking a thread
        with self.state:
            self.OnHold = True

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


# Create a window and pass it to the Application object
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/MountainTest.MOV"
# video_source="/Users/thewaveorthemountain/Formation/S2/Project/TurtleMartinique.mov"
# video_source= /Users/thewaveorthemountain/Formation/S2/Project/Turtles/turtle2.avi
# video_source= /Users/thewaveorthemountain/Formation/S2/Project/Turtles/turtle_2019_005.avi

# csv = /Users/thewaveorthemountain/Formation/S2/Project/Turtles/behaviors_new.csv
# csv = /Users/thewaveorthemountain/Formation/S2/Project/Turtles/behaviors.csv

error_message = ''

try:
    App(tk.Tk(), window_title='TurtleCap')
except Exception as e:
    error_message = e

with open('errors_log.txt', 'a') as writeFile:
    writeFile.write(error_message)