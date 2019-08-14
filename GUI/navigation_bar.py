import tkinter as tk
from GUI.frame_plot import PlotFrame
from GUI.frame_model import ModelFrame
from GUI.frame_read import ReadFrame


class NavigationBar(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.config(bg="yellow")
        self.grid_propagate(False)

        btn_plotframe = tk.Button(self, text="Read", command=lambda: parent.show_main_frame(ReadFrame))
        btn_plotframe.pack(side="left")

        btn_plotframe = tk.Button(self, text="Plot", command=lambda: parent.show_main_frame(PlotFrame))
        btn_plotframe.pack(side="left")

        btn_modelframe = tk.Button(self, text="Model", command=lambda: parent.show_main_frame(ModelFrame))
        btn_modelframe.pack(side="left")
