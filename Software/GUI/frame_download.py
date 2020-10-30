import tkinter as tk
import sys
from tkinter import filedialog

sys.path.append("GUI")
import gui_main_frame as gui_main_frame
from measurement_handler import MeasurementHandler
from visualizer import Visualizer
from tkinter import ttk
from config_handler import cfg
from downloader import Downloader
import misc as fc


class DownloadFrame(tk.Frame):
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

        self.lbl_use_mean = tk.Label(frame_general_settings, text="Use mean measurements", state="disabled")
        self.lbl_use_mean.pack(pady=(10, 0))

        self.ckbox_use_sum_value = tk.IntVar()
        self.ckbox_use_sum = tk.Checkbutton(frame_general_settings, variable=self.ckbox_use_sum_value, state="disabled",
                                            command=self.use_mean_measures_callback)
        self.ckbox_use_sum.pack()

        # # ------------------ ENERGY BALANCE -------------------

        frame_energy_balance_and_components_plotting = tk.Frame(frame_center)
        frame_energy_balance_and_components_plotting.grid(row=1, column=0)

        self.heading_energyBalance = tk.Label(frame_energy_balance_and_components_plotting, text="Energy balance and other components", font=cfg["HEADING_FONT"])
        self.heading_energyBalance.grid(row=0, column=0, columnspan=1)

        frame_ax1 = tk.Frame(frame_energy_balance_and_components_plotting)
        frame_ax1.grid(row=1, column=0)

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

        self.btn_plotSelectedComponents = tk.Button(frame_energy_balance_and_components_plotting, text="Download selected components",
                                                      command=self.download_selected_components)
        self.btn_plotSelectedComponents.grid(row=2, column=0, columnspan=1)

        self.btn_downloadCosipyFormat = tk.Button(frame_energy_balance_and_components_plotting, text="Download cosipy format",
                                                      command=Downloader.download_in_cosipy_format, state="disabled")
        self.btn_downloadCosipyFormat.grid(row=3, column=0, pady=(60, 0))

    def enable_option_to_use_mean_measures(self):
        fc.set_widget_state([self.lbl_use_mean, self.ckbox_use_sum, self.btn_downloadCosipyFormat], "normal")

    def use_mean_measures_callback(self):
        current_selectionsAxis1 = [self.lbox_selectedComponentsAxis1.get(opt) for opt in
                                   self.lbox_selectedComponentsAxis1.curselection()]

        self.lbox_selectedComponentsAxis1.delete(0, 'end')

        if self.ckbox_use_sum_value.get():
            for i, option in enumerate(self.lbox_options_mean_measurement):
                self.lbox_selectedComponentsAxis1.insert(tk.END, option)
                if option in current_selectionsAxis1:
                    self.lbox_selectedComponentsAxis1.selection_set(first=i)
        else:
            for i, option in enumerate(self.lbox_options_single_measurement):
                self.lbox_selectedComponentsAxis1.insert(tk.END, option)
                if option in current_selectionsAxis1:
                    self.lbox_selectedComponentsAxis1.selection_set(first=i)

    def download_selected_components(self):
        chosen_components = [self.lbox_selectedComponentsAxis1.get(opt) for opt in
                         self.lbox_selectedComponentsAxis1.curselection()]

        selected_path = tk.filedialog.asksaveasfile(
            defaultextension=".csv", initialdir="downloads",
            initialfile=f"data_download_{'cumulated_' if self.ckbox_cumulateAxis1_value.get() else ''}" + '_'.join(chosen_components),
            filetypes=(("Csv Files", "*.csv"), ("all files", "*.*")))

        Downloader.download_components(
            components=chosen_components, cumulate_components=self.ckbox_cumulateAxis1_value.get(),
            save_name=selected_path)


singleton = None


def create_singleton():
    global singleton
    singleton = DownloadFrame()  # yet to be initialized
