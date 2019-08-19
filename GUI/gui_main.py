import tkinter as tk
import os
from GUI.main_frame import MainFrame
from GUI.frame_plot import PlotFrame
from GUI.navigation_bar import NavigationBar
from GUI.frame_model import ModelFrame
from GUI.frame_read import ReadFrame
import GUI.info_bar as info_bar
import GUI.navigation_bar as nav_bar
from manage_config import cfg


class GUImain(tk.Tk):
    """
    Main controller of the whole gui
    The scale is set there, the font-type and size as well, the geometry of the window not to
    All the main frames Start page, Dev page and Car page and stored in an dictionary and then tk.raised() via a
    function. This method is working pretty good and it is easy to add new frames.
    """
    def __init__(self):
        tk.Tk.__init__(self)

        # if os.name == 'posix':  # Portable Operating System Interface
        # # create_version_file(".")  # do only on linux - create a version number (from git)

        # so that if clicked outside of entry field focus is released! very important
        self.bind_all("<1>", lambda event: self.set_focus_on_widget(event))

        self.protocol("WM_DELETE_WINDOW", self.close_application)

        # self.geometry(str(1000) + "x" + str(1000) + "+" + "0" + "+0")
        self.minsize(1000, 700)

        self.title("CRAZY NAME")
        # TODO 0, 0,  check on two screens

        # self.state('iconic')  # TODO whats that

        # set favicon .. but only if not linux
        if os.name != 'posix':
            pass
            # self.wm_iconbitmap(cfg.favicon_path)

        # self.config(bg="lightgray")

        self.main_frame = MainFrame(self)
        self.main_frame.pack(side="bottom", fill="both", expand=True)

        # needs to be set, otherwise no weight at all
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.main_frames = {}

        for F in (ModelFrame, PlotFrame, ReadFrame):  # last item here is standard page to show
            frame = F(self.main_frame)
            self.main_frames[F] = frame

        nav_bar.singleton = nav_bar.NavigationBar(self)
        nav_bar.singleton.pack(side="top", fill="both")

        info_bar.singleton = info_bar.InfoBar(self)
        info_bar.singleton.pack(side="top", fill="both", padx=15, pady=10)

        info_bar.singleton["text"] = "Read in a file"

        # show frames
        for main_frame in self.main_frames.values():
            main_frame.grid(row=0, column=0, sticky="nsew")  # padx=20, pady=20

        # self.pack(fill="both", expand=True)

    def show_main_frame(self, cont):
        frame = self.main_frames[cont]
        frame.tkraise()

    def close_application(self):
        self.destroy()

    @staticmethod
    def set_focus_on_widget(event):
        try:
            # ask open filename for example has no attribute focus_set, cause its a string
            event.widget.focus_set()
        except AttributeError:
            pass

if not cfg["NO_GUI"]:
    singleton = GUImain()
