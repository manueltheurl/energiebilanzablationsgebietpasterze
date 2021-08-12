import tkinter as tk
from measurement_handler import MeasurementHandler
import misc as fc
import gui_main_frame as gui_main_frame
import navigation_bar as navigation_bar
import info_bar as info_bar
from tkinter import ttk
import datetime as dt
from reader import Reader
import frame_mean
from config_handler import cfg


class EnergyBalanceFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """

    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid_propagate(False)

        self.heading_energyBalance = tk.Label(self,
                                     text="Calculate Energy balance", font=cfg["HEADING_FONT"])
        self.heading_energyBalance.pack(pady=(25, 30))

        self.lbl_simulate_dimming_brightening = tk.Label(self, text="Simulate global dimming and brightening [W/m^2]")

        self.scale_simulate_dimming_brightening = tk.Scale(self, from_=-9, to=4, orient="horizontal")

        if bool(cfg["PRO_VERSION"]):
            self.scale_simulate_dimming_brightening.pack()
            self.lbl_simulate_dimming_brightening.pack()
        
        self.ckbox_useSummed_value = tk.IntVar()
        self.ckbox_useSummed = tk.Checkbutton(self, variable=self.ckbox_useSummed_value, state="disabled")
        self.ckbox_useSummed.pack(pady=(25, 0))
        self.lbl_useSummed = tk.Label(self, text="Use summed measurements", state="disabled")
        self.lbl_useSummed.pack()
        
        self.btn_calcEnergyBalance = tk.Button(self,
                                               text="Calculate Energy Balance and corresponding theoretical melt rate",
                                               command=self.calculate_energy_balance_and_cumulate_ablation,
                                               state="normal")
        self.btn_calcEnergyBalance.pack(pady=30)

        self.grid(row=0, column=0, sticky="nsew")

        self.energy_balance_calculated = False  # todo currently never gets reset after getting true

    def enable_option_to_use_mean_measures(self):
        fc.set_widget_state([self.lbl_useSummed, self.ckbox_useSummed], "normal")
        self.ckbox_useSummed_value.set(1)

    def calculate_energy_balance_and_cumulate_ablation(self):
        if self.ckbox_useSummed_value.get():
            if not MeasurementHandler.calculate_energy_balance_for_mean_measures(
                    self.scale_simulate_dimming_brightening.get()):
                info_bar.singleton.change_warning_message("Cannot compute energy balance for all measures, did you "
                                                        "consider fixing invalid measures?")
            else:
                info_bar.singleton.change_warning_message("")
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for_mean_measures()
        else:
            if not MeasurementHandler.calculate_energy_balance_for_single_measures(
                    self.scale_simulate_dimming_brightening.get()):
                info_bar.singleton.change_warning_message("Cannot compute energy balance for all measures")
            else:
                info_bar.singleton.change_warning_message("")
            MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for_single_measures()
        # todo maybe make labels that describe what will be done and the button says just process

        self.energy_balance_calculated = True

        navigation_bar.singleton.btn_downloadframe["state"] = "normal"
        navigation_bar.singleton.btn_plotframe["state"] = "normal"

        if frame_mean.singleton.already_averaged_measurements:
            navigation_bar.singleton.btn_conversionframe["state"] = "normal"
            navigation_bar.singleton.show_conversion_frame()
        else:
            navigation_bar.singleton.show_sum_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = EnergyBalanceFrame()
