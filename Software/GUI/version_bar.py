import tkinter as tk
import sys

sys.path.append("GUI")

import frame_read
import frame_energy_balance
import frame_download
import frame_plot
import gui_main_frame
import frame_sum
from manage_config import cfg


class VersionBar(tk.Frame):
    """
    TODO
    """
    singleton_created = False

    def __init__(self):
        if VersionBar.singleton_created:
            raise Exception("NavigationBar is a singleton")
        VersionBar.singleton_created = True

        tk.Frame.__init__(self, gui_main_frame.singleton.frame)

        if int(cfg["PRO_VERSION"]):
            version_appendix = "Professional Edition:"
        else:
            version_appendix = "Community Edition:"

        self.__lbl_version_number = tk.Label(self, text=version_appendix + ' Version ' + cfg["VERSION"])
        self.__lbl_version_number.pack(side="left", padx=5, pady=2)

        self.grid_propagate(False)

        self.grid(row=1, column=0, sticky="nsew")


singleton = None


def create_singleton():
    global singleton
    singleton = VersionBar()
