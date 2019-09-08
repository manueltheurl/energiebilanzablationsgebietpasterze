import tkinter as tk
import GUI.gui_main_frame as gui_main_frame
import visualizer
from tkinter import ttk
import functions as fc


class PlotFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.lbl_use_sum = tk.Label(self, text="Use summed measurement", state="disabled")
        self.lbl_use_sum.pack(pady=(40, 0))

        self.ckbox_use_sum_value = tk.IntVar()
        self.ckbox_use_sum = tk.Checkbutton(self, variable=self.ckbox_use_sum_value, state="disabled")
        self.ckbox_use_sum.pack()

        self.btn_totalEnergyBalance = tk.Button(self, text="Total energy balance",
                                                command=self.plot_total_energy_balance)
        self.btn_totalEnergyBalance.pack(pady=(40, 0))

        self.btn_totalEnergyBalanceTrendEliminate = tk.Button(self, text="Trend eliminate total energy balance",
                                                command=self.plot_trend_eliminate_total_energy_balance)
        self.btn_totalEnergyBalanceTrendEliminate.pack(pady=(10, 0))

        self.lbl_show_ablation = tk.Label(self, text="Show measured ablation", state="normal")
        self.lbl_show_ablation.pack()

        self.ckbox_show_ablation_value = tk.IntVar()
        self.ckbox_show_ablation = tk.Checkbutton(self, variable=self.ckbox_show_ablation_value, state="normal")
        self.ckbox_show_ablation.pack()

        listbox_option = [
            "sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "sensible_heat",
            "latent_heat",
        ]

        self.listbox_selectedComponents = tk.Listbox(self, selectmode="multiple")
        for option in listbox_option:
            self.listbox_selectedComponents.insert(tk.END, option)

        self.listbox_selectedComponents.pack(pady=(30, 0))

        self.btn_energySelectedComponents = tk.Button(self, text="Energy selected components",
                                                command=self.plot_selected_components)
        self.btn_energySelectedComponents.pack()

        self.btn_trendEliminateSelectedComponents = tk.Button(self, text="Trend eliminate selected components",
                                                      command=self.plot_trend_eliminate_selected_components)
        self.btn_trendEliminateSelectedComponents.pack()

    def enable_option_to_use_summed_measurements(self):
        fc.set_widget_state([self.lbl_use_sum, self.ckbox_use_sum], "normal")

    def plot_total_energy_balance(self):
        visualizer.singleton.plot_total_energy_balance(bool(self.ckbox_use_sum_value.get()),
                                                       bool(self.ckbox_show_ablation_value.get()))

    def plot_trend_eliminate_total_energy_balance(self):
        visualizer.singleton.plot_periodic_trend_eliminated_total_energy_balance(bool(self.ckbox_use_sum_value.get()))

    def plot_selected_components(self):
        visualizer.singleton.plot_energy_balance_components(
            [self.listbox_selectedComponents.get(opt) for opt in self.listbox_selectedComponents.curselection()],
            bool(self.ckbox_use_sum_value.get()), bool(self.ckbox_show_ablation_value.get())
        )

    def plot_trend_eliminate_selected_components(self):
        visualizer.singleton.plot_periodic_trend_eliminated_selected_option(
            [self.listbox_selectedComponents.get(opt) for opt in self.listbox_selectedComponents.curselection()],
            bool(self.ckbox_use_sum_value.get())
        )


singleton = None


def create_singleton():
    global singleton
    singleton = PlotFrame()  # yet to be initialized
