"""
This software was written for a bachelor thesis in 2019
The title of the bachelor thesis is "Energiebilanz im Ablationsgebiet der Pasterze"
The thesis can be found via TODO

TODO Rights .. open source .. and that stuff

@author Manuel Theurl
"""

from reader import Reader
from manage_config import cfg
from multiple_measurements import MultipleMeasurements
from visualizer import Visualize
import datetime as dt
import os
from GUI.gui_main import GUImain
import threading
import multiple_measurements


class Manager:
    def __init__(self):
        self.path_to_meteorologic_measurements = cfg["DATA_PATH"]
        self.startTime = "2018-10-18 13:30:00"  # "2012-10-18 05:30:00"
        self.endTime = "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"

    def run(self):
        reader = Reader()
        reader.add_file_path(self.path_to_meteorologic_measurements)

        reader.read_meterologic_file_to_objects(starttime=self.startTime,
                                                endtime=self.endTime,
                                                resolution_by_percentage=100,
                                                resolution_by_time_interval=dt.timedelta(minutes=10))

        # meteorologic_measurements.change_measurement_resolution_by_percentage(1)
        # meteorologic_measurements.change_measurement_resolution_by_time_interval(dt.timedelta(days=1))

        multiple_measurements.singleton.calculate_energy_balance_for_all()

        visualizer = Visualize(multiple_measurements.singleton)

        # visualizer.plot_total_energy_balance()
        visualizer.plot_energy_balance_components(sw_radiation_out=True)


if __name__ == "__main__":
    manager = Manager()
    gui = GUImain(manager)

    if os.name != 'posix':
        gui.lift()
        try:  # TODO yet to test on all different windows versions
            gui.state('zoomed')
        except:
            pass

    gui_thread = threading.Thread(target=gui.mainloop())
    gui_thread.start()
