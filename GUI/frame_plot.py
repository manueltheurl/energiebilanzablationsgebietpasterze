import tkinter as tk
import GUI.gui_main_frame as gui_main_frame
import visualizer
from tkinter import ttk


class ModelFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self):
        tk.Frame.__init__(self, gui_main_frame.singleton.frame)
        self.grid(row=0, column=0, sticky="nsew")

        self.lbl_visualize = tk.Label(self, text="Visualize")
        self.lbl_visualize.pack(padx=30)

        self.btn_totalEnergyBalance = tk.Button(self, text="Total energy balance",
                                                command=self.plot_total_energy_balance)
        self.btn_totalEnergyBalance.pack()

        # button2 = tk.Button(self, text="Plot summed total energy balance",
        #                     command=visualizer.singleton.plot_summed_total_energy_balance)
        # button2.pack()
        #
        # button3 = tk.Button(self, text="Plot summed total energy balance",
        #                     command=visualizer.singleton.plot_summed_total_energy_balance)
        # button3.pack()

    def plot_total_energy_balance(self):
        visualizer.singleton.plot_total_energy_balance()


singleton = None


def create_singleton():
    global singleton
    singleton = ModelFrame()  # yet to be initialized
