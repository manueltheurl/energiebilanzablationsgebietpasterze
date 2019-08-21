import tkinter as tk
import visualizer
import multiple_measurements
import functions as fc


class PlotFrame(tk.Frame):
    """
    Reserves the space for a main frame (3 in total) by creating a frame
    """
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        # self.config(bg="black")
        self.grid_propagate(False)

        self.lbl_currentScope = tk.Label(self, text="Change current scope of all read in measurements")
        self.lbl_currentScope.pack()

        self.ckbox_percentScope_value = tk.IntVar()
        self.ckbox_percentScope = tk.Checkbutton(self,
                                                  command=self.toggle_percent_scope,
                                                  variable=self.ckbox_percentScope_value, state="active")
        self.ckbox_percentScope.pack()

        self.lbl_percentScope = tk.Label(self, text="Percent to take from read in measurements")
        self.lbl_percentScope.pack()
        self.entry_percentScope = tk.Entry(self, state="disabled")
        self.entry_percentScope.pack()

        self.ckbox_timeintervalScope_value = tk.IntVar()
        self.ckbox_timeintervalScope = tk.Checkbutton(self,
                                                 command=self.toggle_time_interval_scope,
                                                 variable=self.ckbox_timeintervalScope_value, state="active")
        self.ckbox_timeintervalScope.pack()

        self.lbl_timeintervalScope = tk.Label(self, text="Percent to take from read in measurements")
        self.lbl_timeintervalScope.pack()
        self.entry_timeintervalScope = tk.Entry(self, state="disabled")
        self.entry_timeintervalScope.pack()

        self.btn_changeCurrentScope = tk.Button(self,
                                                text="Change current scope",
                                                command=self.change_current_scope,
                                                state="active")
        self.btn_changeCurrentScope.pack()

        self.btn_calcEnergyBalance = tk.Button(self,
                                               text="Calculate Energy Balance",
                                               command=multiple_measurements.singleton.calculate_energy_balance_for_all,
                                               state="active")
        self.btn_calcEnergyBalance.pack()

        #  --> TODO
        button1 = tk.Button(self, text="Plot total energy balance", command=visualizer.singleton.plot_total_energy_balance)
        button1.pack()

        button2 = tk.Button(self, text="Plot summed total energy balance",
                           command=visualizer.singleton.plot_summed_total_energy_balance)
        button2.pack()

        button3 = tk.Button(self, text="Plot summed total energy balance",
                               command=visualizer.singleton.plot_summed_total_energy_balance)
        button3.pack()

    def toggle_percent_scope(self):
        widgets_to_toggle_state = [
            self.entry_percentScope
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_percentScope_value.get())

    def toggle_time_interval_scope(self):
        widgets_to_toggle_state = [
            self.entry_timeintervalScope
        ]

        fc.set_widget_state(widgets_to_toggle_state, self.ckbox_timeintervalScope_value.get())

    def change_current_scope(self):
        percent_scope = None
        if self.ckbox_percentScope_value.get():
            percent_scope = self.entry_percentScope.get()

        timeinterval_scope = None
        if self.ckbox_timeintervalScope_value.get():
            timeinterval_scope = self.entry_timeintervalScope.get()

