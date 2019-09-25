import tkinter as tk
import sys
sys.path.append("GUI")
import gui_main_frame as gui_main_frame

import visualizer
from tkinter import ttk


class ModelFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

singleton = None


def create_singleton():
    global singleton
    singleton = ModelFrame()  # yet to be initialized
