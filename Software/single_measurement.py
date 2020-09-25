from datetime import datetime as dt
import energy_balance
from manage_config import cfg
import math as m
from natural_snow_scaler import NaturalSnowScaler
from statistics import mean
import numpy as np
from WetBulb import WetBulb

# TODO maybe make another subclass "ArtificialMeasurement"  or better not?  with just the artificial methods
# TODO get rid off all those properties, this makes it so unreadable, just use them if really necessary


class StationMeasurement:
    def __init__(self, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, measured_ice_thickness):
        # Measured
        self.temperature = temperature
        self.snow_depth_natural = snow_depth
        self.rel_moisture = rel_moisture  # in percent*100 .. e.g. 67
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.air_pressure = air_pressure  # pa
        self.zenith_angle = zenith_angle
        self.tiltx = tiltx
        self.tilty = tilty
        self.measured_ice_thickness = measured_ice_thickness  # this represents the ice thickness at the point of measurement

        # sw out and lw out are negative here even though they are technically positive .. sum of the dict is actual
       
        self.sw_radiation_in = sw_radiation_in
        self.sw_radiation_out = sw_radiation_out
        self.lw_radiation_in = lw_radiation_in
        self.lw_radiation_out = lw_radiation_out

        self.sensible_heat = None  # None, cause else 0 line would be plotted
        self.latent_heat = None
        self.precipitation_heat = None  # NOT calculating currently
        self._total_energy_balance = None
        
        self._cumulated_ice_thickness = None
        self._theoretical_melt_rate = None
        self._snow_depth_delta_natural = None
        self._snow_depth_artificial = None
        self._snow_depth_delta_artificial = None

        # DEPRECATED
        self._swe_input_from_snow = None  # unit TODO
        self._wetbulb_temperature = None
        self._simulate_global_brightening = None  # get rid of that

    def simulate_albedo_oerlemans(self, days_since_last_snowfall):
        """
        Based on J. Oerlemans, W. H . KNAP: A 1 year record of global radiation and albedo in the ablation zone of
        Morteratschgletscher, Switzerland -> equation 4.
        """

        alpha_firn = 0.53
        alpha_frsnow = 0.75
        t_star = 21.9  # host fast the snow albedo approaches the firn albedo
        albedo = alpha_firn + (alpha_frsnow-alpha_firn) * m.exp(-days_since_last_snowfall/t_star)
        self.sw_radiation_out = -self.sw_radiation_in * albedo

    def adapt_meteorological_values_in_respect_to_height_difference(self, height_difference_in_m):
        """
        height_difference is positive if measurement should be higher up
        """
        deg_per_100_meters = 0.65
        self.temperature -= deg_per_100_meters * height_difference_in_m / 100
        self._wetbulb_temperature -= deg_per_100_meters * height_difference_in_m / 100  # is this legitimate?
        # self.calculate_wetbulb_temperature()  # this is taking quite long

        hpa_for_100_meters = 12
        self.air_pressure -= height_difference_in_m * hpa_for_100_meters  # 100 meter and hecto cancel each other out

    def adapt_natural_snowings_in_respect_to_height_difference(self, current_height, reference_height, method):
        if method == "linear":
            """ Leidinger D. 2013 (winter, linear table 7.2)"""
            self.snow_depth_delta_natural *= NaturalSnowScaler.linear_scale_factor(current_height, reference_height)

        elif method == "quadratic":
            """ Leidinger D. 2013 (winter, quadratic table 7.2)"""
            self.snow_depth_delta_natural *= NaturalSnowScaler.quadratic_scale_factor(current_height, reference_height)

        elif method == "fixed_percentage_7":
            self.snow_depth_delta_natural *= NaturalSnowScaler.fixed_percentage_per_100_meter_scale_factor(
                current_height, reference_height, 0.07)

        elif method == "fixed_percentage_10":
            self.snow_depth_delta_natural *= NaturalSnowScaler.fixed_percentage_per_100_meter_scale_factor(
                current_height, reference_height, 0.1)

    def calculate_energy_balance(self, simulate_global_dimming_brightening=0):
        # if self._total_energy_balance is not None:  # so that we wont recalculate for nothing
        # .. since simulate dimming, not anymore cause same measurement can have different actual values
        #     return

        if simulate_global_dimming_brightening:
            self._simulate_global_brightening = simulate_global_dimming_brightening

        if None not in [self.air_pressure, self.wind_speed, self.temperature,
                        self.lw_radiation_out]:
            self.sensible_heat = energy_balance.singleton.calculate_sensible_heat(
                self.air_pressure,
                self.wind_speed,
                self.temperature,
                self.lw_radiation_out,
                self.total_snow_depth
            )

        if None not in [self.temperature, self.rel_moisture, self.wind_speed, self.air_pressure,
                        self.lw_radiation_out]:
            self.latent_heat = energy_balance.singleton.calculate_latent_heat(
                self.temperature,
                self.rel_moisture,
                self.wind_speed,
                self.lw_radiation_out,
                self.air_pressure,
                self.total_snow_depth
            )

        if None not in [None]:
            self.precipitation_heat = energy_balance.singleton.calculate_precipitation_heat()

        try:
            self._total_energy_balance = sum([self.sw_radiation_in,  # get it over property cause may be glob br. simul
                                               self.sw_radiation_out,
                                               self.lw_radiation_in,
                                               self.lw_radiation_out,
                                               self.sensible_heat,
                                               self.latent_heat,
                                               ])
        except TypeError:
            if type(self) == SingleStationMeasurement:
                pass
            else:
                print(self.sw_radiation_in,  # get it over property cause may be glob br. simul
                      self.sw_radiation_out,
                      self.lw_radiation_in,
                      self.lw_radiation_out,
                      self.sensible_heat,
                      self.latent_heat)
                print(self.air_pressure, self.wind_speed, self.temperature)
                print(self.temperature, self.rel_moisture, self.wind_speed)
                exit('Calculating energy balance for mean measurement and something is none')  # Something is None

        if not cfg["IGNORE_PRECIPITATION_HEAT"]:
            self._total_energy_balance += self.precipitation_heat

    def calculate_theoretical_melt_rate(self):
        if None not in [self._total_energy_balance]:
            self._theoretical_melt_rate = energy_balance.singleton.energy_balance_to_melt_rate(
                self._total_energy_balance
            )
            # TODO NO NEGATIVE MELT RATE, DOES IT AFFECT SOMETHING ELSE?
            self._theoretical_melt_rate = 0 if self._theoretical_melt_rate < 0 else self._theoretical_melt_rate

    def calculate_wetbulb_temperature(self):
        # I do not really like the implementation of that WetBulb function, but other than the small bug fix taken this
        # will remain original
        self._wetbulb_temperature = WetBulb(
            np.array([self.temperature]), np.array([self.air_pressure]), np.array([self.rel_moisture]), 1)[0][0]

    # TODO rewrite this whole stuff to only save water equivalents .. else this makes absolutely no sense
    @property
    def total_snow_depth(self):
        try:
            return self.snow_depth_natural + self._snow_depth_artificial
        except TypeError:
            return self.snow_depth_natural

    @property
    def total_snow_water_equivalent(self):
        # in liters per square meter
        return self.natural_snow_water_equivalent + self.artificial_snow_water_equivalent

    @property
    def natural_snow_water_equivalent(self):
        # in liters per square meter
        return self.snow_depth_natural * cfg["NATURAL_SNOW_SWE_FACTOR"] * 1000

    @property
    def artificial_snow_water_equivalent(self):
        # in liters per square meter
        try:
            return self._snow_depth_artificial * cfg["NATURAL_SNOW_SWE_FACTOR"] * 1000
        except TypeError:
            return 0

    @property
    def wetbulb_temperature(self):
        return self._wetbulb_temperature

    @property
    def snow_depth_artificial(self):
        return self._snow_depth_artificial

    @snow_depth_artificial.setter
    def snow_depth_artificial(self, new_value):
        if new_value is not None:
            self._snow_depth_artificial = new_value

    @property
    def snow_depth_delta_natural(self):
        return self._snow_depth_delta_natural

    @snow_depth_delta_natural.setter
    def snow_depth_delta_natural(self, new_value):
        if new_value is not None:
            self._snow_depth_delta_natural = new_value

    @property
    def snow_depth_delta_artificial(self):
        return self._snow_depth_delta_artificial

    @snow_depth_delta_artificial.setter
    def snow_depth_delta_artificial(self, new_value):
        if new_value is not None:
            self._snow_depth_delta_artificial = new_value

    @property
    def swe_input_from_snow(self):
        # DEPRECATED
        return self._swe_input_from_snow

    @swe_input_from_snow.setter
    def swe_input_from_snow(self, value):
        # DEPRECATED
        self._swe_input_from_snow = value

    @property
    def cumulated_ice_thickness(self):
        return self._cumulated_ice_thickness

    @cumulated_ice_thickness.setter
    def cumulated_ice_thickness(self, new_value):
        # for clearing the ablation values
        self._cumulated_ice_thickness = new_value

    @property
    def total_energy_balance(self):
        return self._total_energy_balance

    @property
    def theoretical_melt_rate(self):
        return self._theoretical_melt_rate

    @property
    def albedo(self):
        # TODO ZeroDivisionError: float division by zero
        try:
            return abs(self.sw_radiation_out/self.sw_radiation_in)
        except (ZeroDivisionError, TypeError):
            return None


class SingleStationMeasurement(StationMeasurement):
    """
    Object refers to one single measurement
    Values can be read but NOT be modified
    """

    def __init__(self,
                 datetime: dt, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation
                 ):

        StationMeasurement.__init__(self, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                                    sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation)

        self.__datetime = datetime

    @property
    def datetime(self):
        return self.__datetime


class MeanStationMeasurement(StationMeasurement):
    """
    Object refers to the sum of multiple single measurements
    Values can be read but NOT be modified
    """
    valid_states = {
        "unchecked": 0,
        "valid": 1,
        "invalid": 2,
        "estimated": 3,
    }

    def __init__(self):
        StationMeasurement.__init__(self, None, None, None, None, None, None,
                                    None, None, None, None, None, None, None, None)

        self.measurement_validity = {
            "temperature": self.valid_states["unchecked"],
            "rel_moisture": self.valid_states["unchecked"],
            "air_pressure": self.valid_states["unchecked"],
            "wind_speed": self.valid_states["unchecked"],
            "sw_radiation_in": self.valid_states["unchecked"],
            "sw_radiation_out": self.valid_states["unchecked"],
            "lw_radiation_in": self.valid_states["unchecked"],
            "lw_radiation_out": self.valid_states["unchecked"],
            "snow_delta": self.valid_states["unchecked"],
            "relative_ablation_measured": self.valid_states["unchecked"],
        }

        self.__starting_ice_thickness = None
        self.__ending_ice_thickness = None

        self.__datetime_begin = None
        self.__datetime_end = None

        self.__actual_mm_we_per_d = None  # derived from the ablation measurement
        self.__theoretical_mm_we_per_d = None  # derived from the energy balance

        self.__actual_melt_water_per_sqm = None  # in liters - derived from the ablation measurement
        self.__theoretical_melt_water_per_sqm = None  # in liters - derived from the energy balance

        self.__relative_ablation_measured = None  # in meter ice - directly from the ablation measurement (current - last one), gets set when summing measurement
        self.__relative_ablation_modelled = None  # in meter ice - derived from the energy balance, only if no snow is laying

        self.midday_albedo = None

        self.contains = {
            "single_measurements": 0,
            "sw_radiation_in": 0,
            "sw_radiation_out": 0,
            "lw_radiation_in": 0,
            "lw_radiation_out": 0,
            "sensible_heat": 0,
            "latent_heat": 0,
            "precipitation_heat": 0,
            "total_energy_balance": 0,
            "measured_ice_thickness": 0,
            "cumulated_ice_thickness": 0,
            "theoretical_melt_rate": 0,
            "snow_depth_natural": 0,
            "snow_depth_artificial": 0,
            "rel_moisture": 0,
            "wind_speed": 0,
            "air_pressure": 0,
            "midday_albedo": 0,
            "temperature": 0,
        }

    def __iadd__(self, single_measurement: SingleStationMeasurement):
        self.contains["single_measurements"] += 1

        if self.__datetime_begin is None or single_measurement.datetime < self.__datetime_begin:
            self.__datetime_begin = single_measurement.datetime

        if single_measurement.rel_moisture is not None:
            self.contains["rel_moisture"] += 1
            if self.rel_moisture is None:
                self.rel_moisture = single_measurement.rel_moisture
            else:
                self.rel_moisture += single_measurement.rel_moisture

        if single_measurement.wind_speed is not None:
            self.contains["wind_speed"] += 1
            if self.wind_speed is None:
                self.wind_speed = single_measurement.wind_speed
            else:
                self.wind_speed += single_measurement.wind_speed

        if single_measurement.air_pressure is not None:
            self.contains["air_pressure"] += 1
            if self.air_pressure is None:
                self.air_pressure = single_measurement.air_pressure
            else:
                self.air_pressure += single_measurement.air_pressure

        if single_measurement.sw_radiation_in is not None:
            self.contains["sw_radiation_in"] += 1
            if self.sw_radiation_in is None:
                self.sw_radiation_in = single_measurement.sw_radiation_in
            else:
                self.sw_radiation_in += single_measurement.sw_radiation_in

        if single_measurement.sw_radiation_out is not None:
            self.contains["sw_radiation_out"] += 1
            if self.sw_radiation_out is None:
                self.sw_radiation_out = single_measurement.sw_radiation_out
            else:
                self.sw_radiation_out += single_measurement.sw_radiation_out

        if single_measurement.lw_radiation_in is not None:
            self.contains["lw_radiation_in"] += 1
            if self.lw_radiation_in is None:
                self.lw_radiation_in = single_measurement.lw_radiation_in
            else:
                self.lw_radiation_in += single_measurement.lw_radiation_in

        if single_measurement.lw_radiation_out is not None:
            self.contains["lw_radiation_out"] += 1
            if self.lw_radiation_out is None:
                self.lw_radiation_out = single_measurement.lw_radiation_out
            else:
                self.lw_radiation_out += single_measurement.lw_radiation_out

        if single_measurement.sensible_heat is not None:
            self.contains["sensible_heat"] += 1
            if self.sensible_heat is None:
                self.sensible_heat = single_measurement.sensible_heat
            else:
                self.sensible_heat += single_measurement.sensible_heat

        if single_measurement.latent_heat is not None:
            self.contains["latent_heat"] += 1
            if self.latent_heat is None:
                self.latent_heat = single_measurement.latent_heat
            else:
                self.latent_heat += single_measurement.latent_heat

        if cfg["PRO_VERSION"]:
            if single_measurement.temperature is not None:
                self.contains["temperature"] += 1
                if self.temperature is None:
                    self.temperature = single_measurement.temperature
                else:
                    self.temperature += single_measurement.temperature

        if single_measurement.theoretical_melt_rate is not None:
            self.contains["theoretical_melt_rate"] += 1
            if self._theoretical_melt_rate is None:
                self._theoretical_melt_rate = single_measurement.theoretical_melt_rate
            else:
                self._theoretical_melt_rate += single_measurement.theoretical_melt_rate

        if not cfg["IGNORE_PRECIPITATION_HEAT"]:
            if single_measurement.precipitation_heat is not None:
                self.contains["precipitation_heat"] += 1
                if self.precipitation_heat is None:
                    self.precipitation_heat = single_measurement.precipitation_heat
                else:
                    self.precipitation_heat += single_measurement.precipitation_heat

        if single_measurement.measured_ice_thickness is not None:
            self.contains["measured_ice_thickness"] += 1
            if self.measured_ice_thickness is None:
                self.measured_ice_thickness = single_measurement.measured_ice_thickness
            else:
                self.measured_ice_thickness += single_measurement.measured_ice_thickness

        if single_measurement.cumulated_ice_thickness is not None:
            self.contains["cumulated_ice_thickness"] += 1
            if self._cumulated_ice_thickness is None:
                self.__starting_ice_thickness = single_measurement.cumulated_ice_thickness
                self._cumulated_ice_thickness = single_measurement.cumulated_ice_thickness
            else:
                self._cumulated_ice_thickness += single_measurement.cumulated_ice_thickness

        if single_measurement.snow_depth_natural is not None:
            self.contains["snow_depth_natural"] += 1
            if self.snow_depth_natural is None:
                self.snow_depth_natural = single_measurement.snow_depth_natural
            else:
                self.snow_depth_natural += single_measurement.snow_depth_natural

        if single_measurement.snow_depth_delta_natural is not None:
            if self._snow_depth_delta_natural is None:
                self._snow_depth_delta_natural = single_measurement.snow_depth_delta_natural
            else:
                self._snow_depth_delta_natural += single_measurement.snow_depth_delta_natural

        if single_measurement.snow_depth_artificial is not None:
            self.contains["snow_depth_artificial"] += 1
            if self._snow_depth_artificial is None:
                self._snow_depth_artificial = single_measurement.snow_depth_artificial
            else:
                self._snow_depth_artificial += single_measurement.snow_depth_artificial

        if single_measurement.snow_depth_delta_artificial is not None:
            if self._snow_depth_delta_artificial is None:
                self._snow_depth_delta_artificial = single_measurement.snow_depth_delta_artificial
            else:
                self._snow_depth_delta_artificial += single_measurement.snow_depth_delta_artificial

        if single_measurement.total_energy_balance is not None:
            self.contains["total_energy_balance"] += 1
            if self._total_energy_balance is None:
                self._total_energy_balance = single_measurement.total_energy_balance
            else:
                self._total_energy_balance += single_measurement.total_energy_balance

        if 11 <= single_measurement.datetime.hour <= 13:
            self.contains["midday_albedo"] += 1
            try:
                if self.midday_albedo is None:
                    self.midday_albedo = abs(single_measurement.sw_radiation_out/single_measurement.sw_radiation_in)
                else:
                    self.midday_albedo += abs(single_measurement.sw_radiation_out/single_measurement.sw_radiation_in)
            except:  # TODO
                pass

        return self  # important

    def contains_one_valid_state_for_measure_types(self, valid_state, measure_types):
        for measure_valid_state in [self.measurement_validity[x] for x in measure_types]:
            if measure_valid_state == valid_state:
                return True
        return False

    def __ratio(self, amount_of_specific_value):
        return amount_of_specific_value/self.contains["single_measurements"]

    def __check_if_measurement_is_valid(self):
        """
        TODO rewrite
        At the end of the calculate mean fx, this function is called and according to the result of this function the
        flag is_valid gets set.
        This function is fully subjective and can be adapted as needed
        """

        for key in ["sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "air_pressure", "temperature", "wind_speed"]:
            if self.__ratio(self.contains[key]) < 0.8:
                self.measurement_validity[key] = self.valid_states["invalid"]
            else:
                self.measurement_validity[key] = self.valid_states["valid"]

        for key in ["rel_moisture"]:  # snow delta as well? ablation senseful?
            if self.__ratio(self.contains[key]) < 0.3:
                self.measurement_validity[key] = self.valid_states["invalid"]
            else:
                self.measurement_validity[key] = self.valid_states["valid"]

        for key in ["relative_ablation_measured"]:
            if getattr(self, key) is None:
                self.measurement_validity[key] = self.valid_states["invalid"]
            else:
                self.measurement_validity[key] = self.valid_states["valid"]

    def calculate_mean(self, endtime, end_ablation):
        self.__datetime_end = endtime  # first date of next measurement .. important for calculating melt water
        self.__ending_ice_thickness = end_ablation

        if self.sw_radiation_in is not None:
            self.sw_radiation_in /= self.contains["sw_radiation_in"]

        if self.sw_radiation_out is not None:
            self.sw_radiation_out /= self.contains["sw_radiation_out"]

        if self.lw_radiation_in is not None:
            self.lw_radiation_in /= self.contains["lw_radiation_in"]

        if self.lw_radiation_out is not None:
            self.lw_radiation_out /= self.contains["lw_radiation_out"]

        if self.sensible_heat is not None:
            self.sensible_heat /= self.contains["sensible_heat"]

        if self.latent_heat is not None:
            self.latent_heat /= self.contains["latent_heat"]

        if self.precipitation_heat is not None:
            self.precipitation_heat /= self.contains["precipitation_heat"]

        if cfg["PRO_VERSION"]:
            if self.temperature is not None:
                self.temperature /= self.contains["temperature"]

        if self._theoretical_melt_rate is not None:
            self._theoretical_melt_rate /= self.contains["theoretical_melt_rate"]

        if self.measured_ice_thickness is not None:
            self.measured_ice_thickness /= self.contains["measured_ice_thickness"]

        if self.snow_depth_natural is not None:
            self.snow_depth_natural /= self.contains["snow_depth_natural"]

        if self._snow_depth_artificial is not None:
            self._snow_depth_artificial /= self.contains["snow_depth_artificial"]

        if self.rel_moisture is not None:
            self.rel_moisture /= self.contains["rel_moisture"]

        if self.wind_speed is not None:
            self.wind_speed /= self.contains["wind_speed"]

        if self.air_pressure is not None:
            self.air_pressure /= self.contains["air_pressure"]

        if self._cumulated_ice_thickness is not None:
            self._cumulated_ice_thickness /= self.contains["cumulated_ice_thickness"]

            if self.__starting_ice_thickness is not None and self.__ending_ice_thickness is not None:
                self.__relative_ablation_measured = self.__starting_ice_thickness - self.__ending_ice_thickness
                if int(cfg["SET_NEGATIVE_MEASURED_ABLATION_ZERO"]):
                    if self.__relative_ablation_measured < 0:
                        self.__relative_ablation_measured = 0

        if self.midday_albedo is not None:
            self.midday_albedo /= self.contains["midday_albedo"]

        if self._total_energy_balance is not None:
            self._total_energy_balance /= self.contains["total_energy_balance"]

        self.__check_if_measurement_is_valid()

    def convert_measured_and_modeled_rel_ablations_in_water_equivalents(self):
        """
        todo bad function name

        Ablation values are:
            measured and theoretic melt water per square meter in given time frame of mean measurement
            measured and theoretic mm water equivalent per day
            theoretic ablation in liters or kg of water
        """
        if self.__relative_ablation_measured is not None:
            self.__actual_melt_water_per_sqm = energy_balance.singleton.meter_ablation_to_melt_water(
                self.__relative_ablation_measured)

            self.__actual_mm_we_per_d = energy_balance.singleton.melt_water_per_m2_to_mm_we_per_d(
                self.__actual_melt_water_per_sqm, self.__datetime_end - self.__datetime_begin)

        if self._theoretical_melt_rate is not None:
            self.__theoretical_melt_water_per_sqm = energy_balance.singleton.meltrate_to_melt_water(
                self._theoretical_melt_rate, self.__datetime_end - self.__datetime_begin)

            self.__theoretical_mm_we_per_d = energy_balance.singleton.melt_rate_to_mm_we_per_d(
                self._theoretical_melt_rate)
            if self.total_snow_depth == 0:  # not the right place probably there for this todo, __relative_ablation_measured is set in summing process
                self.__relative_ablation_modelled = energy_balance.singleton.melt_water_to_meter_ablation(
                    self.__theoretical_melt_water_per_sqm)
            else:
                self.__relative_ablation_modelled = 0

    def replace_measure_mean_of(self, mean_measurements, measure_name):
        measures = []
        for mean_measurement in mean_measurements:
            mean_measurement: MeanStationMeasurement
            measures.append(getattr(mean_measurement, measure_name))
        setattr(self, measure_name, mean(measures))
        self.measurement_validity[measure_name] = self.valid_states["estimated"]

    @property
    def datetime_begin(self):
        return self.__datetime_begin

    @property
    def datetime_end(self):
        return self.__datetime_end

    @property
    def relative_ablation_measured(self):
        return self.__relative_ablation_measured

    @relative_ablation_measured.setter
    def relative_ablation_measured(self, val):
        self.__relative_ablation_measured = val

    @property
    def relative_ablation_modelled(self):
        return self.__relative_ablation_modelled

    @property
    def actual_mm_we_per_d(self):
        return self.__actual_mm_we_per_d

    @property
    def theoretical_mm_we_per_d(self):
        return self.__theoretical_mm_we_per_d

    @property
    def actual_melt_water_per_sqm(self):
        return self.__actual_melt_water_per_sqm

    @property
    def theoretical_melt_water_per_sqm(self):
        return self.__theoretical_melt_water_per_sqm

    @property
    def datetime(self):
        return self.__datetime_begin + (self.__datetime_end - self.__datetime_begin) / 2
