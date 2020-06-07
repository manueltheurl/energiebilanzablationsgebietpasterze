import datetime as dt
from mean_measurement import MeanMeasurement
import functions as fc
import os
from manage_config import cfg
import csv
from single_measurement import SingleMeasurement
from snow_to_swe_model import SnowToSwe
import numpy as np


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

    def calculate_water_input_through_snow_for_scope(self):
        snow_observations = []  # snow observations have to be in meters

        # TODO double loop here could of course be prevented, but the aim was to modify the snow to swe model as little as possible

        for obj in [self.__all_mean_measurements[i] for i in sorted(self.__current_mean_index_scope)]:
            obj: MeanMeasurement
            snow_observations.append(obj.snow_depth)

        resolution = self.get_time_resolution(of="summed")

        snow_to_swe_model = SnowToSwe()
        swe_results = snow_to_swe_model.convert(snow_observations, timestep=resolution/60)

        """ Now update the measurements with those calculated values  """
        # resolution seems to be in minutes
        for obj, swe in zip([self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)], swe_results):
            obj: SingleMeasurement
            obj.swe_input_from_snow = swe

        obs = np.array(snow_observations)
        swe_ = np.array(swe_results)


        return swe_results  # todo delete this

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

    def correct_snow_measurements_for_scope(self):
        """
        If measured snow is NULL, then take last measurement as new value
        If measured snow height is < 10cm from June till september, then set 0
        If jump from one measurement to the next is too big, then take previous measurement
        """
        minute_resolution = self.get_time_resolution()
        past_snow_depth = None
        first_snow_depth = True
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if obj.snow_depth is None:
                if first_snow_depth:
                    # when the first depth looking at is None, just set it to 0
                    obj.snow_depth = 0
                    first_snow_depth = False
                else:
                    obj.snow_depth = past_snow_depth

            if 6 <= obj.datetime.month <= 8:
                if obj.snow_depth <= 0.1:
                    obj.snow_depth = 0

            if past_snow_depth is not None and abs(past_snow_depth-obj.snow_depth) > 0.05*minute_resolution:
                obj.snow_depth = past_snow_depth

            if past_snow_depth is not None:
                obj.snow_depth_delta = obj.snow_depth - past_snow_depth

            past_snow_depth = obj.snow_depth

    def simulate_artificial_snowing(self):
        """
        TODO
        """
        minute_resolution = self.get_time_resolution()

        snowing_in_m_height_per_day = float(cfg["ARTIFICIAL_SNOW_PER_DAY"])
        snowing_in_m_per_time_step = snowing_in_m_height_per_day / (24*60) * minute_resolution

        last_snow_depth = None

        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if (10 <= obj.datetime.month <= 12 or 1 <= obj.datetime.month <= 5) and obj.temperature > 0:
                if obj.snow_depth_delta is not None:
                    if last_snow_depth is None:
                        obj.snow_depth += snowing_in_m_per_time_step
                    else:
                        obj.snow_depth_delta += snowing_in_m_per_time_step
                        obj.snow_depth = last_snow_depth + obj.snow_depth_delta

                    last_snow_depth = obj.snow_depth
            else:
                last_snow_depth = None  # important

    def change_albedo_for_snowy_times(self):
        """
        TODO
        """

        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if obj.snow_depth > 0:
                try:
                    obj.sw_radiation_out = -obj.sw_radiation_in * float(cfg["SNOW_ALBEDO"])
                except TypeError:
                    pass

    def calculate_snow_height_deltas_for_scope(self):
        past_snow_depth = None
        for obj in [self.__all_single_measurement_objects[i] for i in sorted(self.__current_single_index_scope)]:
            if past_snow_depth is not None:
                obj.snow_depth_delta = obj.snow_depth - past_snow_depth
            past_snow_depth = obj.snow_depth

    def set_initial_snow_height_to_zero(self, of="summed"):
        """
        This is done for the snow height to swe model, cause the time series has to start with no snow
        """
        if of == "summed":
            first_measurement = self.__all_mean_measurements[sorted(self.__current_mean_index_scope)[0]]
            second_measurement = self.__all_mean_measurements[sorted(self.__current_mean_index_scope)[1]]
        elif of == "scope":
            first_measurement = self.__all_single_measurement_objects[sorted(self.__current_single_index_scope)[0]]
            second_measurement = self.__all_single_measurement_objects[sorted(self.__current_single_index_scope)[1]]
        else:
            return False

        second_measurement.snow_depth_delta = first_measurement.snow_depth
        first_measurement.snow_depth = 0
        first_measurement.snow_depth_delta = 0

    def simulate(self):
        """
        Lets do magic
        """

        total_snowings_in_period = 0

        resolution = self.get_time_resolution(of="summed")
        snow_to_swe_generator = SnowToSwe(resolution).convert_generator(len(self.__current_mean_index_scope))
        actual_snow_height = 0

        for obj in [self.__all_mean_measurements[i] for i in sorted(self.__current_mean_index_scope)]:
            obj: MeanMeasurement

            if obj.snow_depth_delta > 0:  # only on snow accumulation add the snow height
                print("Snow event: ", obj.snow_depth_delta)
                actual_snow_height += obj.snow_depth_delta
                total_snowings_in_period += obj.snow_depth_delta
            obj.snow_depth = actual_snow_height  # overwrite values for plot as well

            if False:
                next(snow_to_swe_generator)
                snow_swe = snow_to_swe_generator.send(actual_snow_height)
            else:
                # conversion from m snow to liters water equivalent
                snow_swe = actual_snow_height * 1000 * float(cfg["SNOW_SWE_FACTOR"])  # TODO what is a legimit factor here?

            # energy balance TODO
            if snow_swe:
                if obj.theoretical_melt_water_per_sqm > 0:
                    snow_depth_scale_factor = (snow_swe-obj.theoretical_melt_water_per_sqm)/snow_swe
                    snow_depth_scale_factor = 0 if snow_depth_scale_factor < 0 else snow_depth_scale_factor
                    print("Reducing snow height by factor", snow_depth_scale_factor)
                    actual_snow_height = actual_snow_height * snow_depth_scale_factor
            else:
                pass
                # actual_snow_height = 0

            print(obj.datetime, "Snow Swe:", snow_swe, "Meltwater:", obj.theoretical_melt_water_per_sqm, "Current snow height:", actual_snow_height)

        print("Total snowings:", total_snowings_in_period)

    def convert_energy_balance_to_water_rate_equivalent_for_scope(self):
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

    def get_vals_and_dates_of_selected_options(self, options, use_summed_measurements=False):
        if use_summed_measurements:
            x_vals = [0] * self.get_measurement_amount(of="summed")
        else:
            x_vals = [0] * self.get_measurement_amount()

        for option in options:
            x_vals = list(map(
                fc.save_add, x_vals,
                self.get_all_of(option, use_summed_measurements=use_summed_measurements)))

        y_dates = self.get_all_of("datetime", use_summed_measurements=use_summed_measurements)

        return x_vals, y_dates

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

        if time_interval.total_seconds()/60 <= self.get_time_resolution(of="scope"):
            print("Warning: Summing with resolution smaller or equal to measurement resolution")

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
        Gets time resolution in integer minutes
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

    def get_total_theoretical_meltwater_per_square_meter_for_current_scope_with_summed_measurements(self):
        """
        Gets the total meltwater in liters for the time frame defined in the scope
        """

        total_meltwater = 0

        for obj in [self.__all_mean_measurements[i] for i in sorted(self.__current_mean_index_scope)]:
            obj: MeanMeasurement
            try:
                total_meltwater += obj.theoretical_melt_water_per_sqm
            except TypeError:  # skip if None
                pass

        return total_meltwater

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
