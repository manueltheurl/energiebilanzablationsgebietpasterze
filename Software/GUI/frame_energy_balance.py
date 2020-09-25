import tkinter as tk
import multiple_measurements
import functions as fc
import gui_main_frame as gui_main_frame
import navigation_bar as navigation_bar
import info_bar as info_bar
from tkinter import ttk
import datetime as dt
import reader
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

        self.btn_calcEnergyBalance = tk.Button(self,
                                               text="Calculate Energy Balance and corresponding theoretical melt rate",
                                               command=self.calculate_energy_balance_and_cumulate_ablation,
                                               state="normal")
        self.btn_calcEnergyBalance.pack(pady=30)

        self.grid(row=0, column=0, sticky="nsew")

    def calculate_energy_balance_and_cumulate_ablation(self):
        multiple_measurements.singleton.calculate_energy_balance_for("scope",
            self.scale_simulate_dimming_brightening.get()
        )

        # todo maybe make labels that describe what will be done and the button says just process

        multiple_measurements.singleton.convert_energy_balance_to_water_rate_equivalent_for()
        # multiple_measurements.singleton.calculate_ablation_and_theoretical_melt_rate_to_meltwater_per_square_meter_for_scope()

        navigation_bar.singleton.btn_downloadframe["state"] = "normal"
        navigation_bar.singleton.show_sum_frame()


singleton = None


def create_singleton():
    global singleton
    singleton = EnergyBalanceFrame()
