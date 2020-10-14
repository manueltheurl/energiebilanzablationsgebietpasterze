import tkinter as tk
import sys
sys.path.append("GUI")

import gui_main_frame
import navigation_bar
from measurement_handler import MeasurementHandler
from config_handler import cfg


class ConversionFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.heading_sum = tk.Label(self, text="Conversion of measured and modeled melt rate to water equivalent", font=cfg["HEADING_FONT"])
        self.heading_sum.pack(pady=(25, 30))

        self.btn_convert = tk.Button(self, text="Convert", command=self.convert)
        self.btn_convert.pack(pady=40)

        self.btn_sumSkip = tk.Button(self, text="Skip",
                                     command=navigation_bar.singleton.show_plot_frame)
        self.btn_sumSkip.pack(pady=30)

    def convert(self):
        MeasurementHandler.convert_measured_and_modeled_rel_ablations_in_water_equivalents_for_mean_measures()
        navigation_bar.singleton.show_plot_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = ConversionFrame()  # yet to be initialized
