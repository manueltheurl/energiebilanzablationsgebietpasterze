from single_measurement import SingleMeasurement
import datetime as dt
from manage_config import cfg
import multiple_measurements
import functions as fc


class Reader:
    singleton_created = False

    def __init__(self):
        if Reader.singleton_created:
            raise Exception("Reader is a singleton")
        Reader.singleton_created = True

        self.__file_path = None
        self.delimiter = ","
        self.no_data = "NULL"
        self.valid_flags = ["0", "1", "3"]  # 0: not sure, 1: correct, 2: not correct, 3: doubts, 255: not measured
        self.number_of_data_attributes = 16

        self.__file_metadata = {
            "time_resolution": None,  # warning: this is determined by the time diff of the first two measurements only
            "time_of_first_measurement": None,
            "time_of_last_measurement": None
        }

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

            try:
                last_line_parts = file.readlines()[-1].split(self.delimiter)
            except:
                print("TODO whats that error here? ")
                last_line_parts = file.readlines()[-2].split(self.delimiter)

            datetime_first_measurement = fc.string_date_to_datetime(first_line_parts[0])
            datetime_second_measurement = fc.string_date_to_datetime(second_line_parts[0])
            datetime_last_measurement = fc.string_date_to_datetime(last_line_parts[0])

            return [
                datetime_second_measurement - datetime_first_measurement,
                datetime_first_measurement,
                datetime_last_measurement
            ]

    def fetch_file_metadata(self):
        time_resolution, time_of_first_measure, time_of_last_measure = self.read_measurements_metadata()
        self.__set_file_metadata(time_resolution, time_of_first_measure, time_of_last_measure)

    def __set_file_metadata(self, time_resolution, time_of_first_measurement, time_of_last_measurement):
        self.__file_metadata["time_resolution"] = time_resolution
        self.__file_metadata["time_of_first_measurement"] = time_of_first_measurement
        self.__file_metadata["time_of_last_measurement"] = time_of_last_measurement

    def get_single_file_metadata(self, key):
        return self.__file_metadata[key]

    def read_meterologic_file_to_objects(self, starttime=None,
                                         endtime=None, resolution_by_percentage=None, resolution_by_time_interval=None,
                                         resolution_by_months=None, resolution_by_years=None):

        multiple_measurements.singleton.reset_scope_to_none()  # reset
        multiple_measurements.singleton.clear_all_single_measurements()  # reset
        multiple_measurements.singleton.clear_summed_measurements()  # reset
        percentage_threshold = None
        reference_month = None  # used if resolution_by_months is not None
        reference_year = None  # used if resolution_by_years is not None

        if starttime is not None:
            if type(starttime) is str:
                starttime = dt.datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
        if endtime is not None:
            if type(starttime) is str:
                endtime = dt.datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")
        if resolution_by_percentage is not None:
            percentage_threshold = 100  # so that first one is always there
        if resolution_by_time_interval is not None:
            resolution_reference_time = None  # TODO does it matter if startime is far in the past?

        with open(self.__file_path) as file:
            next(file)  # skip first line, contains description of values not actual data

            for line in file:  # nasty .. line ends with
                parts = line[:-1].split(self.delimiter)  # gets rid of linebreak in the end first

                if len(parts) < self.number_of_data_attributes:  # plausibility check
                    continue

                datetime = fc.string_date_to_datetime(parts[0])  # double quotes around date

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

                    if percentage_threshold is not None:
                        percentage_threshold += resolution_by_percentage
                        if percentage_threshold >= 100:
                            percentage_threshold %= 100
                        else:
                            continue

                    # only one of that events can occur
                    if resolution_by_time_interval is not None:
                        if resolution_reference_time is None:  # first time .. no reference time there
                            resolution_reference_time = datetime
                        else:  # all the following times
                            if datetime - resolution_reference_time >= resolution_by_time_interval:
                                resolution_reference_time = datetime
                            else:
                                continue

                    elif resolution_by_months is not None:
                        if reference_month is None:
                            reference_month = datetime.month
                        elif fc.get_difference_of_months(reference_month, datetime.month) < resolution_by_months:
                            continue
                        else:
                            reference_month = datetime.month

                    elif resolution_by_years is not None:
                        if reference_year is None:
                            reference_year = datetime.year
                        elif datetime.year - reference_year < resolution_by_years:
                            continue
                        else:
                            reference_year = datetime.year

                    if False:
                        air_pressure_hpa = self.convert_to_float_or_none(parts[6])
                        air_pressure_pa = None if air_pressure_hpa is None else air_pressure_hpa * 100
                        multiple_measurements.singleton.add_single_measurement(
                            SingleMeasurement(
                                datetime=datetime,
                                temperature=self.convert_to_float_or_none(parts[2]),
                                rel_moisture=self.convert_to_float_or_none(parts[3]),
                                wind_speed=self.convert_to_float_or_none(parts[4]),
                                wind_direction=self.convert_to_float_or_none(parts[5]),
                                air_pressure=air_pressure_pa,
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
                    else:
                        if True:
                            air_pressure_hpa = self.convert_to_float_or_none(parts[14]) if parts[
                                                                                               15] in self.valid_flags else None
                            air_pressure_pa = None if air_pressure_hpa is None else air_pressure_hpa * 100

                            # This could be summarized maybe .. cause its always the index after the actual data
                            temperature = self.convert_to_float_or_none(parts[2]) if parts[
                                                                                         3] in self.valid_flags else None
                            rel_moist = self.convert_to_float_or_none(parts[6]) if parts[
                                                                                       7] in self.valid_flags else None
                            windspeed = self.convert_to_float_or_none(parts[10]) if parts[
                                                                                        11] in self.valid_flags else None
                            winddir = self.convert_to_float_or_none(parts[12]) if parts[
                                                                                      13] in self.valid_flags else None

                            """ in measurement file negative measurements are invalid, yet they should be 0 for swi """
                            if parts[19] not in self.valid_flags:
                                sw_in = self.convert_to_float_or_none(parts[18])
                                if sw_in is not None and sw_in < 0:
                                    sw_in = 0
                            else:
                                sw_in = self.convert_to_float_or_none(parts[18])

                            sw_out = self.convert_to_float_or_none(parts[20], negative=True) if parts[
                                                                                                    21] in self.valid_flags else None
                            lw_in = self.convert_to_float_or_none(parts[22]) if parts[23] in self.valid_flags else None
                            lw_out = self.convert_to_float_or_none(parts[24], negative=True) if parts[
                                                                                                    25] in self.valid_flags else None
                            snow_depth = self.convert_to_float_or_none(parts[27]) if parts[28] in self.valid_flags else None
                            ablation = self.convert_to_float_or_none(parts[29]) if parts[30] in self.valid_flags else None

                            multiple_measurements.singleton.add_single_measurement(
                                SingleMeasurement(
                                    datetime=datetime,
                                    temperature=temperature,
                                    rel_moisture=rel_moist,
                                    wind_speed=windspeed,
                                    wind_direction=winddir,
                                    air_pressure=air_pressure_pa,
                                    sw_radiation_in=sw_in,
                                    sw_radiation_out=sw_out,
                                    lw_radiation_in=lw_in,
                                    lw_radiation_out=lw_out,
                                    zenith_angle=self.convert_to_float_or_none(parts[26]),  # no valid flag available
                                    tiltx=self.convert_to_float_or_none(parts[16]),  # no valid flag available
                                    tilty=self.convert_to_float_or_none(parts[17]),  # no valid flag available
                                    snow_depth=snow_depth,
                                    ablation=ablation
                                )
                            )
                        else:
                            air_pressure_hpa = self.convert_to_float_or_none(parts[14])
                            air_pressure_pa = None if air_pressure_hpa is None else air_pressure_hpa * 100

                            # The Flags could be taken into account as well TODO

                            multiple_measurements.singleton.add_single_measurement(
                                SingleMeasurement(
                                    datetime=datetime,
                                    temperature=self.convert_to_float_or_none(parts[2]),
                                    rel_moisture=self.convert_to_float_or_none(parts[6]),
                                    wind_speed=self.convert_to_float_or_none(parts[10]),
                                    wind_direction=self.convert_to_float_or_none(parts[12]),
                                    air_pressure=air_pressure_pa,
                                    sw_radiation_in=self.convert_to_float_or_none(parts[18]),
                                    sw_radiation_out=self.convert_to_float_or_none(parts[20], negative=True),
                                    lw_radiation_in=self.convert_to_float_or_none(parts[22]),
                                    lw_radiation_out=self.convert_to_float_or_none(parts[24], negative=True),
                                    zenith_angle=self.convert_to_float_or_none(parts[26]),
                                    tiltx=self.convert_to_float_or_none(parts[16]),
                                    tilty=self.convert_to_float_or_none(parts[17]),
                                    snow_depth=self.convert_to_float_or_none(parts[27]),
                                    ablation=self.convert_to_float_or_none(parts[29])
                                )
                            )

singleton = Reader()
