"""
This software was written for a bachelor thesis in 2019
The title of the bachelor thesis is "Energiebilanz im Ablationsgebiet der Pasterze"
The thesis can be found via TODO

TODO Rights .. open source .. and that stuff

@autor Manuel Theurl
"""

from reader import Reader
from manage_config import cfg
from multiple_measurements import MultipleMeasurements
from visualizer import Visualize


class Runner:
    def __init__(self):
        self.path_to_meteorologic_measurements = cfg["DATA_PATH"]
        self.startTime = "2015-10-18 05:30:00"  # "2012-10-18 05:30:00"
        self.endTime = "2019-01-27 09:00:00"  # "2019-06-27 09:00:00"

    def run(self):
        reader = Reader(self.path_to_meteorologic_measurements)

        meteorologic_measurements = MultipleMeasurements()

        reader.read_meterologic_file_to_objects(meteorologic_measurements, starttime=self.startTime,
                                                endtime=self.endTime)

        meteorologic_measurements.calculate_energy_balance_for_all()

        visualizer = Visualize(meteorologic_measurements)

        visualizer.plot_energy_balance_components(sensible_heat=True, latent_heat=True)


if __name__ == "__main__":
    runner = Runner()
    runner.run()
