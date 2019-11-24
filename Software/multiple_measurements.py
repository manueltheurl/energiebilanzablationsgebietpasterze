import datetime as dt
from mean_measurement import MeanMeasurement
import functions as fc
import os
from manage_config import cfg
import csv


class MultipleMeasurements:
    singleton_created = False

    def __init__(self):
        if MultipleMeasurements.singleton_created:
            raise Exception("Reader is a singleton")
        MultipleMeasurements.singleton_created = True

        self.__all_single_measurement_objects = []
        self.__current_single_index_scope = set()  # current indexes that will be used are saved in here; default: all

        self.__all_mean_measurements = []  # Empty in the beginning .. can later be calculated and used
        self.__current_mean_index_scope = set()

    def clear_all_single_measurements(self):
        self.__all_single_measurement_objects = []

    def add_single_measurement(self, single_measurement_object):
        self.__current_single_index_scope.add(len(self.__all_single_measurement_objects))
        self.__all_single_measurement_objects.append(single_measurement_object)

    def add_summed_measurement(self, summed_measurement_object):
        self.__current_mean_index_scope.add(len(self.__all_mean_measurements))
        self.__all_mean_measurements.append(summed_measurement_object)

    def calculate_energy_balance_for_scope(self, simulate_global_dimming_brightening=0):
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            obj.calculate_energy_balance(simulate_global_dimming_brightening)

    def cumulate_ablation_for_scope(self):
        old_ablation_value = None
        current_subtractive = 0

        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if obj.ablation is not None:
                if old_ablation_value is None:
                    old_ablation_value = obj.ablation
                else:
                    if old_ablation_value < obj.ablation - float(cfg["ABLATION_THRESHOLD_FOR_UNNATURALITY"]):
                        current_subtractive += obj.ablation - old_ablation_value
                    elif old_ablation_value > obj.ablation + float(cfg["ABLATION_THRESHOLD_FOR_UNNATURALITY"]):
                        continue  # cant be either .. first drop of ablation when picking up station

                    old_ablation_value = obj.ablation
                    obj.cumulated_ablation = obj.ablation - current_subtractive

    def check_for_snow_covering_for_scope(self):
        # cumulate_ablation_for_scope has to be called before
        # TODO think of something good here

        # for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
        #     if obj.cumulated_ablation is not None:
        #         pass
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if 6 <= obj.datetime.month <= 8:
                obj.is_snow_covered = False
            else:
                obj.is_snow_covered = True

    def convert_energy_balance_to_water_equivalent_for_scope(self):
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            obj.calculate_theoretical_melt_rate()

    def get_all_of(self, attribute_name, use_summed_measurements=False):
        if use_summed_measurements:
            return list(map(
                lambda obj: getattr(obj, attribute_name),
                # set messes with the order, sorted creates a list of the set
                [self.__all_mean_measurements[i] for i in sorted(self.__current_mean_index_scope)]
            ))
        else:
            return list(map(
                lambda obj: getattr(obj, attribute_name),
                # set messes with the order, sorted creates a list of the set
                [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]
            ))

    def sum_measurements_by_amount(self, amount):
        self.clear_summed_measurements()

        scoped_measurements = [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]
        multiple_separated_measurements = [scoped_measurements[x:x + amount] for x in range(0, len(scoped_measurements), amount)]

        # for moving average this could be used  # TODO make another option maybe
        # multiple_separated_measurements = [
        #     scoped_measurements[i:i + amount] for i in range(len(scoped_measurements) - amount + 1)
        # ]

        for i, separated_measurements in enumerate(multiple_separated_measurements):
            summed_measurement = MeanMeasurement()

            for single_measurement in separated_measurements:
                summed_measurement += single_measurement

            try:
                summed_measurement.calculate_mean(
                    endtime=multiple_separated_measurements[i+1][0].datetime,
                    end_ablation=multiple_separated_measurements[i+1][0].cumulated_ablation)
            except IndexError:
                # last one
                summed_measurement.calculate_mean(
                    endtime=separated_measurements[-1].datetime,
                    end_ablation=separated_measurements[-1].cumulated_ablation)

            self.add_summed_measurement(summed_measurement)

    def clear_summed_measurements(self):
        self.__all_mean_measurements.clear()
        self.__current_mean_index_scope.clear()

    def sum_measurements_by_time_interval(self, time_interval: dt.timedelta):
        self.clear_summed_measurements()

        resolution_reference_time = None
        summed_measurement = MeanMeasurement()

        for single_measurement in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if resolution_reference_time is None:  # first time .. no reference time there
                resolution_reference_time = single_measurement.datetime

            # all the following times
            if single_measurement.datetime - resolution_reference_time >= time_interval:
                resolution_reference_time = single_measurement.datetime

                summed_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ablation)
                self.add_summed_measurement(summed_measurement)

                # reset summed_measurement and add current to it
                summed_measurement = MeanMeasurement()
                summed_measurement += single_measurement

            else:
                summed_measurement += single_measurement

    def sum_measurements_by_months(self, months):
        self.clear_summed_measurements()

        reference_month = None
        summed_measurement = MeanMeasurement()

        for single_measurement in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if reference_month is None:  # first time .. no reference time there
                reference_month = single_measurement.datetime.month

            # all the following times
            if fc.get_difference_of_months(reference_month, single_measurement.datetime.month) < months:
                summed_measurement += single_measurement
            else:
                reference_month = single_measurement.datetime.month

                summed_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ablation)
                self.add_summed_measurement(summed_measurement)

                # reset summed_measurement and add current to it
                summed_measurement = MeanMeasurement()
                summed_measurement += single_measurement

    def sum_measurements_by_years(self, years):
        self.clear_summed_measurements()

        reference_years = None
        summed_measurement = MeanMeasurement()

        for single_measurement in [self.__all_single_measurement_objects[i] for i in
                                   sorted(self.__current_single_index_scope)]:
            if reference_years is None:  # first time .. no reference time there
                reference_years = single_measurement.datetime.year

            # all the following times
            if fc.get_difference_of_months(reference_years, single_measurement.datetime.year) < years:
                summed_measurement += single_measurement
            else:
                reference_years = single_measurement.datetime.year

                summed_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ablation)
                self.add_summed_measurement(summed_measurement)

                # reset summed_measurement and add current to it
                summed_measurement = MeanMeasurement()
                summed_measurement += single_measurement

    def reset_scope_to_all(self):
        self.__current_single_index_scope = set(range(len(self.__all_single_measurement_objects)))
        self.__current_mean_index_scope = set(range(len(self.__all_mean_measurements)))

    def reset_scope_to_none(self):
        self.__current_single_index_scope = set()
        self.__current_mean_index_scope = set()

    def change_measurement_scope_by_time_interval(self, time_interval: dt.timedelta):
        """
        TODO
        :param time_interval:
        :return:
        """
        indexes_to_remove = set()
        reference_time = self.__all_single_measurement_objects[0].datetime

        for index in list(self.__current_single_index_scope)[1:]:
            current_time = self.__all_single_measurement_objects[index].datetime

            if current_time - reference_time >= time_interval:
                reference_time = current_time
            else:
                indexes_to_remove.add(index)

        self.__current_single_index_scope.difference_update(indexes_to_remove)

        if self.__all_mean_measurements:
            indexes_to_remove = set()
            reference_time = self.__all_mean_measurements[0].datetime

            for index in list(self.__current_mean_index_scope)[1:]:
                current_time = self.__all_mean_measurements[index].datetime

                if current_time - reference_time >= time_interval:
                    reference_time = current_time
                else:
                    indexes_to_remove.add(index)

            self.__current_mean_index_scope.difference_update(indexes_to_remove)

    def change_measurement_scope_by_months(self, months):
        indexes_to_remove = set()
        reference_month = self.__all_single_measurement_objects[0].datetime.month

        for index in list(self.__current_single_index_scope)[1:]:
            current_month = self.__all_single_measurement_objects[index].datetime.month

            if fc.get_difference_of_months(reference_month, current_month) < months:
                indexes_to_remove.add(index)
            else:
                reference_month = current_month

        self.__current_single_index_scope.difference_update(indexes_to_remove)

        if self.__all_mean_measurements:
            indexes_to_remove = set()
            reference_month = self.__all_mean_measurements[0].datetime.month

            for index in list(self.__current_mean_index_scope)[1:]:
                current_month = self.__all_mean_measurements[index].datetime.month

                if fc.get_difference_of_months(reference_month, current_month) < months:
                    indexes_to_remove.add(index)
                else:
                    reference_month = current_month

            self.__current_mean_index_scope.difference_update(indexes_to_remove)

    def change_measurement_scope_by_years(self, years):
        indexes_to_remove = set()
        reference_year = self.__all_single_measurement_objects[0].datetime.year

        for index in list(self.__current_single_index_scope)[1:]:
            current_year = self.__all_single_measurement_objects[index].datetime.year

            if current_year - reference_year < years:
                indexes_to_remove.add(index)
            else:
                reference_year = current_year

        self.__current_single_index_scope.difference_update(indexes_to_remove)

        if self.__all_mean_measurements:
            indexes_to_remove = set()
            reference_year = self.__all_mean_measurements[0].datetime.year

            for index in list(self.__current_mean_index_scope)[1:]:
                current_year = self.__all_mean_measurements[index].datetime.year

                if current_year - reference_year < years:
                    indexes_to_remove.add(index)
                else:
                    reference_year = current_year

            self.__current_mean_index_scope.difference_update(indexes_to_remove)

    def change_measurement_scope_by_percentage(self, percentage: int):
        """

        :param percentage: reaching from 0 to 100
        :return:
        """
        threshold = 100  # so that first one is always there
        indexes_to_remove = set()

        for index in self.__current_single_index_scope:
            threshold += percentage
            if threshold >= 100:
                threshold %= 100
            else:
                indexes_to_remove.add(index)  # if not a member, a KeyError is raised

        self.__current_single_index_scope.difference_update(indexes_to_remove)

        if self.__all_mean_measurements:
            threshold = 100  # so that first one is always there
            indexes_to_remove = set()

            for index in self.__current_mean_index_scope:
                threshold += percentage
                if threshold >= 100:
                    threshold %= 100
                else:
                    indexes_to_remove.add(index)  # if not a member, a KeyError is raised

            self.__current_mean_index_scope.difference_update(indexes_to_remove)

    def change_measurement_resolution_by_start_end_time(self, starttime=None, endtime=None):
        if starttime is not None:
            if type(starttime) != dt.datetime:
                starttime = dt.datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
        if endtime is not None:
            if type(endtime) != dt.datetime:
                endtime = dt.datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")

        indexes_to_remove = set()

        if starttime is not None or endtime is not None:
            for index in self.__current_single_index_scope:
                if starttime is not None:
                    if starttime > self.__all_single_measurement_objects[index].datetime:
                        indexes_to_remove.add(index)

                if endtime is not None:
                    if endtime < self.__all_single_measurement_objects[index].datetime:
                        indexes_to_remove.add(index)

        self.__current_single_index_scope.difference_update(indexes_to_remove)

        if self.__all_mean_measurements:
            indexes_to_remove = set()

            if starttime is not None or endtime is not None:
                for index in self.__current_mean_index_scope:
                    if starttime is not None:
                        if starttime > self.__all_mean_measurements[index].datetime:
                            indexes_to_remove.add(index)

                    if endtime is not None:
                        if endtime < self.__all_mean_measurements[index].datetime:
                            indexes_to_remove.add(index)

            self.__current_mean_index_scope.difference_update(indexes_to_remove)

    def get_measurement_amount(self, of="all"):
        if of == "summed":
            return len(self.__all_mean_measurements)
        elif of == "scope":
            return len(self.__current_single_index_scope)

        return len(self.__all_single_measurement_objects)

    def get_date_of_first_measurement(self, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "summed":
            return self.__all_mean_measurements[0].datetime_begin
        elif of == "scope":
            return self.__all_single_measurement_objects[sorted(self.__current_single_index_scope)[0]].datetime

        return self.__all_single_measurement_objects[0].datetime

    def get_date_of_last_measurement(self, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "summed":
            return self.__all_mean_measurements[-1].datetime_begin
        elif of == "scope":
            return self.__all_single_measurement_objects[sorted(self.__current_single_index_scope)[-1]].datetime

        return self.__all_single_measurement_objects[-1].datetime

    def get_time_resolution(self, of="all", as_beautiful_string=False, as_time_delta=False):
        """
        Based on the first two measurements!
        """

        if of == "summed":
            time_delta = self.__all_mean_measurements[1].datetime_begin - self.__all_mean_measurements[0].datetime_begin
        elif of == "scope":
            scope_indexes = sorted(self.__current_single_index_scope)
            time_delta = self.__all_single_measurement_objects[scope_indexes[1]].datetime - self.__all_single_measurement_objects[scope_indexes[0]].datetime
        else:
            time_delta = self.__all_single_measurement_objects[1].datetime - self.__all_single_measurement_objects[0].datetime

        if as_beautiful_string:
            return fc.make_seconds_beautiful_string(time_delta.total_seconds())

        if as_time_delta:
            return time_delta

        return int(time_delta.total_seconds() // 60)

    def download_components(self, options: list, use_summed_measurements=False):
        # currently not support for downloading summed measurements

        if not os.path.exists(cfg["RESULT_DATA_DOWNLOAD_PATH"]):
            os.makedirs(cfg["RESULT_DATA_DOWNLOAD_PATH"])

        with open(cfg["RESULT_DATA_DOWNLOAD_PATH"] + "/data_download_" + '_'.join(options) + ".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Date"] + options)

            if use_summed_measurements:
                measures_to_take = [
                    self.__all_mean_measurements[i] for i in sorted(self.__current_mean_index_scope)]
            else:
                measures_to_take = [
                    self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]

            for obj in measures_to_take:
                line_to_write = [obj.datetime]
                for option in options:
                    item = getattr(obj, option)
                    if item is not None:
                        line_to_write.append(round(item, 5))
                    else:
                        line_to_write.append("None")
                writer.writerow(line_to_write)


singleton = MultipleMeasurements()