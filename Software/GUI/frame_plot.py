import tkinter as tk

import sys
sys.path.append("GUI")
import gui_main_frame
import visualizer
from tkinter import ttk
import functions as fc
from manage_config import cfg


class PlotFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    did_sum_measurements = False

    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        # ------------------ GENERAL SETTINGS -------------------
        self.heading_general_settings = tk.Label(self, text="General settings", font=cfg["HEADING_FONT"])
        self.heading_general_settings.pack(pady=(25, 0))

        self.lbl_use_sum = tk.Label(self, text="Use summed measurement", state="disabled")
        self.lbl_use_sum.pack(pady=(10, 0))

        self.ckbox_use_sum_value = tk.IntVar()
        self.ckbox_use_sum = tk.Checkbutton(self, variable=self.ckbox_use_sum_value, state="disabled")
        self.ckbox_use_sum.pack()

        self.lbl_accumulate_plots = tk.Label(self, text="Accumulate Plots")
        self.lbl_accumulate_plots.pack(pady=(10, 0))

        self.ckbox_accumulate_plots_value = tk.IntVar()
        self.ckbox_accumulate_plots = tk.Checkbutton(self, variable=self.ckbox_accumulate_plots_value)
        self.ckbox_accumulate_plots.pack()

        # ------------------ ENERGY BALANCE -------------------
        self.heading_energyBalance = tk.Label(self, text="Energy balance", font=cfg["HEADING_FONT"])
        self.heading_energyBalance.pack(pady=(25, 0))

        self.btn_totalEnergyBalance = tk.Button(self, text="Total energy balance",
                                                command=self.plot_total_energy_balance)
        self.btn_totalEnergyBalance.pack(pady=(20, 10))

        self.lbl_secondAxis = tk.Label(self, text="Second axis", state="normal")
        self.lbl_secondAxis.pack()

        self.ckbox_secondAxis_value = tk.IntVar()
        self.ckbox_secondAxis = tk.Checkbutton(self, variable=self.ckbox_secondAxis_value, command=self.add_second_axis)
        self.ckbox_secondAxis.pack()

        self.radBut_show_ablation_or_water_equivalent_value = tk.StringVar()
        self.radBut_show_ablation = tk.Radiobutton(
            self, variable=self.radBut_show_ablation_or_water_equivalent_value, state="disabled", value="show_ablation",
            text="Show measured ablation [m]")
        self.radBut_show_ablation.pack()

        self.radBut_show_water_equivalent = tk.Radiobutton(
            self, variable=self.radBut_show_ablation_or_water_equivalent_value, state="disabled",
            value="show_water_equivalent", text="Show measured and calculated ablation water equivalent [mm/d]")
        self.radBut_show_water_equivalent.pack()

        self.radBut_show_ablation_or_water_equivalent_value.set("show_ablation")

        listbox_option = [
            "sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "sensible_heat",
            "latent_heat",
        ]

        self.listbox_selectedComponents = tk.Listbox(self, selectmode="multiple", height=6)
        for option in listbox_option:
            self.listbox_selectedComponents.insert(tk.END, option)

        self.listbox_selectedComponents.pack(pady=(30, 0))

        self.btn_energySelectedComponents = tk.Button(self, text="Energy selected components",
                                                      command=self.plot_selected_components)
        self.btn_energySelectedComponents.pack()

        # ------------------ TREND ELIMINATION -------------------
        self.heading_trendEliminate = tk.Label(self, text="Trend Elimination", state="normal", font=cfg["HEADING_FONT"])
        self.heading_trendEliminate.pack(pady=(25, 0))

        self.btn_totalEnergyBalanceTrendEliminate = tk.Button(self, text="Trend eliminate total energy balance",
                                                              command=self.plot_trend_eliminate_total_energy_balance)
        self.btn_totalEnergyBalanceTrendEliminate.pack(pady=(10, 0))

        self.btn_trendEliminateSelectedComponents = tk.Button(self, text="Trend eliminate selected components",
                                                              command=self.plot_trend_eliminate_selected_components)
        self.btn_trendEliminateSelectedComponents.pack()

    def enable_option_to_use_summed_measurements(self):
        fc.set_widget_state([self.lbl_use_sum, self.ckbox_use_sum], "normal")

        if bool(self.ckbox_secondAxis_value.get()):
            fc.set_widget_state([self.radBut_show_water_equivalent], "normal")

    def add_second_axis(self):
        if bool(self.ckbox_secondAxis_value.get()):
            fc.set_widget_state([self.radBut_show_ablation], "active")

            if self.did_sum_measurements:
                fc.set_widget_state([self.radBut_show_water_equivalent], "normal")
        else:
            fc.set_widget_state([self.radBut_show_ablation, self.radBut_show_water_equivalent], "disabled")

    def check_accumulate_flag(self):
        visualizer.singleton.accumulate_plots = bool(self.ckbox_accumulate_plots_value.get())

    def plot_total_energy_balance(self):
        self.check_accumulate_flag()
        visualizer.singleton.plot_total_energy_balance(
            bool(self.ckbox_use_sum_value.get()),
            bool(self.ckbox_secondAxis_value.get()) and self.radBut_show_ablation_or_water_equivalent_value.get())

    def plot_selected_components(self):
        self.check_accumulate_flag()
        visualizer.singleton.plot_energy_balance_components(
            [self.listbox_selectedComponents.get(opt) for opt in self.listbox_selectedComponents.curselection()],
            bool(self.ckbox_use_sum_value.get())
        )

    def plot_trend_eliminate_total_energy_balance(self):
        self.check_accumulate_flag()
        visualizer.singleton.plot_periodic_trend_eliminated_total_energy_balance(
            bool(self.ckbox_use_sum_value.get())
        )

    def plot_trend_eliminate_selected_components(self):
        self.check_accumulate_flag()
        visualizer.singleton.plot_periodic_trend_eliminated_selected_option(
            [self.listbox_selectedComponents.get(opt) for opt in self.listbox_selectedComponents.curselection()],
            bool(self.ckbox_use_sum_value.get())
        )


singleton = None


def create_singleton():
    global singleton
    singleton = PlotFrame()  # yet to be initialized
