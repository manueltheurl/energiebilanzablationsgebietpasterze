import tkinter as tk
import sys

sys.path.append("GUI")

import frame_read
import frame_scope
import frame_energy_balance
import frame_download
import frame_plot
import gui_main_frame
import frame_sum
import frame_prepare_measurements


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

        self.btn_scopeframe = tk.Button(self, text="Scope",
                                                command=self.show_scope_frame, state="disabled")
        self.btn_scopeframe.pack(side="left")
        self.__all_buttons.append(self.btn_scopeframe)

        self.btn_prepareframe = tk.Button(self, text="Prepare", command=self.show_prepare_frame,
                                      state="disabled")
        self.btn_prepareframe.pack(side="left")
        self.__all_buttons.append(self.btn_prepareframe)

        self.btn_energybalanceframe = tk.Button(self, text="Energy balance",
                                                command=self.show_energy_balance_frame, state="disabled")
        self.btn_energybalanceframe.pack(side="left")
        self.__all_buttons.append(self.btn_energybalanceframe)

        self.btn_sumframe = tk.Button(self, text="Sum", command=self.show_sum_frame,
                                      state="disabled")
        self.btn_sumframe.pack(side="left")
        self.__all_buttons.append(self.btn_sumframe)

        self.btn_plotframe = tk.Button(self, text="Plot", command=self.show_plot_frame, state="disabled")
        self.btn_plotframe.pack(side="left")
        self.__all_buttons.append(self.btn_plotframe)

        self.btn_downloadframe = tk.Button(self, text="Download", command=self.show_download_frame, state="disabled")
        self.btn_downloadframe.pack(side="left")
        self.__all_buttons.append(self.btn_downloadframe)

        self.pack(side="top", fill="both")

    def show_read_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_read)
        self.btn_readframe["state"] = "active"

    def show_scope_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_scope)
        self.btn_scopeframe["state"] = "active"
        self.btn_prepareframe["state"] = "normal"

    def show_energy_balance_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_energy_balance)
        self.btn_energybalanceframe["state"] = "active"

    def show_prepare_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_prepare_measurements)
        self.btn_prepareframe["state"] = "active"

    def show_sum_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_sum)
        self.btn_sumframe["state"] = "active"
        self.btn_plotframe["state"] = "normal"

    def show_plot_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_plot)
        self.btn_plotframe["state"] = "active"

    def show_download_frame(self):
        self.__set_state_of_buttons_normal()
        gui_main_frame.singleton.show_main_frame(frame_download)
        self.btn_downloadframe["state"] = "active"

    def __set_state_of_buttons_normal(self):
        for button in self.__all_buttons:
            if not button["state"] == "disabled":
                button["state"] = "normal"


singleton = None


def create_singleton():
    global singleton
    singleton = NavigationBar()
