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

    def add_single_measurement(self, single_measurement_objects):
        self.__current_index_scope.add(len(self.__all_single_measurement_objects))
        self.__all_single_measurement_objects.append(single_measurement_objects)

    def calculate_energy_balance_for_scope(self):
        print("calculating energy balance for current scope")
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]:
            obj.calculate_energy_balance()

    # def calculate_energy_balance_for_all(self):
    #     # function probably not even needed
    #     print("calculating energy balance for all")
    #     for obj in self.__all_single_measurement_objects:
    #         obj.calculate_energy_balance()

    def get_all_of(self, attribute_name, use_summed_measurements=False):
        if use_summed_measurements:
            return list(map(lambda obj: getattr(obj, attribute_name), self.__all_mean_measurements))

        else:
            return list(map(
                lambda obj: getattr(obj, attribute_name),
                # set messes with the order, sorted creates a list of the set
                [self.__all_single_measurement_objects[i] for i in sorted(self.__current_index_scope)]
            ))

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

    def get_measurement_amount(self, of="all"):
        if of == "summed":
            return len(self.__all_mean_measurements)
        elif of == "scope":
            return len(self.__current_index_scope)

        return len(self.__all_single_measurement_objects)

    def get_date_of_first_measurement(self, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "summed":
            return self.__all_mean_measurements[0].datetime_begin
        elif of == "scope":
            return self.__all_single_measurement_objects[sorted(self.__current_index_scope)[0]].datetime

        return self.__all_single_measurement_objects[0].datetime

    def get_date_of_last_measurement(self, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "summed":
            return self.__all_mean_measurements[-1].datetime_begin
        elif of == "scope":
            return self.__all_single_measurement_objects[sorted(self.__current_index_scope)[-1]].datetime

        return self.__all_single_measurement_objects[-1].datetime

    def get_time_resolution(self, of="all"):
        """
        Based on the first two measurements!
        :return Timedelta in minutes
        """

        if of == "summed":
            time_delta = self.__all_mean_measurements[1].datetime_begin - self.__all_mean_measurements[0].datetime_begin
        elif of == "scope":
            scope_indexes = sorted(self.__current_index_scope)
            time_delta = self.__all_single_measurement_objects[scope_indexes[1]].datetime - self.__all_single_measurement_objects[scope_indexes[0]].datetime
        else:
            time_delta = self.__all_single_measurement_objects[1].datetime - self.__all_single_measurement_objects[0].datetime

        return time_delta.seconds // 60


singleton = MultipleMeasurements()
