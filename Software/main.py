"""
This software was written for a bachelor thesis in 2019
The title of the bachelor thesis is "Energiebilanz im Ablationsgebiet der Pasterze"
The thesis can be found via TODO

TODO Rights .. open source .. and that stuff

@author Manuel Theurl
"""

from manage_config import cfg
import datetime as dt
import os
import threading
import multiple_measurements
import reader
import sys
import pickle
import numpy as np

sys.path.append("GUI")


# The gui is constructed as singletons .. this order therefor has to be maintained
import gui_main_frame as gui_main
import navigation_bar
import version_bar
import info_bar
import frame_plot
import frame_energy_balance
import frame_download
import frame_read
import frame_energy_balance as frame_scope
import frame_sum
import visualizer


if __name__ == "__main__":
    """
    Order matters here, cause all need the gui_main_frame
    So each singleton is saved in a singleton variable in the corresponding file. So every file can then access
    those singletons by including the module    
    """
    gui_main.create_singleton()
    navigation_bar.create_singleton()
    info_bar.create_singleton()
    frame_scope.create_singleton()
    frame_plot.create_singleton()
    frame_download.create_singleton()
    frame_sum.create_singleton()
    frame_read.create_singleton()
    version_bar.create_singleton()

    gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
    gui_thread.start()

    # gui_main.singleton.mainloop()
