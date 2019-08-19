import tkinter as tk
import visualizer
import multiple_measurements


class PlotFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.config(bg="black")
        self.grid_propagate(False)

        button1 = tk.Button(self, text="Plot total energy balance", command=visualizer.singleton.plot_total_energy_balance)
        button1.pack()

        button2 = tk.Button(self, text="Plot summed total energy balance",
                           command=visualizer.singleton.plot_summed_total_energy_balance)
        button2.pack()

        button3 = tk.Button(self, text="Plot summed total energy balance",
                               command=visualizer.singleton.plot_summed_total_energy_balance)
        button3.pack()

