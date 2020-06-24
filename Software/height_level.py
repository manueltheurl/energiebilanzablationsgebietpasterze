import numpy as np


class HeightLevel:
    def __init__(self, lower_border, upper_border):
        self.lower_border = lower_border
        self.upper_border = upper_border

        self.area = None
        self.mean_radiation = dict()
        self.shape_layer = None  # TODO change to shape path
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

    def __str__(self):
        pass  # TODO

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
        return (self.upper_border+self.lower_border)/2
