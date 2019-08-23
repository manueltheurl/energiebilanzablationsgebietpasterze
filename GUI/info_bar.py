import tkinter as tk
import GUI.gui_main_frame as gui_main_frame


class InfoBar(tk.Label):
    """
    TODO
    """
    singleton_created = False

    def __init__(self):
        if InfoBar.singleton_created:
            raise Exception("InfoBar is a singleton")
        InfoBar.singleton_created = True

        tk.Label.__init__(self, gui_main_frame.singleton, anchor="w")

        self.pack(side="top", fill="both", padx=15, pady=10)

        self["text"] = "Read in a file"


singleton = None


def create_singleton():
    global singleton
    singleton = InfoBar()
