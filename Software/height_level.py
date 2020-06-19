class HeightLevel:
    def __init__(self, lower_border, upper_border):
        self.lower_border = lower_border
        self.upper_border = upper_border

        self.area = None
        self.mean_radiation = dict()
        self.shape_layer = None
        self.simulated_measurements = []

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
