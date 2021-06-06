import datetime as dt
import misc as fc
import os
from config_handler import cfg
import csv
from measurement import SingleStationMeasurement, MeanStationMeasurement
# from snow_to_swe_model import SnowToSwe
import numpy as np
from height_level import HeightLevel
import copy
import scipy.signal
import pickle


class MeasurementHandler:
    """
    Module that handles the read in measurements. Measurements can be manipulated, filtered, averaged, .. . The current
    scope at which measurements it is currenly looked at can be changed. This can be helpful to save computation time.

    Handles all single station measurements, and all mean station measurements that are computed out of the single
    station measurements.

    # todo any ideas on how to split this huge class into some parts?
    maybe like here below this class. Multiple other classes like maybe singleMeasureHandler, MeanMeasureHandler,
    combined measure handler ..  then we could get rid off the for_single, for_mean and that stuff. The overall
    MeasurementHandler would still contain the indexes and lists of measures

    but what about saving then?

    """
    all_single_measures = []
    current_single_index_scope = set()  # current indexes that will be used are saved in here; default: all

    all_mean_measures = []  # Empty in the beginning .. can later be calculated and used
    current_mean_index_scope = set()

    @classmethod
    def reset_scope_to_all(cls):
        """
        Resets scope of single and mean measures to all availabe measures
        """
        cls.current_single_index_scope = set(range(len(cls.all_single_measures)))
        cls.current_mean_index_scope = set(range(len(cls.all_mean_measures)))

    @classmethod
    def reset_scope_to_none(cls):
        """
        Resets scope of single and mean measures to empty
        """
        cls.current_single_index_scope = set()
        cls.current_mean_index_scope = set()

    @classmethod
    def clear_all_single_measurements(cls):
        """
        Empties all single measures.
        """
        cls.all_single_measures = []

    @classmethod
    def clear_all_mean_measurements(cls):
        """
        Empties all mean measures.
        """
        cls.all_mean_measures.clear()
        cls.current_mean_index_scope.clear()

    @classmethod
    def add_single_measurement(cls, single_measurement_object: SingleStationMeasurement):
        """
        Adds one single station measure to the pool of single measures

        :param single_measurement_object: SingleStationMeasurement to add to pool
        """
        cls.current_single_index_scope.add(len(cls.all_single_measures))
        cls.all_single_measures.append(single_measurement_object)

    @classmethod
    def add_mean_measurement(cls, mean_measurement_object: MeanStationMeasurement):
        """
        Adds one mean station measure to pool of mean measures

        :param mean_measurement_object: MeanStationMeasurement to add to pool
        """
        cls.current_mean_index_scope.add(len(cls.all_mean_measures))
        cls.all_mean_measures.append(mean_measurement_object)

    # explicit is better than implicit ..

    @classmethod
    def calculate_energy_balance_for_single_measures(cls, simulate_global_dimming_brightening=0):
        """
        Calculates energy balance of single measurements that are currently set for scope. Continues with remaining
        measures if one calculation should fail.

        :param simulate_global_dimming_brightening: optional mean additional lwi that is caused by global dimming ..
                in W/m2
        :return: True if all calculations are successful, False if one or more fails. Fails when mean measurement does
                not contain all the necessary information for calculating the energy balance
        """
        all_successful = True
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if not obj.calculate_energy_balance(simulate_global_dimming_brightening):
                all_successful = False
        return all_successful

    @classmethod
    def calculate_energy_balance_for_mean_measures(cls, simulate_global_dimming_brightening=0):
        """
        Calculates energy balance of mean measurements that are currently set for scope. Continues with remaining
        measures if one calculation should fail.

        :param simulate_global_dimming_brightening: optional mean additional lwi that is caused by global dimming ..
                in W/m2
        :return: True if all calculations are successful, False if one or more fails. Fails when mean measurement does
                not contain all the necessary information for calculating the energy balance
        """
        all_successful = True
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            if not obj.calculate_energy_balance(simulate_global_dimming_brightening):
                all_successful = False
        return all_successful

    @classmethod
    def cumulate_ice_thickness_measures_for_single_measures(cls, method=None):
        """
        Adds a new variable to the single measurement, that corresponds to the cumulated ice thickness that results from
        adding up all deltas of the single measures (of scope) from before. Filters these values a bit, by a given
        method for example.

        :param method: None or "SameLevelPositiveFix"
        """
        old_measured_ice_thickness_value = None
        current_subtractive = 0
        ice_thickness_before_increasing_again = None

        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if obj.measured_ice_thickness is not None:
                if old_measured_ice_thickness_value is None:
                    old_measured_ice_thickness_value = obj.measured_ice_thickness
                else:
                    if old_measured_ice_thickness_value < obj.measured_ice_thickness - float(cfg["ABLATION_THRESHOLD_FOR_UNNATURALITY"]):
                        current_subtractive += obj.measured_ice_thickness - old_measured_ice_thickness_value
                    elif old_measured_ice_thickness_value > obj.measured_ice_thickness + float(cfg["ABLATION_THRESHOLD_FOR_UNNATURALITY"]):
                        continue  # cant be either .. first drop of ablation when picking up station

                    new_ice_thickness_value = obj.measured_ice_thickness - current_subtractive

                    if method == "SameLevelPositiveFix":
                        """ If ice thickness is getting larger, wait until it is at the same level as before and then
                         continue to get smaller again"""
                        if ice_thickness_before_increasing_again is None:
                            if new_ice_thickness_value > old_measured_ice_thickness_value-current_subtractive:
                                if ice_thickness_before_increasing_again is None:
                                    ice_thickness_before_increasing_again = old_measured_ice_thickness_value-current_subtractive
                                new_ice_thickness_value = ice_thickness_before_increasing_again
                            else:
                                if ice_thickness_before_increasing_again is not None:
                                    ice_thickness_before_increasing_again = None
                        else:
                            if new_ice_thickness_value < ice_thickness_before_increasing_again:
                                ice_thickness_before_increasing_again = None
                            else:
                                new_ice_thickness_value = ice_thickness_before_increasing_again

                    obj.cumulated_ice_thickness = new_ice_thickness_value
                    old_measured_ice_thickness_value = obj.measured_ice_thickness

    @classmethod
    def correct_long_wave_measurements_for_single_measures(cls):
        """
        todo
        """
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if None not in [obj.lw_radiation_out, obj.lw_radiation_in]:
                if obj.lw_radiation_out < int(cfg["MIN_LWO_VALUE"]):
                    # obj.lw_radiation_in -= (int(cfg["MIN_LWO_VALUE"])-obj.lw_radiation_out)  # fix offset?
                    obj.lw_radiation_out = int(cfg["MIN_LWO_VALUE"])

    @classmethod
    def correct_short_wave_measurements_for_single_measures(cls):
        """
        If no snow is laying, then set fixed ice albedo. If albedo is below min ice albedo, set to min ice albedo
        """
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if obj.sw_radiation_in is not None:
                if obj.sw_radiation_in < 0:  # cannot be negative
                    obj.sw_radiation_in = 0

                if obj.sw_radiation_out is not None:
                    if obj.albedo is not None and obj.albedo < cfg["CLEAN_ICE_ALBEDO"]:
                        obj.sw_radiation_out = -cfg["CLEAN_ICE_ALBEDO"] * obj.sw_radiation_in

                    if not obj.total_snow_depth:
                        obj.sw_radiation_out = -cfg["CLEAN_ICE_ALBEDO"]*obj.sw_radiation_in

    @classmethod
    def correct_snow_measurements_for_single_measures(cls):
        """
        If measured snow is NULL, then take last measurement as new value
        If measured snow height is < 10cm from June till september, then set 0
        If jump from one measurement to the next is too big, then take previous measurement
        Some additional filters are implemented here, too much to docu .. overall it can be said that the
        snow measures of the example are really bad.
        """

        manual_jump_restrictions = [(dt.datetime(2017, 4, 15), dt.datetime(2017, 4, 25)),
                                    (dt.datetime(2018, 10, 28), dt.datetime(2018, 12, 1)),
                                    (dt.datetime(2013, 3, 1), dt.datetime(2013, 3, 25))]

        minute_resolution = cls.get_time_resolution()
        past_snow_depth = None
        first_snow_depth = True
        last_one_not_none = None
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if obj.snow_depth_natural is None:
                if first_snow_depth:
                    # when the first depth looking at is None, just set it to 0
                    obj.snow_depth_natural = 0
                    first_snow_depth = False
                else:
                    obj.snow_depth_natural = past_snow_depth
            else:
                if last_one_not_none is not None and (obj.datetime - last_one_not_none.datetime) < dt.timedelta(
                        days=100):
                    if 1.665 <= obj.snow_depth_natural <= 1.715 or 1.74 <= obj.snow_depth_natural <= 1.82:
                        obj.snow_depth_natural = past_snow_depth

                    max_jump_per_min = 0.028

                    for jump_restricted_area in manual_jump_restrictions:
                        if jump_restricted_area[0] <= obj.datetime <= jump_restricted_area[1]:
                            max_jump_per_min = 0.005
                            break

                    # if 7 <= obj.datetime.month <= 8:
                    #     obj.snow_depth_natural = 0

                    # setting snow height to 0 if albedo indicates so
                    if obj.albedo is not None and obj.albedo < 0.5:
                        obj.snow_depth_natural = 0

                    # TODO has this to be at bottom?  probably yes right that way
                    if past_snow_depth is not None and abs(
                            obj.snow_depth_natural - past_snow_depth) > max_jump_per_min * minute_resolution:
                        obj.snow_depth_natural = past_snow_depth

                last_one_not_none = obj
            past_snow_depth = obj.snow_depth_natural

        # lets apply a median filter as well
        for filtered, obj in zip(
                scipy.signal.medfilt([cls.all_single_measures[i].snow_depth_natural for i in sorted(cls.current_single_index_scope)], 501),
                [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]):

            obj.snow_depth_natural = filtered

    @classmethod
    def calculate_snow_height_deltas_for_single_measures(cls):
        past_snow_depth = None
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if past_snow_depth is not None and obj.snow_depth_natural is not None:
                obj.snow_depth_delta_natural = obj.snow_depth_natural - past_snow_depth
            past_snow_depth = obj.snow_depth_natural

    @classmethod
    def get_time_frames_of_measure_types_with_at_least_one_with_state_for_mean_measures(cls, valid_state, measure_types):
        """
        todo  really bad fx name

        :param valid_state:  valid_state one of MeanStationMeasurement.valid_states keys
        :param measure_types: measure_types list of strings of measure types, like [temperature, rel_moisture, ..]
        :return:
        """
        valid_state_frame_started = False
        valid_state_time_frames = []
        current_state_frame = [None, None]
        last_datetime_end = None
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            has_valid_state = obj.contains_one_valid_state_for_measure_types(valid_state, measure_types)
            if has_valid_state and not valid_state_frame_started:
                current_state_frame[0] = obj.datetime_begin
                valid_state_frame_started = True
            elif not has_valid_state and valid_state_frame_started:
                current_state_frame[1] = last_datetime_end
                valid_state_time_frames.append(current_state_frame)
                current_state_frame = [None, None]
                valid_state_frame_started = False
            last_datetime_end = obj.datetime_end
        return valid_state_time_frames

    @classmethod
    def get_time_frames_of_valid_state_for_mean_measures(cls, valid_state):
        """

        :param valid_state: one of MeanMeasurement.valid_states values
        :return:
        """
        # height level number does not matter for this

        valid_state_frame_started = False
        valid_state_time_frames = []
        current_state_frame = [None, None]
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            if obj.valid_state == valid_state and not valid_state_frame_started:
                current_state_frame[0] = obj.datetime_begin
                valid_state_frame_started = True
            elif obj.valid_state != valid_state and valid_state_frame_started:
                current_state_frame[1] = obj.datetime_end
                valid_state_time_frames.append(current_state_frame)
                current_state_frame = [None, None]
                valid_state_frame_started = False
        return valid_state_time_frames

    @classmethod
    def overall_height_level_simulation(cls, height_level, radiations_at_station):
        """
        TODO

        Lets do magic
        Returning the swe melted in this simulation. Cause in October, November it can happen, that there is still
        melting going on, because too little snow is laying

        :param height_level:
        :param radiations_at_station:
        :return:
        """
        height_level: HeightLevel

        minute_resolution = cls.get_time_resolution(of="averaged")

        first_measurement_of_scope = cls.all_mean_measures[sorted(cls.current_mean_index_scope)[0]]
        first_measurement_of_scope: MeanStationMeasurement

        current_height_lvl_time_of_last_snow_fall = None

        # temporary data
        if not first_measurement_of_scope.snow_depth_natural or True:  # if None or 0
            current_height_lvl_natural_snow_height = 0
        else:  # or is it better to always start with 0? for better comparison? TODO currently deactivated
            current_height_lvl_time_of_last_snow_fall = first_measurement_of_scope.datetime
            current_height_lvl_natural_snow_height = first_measurement_of_scope.snow_depth_natural

        # no artificial snow in the beginning
        current_height_lvl_artificial_snow_height = 0
        glacier_melt_water_equivalent_in_liters = 0

        for __obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            __obj: MeanStationMeasurement

            """ Adapt radiation """
            day_of_year = __obj.datetime.timetuple().tm_yday if __obj.datetime.timetuple().tm_yday < 366 else 365
            radiation_scale_factor = __obj.sw_radiation_in/radiations_at_station[day_of_year]

            measure_obj = copy.deepcopy(__obj)

            """ Adapt meteorologic values to the height """
            measure_obj.adapt_meteorological_values_in_respect_to_height_difference(height_level.height-float(cfg["AWS_STATION_HEIGHT"]))
            measure_obj.adapt_natural_snowings_in_respect_to_height_difference(height_level.height, float(cfg["AWS_STATION_HEIGHT"]), method="linear")

            """ Now that temperature is adapted, lets snow artificially """
            if int(cfg["ARTIFICIAL_SNOWING_USE_WET_BULB_TEMPERATURE"]):
                if measure_obj.wetbulb_temperature < float(cfg["ARTIFICIAL_SNOWING_TEMPERATURE_THRESHOLD"]):
                    measure_obj.snow_depth_delta_artificial = float(height_level.artificial_snowing_per_day) * minute_resolution / 60 / 24
            else:
                if measure_obj.temperature < float(cfg["ARTIFICIAL_SNOWING_TEMPERATURE_THRESHOLD"]):
                    measure_obj.snow_depth_delta_artificial = float(height_level.artificial_snowing_per_day) * minute_resolution / 60 / 24

            if measure_obj.snow_depth_delta_natural > 0:  # only on snow accumulation add the snow height
                current_height_lvl_natural_snow_height += measure_obj.snow_depth_delta_natural
                current_height_lvl_time_of_last_snow_fall = measure_obj.datetime

            if measure_obj.snow_depth_delta_artificial is not None and measure_obj.snow_depth_delta_artificial > 0:  # only on snow accumulation add the snow height
                current_height_lvl_artificial_snow_height += measure_obj.snow_depth_delta_artificial
                current_height_lvl_time_of_last_snow_fall = measure_obj.datetime

            measure_obj.sw_radiation_in = height_level.mean_radiation[day_of_year] * radiation_scale_factor

            if current_height_lvl_natural_snow_height+current_height_lvl_artificial_snow_height > 0:
                measure_obj.simulate_albedo_oerlemans((measure_obj.datetime - current_height_lvl_time_of_last_snow_fall).total_seconds() / 60 / 60 / 24)

            # conversion from m snow to liters water equivalent
            total_snow_swe = (current_height_lvl_natural_snow_height * float(cfg["NATURAL_SNOW_SWE_FACTOR"]) +
                              current_height_lvl_artificial_snow_height * float(cfg["ARTIFICIAL_SNOW_SWE_FACTOR"])
                              ) * 1000

            measure_obj.calculate_energy_balance()
            measure_obj.calculate_theoretical_melt_rate()
            measure_obj.convert_measured_and_modeled_rel_ablations_in_water_equivalents()

            if total_snow_swe and measure_obj.theoretical_melt_water_per_sqm > 0:
                snow_depth_scale_factor = (total_snow_swe-measure_obj.theoretical_melt_water_per_sqm)/total_snow_swe
                snow_depth_scale_factor = 0 if snow_depth_scale_factor < 0 else snow_depth_scale_factor
                current_height_lvl_natural_snow_height *= snow_depth_scale_factor
                current_height_lvl_artificial_snow_height *= snow_depth_scale_factor

            if measure_obj.theoretical_melt_water_per_sqm-total_snow_swe > 0:
                glacier_melt_water_equivalent_in_liters += (measure_obj.theoretical_melt_water_per_sqm-total_snow_swe)

            measure_obj.snow_depth_natural = current_height_lvl_natural_snow_height  # overwrite values for plot as well
            measure_obj.snow_depth_artificial = current_height_lvl_artificial_snow_height  # overwrite values for plot as well

            height_level.simulated_measurements.append(measure_obj)
        return glacier_melt_water_equivalent_in_liters

    @classmethod
    def convert_energy_balance_to_water_rate_equivalent_for_single_measures(cls):
        """
        todo
        """
        for obj in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            obj.calculate_theoretical_melt_rate()

    @classmethod
    def convert_energy_balance_to_water_rate_equivalent_for_mean_measures(cls):
        """
        todo
        """
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            obj.calculate_theoretical_melt_rate()

    @classmethod
    def calculate_relative_ablation_for_mean_measures(cls, set_negative_ablation_zero=True):
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            obj.calculate_relative_ablation(set_negative_ablation_zero=set_negative_ablation_zero)

    @classmethod
    def convert_measured_and_modeled_rel_ablations_in_water_equivalents_for_mean_measures(cls):
        """
        Averaged only, as the time frame is needed for that (start and endtime)
        """
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            obj.convert_measured_and_modeled_rel_ablations_in_water_equivalents()

    @classmethod
    def get_all_of(cls, attribute_name, use_mean_measurements=False):
        """
        todo
        Explicit is better than implicit, but for now, lets keep like this with the use_mean_measurements

        :param attribute_name:
        :param use_mean_measurements:
        :return:
        """
        if use_mean_measurements:
            return list(map(
                lambda obj: getattr(obj, attribute_name),
                # set messes with the order, sorted creates a list of the set
                [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]
            ))
        else:
            return list(map(
                lambda obj: getattr(obj, attribute_name),
                # set messes with the order, sorted creates a list of the set
                [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]
            ))

    @classmethod
    def get_cumulated_vals_of_components(cls, components, use_mean_measurements=False):
        """
        todo
        Explicit is better than implicit, but for now, lets keep like this with the use_mean_measurements

        :param components:
        :param use_mean_measurements:
        :return:
        """
        if use_mean_measurements:
            x_vals = [0] * cls.get_measurement_amount(of="averaged")
        else:
            x_vals = [0] * cls.get_measurement_amount()

        for component in components:
            x_vals = list(map(
                fc.save_add, x_vals,
                cls.get_all_of(component, use_mean_measurements=use_mean_measurements)))

        return x_vals

    @classmethod
    def get_measurement_amount(cls, of="all"):
        if of == "averaged":
            return len(cls.all_mean_measures)
        elif of == "scope":
            return len(cls.current_single_index_scope)

        return len(cls.all_single_measures)

    @classmethod
    def get_date_of_first_measurement(cls, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "averaged":
            return cls.all_mean_measures[0].datetime_begin
        elif of == "scope":
            return cls.all_single_measures[sorted(cls.current_single_index_scope)[0]].datetime

        return cls.all_single_measures[0].datetime

    @classmethod
    def get_date_of_last_measurement(cls, of="all"):
        # this presupposes that the measurements are read in sorted ascending by date
        if of == "averaged":
            return cls.all_mean_measures[-1].datetime_begin
        elif of == "scope":
            return cls.all_single_measures[sorted(cls.current_single_index_scope)[-1]].datetime

        return cls.all_single_measures[-1].datetime

    @classmethod
    def get_time_resolution(cls, of="all", as_beautiful_string=False, as_time_delta=False):
        """
        Gets time resolution in integer minutes
        Based on the first two measurements!
        """

        if of == "averaged":
            time_delta = cls.all_mean_measures[1].datetime_begin - cls.all_mean_measures[0].datetime_begin
        elif of == "scope":
            scope_indexes = sorted(cls.current_single_index_scope)
            time_delta = cls.all_single_measures[scope_indexes[1]].datetime - cls.all_single_measures[scope_indexes[0]].datetime
        else:
            time_delta = cls.all_single_measures[1].datetime - cls.all_single_measures[0].datetime

        if as_beautiful_string:
            return fc.make_seconds_beautiful_string(time_delta.total_seconds())

        if as_time_delta:
            return time_delta

        return int(time_delta.total_seconds() // 60)

    """ SCOPINGS """

    @classmethod
    def change_measurement_scope_by_time_interval(cls, time_interval: dt.timedelta):
        """
        TODO
        :param time_interval:
        :return:
        """
        indexes_to_remove = set()
        reference_time = cls.all_single_measures[0].datetime

        for index in list(cls.current_single_index_scope)[1:]:
            current_time = cls.all_single_measures[index].datetime

            if current_time - reference_time >= time_interval:
                reference_time = current_time
            else:
                indexes_to_remove.add(index)

        cls.current_single_index_scope.difference_update(indexes_to_remove)

        if cls.all_mean_measures:
            indexes_to_remove = set()
            reference_time = cls.all_mean_measures[0].datetime

            for index in list(cls.current_mean_index_scope)[1:]:
                current_time = cls.all_mean_measures[index].datetime

                if current_time - reference_time >= time_interval:
                    reference_time = current_time
                else:
                    indexes_to_remove.add(index)

            cls.current_mean_index_scope.difference_update(indexes_to_remove)

    @classmethod
    def change_measurement_scope_by_months(cls, months):
        """
        todo
        Doing so for single and mean measures.

        :param months:
        :return:
        """
        indexes_to_remove = set()
        reference_month = cls.all_single_measures[0].datetime.month

        for index in list(cls.current_single_index_scope)[1:]:
            current_month = cls.all_single_measures[index].datetime.month

            if fc.get_difference_of_months(reference_month, current_month) < months:
                indexes_to_remove.add(index)
            else:
                reference_month = current_month

        cls.current_single_index_scope.difference_update(indexes_to_remove)

        if cls.all_mean_measures:
            indexes_to_remove = set()
            reference_month = cls.all_mean_measures[0].datetime.month

            for index in list(cls.current_mean_index_scope)[1:]:
                current_month = cls.all_mean_measures[index].datetime.month

                if fc.get_difference_of_months(reference_month, current_month) < months:
                    indexes_to_remove.add(index)
                else:
                    reference_month = current_month

            cls.current_mean_index_scope.difference_update(indexes_to_remove)

    @classmethod
    def change_measurement_scope_by_years(cls, years):
        """
        todo
        Doing so for single and mean measures

        :param years:
        :return:
        """
        indexes_to_remove = set()
        reference_year = cls.all_single_measures[0].datetime.year

        for index in list(cls.current_single_index_scope)[1:]:
            current_year = cls.all_single_measures[index].datetime.year

            if current_year - reference_year < years:
                indexes_to_remove.add(index)
            else:
                reference_year = current_year

        cls.current_single_index_scope.difference_update(indexes_to_remove)

        if cls.all_mean_measures:
            indexes_to_remove = set()
            reference_year = cls.all_mean_measures[0].datetime.year

            for index in list(cls.current_mean_index_scope)[1:]:
                current_year = cls.all_mean_measures[index].datetime.year

                if current_year - reference_year < years:
                    indexes_to_remove.add(index)
                else:
                    reference_year = current_year

            cls.current_mean_index_scope.difference_update(indexes_to_remove)

    @classmethod
    def change_measurement_scope_by_percentage(cls, percentage: int):
        """
        todo
        Doing so for single and mean measures

        :param percentage: reaching from 0 to 100
        :return:
        """
        threshold = 100  # so that first one is always there
        indexes_to_remove = set()

        for index in cls.current_single_index_scope:
            threshold += percentage
            if threshold >= 100:
                threshold %= 100
            else:
                indexes_to_remove.add(index)  # if not a member, a KeyError is raised

        cls.current_single_index_scope.difference_update(indexes_to_remove)

        if cls.all_mean_measures:
            threshold = 100  # so that first one is always there
            indexes_to_remove = set()

            for index in cls.current_mean_index_scope:
                threshold += percentage
                if threshold >= 100:
                    threshold %= 100
                else:
                    indexes_to_remove.add(index)  # if not a member, a KeyError is raised

            cls.current_mean_index_scope.difference_update(indexes_to_remove)

    @classmethod
    def change_measurement_resolution_by_start_end_time(cls, starttime=None, endtime=None):
        """
        todo
        Doing so for single and mean measures.

        WARNING: If you use this function multiple times, do not forget to reset scope before new constraint

        :param starttime:
        :param endtime:
        :return:
        """

        if starttime is not None:
            if type(starttime) != dt.datetime:
                starttime = dt.datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S")
        if endtime is not None:
            if type(endtime) != dt.datetime:
                endtime = dt.datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")

        indexes_to_remove = set()

        if starttime is not None or endtime is not None:
            for index in cls.current_single_index_scope:
                if starttime is not None:
                    if starttime > cls.all_single_measures[index].datetime:
                        indexes_to_remove.add(index)

                if endtime is not None:
                    if endtime < cls.all_single_measures[index].datetime:
                        indexes_to_remove.add(index)

        cls.current_single_index_scope.difference_update(indexes_to_remove)

        if cls.all_mean_measures:
            indexes_to_remove = set()

            if starttime is not None or endtime is not None:
                for index in cls.current_mean_index_scope:
                    if starttime is not None:
                        if starttime > cls.all_mean_measures[index].datetime:
                            indexes_to_remove.add(index)

                    if endtime is not None:
                        if endtime < cls.all_mean_measures[index].datetime:
                            indexes_to_remove.add(index)

            cls.current_mean_index_scope.difference_update(indexes_to_remove)

    """ Creation of mean measurements """

    @classmethod
    def mean_measurements_by_amount(cls, amount):
        """
        Mean instead of mean maybe? todo  (for other mean fxs as well then)

        :param amount:
        :return:
        """
        cls.clear_all_mean_measurements()

        scoped_measurements = [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]
        multiple_separated_measurements = [scoped_measurements[x:x + amount] for x in range(0, len(scoped_measurements), amount)]

        # for moving average this could be used  # TODO make another option maybe
        # multiple_separated_measurements = [
        #     scoped_measurements[i:i + amount] for i in range(len(scoped_measurements) - amount + 1)
        # ]

        for i, separated_measurements in enumerate(multiple_separated_measurements):
            averaged_measurement = MeanStationMeasurement()

            for single_measurement in separated_measurements:
                averaged_measurement += single_measurement

            try:
                averaged_measurement.calculate_mean(
                    endtime=multiple_separated_measurements[i+1][0].datetime,
                    end_ablation=multiple_separated_measurements[i+1][0].cumulated_ice_thickness)
            except IndexError:
                # last one
                averaged_measurement.calculate_mean(
                    endtime=separated_measurements[-1].datetime,
                    end_ablation=separated_measurements[-1].cumulated_ice_thickness)

            cls.add_mean_measurement(averaged_measurement)

    @classmethod
    def mean_measurements_by_time_interval(cls, time_interval: dt.timedelta):
        """
        todo

        :param time_interval:
        :return:
        """
        cls.clear_all_mean_measurements()

        resolution_reference_time = None
        averaged_measurement = MeanStationMeasurement()

        if time_interval.total_seconds()/60 <= cls.get_time_resolution(of="scope"):
            print("Warning: meanming with resolution smaller or equal to measurement resolution")

        for single_measurement in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if resolution_reference_time is None:  # first time .. no reference time there
                resolution_reference_time = single_measurement.datetime

            # all the following times
            if single_measurement.datetime - resolution_reference_time >= time_interval:
                resolution_reference_time = single_measurement.datetime
                averaged_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ice_thickness)
                cls.add_mean_measurement(averaged_measurement)

                # reset averaged_measurement and add current to it
                averaged_measurement = MeanStationMeasurement()
                averaged_measurement += single_measurement

            else:
                averaged_measurement += single_measurement

    @classmethod
    def mean_measurements_by_months(cls, months):
        """
        todo

        :param months:
        :return:
        """
        cls.clear_all_mean_measurements()

        reference_month = None
        averaged_measurement = MeanStationMeasurement()

        for single_measurement in [cls.all_single_measures[i] for i in sorted(cls.current_single_index_scope)]:
            if reference_month is None:  # first time .. no reference time there
                reference_month = single_measurement.datetime.month

            # all the following times
            if fc.get_difference_of_months(reference_month, single_measurement.datetime.month) < months:
                averaged_measurement += single_measurement
            else:
                reference_month = single_measurement.datetime.month

                averaged_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ice_thickness)
                cls.add_mean_measurement(averaged_measurement)

                # reset averaged_measurement and add current to it
                averaged_measurement = MeanStationMeasurement()
                averaged_measurement += single_measurement

    @classmethod
    def mean_measurements_by_years(cls, years):
        """
        todo

        :param years:
        :return:
        """
        cls.clear_all_mean_measurements()

        reference_years = None
        averaged_measurement = MeanStationMeasurement()

        for single_measurement in [cls.all_single_measures[i] for i in
                                   sorted(cls.current_single_index_scope)]:
            if reference_years is None:  # first time .. no reference time there
                reference_years = single_measurement.datetime.year

            # all the following times
            if fc.get_difference_of_months(reference_years, single_measurement.datetime.year) < years:
                averaged_measurement += single_measurement
            else:
                reference_years = single_measurement.datetime.year

                averaged_measurement.calculate_mean(endtime=single_measurement.datetime,
                                                  end_ablation=single_measurement.cumulated_ice_thickness)
                cls.add_mean_measurement(averaged_measurement)

                # reset averaged_measurement and add current to it
                averaged_measurement = MeanStationMeasurement()
                averaged_measurement += single_measurement

    @classmethod
    def get_total_theoretical_meltwater_per_square_meter_for_mean_measures(cls):
        """
        Gets the total meltwater in liters for the time frame defined in the scope
        """

        total_meltwater = 0

        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            obj: MeanStationMeasurement
            try:
                total_meltwater += obj.theoretical_melt_water_per_sqm
            except TypeError:  # skip if None
                pass

        return total_meltwater

    @classmethod
    def fix_invalid_mean_measurements(cls,
                                      measurements_to_fix=("temperature", "rel_moisture", "air_pressure",
                                                             "wind_speed", "sw_radiation_in", "sw_radiation_out",
                                                             "lw_radiation_in", "lw_radiation_out", "snow_delta",
                                                             "relative_ablation_measured")):
        """
        Scope must include several years for this to work

        :param measurements_to_fix:
        :return:
        """
        percentages_replaced = []
        for measure_name in measurements_to_fix:
            print("Fixing", measure_name)
            invalid_measurements_and_replacements = dict()

            for i in sorted(cls.current_mean_index_scope):
                obj = cls.all_mean_measures[i]
                obj: MeanStationMeasurement

                if obj.measurement_validity[measure_name] == MeanStationMeasurement.valid_states["invalid"]:
                    invalid_measurements_and_replacements[obj] = list()

            for i in sorted(cls.current_mean_index_scope):
                obj = cls.all_mean_measures[i]
                obj: MeanStationMeasurement

                if obj.measurement_validity[measure_name] == MeanStationMeasurement.valid_states["valid"]:
                    current_datetime = copy.deepcopy(obj.datetime)

                    for invalid_measurement, replacement_measurements in invalid_measurements_and_replacements.items():
                        year_of_invalid = invalid_measurement.datetime_begin.year  # endtime is ignored here

                        """ Handling of february the 29th, is there a more elegant solution? """

                        """ So that a valid measurement on 29th of february can be used for replacing an invalid on
                         28th """
                        try:
                            current_datetime = current_datetime.replace(year=year_of_invalid)  # adapt year to compare
                        except ValueError:
                            current_datetime = current_datetime.replace(year=year_of_invalid, day=28)  # leap year

                        invalid_datetime_begin_copy = None  # only create deepcopy if necessary, else much longer computation time
                        invalid_datetime_end_copy = None

                        """ For making it possible to replace and invalid measurement on 29th of february with measures
                         from 28th of February"""
                        if invalid_measurement.datetime_begin.day == 29 and invalid_measurement.datetime_begin.month == 2:
                            invalid_datetime_begin_copy = copy.deepcopy(invalid_measurement.datetime_begin)
                            invalid_datetime_begin_copy = invalid_datetime_begin_copy.replace(day=28)

                            """ When replacing it for end time, it must have been replaced for start time as well,
                             else the end time can be before the start time, which does not make sense"""
                            if invalid_measurement.datetime_end.day == 29 and invalid_measurement.datetime_end.month == 2:
                                invalid_datetime_end_copy = copy.deepcopy(invalid_measurement.datetime_end)
                                invalid_datetime_end_copy = invalid_datetime_end_copy.replace(day=28)

                        date_ref_begin = invalid_measurement.datetime_begin if invalid_datetime_begin_copy is None else invalid_datetime_begin_copy
                        date_ref_end = invalid_measurement.datetime_end if invalid_datetime_end_copy is None else invalid_datetime_end_copy

                        if date_ref_begin <= current_datetime < date_ref_end:
                            replacement_measurements.append(obj)

            i = 0
            for invalid_measurement, replacement_measurements in invalid_measurements_and_replacements.items():
                if replacement_measurements:
                    invalid_measurement.replace_measure_mean_of(replacement_measurements, measure_name)
                    i += 1
                else:
                    print(invalid_measurement.datetime, "No replacement measurements found")

            print(f"{i}/{len(invalid_measurements_and_replacements)} invalid averaged measurements have been replaced")
            if len(invalid_measurements_and_replacements):
                percentages_replaced.append(i/len(invalid_measurements_and_replacements)*100)
        return np.mean(percentages_replaced)

    @classmethod
    def calculate_wetbulb_temperature_for_mean_measures(cls):
        """
        todo
        """
        for obj in [cls.all_mean_measures[i] for i in sorted(cls.current_mean_index_scope)]:
            obj.calculate_wetbulb_temperature()


    @classmethod
    def save_me(cls, save_path):
        """
        Class method that saves the whole class including all class variables, not only an instance.
        A bit hacky but pretty nice.

        :param save_path: path to save the serialized class
        """
        with open(save_path, 'wb') as f:
            dill.dump(globals()[cls.__name__], f)

    @classmethod
    def save_me2(cls, save_path):
        """
        Class method that saves the whole class including all class variables, not only an instance.
        A bit hacky but pretty nice.

        :param save_path: path to save the serialized class
        """
        with open(save_path+"1", 'wb') as f:
            pickle.dump(cls.current_single_index_scope, f)
        with open(save_path+"2", 'wb') as f:
            pickle.dump(cls.all_single_measures, f)
        with open(save_path + "3", 'wb') as f:
            pickle.dump(cls.current_mean_index_scope, f)
        with open(save_path + "4", 'wb') as f:
            pickle.dump(cls.all_mean_measures, f)

    @classmethod
    def load_me(cls, load_path):
        """
        Class method to load the whole previously saved class. This method sets all the class variables to the values
        which were previously saved with the class.
        A bit hacky but pretty nice.

        :param load_path: path to load the serialized class from
        """
        # with open(load_path+"1", 'rb') as fd:
        #     globals()[cls.__name__] = dill.load(fd)

        one = pickle.load(open(load_path+"1", "rb"))
        two = pickle.load(open(load_path+"2", "rb"))
        three = pickle.load(open(load_path+"3", "rb"))
        fore = pickle.load(open(load_path+"4", "rb"))
        return one, two, three, fore



# class OtherOne:
#     @classmethod
#     def sdf(cls):
#         MeasurementHandler.convert_energy_balance_to_water_rate_equivalent_for_single_measures()