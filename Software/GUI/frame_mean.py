import tkinter as tk
import sys
sys.path.append("GUI")

import gui_main_frame
import navigation_bar
from visualizer import Visualizer
from tkinter import ttk
import misc as fc
import info_bar
import misc
import datetime
from measurement_handler import MeasurementHandler
import frame_plot
import datetime as dt
import measurement
from config_handler import cfg
import frame_energy_balance
import frame_download


class MeanFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """

    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.heading_mean = tk.Label(self,
                                     text="Average measurements", font=cfg["HEADING_FONT"])
        self.heading_mean.pack(pady=(25, 30))

        # check if wanna mean measurements
        self.ckbox_meanByAmount_value = tk.IntVar()
        self.ckbox_meanByAmount = tk.Checkbutton(self,
                                                command=self.toggle_mean_measurements_by_amount,
                                                variable=self.ckbox_meanByAmount_value, state="normal")
        self.ckbox_meanByAmount.pack()

        self.lbl_meanByAmount = tk.Label(self, text="Average measurements by amount")
        self.lbl_meanByAmount.pack()
        self.entry_meanByAmount = tk.Entry(self, state="disabled")
        self.entry_meanByAmount.pack()

        self.ckbox_meanByTimeInterval_value = tk.IntVar()
        self.ckbox_meanByTimeInterval = tk.Checkbutton(self,
                                                      command=self.toggle_mean_measurements_by_time_interval,
                                                      variable=self.ckbox_meanByTimeInterval_value)
        self.ckbox_meanByTimeInterval.pack()
        self.lbl_meanByTimeInterval = tk.Label(self, text="Average measurements by time interval")
        self.lbl_meanByTimeInterval.pack()
        self.entry_meanByTimeInterval = tk.Entry(self, state="disabled")
        self.entry_meanByTimeInterval.pack()
        self.lbl_timeInterval = tk.Label(self, text="Time interval unit")
        self.lbl_timeInterval.pack()
        self.cmbobox_meanByTimeIntervalUnit = ttk.Combobox(self, values=["Minutes", "Hours", "Days", "Months", "Years"],
                                                          state="disabled")
        self.cmbobox_meanByTimeIntervalUnit.pack()
        self.ckbox_meanByTimeInterval.pack(padx=10)

        self.ckbox_fixInvalid_value = tk.IntVar()
        self.ckbox_fixInvalid = tk.Checkbutton(
            self, variable=self.ckbox_fixInvalid_value,
            command=lambda: fc.set_widget_state([self.lbox_selectedOptionsToFix], self.ckbox_fixInvalid_value.get()))
        self.ckbox_fixInvalid.pack(pady=(25, 0))
        self.lbl_fixInvalid = tk.Label(self, text="Fix invalid measurements by mean of other years")
        self.lbl_fixInvalid.pack()

        self.lbox_selectedOptionsToFix = tk.Listbox(self, selectmode="multiple", height=10, exportselection=0)
        options_to_fix = ("temperature", "rel_moisture", "air_pressure", "wind_speed", "sw_radiation_in", "sw_radiation_out",
                      "lw_radiation_in", "lw_radiation_out", "snow_delta", "relative_ablation_measured")
        for option in options_to_fix:
            self.lbox_selectedOptionsToFix.insert(tk.END, option)
        self.lbox_selectedOptionsToFix.pack()
        for i in range(len(options_to_fix)):
            self.lbox_selectedOptionsToFix.selection_set(first=i)
        self.lbox_selectedOptionsToFix["state"] = "disabled"

        self.btn_meanMeasurements = tk.Button(self, text="Average measurements",
                                             command=self.create_averaged_measurement, state="disabled")
        self.btn_meanMeasurements.pack(pady=40)

        self.btn_meanSkip = tk.Button(self, text="Skip",
                                     command=navigation_bar.singleton.show_energy_balance_frame)
        self.btn_meanSkip.pack(pady=30)

        self.already_averaged_measurements = False  # todo currently never gets reset after getting true

    def toggle_mean_measurements_by_amount(self):
        widgets_to_toggle_state = [
            self.entry_meanByAmount
        ]

        # deactivate other option
        if self.ckbox_meanByAmount_value.get():
            if self.ckbox_meanByTimeInterval_value.get():
                self.toggle_mean_measurements_by_time_interval()
            fc.set_widget_state([self.ckbox_meanByTimeInterval], "disabled")
        else:
            fc.set_widget_state([self.ckbox_meanByTimeInterval], "normal")

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_meanByAmount_value.get())
        fc.set_widget_state([self.btn_meanMeasurements],
                            self.ckbox_meanByAmount_value.get() or self.ckbox_meanByTimeInterval_value.get())

    def toggle_mean_measurements_by_time_interval(self):
        widgets_to_toggle_state = [
            self.entry_meanByTimeInterval,
            self.cmbobox_meanByTimeIntervalUnit
        ]

        # deactivate other option
        if self.ckbox_meanByTimeInterval_value.get():
            if self.ckbox_meanByAmount_value.get():
                self.toggle_mean_measurements_by_amount()
            fc.set_widget_state([self.ckbox_meanByAmount], "disabled")
        else:
            fc.set_widget_state([self.ckbox_meanByAmount], "normal")

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_meanByTimeInterval_value.get())
        fc.set_widget_state([self.btn_meanMeasurements],
                            self.ckbox_meanByAmount_value.get() or self.ckbox_meanByTimeInterval_value.get())

    def create_averaged_measurement(self):
        info_bar_text = ""
        mean_by_amount = None
        mean_by_months = None
        mean_by_years = None

        # make sure that endtime is set correctly .. this presupposes homogen measurements

        if self.ckbox_meanByAmount_value.get():
            mean_by_amount = self.entry_meanByAmount.get()

        mean_by_time_interval = None

        if self.ckbox_meanByTimeInterval_value.get():
            if self.entry_meanByTimeInterval.get().isdigit():
                time_interval_unit = self.cmbobox_meanByTimeIntervalUnit.get()

                if time_interval_unit == "Minutes":
                    mean_by_time_interval = dt.timedelta(minutes=int(self.entry_meanByTimeInterval.get()))
                elif time_interval_unit == "Hours":
                    mean_by_time_interval = dt.timedelta(hours=int(self.entry_meanByTimeInterval.get()))
                elif time_interval_unit == "Days":
                    mean_by_time_interval = dt.timedelta(days=int(self.entry_meanByTimeInterval.get()))
                elif time_interval_unit == "Months":
                    mean_by_months = int(self.entry_meanByTimeInterval.get())
                elif time_interval_unit == "Years":
                    mean_by_years = int(self.entry_meanByTimeInterval.get())

        if mean_by_amount is not None and mean_by_amount.isdigit():
            info_bar_text += "One average measurement contains: " + str(mean_by_amount)
            MeasurementHandler.mean_measurements_by_amount(int(mean_by_amount))
        elif mean_by_time_interval is not None:
            frame_plot.singleton.enable_option_to_use_mean_measures()
            info_bar_text += "Measurements every " +\
                             fc.make_seconds_beautiful_string(mean_by_time_interval.total_seconds()) + " minutes averaged"
            MeasurementHandler.mean_measurements_by_time_interval(mean_by_time_interval)
        elif mean_by_months is not None:
            MeasurementHandler.mean_measurements_by_months(mean_by_months)
            info_bar_text += "Measurements every " + str(mean_by_months) + " months averaged"
        elif mean_by_years is not None:
            MeasurementHandler.mean_measurements_by_years(mean_by_years)
            info_bar_text += "Measurements every " + str(mean_by_years) + " years averaged"
        else:
            return  # shouldnt get here

        if self.ckbox_fixInvalid_value.get():
            optionsToFix = [self.lbox_selectedOptionsToFix.get(opt) for opt in self.lbox_selectedOptionsToFix.curselection()]
            percentage_replaced = MeasurementHandler.fix_invalid_mean_measurements(optionsToFix)
            if percentage_replaced < 100:
                info_bar.singleton.change_error_message("Not all measurements can be fixed, can you take a longer time span?")
            else:
                info_bar.singleton.change_error_message("")
            info_bar_text += f"  ({round(percentage_replaced, 2)}% invalid replaced)"

        self.already_averaged_measurements = True
        info_bar.singleton.change_mean_info(info_bar_text)
        frame_plot.singleton.enable_option_to_use_mean_measures()
        frame_energy_balance.singleton.enable_option_to_use_mean_measures()
        frame_download.singleton.enable_option_to_use_mean_measures()

        if frame_energy_balance.singleton.energy_balance_calculated:
            navigation_bar.singleton.btn_conversionframe["state"] = "normal"
            navigation_bar.singleton.show_conversion_frame()
        else:
            navigation_bar.singleton.show_energy_balance_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = MeanFrame()  # yet to be initialized
