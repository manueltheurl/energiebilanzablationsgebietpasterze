import numpy as np
from height_level import HeightLevel
from config_handler import cfg


class HydrologicYear:
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

    @property
    def overall_amount_of_snow_needed_in_cubic_meters(self):
        """
        calculate once, use as attribute as often as you want, but WARNING, if this value changes in reality, it will
        not change here after once calculated

        """
        return self.overall_amount_of_water_needed_in_liters/cfg["ARTIFICIAL_SNOW_SWE_FACTOR"]/1000

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

    def get_height_level_close_to_height(self, desired_height):
        abs_diffs_to_height = []
        for height_level in self.height_level_objects:
            abs_diffs_to_height.append(abs(height_level.height-desired_height))
        return self.height_level_objects[np.argmin(abs_diffs_to_height)]

    def get_distributed_amount_of_height_levels(self, amount):
        idx = list(np.round(np.linspace(0, len(self.height_level_objects) - 1, amount)).astype(int))
        return [self.height_level_objects[x] for x in idx]
