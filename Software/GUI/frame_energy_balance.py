import tkinter as tk
import multiple_measurements
import functions as fc
import gui_main_frame as gui_main_frame
import navigation_bar as navigation_bar
import info_bar as info_bar
from tkinter import ttk
import datetime as dt
import reader
import frame_sum
from manage_config import cfg


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

    def enable_option_to_use_summed_measurements(self):
        fc.set_widget_state([self.lbl_useSummed, self.ckbox_useSummed], "normal")
        self.ckbox_useSummed_value.set(1)

    def calculate_energy_balance_and_cumulate_ablation(self):
        forwhich = "summed" if self.ckbox_useSummed_value.get() else "scope"

        if not multiple_measurements.singleton.calculate_energy_balance_for(
                forwhich, self.scale_simulate_dimming_brightening.get()):
            info_bar.singleton.change_error_message("Some measurements are None, cannot calculate energy balance, did you fix invalid messages?")
            return
        else:
            info_bar.singleton.change_error_message("")

        # todo maybe make labels that describe what will be done and the button says just process
        multiple_measurements.singleton.convert_energy_balance_to_water_rate_equivalent_for(forwhich)

        self.energy_balance_calculated = True

        navigation_bar.singleton.btn_downloadframe["state"] = "normal"
        navigation_bar.singleton.btn_plotframe["state"] = "normal"

        if frame_sum.singleton.already_summed_measurements:
            navigation_bar.singleton.btn_conversionframe["state"] = "normal"
            navigation_bar.singleton.show_conversion_frame()
        else:
            navigation_bar.singleton.show_sum_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = EnergyBalanceFrame()
