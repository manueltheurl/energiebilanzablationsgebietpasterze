import tkinter as tk
import sys

sys.path.append("GUI")

import frame_read
import frame_energy_balance
import frame_model
import frame_plot
import gui_main_frame
import frame_sum


class NavigationBar(tk.Frame):
    """
    TODO
    """
    singleton_created = False

    def __init__(self):
        if NavigationBar.singleton_created:
            raise Exception("NavigationBar is a singleton")
        NavigationBar.singleton_created = True

        tk.Frame.__init__(self, gui_main_frame.singleton)
        # self.config(bg="yellow")
        self.grid_propagate(False)

        self.__all_buttons = []

        self.btn_readframe = tk.Button(self, text="Read", command=self.show_read_frame)
        self.btn_readframe.pack(side="left")
        self.__all_buttons.append(self.btn_readframe)

        self.btn_energybalanceframe = tk.Button(self, text="Scope/Energy Balance", command=self.show_energy_balance_frame,
                                        state="disabled")
        self.btn_energybalanceframe.pack(side="left")
        self.__all_buttons.append(self.btn_energybalanceframe)

        self.btn_sumframe = tk.Button(self, text="Sum", command=self.show_sum_frame,
                                      state="disabled")
        self.btn_sumframe.pack(side="left")
        self.__all_buttons.append(self.btn_sumframe)

        self.btn_plotframe = tk.Button(self, text="Plot", command=self.show_plot_frame,
                                  state="disabled")
        self.btn_plotframe.pack(side="left")
        self.__all_buttons.append(self.btn_plotframe)

        self.btn_modelframe = tk.Button(self, text="Model", command=self.show_model_frame,
                                   state="disabled")
        self.btn_modelframe.pack(side="left")
        self.__all_buttons.append(self.btn_modelframe)

        self.pack(side="top", fill="both")

    def show_read_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_read)
        self.btn_readframe["state"] = "active"  # aint working

    def show_energy_balance_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_energy_balance)
        self.btn_energybalanceframe["state"] = "active"  # aint working

    def show_sum_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_sum)
        self.btn_sumframe["state"] = "active"  # aint working

    def show_plot_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_plot)
        self.btn_plotframe["state"] = "active"

    def show_model_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_model)
        self.btn_modelframe["state"] = "active"

    def __set_state_of_buttons_normal(self):
        for button in self.__all_buttons:
            if not button["state"] == "disabled":
                button["state"] = "normal"


singleton = None


def create_singleton():
    global singleton
    singleton = NavigationBar()

