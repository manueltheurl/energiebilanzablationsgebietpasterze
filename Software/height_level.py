import numpy as np
from single_measurement import MeanMeasurement
from manage_config import cfg
from energy_balance import ONE_YEAR


class HeightLevel:
    def __init__(self, lower_border, upper_border):
        self.lower_border = lower_border
        self.upper_border = upper_border

        self.area = None  # in m^2
        self.mean_radiation = dict()
        self.mean_height = None
        self.mean_winter_balance = None
        self.shape_layer_path = None
        self.artificial_snowing_per_day = None
        self.simulated_measurements = []

    @classmethod
    def get_beautiful_height_levels_by_step(cls, beauty_interval, min_val, max_val):
        height_lvl_objs = []

        current_level = min_val - min_val % beauty_interval
        last_lvl = min_val
        while current_level < max_val - beauty_interval:
            current_level += beauty_interval
            height_lvl_objs.append(cls(last_lvl, current_level))
            last_lvl = current_level
        else:
            height_lvl_objs.append(cls(last_lvl, max_val))
        return height_lvl_objs

    @classmethod
    def get_height_levels_by_amount(cls, amount_of_levels, min_val, max_val):
        height_levels = np.linspace(min_val, max_val, amount_of_levels + 1)
        return [cls(height_levels[i], height_levels[i + 1]) for i in range(len(height_levels) - 1)]

    def set_mean_radiation_for_365_days(self, mean_radiation_list):
        pass

    def get_mean_radiation_for(self, date):  # or maybe make property
        pass

    def get_mean_yearly_water_consumption_of_snow_canons_per_square_meter_in_liters(self):
        overall_time_spawn = self.simulated_measurements[-1].datetime-self.simulated_measurements[0].datetime
        overall_water_consumption_of_canon = 0
        for simulated_measure in self.simulated_measurements:
            simulated_measure: MeanMeasurement
            # conversion from m snow to liters water equivalent
            try:
                overall_water_consumption_of_canon += simulated_measure.snow_depth_delta_artificial * 1000 * float(cfg["ARTIFICIAL_SNOW_SWE_FACTOR"])
            except TypeError:
                pass

        return overall_water_consumption_of_canon * (ONE_YEAR.total_seconds()/overall_time_spawn.total_seconds())

    def get_mean_yearly_water_consumption_of_snow_canons_for_height_level_in_liters(self):
        return self.get_mean_yearly_water_consumption_of_snow_canons_per_square_meter_in_liters() * self.area

    def __str__(self):
        return f"Height Level {int(self.lower_border)}-{int(self.upper_border)}"

    def get_total_natural_snowings(self):
        total_natural_snowings_in_period = 0
        for measure_obj in self.simulated_measurements:
            if measure_obj.snow_depth_delta_natural is not None and measure_obj.snow_depth_delta_natural > 0:  # only on snow accumulation add the snow height
                total_natural_snowings_in_period += measure_obj.snow_depth_delta_natural
        return total_natural_snowings_in_period

    def get_total_artificial_snowings(self):
        total_artificial_snowings_in_period = 0
        for measure_obj in self.simulated_measurements:
            if measure_obj.snow_depth_delta_artificial is not None and measure_obj.snow_depth_delta_artificial > 0:  # only on snow accumulation add the snow height
                total_artificial_snowings_in_period += measure_obj.snow_depth_delta_artificial
        return total_artificial_snowings_in_period

    @property
    def height(self):
        return self.mean_height
        # return (self.upper_border+self.lower_border)/2

    def is_continuously_snow_laying(self):
        first_snow_event_happened = False
        for measure in self.simulated_measurements:
            measure: MeanMeasurement
            if not measure.total_snow_depth and first_snow_event_happened:
                return False
            else:
                if measure.total_snow_depth > 0.1:  # 10 cm have to be reached once for it to count
                    first_snow_event_happened = True
        return True

    def clear_simulated_measurements(self):
        self.simulated_measurements = []


class MeteorologicalYear:
    def __init__(self, height_level_objects):
        self.height_level_objects = height_level_objects
        self.__overall_amount_of_water_needed_in_liters = None  # will be calculated

    @property
    def overall_amount_of_water_needed_in_liters(self):
        """
        calculate once, use as attribute as often as you want, but WARNING, if this value changes in reality, it will
        not change here after once calculated

        """
        if self.__overall_amount_of_water_needed_in_liters is None:
            self.__overall_amount_of_water_needed_in_liters = self.__get_overall_amount_of_water_needed_in_liters()
        return self.__overall_amount_of_water_needed_in_liters

    def __get_overall_amount_of_water_needed_in_liters(self):
        total_overall_amount_of_water_in_liters = 0
        for height_level in self.height_level_objects:
            height_level: HeightLevel
            total_amount_water_for_height_level = height_level.get_mean_yearly_water_consumption_of_snow_canons_for_height_level_in_liters()
            # print(height_level)
            # print(f" - Total water needed: {round(total_amount_water_for_height_level / 1000, 1)} m^3")
            # print(
            #     f" - Water per square meter: {round(total_amount_water_for_height_level / height_level.area, 1)} liters")
            total_overall_amount_of_water_in_liters += total_amount_water_for_height_level
        return total_overall_amount_of_water_in_liters
