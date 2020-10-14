import tkinter as tk

import sys
sys.path.append("GUI")
import gui_main_frame
from visualizer import Visualizer
from tkinter import ttk
import misc as fc
from config_handler import cfg


class PlotFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """

    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        frame_center = tk.Frame(self)
        frame_center.pack()

        frame_general_settings = tk.Frame(frame_center)
        frame_general_settings.grid(row=0, column=0, columnspan=2)

        # ------------------ GENERAL SETTINGS -------------------
        self.heading_general_settings = tk.Label(frame_general_settings, text="General settings", font=cfg["HEADING_FONT"])
        self.heading_general_settings.pack(pady=(25, 0))

        self.lbl_use_sum = tk.Label(frame_general_settings, text="Use summed measurement", state="disabled")
        self.lbl_use_sum.pack(pady=(10, 0))

        self.ckbox_use_sum_value = tk.IntVar()
        self.ckbox_use_sum = tk.Checkbutton(frame_general_settings, variable=self.ckbox_use_sum_value, state="disabled",
                                            command=self.use_summed_measurements_callback)
        self.ckbox_use_sum.pack()

        self.lbl_accumulate_plots = tk.Label(frame_general_settings, text="Accumulate Plots")
        self.lbl_accumulate_plots.pack(pady=(10, 0))

        self.ckbox_accumulate_plots_value = tk.IntVar()
        self.ckbox_accumulate_plots = tk.Checkbutton(frame_general_settings, variable=self.ckbox_accumulate_plots_value)
        self.ckbox_accumulate_plots.pack()

        # # ------------------ ENERGY BALANCE -------------------

        frame_energy_balance_and_components_plotting = tk.Frame(frame_center)
        frame_energy_balance_and_components_plotting.grid(row=1, column=0)

        self.heading_energyBalance = tk.Label(frame_energy_balance_and_components_plotting, text="Energy balance and other components", font=cfg["HEADING_FONT"])
        self.heading_energyBalance.grid(row=0, column=0, columnspan=2)

        frame_ax1 = tk.Frame(frame_energy_balance_and_components_plotting)
        frame_ax2 = tk.Frame(frame_energy_balance_and_components_plotting)
        frame_ax1.grid(row=1, column=0)
        frame_ax2.grid(row=1, column=1)

        self.lbox_options_single_measurement = [
            "total_energy_balance", "sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out",
            "sensible_heat", "latent_heat",
        ]
        self.lbox_options_mean_measurement = self.lbox_options_single_measurement.copy()

        if cfg["PRO_VERSION"]:
            for option in ["temperature", "snow_depth_natural", "snow_depth_artificial", "total_snow_depth",
                                 "rel_moisture", "wind_speed", "air_pressure", "measured_ice_thickness",
                                 "cumulated_ice_thickness"]:
                self.lbox_options_single_measurement.append(option)
                self.lbox_options_mean_measurement.append(option)

            self.lbox_options_single_measurement.extend([])  # nothing? probably
            self.lbox_options_mean_measurement.extend(["actual_melt_water_per_sqm", "theoretical_melt_water_per_sqm"])  # some more?

        self.lbl_Axis1 = tk.Label(frame_ax1, text="First axis", state="normal")
        self.lbl_Axis1.pack()
        self.lbl_cumulateAxis1 = tk.Label(frame_ax1, text="Cumulate components", state="normal")
        self.lbl_cumulateAxis1.pack(pady=(25, 0))
        self.ckbox_cumulateAxis1_value = tk.IntVar()
        self.ckbox_cumulateAxis1 = tk.Checkbutton(frame_ax1, variable=self.ckbox_cumulateAxis1_value)
        self.ckbox_cumulateAxis1.pack()
        self.lbox_selectedComponentsAxis1 = tk.Listbox(frame_ax1, selectmode="multiple", height=6, exportselection=0)
        for option in self.lbox_options_single_measurement:
            self.lbox_selectedComponentsAxis1.insert(tk.END, option)
        self.lbox_selectedComponentsAxis1.pack(side="left", fill="y")
        self.lbox_selectedComponentsAxis1.selection_set(first=0)
        scrollbar = tk.Scrollbar(frame_ax1, orient="vertical")
        scrollbar.config(command=self.lbox_selectedComponentsAxis1.yview)
        scrollbar.pack(side="right", fill="y")
        self.lbox_selectedComponentsAxis1.config(yscrollcommand=scrollbar.set)

        self.lbl_Axis2 = tk.Label(frame_ax2, text="Second axis", state="normal")
        self.lbl_Axis2.pack()
        self.lbl_cumulateAxis2 = tk.Label(frame_ax2, text="Cumulate components", state="normal")
        self.lbl_cumulateAxis2.pack(pady=(25, 0))
        self.ckbox_cumulateAxis2_value = tk.IntVar()
        self.ckbox_cumulateAxis2 = tk.Checkbutton(frame_ax2, variable=self.ckbox_cumulateAxis2_value)
        self.ckbox_cumulateAxis2.pack()
        self.lbox_selectedComponentsAxis2 = tk.Listbox(frame_ax2, selectmode="multiple", height=6, exportselection=0)
        for option in self.lbox_options_single_measurement:
            self.lbox_selectedComponentsAxis2.insert(tk.END, option)
        self.lbox_selectedComponentsAxis2.pack(side="left", fill="y")
        scrollbar = tk.Scrollbar(frame_ax2, orient="vertical")
        scrollbar.config(command=self.lbox_selectedComponentsAxis2.yview)
        scrollbar.pack(side="right", fill="y")
        self.lbox_selectedComponentsAxis2.config(yscrollcommand=scrollbar.set)

        self.btn_plotSelectedComponents = tk.Button(frame_energy_balance_and_components_plotting, text="Visualize selected components",
                                                      command=self.plot_selected_components)
        self.btn_plotSelectedComponents.grid(row=2, column=0, columnspan=2)

        # ------------------ TREND ELIMINATION -------------------
        frame_trend_elimination = tk.Frame(frame_center)
        frame_trend_elimination.grid(row=2, column=0)

        self.heading_trendEliminate = tk.Label(frame_trend_elimination, text="Trend Elimination", state="normal", font=cfg["HEADING_FONT"])
        self.heading_trendEliminate.pack(pady=(25, 0))

        self.btn_trendEliminateSelectedComponents = tk.Button(
            frame_trend_elimination, text="Trend eliminate selected first axis components (cumulated)",
            command=self.plot_trend_eliminate_selected_components)
        self.btn_trendEliminateSelectedComponents.pack()

    def use_summed_measurements_callback(self):
        current_selectionsAxis1 = [self.lbox_selectedComponentsAxis1.get(opt) for opt in self.lbox_selectedComponentsAxis1.curselection()]
        current_selectionsAxis2 = [self.lbox_selectedComponentsAxis2.get(opt) for opt in self.lbox_selectedComponentsAxis2.curselection()]

        self.lbox_selectedComponentsAxis1.delete(0, 'end')
        self.lbox_selectedComponentsAxis2.delete(0, 'end')

        if self.ckbox_use_sum_value.get():
            for i, option in enumerate(self.lbox_options_mean_measurement):
                self.lbox_selectedComponentsAxis1.insert(tk.END, option)
                if option in current_selectionsAxis1:
                    self.lbox_selectedComponentsAxis1.selection_set(first=i)
                self.lbox_selectedComponentsAxis2.insert(tk.END, option)
                if option in current_selectionsAxis2:
                    self.lbox_selectedComponentsAxis2.selection_set(first=i)
        else:
            for i, option in enumerate(self.lbox_options_single_measurement):
                self.lbox_selectedComponentsAxis1.insert(tk.END, option)
                if option in current_selectionsAxis1:
                    self.lbox_selectedComponentsAxis1.selection_set(first=i)
                self.lbox_selectedComponentsAxis2.insert(tk.END, option)
                if option in current_selectionsAxis2:
                    self.lbox_selectedComponentsAxis2.selection_set(first=i)

    def enable_option_to_use_summed_measurements(self):
        fc.set_widget_state([self.lbl_use_sum, self.ckbox_use_sum], "normal")

    def check_accumulate_flag(self):
        Visualizer.accumulate_plots = bool(self.ckbox_accumulate_plots_value.get())

    def plot_selected_components(self):
        self.check_accumulate_flag()

        Visualizer.plot_components(
            components1=[self.lbox_selectedComponentsAxis1.get(opt) for opt in self.lbox_selectedComponentsAxis1.curselection()],
            cumulate_components1=self.ckbox_cumulateAxis1_value.get(),
            components2=[self.lbox_selectedComponentsAxis2.get(opt) for opt in self.lbox_selectedComponentsAxis2.curselection()],
            cumulate_components2=self.ckbox_cumulateAxis2_value.get(),
            use_summed_measurements=bool(self.ckbox_use_sum_value.get()),
        )

    def plot_trend_eliminate_selected_components(self):
        self.check_accumulate_flag()
        Visualizer.plot_periodic_trend_eliminated_selected_option(
            [self.lbox_selectedComponentsAxis1.get(opt) for opt in self.lbox_selectedComponentsAxis1.curselection()],
            bool(self.ckbox_use_sum_value.get())
        )


singleton = None


def create_singleton():
    global singleton
    singleton = PlotFrame()  # yet to be initialized
