import tkinter as tk
import GUI.gui_main_frame as gui_main_frame
import visualizer
from tkinter import ttk
import GUI.navigation_bar as navigation_bar
import functions as fc


class SumFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

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
        self.cmbobox_timeIntervalUnit = ttk.Combobox(self, values=["Minutes", "Hours", "Days"], state="disabled")
        self.cmbobox_timeIntervalUnit.pack()
        self.ckbox_sumByTimeInterval.pack(padx=10)

        self.btn_sumMeasurements = tk.Button(self, text="Sum measurements",
                                             command=self.create_summed_measurement, state="disabled")
        self.btn_sumMeasurements.pack(pady=30)

        self.btn_sumSkip = tk.Button(self, text="Skip",
                                     command=navigation_bar.singleton.show_plot_frame)
        self.btn_sumSkip.pack(pady=30)

    def toggle_sum_measurements_by_amount(self):
        widgets_to_toggle_state = [
            self.entry_sumByAmount
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_sumByAmount_value.get())
        fc.set_widget_state([self.btn_sumMeasurements],
                            self.ckbox_sumByAmount_value.get() or self.ckbox_sumByTimeInterval_value.get())

    def toggle_sum_measurements_by_time_interval(self):
        widgets_to_toggle_state = [
            self.entry_sumByTimeInterval,
            self.cmbobox_timeIntervalUnit
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_sumByTimeInterval_value.get())
        fc.set_widget_state([self.btn_sumMeasurements],
                            self.ckbox_sumByAmount_value.get() or self.ckbox_sumByTimeInterval_value.get())

    def sum_measurements_by_amount(self):
        pass

    def sum_measurements_by_time_interval(self):
        pass

    def create_summed_measurement(self):
        pass


singleton = None


def create_singleton():
    global singleton
    singleton = SumFrame()  # yet to be initialized
