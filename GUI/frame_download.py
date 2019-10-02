import tkinter as tk
import sys
sys.path.append("GUI")
import gui_main_frame as gui_main_frame
import multiple_measurements
import visualizer
from tkinter import ttk


class ModelFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.lbl_heading_download = tk.Label(self, text="Download generated data to .csv", state="normal")
        self.lbl_heading_download.pack(pady=(40, 0))

        self.btn_totalEnergyBalance = tk.Button(self, text="Total energy balance",
                                                command=self.download_total_energy_balance)
        self.btn_totalEnergyBalance.pack(pady=(40, 0))

        self.btn_cleanedAblation = tk.Button(self, text="Cleaned Ablation",
                                                command=self.download_cleaned_ablation)
        self.btn_cleanedAblation.pack(pady=(40, 0))

        listbox_option = [
            "sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "sensible_heat",
            "latent_heat",
        ]

        self.listbox_selectedComponents = tk.Listbox(self, selectmode="multiple")
        for option in listbox_option:
            self.listbox_selectedComponents.insert(tk.END, option)

        self.listbox_selectedComponents.pack(pady=(30, 0))

        self.btn_energySelectedComponents = tk.Button(self, text="Selected components",
                                                command=self.download_selected_components)
        self.btn_energySelectedComponents.pack()

    @staticmethod
    def download_total_energy_balance():
        multiple_measurements.singleton.download_whole_energy_balance()

    @staticmethod
    def download_cleaned_ablation():
        # aint a component of that .. TODO not the best name for the fx
        multiple_measurements.singleton.download_components_of_energy_balance(["ablation"])

    def download_selected_components(self):
        multiple_measurements.singleton.download_components_of_energy_balance(
            [self.listbox_selectedComponents.get(opt) for opt in self.listbox_selectedComponents.curselection()]
        )


singleton = None


def create_singleton():
    global singleton
    singleton = ModelFrame()  # yet to be initialized
