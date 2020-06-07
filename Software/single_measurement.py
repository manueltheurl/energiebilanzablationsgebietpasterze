from datetime import datetime as dt
import energy_balance
from manage_config import cfg


class Measurement:
    def __init__(self, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation):

        self._ablation = ablation  # this represents the ice thickness at the point of measurement
        self._theoretical_melt_rate = None
        self._cumulated_ablation = None
        # sw out and lw out are negative here even though they are technically positive .. sum of the dict is actual
        # energy balance then
        self._energy_balance_components = {
            "sw_radiation_in": sw_radiation_in,
            "sw_radiation_out": sw_radiation_out,
            "lw_radiation_in": lw_radiation_in,
            "lw_radiation_out": lw_radiation_out,
            "sensible_heat": None,  # None, cause else 0 line would be plotted
            "latent_heat": None,
            "precipitation_heat": None,  # NOT calculating currently
        }

        self._simulate_global_brightening = None

        self._temperature = temperature
        self._snow_depth_natural = snow_depth  # WARNING, some crazy data here unedited
        self._snow_depth_delta_natural = None  # increasing of snow y data here
        self._snow_depth_artificial = None
        self._snow_depth_delta_artificial = None

        self._total_energy_balance = None

        self._swe_input_from_snow = None  # unit TODO

        self._rel_moisture = rel_moisture  # in percent*100 .. e.g. 67
        self._wind_speed = wind_speed
        self._wind_direction = wind_direction
        self._air_pressure = air_pressure
        self._zenith_angle = zenith_angle
        self._tiltx = tiltx
        self._tilty = tilty

    def change_albedo(self, new_albedo):
        self._energy_balance_components["sw_radiation_out"] = -self._energy_balance_components["sw_radiation_in"] * new_albedo

    def calculate_energy_balance(self, simulate_global_dimming_brightening=0):
        # if self._total_energy_balance is not None:  # so that we wont recalculate for nothing
        # .. since simulate dimming, not anymore cause same measurement can have different actual values
        #     return

        if simulate_global_dimming_brightening:
            self._simulate_global_brightening = simulate_global_dimming_brightening

        if None not in [self._air_pressure, self._wind_speed, self._temperature,
                        self._energy_balance_components["lw_radiation_out"]]:
            self._energy_balance_components["sensible_heat"] = energy_balance.singleton.calculate_sensible_heat(
                self._air_pressure,
                self._wind_speed,
                self._temperature,
                self._energy_balance_components["lw_radiation_out"],
                self.total_snow_depth
            )

        if None not in [self._temperature, self._rel_moisture, self._wind_speed,
                        self._energy_balance_components["lw_radiation_out"]]:
            self._energy_balance_components["latent_heat"] = energy_balance.singleton.calculate_latent_heat(
                self._temperature,
                self._rel_moisture,
                self._wind_speed,
                self._energy_balance_components["lw_radiation_out"],
                self.total_snow_depth
            )

        if None not in [None]:
            self._energy_balance_components[
                "precipitation_heat"] = energy_balance.singleton.calculate_precipitation_heat()

        try:
            self._total_energy_balance = sum([self.sw_radiation_in,  # get it over property cause may be glob br. simul
                                               self._energy_balance_components["sw_radiation_out"],
                                               self._energy_balance_components["lw_radiation_in"],
                                               self._energy_balance_components["lw_radiation_out"],
                                               self._energy_balance_components["sensible_heat"],
                                               self._energy_balance_components["latent_heat"],
                                               ])
            if not cfg["IGNORE_PRECIPITATION_HEAT"]:
                self._total_energy_balance += self._energy_balance_components["precipitation_heat"]
        except TypeError:
            pass

    def calculate_theoretical_melt_rate(self):
        if None not in [self._total_energy_balance]:
            self._theoretical_melt_rate = energy_balance.singleton.energy_balance_to_melt_rate(
                self._total_energy_balance
            )
            # TODO NO NEGATIVE MELT RATE, DOES IT AFFECT SOMETHING ELSE?
            self._theoretical_melt_rate = 0 if self._theoretical_melt_rate < 0 else self._theoretical_melt_rate


    @property
    def total_snow_depth(self):
        try:
            return self._snow_depth_natural + self._snow_depth_artificial
        except TypeError:
            return self._snow_depth_natural

    @property
    def temperature(self):
        return self._temperature

    @property
    def rel_moisture(self):
        return self._rel_moisture

    @property
    def wind_speed(self):
        return self._wind_speed

    @property
    def wind_direction(self):
        return self._wind_direction

    @property
    def air_pressure(self):
        return self._air_pressure

    @property
    def sw_radiation_in(self):
        if self._simulate_global_brightening is not None:
            return self._energy_balance_components["sw_radiation_in"] + self._simulate_global_brightening
        return self._energy_balance_components["sw_radiation_in"]

    @property
    def sw_radiation_out(self):
        return self._energy_balance_components["sw_radiation_out"]

    @sw_radiation_out.setter
    def sw_radiation_out(self, value):
        self._energy_balance_components["sw_radiation_out"] = value

    @property
    def lw_radiation_in(self):
        return self._energy_balance_components["lw_radiation_in"]

    @property
    def lw_radiation_out(self):
        return self._energy_balance_components["lw_radiation_out"]

    @property
    def sensible_heat(self):
        return self._energy_balance_components["sensible_heat"]

    @property
    def latent_heat(self):
        return self._energy_balance_components["latent_heat"]

    @property
    def precipitation_energy(self):
        return self._energy_balance_components["precipitation_heat"]

    @property
    def zenith_angle(self):
        return self._zenith_angle

    @property
    def tiltx(self):
        return self._tiltx

    @property
    def tilty(self):
        return self._tilty

    @property
    def snow_depth_natural(self):
        return self._snow_depth_natural

    @snow_depth_natural.setter
    def snow_depth_natural(self, new_value):
        if new_value is not None:
            self._snow_depth_natural = new_value

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
        return self._swe_input_from_snow

    @swe_input_from_snow.setter
    def swe_input_from_snow(self, value):
        self._swe_input_from_snow = value

    @property
    def ablation(self):
        return self._ablation

    @property
    def cumulated_ablation(self):
        return self._cumulated_ablation

    @cumulated_ablation.setter
    def cumulated_ablation(self, new_value):
        # for clearning the ablation values
        self._cumulated_ablation = new_value

    @property
    def total_energy_balance(self):
        return self._total_energy_balance

    @property
    def theoretical_melt_rate(self):
        return self._theoretical_melt_rate


class SingleMeasurement(Measurement):
    """
    Object refers to one single measurement
    Values can be read but NOT be modified
    """

    def __init__(self,
                 datetime: dt, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation
                 ):

        Measurement.__init__(self, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation)

        self.__datetime = datetime

    @property
    def datetime(self):
        return self.__datetime


class MeanMeasurement(Measurement):
    """
    Object refers to the sum of multiple single measurements
    Values can be read but NOT be modified
    """

    def __init__(self):
        Measurement.__init__(self, None, None, None, None, None, None,
                 None, None, None, None, None, None, None, None)

        self.__relative_ablation_measured = None
        self.__relative_ablation_modelled = None

        self.__starting_ablation = None
        self.__ending_ablation = None

        self.__datetime_begin = None
        self.__datetime_end = None

        self.__actual_mm_we_per_d = None
        self.__theoretical_mm_we_per_d = None

        self.__actual_melt_water_per_sqm = None
        self.__theoretical_melt_water_per_sqm = None

        self.contains_sw_in = 0
        self.contains_sw_out = 0
        self.contains_lw_in = 0
        self.contains_lw_out = 0
        self.contains_sensible_heat = 0
        self.contains_latent_heat = 0
        self.contains_precipitation_heat = 0
        self.contains_total_energy_balance = 0
        self.contains_ablation = 0
        self.contains_cumulated_ablation = 0
        self.contains_theoretical_melt_rate = 0
        self.contains_snow_depth_natural = 0
        self.contains_snow_depth_artificial = 0
        self.contains_rel_moisture = 0
        self.contains_wind_speed = 0
        self.contains_air_pressure = 0

        if cfg["PRO_VERSION"]:
            self._temperature = None
            self.contains_temperature = 0

    def __iadd__(self, single_measurement: SingleMeasurement):
        if self.__datetime_begin is None or single_measurement.datetime < self.__datetime_begin:
            self.__datetime_begin = single_measurement.datetime

        if single_measurement.rel_moisture is not None:
            self.contains_rel_moisture += 1
            if self._rel_moisture is None:
                self._rel_moisture = single_measurement.rel_moisture
            else:
                self._rel_moisture += single_measurement.rel_moisture

        if single_measurement.wind_speed is not None:
            self.contains_wind_speed += 1
            if self._wind_speed is None:
                self._wind_speed = single_measurement.wind_speed
            else:
                self._wind_speed += single_measurement.wind_speed

        if single_measurement.air_pressure is not None:
            self.contains_air_pressure += 1
            if self._air_pressure is None:
                self._air_pressure = single_measurement.air_pressure
            else:
                self._air_pressure += single_measurement.air_pressure

        if single_measurement.sw_radiation_in is not None:
            self.contains_sw_in += 1
            if self._energy_balance_components["sw_radiation_in"] is None:
                self._energy_balance_components["sw_radiation_in"] = single_measurement.sw_radiation_in
            else:
                self._energy_balance_components["sw_radiation_in"] += single_measurement.sw_radiation_in

        if single_measurement.sw_radiation_out is not None:
            self.contains_sw_out += 1
            if self._energy_balance_components["sw_radiation_out"] is None:
                self._energy_balance_components["sw_radiation_out"] = single_measurement.sw_radiation_out
            else:
                self._energy_balance_components["sw_radiation_out"] += single_measurement.sw_radiation_out

        if single_measurement.lw_radiation_in is not None:
            self.contains_lw_in += 1
            if self._energy_balance_components["lw_radiation_in"] is None:
                self._energy_balance_components["lw_radiation_in"] = single_measurement.lw_radiation_in
            else:
                self._energy_balance_components["lw_radiation_in"] += single_measurement.lw_radiation_in

        if single_measurement.lw_radiation_out is not None:
            self.contains_lw_out += 1
            if self._energy_balance_components["lw_radiation_out"] is None:
                self._energy_balance_components["lw_radiation_out"] = single_measurement.lw_radiation_out
            else:
                self._energy_balance_components["lw_radiation_out"] += single_measurement.lw_radiation_out

        if single_measurement.sensible_heat is not None:
            self.contains_sensible_heat += 1
            if self._energy_balance_components["sensible_heat"] is None:
                self._energy_balance_components["sensible_heat"] = single_measurement.sensible_heat
            else:
                self._energy_balance_components["sensible_heat"] += single_measurement.sensible_heat

        if single_measurement.latent_heat is not None:
            self.contains_latent_heat += 1
            if self._energy_balance_components["latent_heat"] is None:
                self._energy_balance_components["latent_heat"] = single_measurement.latent_heat
            else:
                self._energy_balance_components["latent_heat"] += single_measurement.latent_heat

        if cfg["PRO_VERSION"]:
            if single_measurement.temperature is not None:
                self.contains_temperature += 1
                if self._temperature is None:
                    self._temperature = single_measurement.temperature
                else:
                    self._temperature += single_measurement.temperature

        if single_measurement.theoretical_melt_rate is not None:
            self.contains_theoretical_melt_rate += 1
            if self._theoretical_melt_rate is None:
                self._theoretical_melt_rate = single_measurement.theoretical_melt_rate
            else:
                self._theoretical_melt_rate += single_measurement.theoretical_melt_rate

        if not cfg["IGNORE_PRECIPITATION_HEAT"]:
            if single_measurement.precipitation_energy is not None:
                self.contains_precipitation_heat += 1
                if self._energy_balance_components["precipitation_heat"] is None:
                    self._energy_balance_components["precipitation_heat"] = single_measurement.precipitation_energy
                else:
                    self._energy_balance_components["precipitation_heat"] += single_measurement.precipitation_energy

        if single_measurement.ablation is not None:
            self.contains_ablation += 1
            if self._ablation is None:
                self._ablation = single_measurement.ablation
            else:
                self._ablation += single_measurement.ablation

        if single_measurement.cumulated_ablation is not None:
            self.contains_cumulated_ablation += 1
            if self._cumulated_ablation is None:
                self.__starting_ablation = single_measurement.cumulated_ablation
                self._cumulated_ablation = single_measurement.cumulated_ablation
            else:
                self._cumulated_ablation += single_measurement.cumulated_ablation

        if single_measurement.snow_depth_natural is not None:
            self.contains_snow_depth_natural += 1
            if self._snow_depth_natural is None:
                self._snow_depth_natural = single_measurement.snow_depth_natural
            else:
                self._snow_depth_natural += single_measurement.snow_depth_natural

        if single_measurement.snow_depth_delta_natural is not None:
            if self._snow_depth_delta_natural is None:
                self._snow_depth_delta_natural = single_measurement.snow_depth_delta_natural
            else:
                self._snow_depth_delta_natural += single_measurement.snow_depth_delta_natural

        if single_measurement.snow_depth_artificial is not None:
            self.contains_snow_depth_artificial += 1
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
            self.contains_total_energy_balance += 1
            if self._total_energy_balance is None:
                self._total_energy_balance = single_measurement.total_energy_balance
            else:
                self._total_energy_balance += single_measurement.total_energy_balance

        return self  # important

    def calculate_mean(self, endtime, end_ablation):
        self.__datetime_end = endtime  # first date of next measurement .. important for calculating melt water
        self.__ending_ablation = end_ablation

        if self._energy_balance_components["sw_radiation_in"] is not None:
            self._energy_balance_components["sw_radiation_in"] /= self.contains_sw_in

        if self._energy_balance_components["sw_radiation_out"] is not None:
            self._energy_balance_components["sw_radiation_out"] /= self.contains_sw_out

        if self._energy_balance_components["lw_radiation_in"] is not None:
            self._energy_balance_components["lw_radiation_in"] /= self.contains_lw_in

        if self._energy_balance_components["lw_radiation_out"] is not None:
            self._energy_balance_components["lw_radiation_out"] /= self.contains_lw_out

        if self._energy_balance_components["sensible_heat"] is not None:
            self._energy_balance_components["sensible_heat"] /= self.contains_sensible_heat

        if self._energy_balance_components["latent_heat"] is not None:
            self._energy_balance_components["latent_heat"] /= self.contains_latent_heat

        if self._energy_balance_components["precipitation_heat"] is not None:
            self._energy_balance_components["precipitation_heat"] /= self.contains_precipitation_heat

        if cfg["PRO_VERSION"]:
            if self._temperature is not None:
                self._temperature /= self.contains_temperature

        if self._theoretical_melt_rate is not None:
            self._theoretical_melt_rate /= self.contains_theoretical_melt_rate

        if self._ablation is not None:
            self._ablation /= self.contains_ablation

        if self._snow_depth_natural is not None:
            self._snow_depth_natural /= self.contains_snow_depth_natural

        if self._snow_depth_artificial is not None:
            self._snow_depth_artificial /= self.contains_snow_depth_artificial

        if self._rel_moisture is not None:
            self._rel_moisture /= self.contains_rel_moisture

        if self._wind_speed is not None:
            self._wind_speed /= self.contains_wind_speed

        if self._air_pressure is not None:
            self._air_pressure /= self.contains_air_pressure

        if self._cumulated_ablation is not None:
            self._cumulated_ablation /= self.contains_cumulated_ablation

            if self.__starting_ablation is not None and self.__ending_ablation is not None:
                self.__relative_ablation_measured = self.__ending_ablation - self.__starting_ablation

        if self._total_energy_balance is not None:
            self._total_energy_balance /= self.contains_total_energy_balance

    def calculate_ablation_and_theoretical_melt_rate_to_meltwater_per_square_meter(self):
        if True:  # TODO AND previously: self.is_snow_covered is False:  # dontcalculate_ablation_and_theoretical_melt_rate_to_meltwater_per_square_meter change, None is False also
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

                self.__relative_ablation_modelled = energy_balance.singleton.melt_water_to_meter_ablation(
                    self.__theoretical_melt_water_per_sqm)

    @property
    def datetime_begin(self):
        return self.__datetime_begin

    @property
    def relative_ablation_measured(self):
        return self.__relative_ablation_measured

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
    def albedo(self):
        return abs(self.sw_radiation_out/self.sw_radiation_in)

    @property
    def actual_melt_water_per_sqm(self):
        return self.__actual_melt_water_per_sqm

    @property
    def theoretical_melt_water_per_sqm(self):
        return self.__theoretical_melt_water_per_sqm

    @property
    def datetime(self):
        return self.__datetime_begin + (self.__datetime_end - self.__datetime_begin) / 2
