from single_measurement import SingleMeasurement
from datetime import datetime as dt
from manage_config import cfg
import multiple_measurements
import GUI.info_bar as info_bar
import GUI.gui_main as gui_main
import GUI.frame_plot as frame_plot


class Reader:
    singleton_created = False

    def __init__(self):
        if Reader.singleton_created:
            raise Exception("Reader is a singleton")
        Reader.singleton_created = True

        self.__file_path = None
        self.delimiter = ","
        self.no_data = "NULL"
        self.number_of_data_attributes = 16

    def add_file_path(self, filepath):
        self.__file_path = filepath

    def convert_to_float_or_none(self, data_string, negative=False):
        if self.no_data in data_string:  # can be NULL\n as well
            return None

        if negative:
            return - float(data_string)
        return float(data_string)

    def read_measurements_metadata(self):
        with open(self.__file_path) as file:
            next(file)  # skip first line, contains no data
            first_line_parts = next(file).split(self.delimiter)
            second_line_parts = next(file).split(self.delimiter)
            last_line_parts = file.readlines()[-2].split(self.delimiter)  # TODO better way to find last actual data line?

            datetime_first_measurement = dt.strptime(first_line_parts[0], "\"%Y-%m-%d %H:%M:%S\"")
            datetime_second_measurement = dt.strptime(second_line_parts[0], "\"%Y-%m-%d %H:%M:%S\"")
            datetime_last_measurement = dt.strptime(last_line_parts[0], "\"%Y-%m-%d %H:%M:%S\"")

            return [
                datetime_second_measurement - datetime_first_measurement,
                datetime_first_measurement,
                datetime_last_measurement
            ]

    def read_meterologic_file_to_objects(self, starttime=None,
                                         endtime=None, resolution_by_percentage=None, resolution_by_time_interval=None):

        if starttime is not None:
            starttime = dt.strptime(starttime, "%Y-%m-%d %H:%M:%S")
        if endtime is not None:
            endtime = dt.strptime(endtime, "%Y-%m-%d %H:%M:%S") if endtime is not None else None
        if resolution_by_percentage is not None:
            percentage_threshold = 0
        if resolution_by_time_interval is not None:
            resolution_reference_time = None  # TODO does it matter if startime is widely in the past?

        with open(self.__file_path) as file:
            next(file)  # skip first line, contains description of values not actual data

            for _ in range(cfg["SKIP_LINES"]):  # TODO just for testing
                next(file)

            i = 0  # number of read in measurements
            for line in file:
                parts = line.split(self.delimiter)

                if len(parts) < self.number_of_data_attributes:  # plausibility check
                    continue

                datetime = dt.strptime(parts[0], "\"%Y-%m-%d %H:%M:%S\"")  # double quotes around date

                if starttime is not None and endtime is not None:
                    time_condition = starttime <= datetime <= endtime
                elif starttime is None and endtime is None:
                    time_condition = True
                elif starttime is None and endtime is not None:
                    time_condition = datetime <= endtime
                elif starttime is not None and endtime is None:
                    time_condition = starttime <= datetime
                else:  # never should get here
                    time_condition = False

                if time_condition:

                    if resolution_by_percentage is not None:
                        percentage_threshold += resolution_by_percentage
                        if percentage_threshold >= 100:
                            percentage_threshold = 0
                        else:
                            continue

                    if resolution_by_time_interval is not None:
                        if resolution_reference_time is None:  # first time .. no reference time there
                            resolution_reference_time = datetime
                        else:  # all the following times
                            if datetime - resolution_reference_time >= resolution_by_time_interval:
                                resolution_reference_time = datetime
                            else:
                                continue

                    multiple_measurements.singleton.add_single_measurement(
                        SingleMeasurement(
                            datetime=datetime,
                            temperature=self.convert_to_float_or_none(parts[2]),
                            rel_moisture=self.convert_to_float_or_none(parts[3]),
                            wind_speed=self.convert_to_float_or_none(parts[4]),
                            wind_direction=self.convert_to_float_or_none(parts[5]),
                            air_pressure=self.convert_to_float_or_none(parts[6]),
                            sw_radiation_in=self.convert_to_float_or_none(parts[7]),
                            sw_radiation_out=self.convert_to_float_or_none(parts[8], negative=True),
                            lw_radiation_in=self.convert_to_float_or_none(parts[9]),
                            lw_radiation_out=self.convert_to_float_or_none(parts[10], negative=True),
                            zenith_angle=self.convert_to_float_or_none(parts[11]),
                            tiltx=self.convert_to_float_or_none(parts[12]),
                            tilty=self.convert_to_float_or_none(parts[13]),
                            snow_depth=self.convert_to_float_or_none(parts[14]),
                            ablation=self.convert_to_float_or_none(parts[15])
                        )
                    )

                    i += 1

        return i


singleton = Reader()
