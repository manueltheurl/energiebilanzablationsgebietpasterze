import datetime as dt
import reader
from mean_measurement import MeanMeasurement


class MultipleMeasurements:
    singleton_created = False

    def __init__(self):
        if MultipleMeasurements.singleton_created:
            raise Exception("Reader is a singleton")
        MultipleMeasurements.singleton_created = True

        self.__all_single_measurement_objects = []
        self.__current_index_scope = set()  # current indexes that will be used are saved in here .. all by default

        self.__all_mean_measurements = []  # Empty in the beginning .. can later be calculated and used

        self.__measurement_metadata = {
            "time_resolution": None,  # warning: this is determined by the time diff of the first two measurements only
            "time_of_first_measurement": None,
            "time_of_last_measurement": None
        }

    def add_single_measurement(self, single_measurement_objects):
        self.__current_index_scope.add(len(self.__all_single_measurement_objects))
        self.__all_single_measurement_objects.append(single_measurement_objects)

    def fetch_measurements_metadata(self):
        time_resolution, time_of_first_measure, time_of_last_measure = reader.singleton.read_measurements_metadata()
        self.set_measurement_metadata(time_resolution, time_of_first_measure, time_of_last_measure)

    def set_measurement_metadata(self, time_resolution, time_of_first_measurement, time_of_last_measurement):
        self.__measurement_metadata["time_resolution"] = time_resolution
        self.__measurement_metadata["time_of_first_measurement"] = time_of_first_measurement
        self.__measurement_metadata["time_of_last_measurement"] = time_of_last_measurement

    def get_single_measurement_metadata(self, key):
        return self.__measurement_metadata[key]

    def calculate_energy_balance_for_all(self):
        for obj in self.__all_single_measurement_objects:
            obj.calculate_energy_balance()

    def get_all_of(self, attribute_name):
        return list(map(
            lambda obj: getattr(obj, attribute_name),
            # set messes with the order, sorted creates a list of the set
            [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]
        ))

    def mean_get_all_of(self, attribute_name):
        return list(map(lambda obj: getattr(obj, attribute_name), self.__all_mean_measurements))

    def sum_measurements_by_amount(self, amount):
        self.__all_mean_measurements.clear()

        scoped_measurements = [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]

        multiple_separated_measurements = [
            scoped_measurements[i:i+amount] for i in range(len(scoped_measurements) - amount + 1)
        ]

        for separated_measurements in multiple_separated_measurements:
            summed_measurement = MeanMeasurement()

            for single_measurement in separated_measurements:
                summed_measurement += single_measurement

            summed_measurement.calculate_mean()

            self.__all_mean_measurements.append(summed_measurement)

    def sum_measurements_by_time_interval(self, time_interval: dt.timedelta):
        self.__all_mean_measurements.clear()

        resolution_reference_time = None
        summed_measurement = MeanMeasurement()

        for single_measurement in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]:
            if resolution_reference_time is None:  # first time .. no reference time there
                resolution_reference_time = single_measurement.datetime

            # all the following times
            if single_measurement.datetime - resolution_reference_time >= time_interval:
                resolution_reference_time = single_measurement.datetime

                summed_measurement.calculate_mean()
                self.__all_mean_measurements.append(summed_measurement)

                # reset summed_measurement and add current to it
                summed_measurement = MeanMeasurement()
                summed_measurement += single_measurement

            else:
                summed_measurement += single_measurement

    def reset_scope_to_all(self):
        self.__current_index_scope = set(range(len(self.__all_single_measurement_objects)))

    def change_measurement_resolution_by_time_interval(self, time_interval: dt.timedelta):
        """
        TODO
        :param time_interval:
        :return:
        """
        indexes_to_remove = set()
        reference_time = self.__all_single_measurement_objects[0].datetime

        for index in self.__current_index_scope:
            current_time = self.__all_single_measurement_objects[index].datetime

            if current_time - reference_time >= time_interval:
                reference_time = current_time
            else:
                indexes_to_remove.add(index)

        self.__current_index_scope.difference_update(indexes_to_remove)

    def change_measurement_resolution_by_percentage(self, percentage: int):
        """

        :param percentage: reaching from 0 to 100
        :return:
        """
        threshold = 0
        indexes_to_remove = set()

        for index in self.__current_index_scope:
            threshold += percentage
            if threshold >= 100:
                threshold = 0
            else:
                indexes_to_remove.add(index)  # if not a member, a KeyError is raised

        self.__current_index_scope.difference_update(indexes_to_remove)

    def get_measurement_amount(self, summed=False):
        if summed:
            return len(self.__all_mean_measurements)

        return len(self.__all_single_measurement_objects)

    def get_date_of_first_measurement(self, summed=False):
        # this presupposes that the measurements are read in sorted ascending by date
        if summed:
            return self.__all_mean_measurements[0].datetime_begin
        return self.__all_single_measurement_objects[0].datetime

    def get_date_of_last_measurement(self, summed=False):
        # this presupposes that the measurements are read in sorted ascending by date
        if summed:
            return self.__all_mean_measurements[-1].datetime_begin
        return self.__all_single_measurement_objects[-1].datetime


singleton = MultipleMeasurements()
