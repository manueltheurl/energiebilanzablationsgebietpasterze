import tkinter as tk
import sys
sys.path.append("GUI")

import gui_main_frame
import navigation_bar
from visualizer import Visualizer
from tkinter import ttk
import functions as fc
import info_bar
import functions
import datetime
from measurement_handler import MeasurementHandler
import frame_plot
import datetime as dt
import measurement
from config_handler import cfg
import frame_energy_balance


class SumFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """

    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.heading_sum = tk.Label(self,
                                     text="Sum measurements together", font=cfg["HEADING_FONT"])
        self.heading_sum.pack(pady=(25, 30))

        # check if wanna sum measurements
        self.ckbox_sumByAmount_value = tk.IntVar()
        self.ckbox_sumByAmount = tk.Checkbutton(self,
                                                command=self.toggle_sum_measurements_by_amount,
                                                variable=self.ckbox_sumByAmount_value, state="normal")
        self.ckbox_sumByAmount.pack()

        self.lbl_sumByAmount = tk.Label(self, text="Sum measurements by amount")
        self.lbl_sumByAmount.pack()
        self.entry_sumByAmount = tk.Entry(self, state="disabled")
        self.entry_sumByAmount.pack()

        self.ckbox_sumByTimeInterval_value = tk.IntVar()
        self.ckbox_sumByTimeInterval = tk.Checkbutton(self,
                                                      command=self.toggle_sum_measurements_by_time_interval,
                                                      variable=self.ckbox_sumByTimeInterval_value)
        self.ckbox_sumByTimeInterval.pack()
        self.lbl_sumByTimeInterval = tk.Label(self, text="Sum measurements by time interval")
        self.lbl_sumByTimeInterval.pack()
        self.entry_sumByTimeInterval = tk.Entry(self, state="disabled")
        self.entry_sumByTimeInterval.pack()
        self.lbl_timeInterval = tk.Label(self, text="Time interval unit")
        self.lbl_timeInterval.pack()
        self.cmbobox_sumByTimeIntervalUnit = ttk.Combobox(self, values=["Minutes", "Hours", "Days", "Months", "Years"],
                                                          state="disabled")
        self.cmbobox_sumByTimeIntervalUnit.pack()
        self.ckbox_sumByTimeInterval.pack(padx=10)

        self.ckbox_fixInvalid_value = tk.IntVar()
        self.ckbox_fixInvalid = tk.Checkbutton(self, variable=self.ckbox_fixInvalid_value)
        self.ckbox_fixInvalid.pack(pady=(45, 0))
        self.lbl_fixInvalid = tk.Label(self, text="Fix invalid measurements by mean of other years")
        self.lbl_fixInvalid.pack()

        self.btn_sumMeasurements = tk.Button(self, text="Sum measurements",
                                             command=self.create_summed_measurement, state="disabled")
        self.btn_sumMeasurements.pack(pady=40)

        self.btn_sumSkip = tk.Button(self, text="Skip",
                                     command=navigation_bar.singleton.show_energy_balance_frame)
        self.btn_sumSkip.pack(pady=30)

        self.already_summed_measurements = False  # todo currently never gets reset after getting true

    def toggle_sum_measurements_by_amount(self):
        widgets_to_toggle_state = [
            self.entry_sumByAmount
        ]

        # deactivate other option
        if self.ckbox_sumByAmount_value.get():
            if self.ckbox_sumByTimeInterval_value.get():
                self.toggle_sum_measurements_by_time_interval()
            fc.set_widget_state([self.ckbox_sumByTimeInterval], "disabled")
        else:
            fc.set_widget_state([self.ckbox_sumByTimeInterval], "normal")

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_sumByAmount_value.get())
        fc.set_widget_state([self.btn_sumMeasurements],
                            self.ckbox_sumByAmount_value.get() or self.ckbox_sumByTimeInterval_value.get())

    def toggle_sum_measurements_by_time_interval(self):
        widgets_to_toggle_state = [
            self.entry_sumByTimeInterval,
            self.cmbobox_sumByTimeIntervalUnit
        ]

        # deactivate other option
        if self.ckbox_sumByTimeInterval_value.get():
            if self.ckbox_sumByAmount_value.get():
                self.toggle_sum_measurements_by_amount()
            fc.set_widget_state([self.ckbox_sumByAmount], "disabled")
        else:
            fc.set_widget_state([self.ckbox_sumByAmount], "normal")

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_sumByTimeInterval_value.get())
        fc.set_widget_state([self.btn_sumMeasurements],
                            self.ckbox_sumByAmount_value.get() or self.ckbox_sumByTimeInterval_value.get())

    def create_summed_measurement(self):
        info_bar_text = ""
        sum_by_amount = None
        sum_by_months = None
        sum_by_years = None

        # make sure that endtime is set correctly .. this presupposes homogen measurements

        if self.ckbox_sumByAmount_value.get():
            sum_by_amount = self.entry_sumByAmount.get()

        sum_by_time_interval = None

        if self.ckbox_sumByTimeInterval_value.get():
            if self.entry_sumByTimeInterval.get().isdigit():
                time_interval_unit = self.cmbobox_sumByTimeIntervalUnit.get()

                if time_interval_unit == "Minutes":
                    sum_by_time_interval = dt.timedelta(minutes=int(self.entry_sumByTimeInterval.get()))
                elif time_interval_unit == "Hours":
                    sum_by_time_interval = dt.timedelta(hours=int(self.entry_sumByTimeInterval.get()))
                elif time_interval_unit == "Days":
                    sum_by_time_interval = dt.timedelta(days=int(self.entry_sumByTimeInterval.get()))
                elif time_interval_unit == "Months":
                    sum_by_months = int(self.entry_sumByTimeInterval.get())
                elif time_interval_unit == "Years":
                    sum_by_years = int(self.entry_sumByTimeInterval.get())

        if sum_by_amount is not None and sum_by_amount.isdigit():
            info_bar_text += "One summed measurement contains: " + str(sum_by_amount)
            MeasurementHandler.sum_measurements_by_amount(int(sum_by_amount))
        elif sum_by_time_interval is not None:
            frame_plot.singleton.enable_option_to_use_summed_measurements()
            info_bar_text += "Measurements every " +\
                             fc.make_seconds_beautiful_string(sum_by_time_interval.total_seconds()) + " minutes summed"
            MeasurementHandler.sum_measurements_by_time_interval(sum_by_time_interval)
        elif sum_by_months is not None:
            MeasurementHandler.sum_measurements_by_months(sum_by_months)
            info_bar_text += "Measurements every " + str(sum_by_months) + " months summed"
        elif sum_by_years is not None:
            MeasurementHandler.sum_measurements_by_years(sum_by_years)
            info_bar_text += "Measurements every " + str(sum_by_years) + " years summed"
        else:
            return  # shouldnt get here

        if self.ckbox_fixInvalid_value.get():
            # todo drop down list to choose which measurements to fix .. currently just everything by default
            percentage_replaced = MeasurementHandler.fix_invalid_summed_measurements()
            if percentage_replaced < 100:
                info_bar.singleton.change_error_message("Not all measurements can be fixed, can you take a longer time span?")
            else:
                info_bar.singleton.change_error_message("")
            info_bar_text += f"  ({percentage_replaced}% invalid replaced)"

        self.already_summed_measurements = True
        info_bar.singleton.change_sum_info(info_bar_text)
        frame_plot.singleton.enable_option_to_use_summed_measurements()
        frame_energy_balance.singleton.enable_option_to_use_summed_measurements()

        if frame_energy_balance.singleton.energy_balance_calculated:
            navigation_bar.singleton.btn_conversionframe["state"] = "normal"
            navigation_bar.singleton.show_conversion_frame()
        else:
            navigation_bar.singleton.show_energy_balance_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = SumFrame()  # yet to be initialized
