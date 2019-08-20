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
from GUI.gui_main import GUImain
import threading
import multiple_measurements
import reader
import numpy as np
import GUI.gui_main as gui_main
import visualizer


class Manager:
    def __init__(self):
        self.path_to_meteorologic_measurements = cfg["DATA_PATH"]
        self.startTime = "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"

    def read(self):

        reader.singleton.add_file_path(self.path_to_meteorologic_measurements)

        multiple_measurements.singleton.fetch_measurements_metadata()

        reader.singleton.read_meterologic_file_to_objects(starttime=None,
                                                          endtime=None,
                                                          resolution_by_percentage=10,
                                                          resolution_by_time_interval=None)

        # meteorologic_measurements.change_measurement_resolution_by_percentage(1)
        # meteorologic_measurements.change_measurement_resolution_by_time_interval(dt.timedelta(days=1))

    def calculate(self):

        multiple_measurements.singleton.calculate_energy_balance_for_all()
        # multiple_measurements.singleton.sum_measurements_by_amount(30)

        multiple_measurements.singleton.sum_measurements_by_time_interval(dt.timedelta(days=5))

    def visualize(self):
        # print("BALA")
        # visualizer.plot_total_energy_balance()
        # visualizer.singleton.plot_summed_total_energy_balance()

        visualizer.singleton.plot_periodic_trend_eliminated("total_energy_balance")
        visualizer.singleton.plot_periodic_trend_eliminated("sw_radiation_in")
        # visualizer.singleton.plot_periodic_trend_eliminated("sw_radiation_out")
        # visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_in")
        # visualizer.singleton.plot_periodic_trend_eliminated("lw_radiation_out")
        # visualizer.singleton.plot_periodic_trend_eliminated("sensible_heat")
        # visualizer.singleton.plot_periodic_trend_eliminated("latent_heat")

        # visualizer.plot_energy_balance_components(latent_heat=True)


if __name__ == "__main__":
    if cfg["NO_GUI"]:
        manager = Manager()
        manager.read()
        manager.calculate()
        manager.visualize()

    else:
        if os.name != 'posix':
            gui_main.singleton.lift()
            try:  # TODO yet to test on all different windows versions
                gui_main.singleton.state('zoomed')
            except:
                pass

        gui_thread = threading.Thread(target=gui_main.singleton.mainloop())
        gui_thread.start()

        # gui_main.singleton.mainloop()
