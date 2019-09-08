import tkinter as tk
import os


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

        self.title("Pasterze Energy Balance Calculator")

        # self.state('iconic')  # TODO whats that

        # set favicon .. but only if not linux
        if os.name != 'posix':
            pass
            # self.wm_iconbitmap(cfg.favicon_path)

        # self.config(bg="lightgray")

        self.frame = tk.Frame(self)
        self.frame.pack(side="bottom", fill="both", expand=True)

        # needs to be set, otherwise no weight at all
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

    @staticmethod
    def show_main_frame(singleton_file):
        singleton_file.singleton.tkraise()

    def close_application(self):
        self.destroy()

    @staticmethod
    def set_focus_on_widget(event):
        try:
            # ask open filename for example has no attribute focus_set, cause its a string
            event.widget.focus_set()
        except AttributeError:
            pass


singleton = None


def create_singleton():
    global singleton
    singleton = GUImain()
