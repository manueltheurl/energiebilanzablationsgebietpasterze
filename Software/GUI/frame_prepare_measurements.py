import tkinter as tk
from tkinter import filedialog
import sys
sys.path.append("GUI")
from reader import Reader
from measurement_handler import MeasurementHandler
from tkinter import ttk
import datetime as dt
import info_bar as info_bar
import gui_main_frame as gui_main_frame
import frame_plot as frame_plot
import misc as fc
import navigation_bar as navigation_bar
import frame_energy_balance as frame_energy_balance
from config_handler import cfg


class PrepareMeasurementsFrame(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.grid_propagate(False)

        self.file_path = None

        self.heading_prepare = tk.Label(self, text="Prepare and modify measurements", font=cfg["HEADING_FONT"])
        self.heading_prepare.pack(pady=(25, 0))

        self.ckbox_correctSnowMeasures_value = tk.IntVar(value=1)
        self.ckbox_correctSnowMeasures = tk.Checkbutton(self, variable=self.ckbox_correctSnowMeasures_value)
        self.ckbox_correctSnowMeasures.pack(pady=(25, 0))
        self.lbl_correctSnowMeasures = tk.Label(self, text="Correct snow measurements")
        self.lbl_correctSnowMeasures.pack()

        self.ckbox_correctSW_value = tk.IntVar(value=1)
        self.ckbox_correctSW = tk.Checkbutton(self, variable=self.ckbox_correctSW_value)
        self.ckbox_correctSW.pack(pady=(25, 0))
        self.lbl_correctSW = tk.Label(self, text="Correct short wave measurements")
        self.lbl_correctSW.pack()

        self.ckbox_correctLW_value = tk.IntVar()
        self.ckbox_correctLW = tk.Checkbutton(self, variable=self.ckbox_correctLW_value)
        self.ckbox_correctLW.pack(pady=(25, 0))
        self.lbl_correctLW = tk.Label(self, text="Correct long wave measurements")
        self.lbl_correctLW.pack()

        self.ckbox_correctAblation_value = tk.IntVar(value=1)
        self.ckbox_correctAblation = tk.Checkbutton(self, variable=self.ckbox_correctAblation_value)
        self.ckbox_correctAblation.pack(pady=(25, 0))
        self.lbl_correctAblation = tk.Label(self, text="Method 'same level positive fix' for cumulating ablation")
        self.lbl_correctAblation.pack()

        self.lbl_infoCumulateAblation = tk.Label(self, text="Cumulating ablation")
        self.lbl_infoCumulateAblation.pack(pady=(40, 0))

        self.lbl_infoSnowHeightDeltaCalculation = tk.Label(self, text="Calculating snow height deltas")
        self.lbl_infoSnowHeightDeltaCalculation.pack(pady=(15, 0))

        self.btn_readFilesToObjects = tk.Button(self,
                                                text="Prepare measurements",
                                                command=self.combined_preparing_of_measurements)
        self.btn_readFilesToObjects.pack(pady=30)

    def combined_preparing_of_measurements(self):
        if self.ckbox_correctSnowMeasures_value.get():
            MeasurementHandler.correct_snow_measurements_for_single_measures()
        if self.ckbox_correctLW_value.get():
            MeasurementHandler.correct_long_wave_measurements_for_single_measures()
        if self.ckbox_correctSW_value.get():
            MeasurementHandler.correct_short_wave_measurements_for_single_measures()

        if self.ckbox_correctAblation_value.get():
            MeasurementHandler.cumulate_ice_thickness_measures_for_single_measures(method="SameLevelPositiveFix")
        else:
            MeasurementHandler.cumulate_ice_thickness_measures_for_single_measures(method=None)

        MeasurementHandler.calculate_snow_height_deltas_for_single_measures()

        navigation_bar.singleton.show_sum_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = PrepareMeasurementsFrame()
