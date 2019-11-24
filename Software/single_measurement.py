from datetime import datetime as dt
import energy_balance
from manage_config import cfg


class SingleMeasurement:
    """
    Object refers to one single measurement
    Values can be read but NOT be modified
    """

    def __init__(self,
                 datetime: dt, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
                 sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation
                 ):

        # sw out and lw out are negative here even though they are technically positive .. sum of the dict is actual
        # energy balance then

        self.__energy_balance_components = {
            "sw_radiation_in": sw_radiation_in,
            "sw_radiation_out": sw_radiation_out,
            "lw_radiation_in": lw_radiation_in,
            "lw_radiation_out": lw_radiation_out,
            "sensible_heat": None,  # None, cause else 0 line would be plotted
            "latent_heat": None,
        }
        if not cfg["IGNORE_PRECIPITATION_HEAT"]:
            self.__energy_balance_components["precipitation_heat"] = None

        self.__datetime = datetime
        self.__temperature = temperature
        self.__rel_moisture = rel_moisture  # in percent*100 .. e.g. 67
        self.__wind_speed = wind_speed
        self.__wind_direction = wind_direction
        self.__air_pressure = air_pressure
        self.__zenith_angle = zenith_angle
        self.__tiltx = tiltx
        self.__tilty = tilty
        self.__snow_depth = snow_depth  # WARNING, some crazy data here
        self.__ablation = ablation  # this represents the ice thickness at the point of measurement
        self.__cumulated_ablation = None
        self.__theoretical_melt_rate = None
        self.__total_energy_balance = None  # not calculated yet
        self.__simulate_global_brightening = None

        self.is_snow_covered = None

    def calculate_energy_balance(self, simulate_global_dimming_brightening=0):
        # if self.__total_energy_balance is not None:  # so that we wont recalculate for nothing
        # .. since simulate dimming, not anymore cause same measurement can have different actual values
        #     return

        if simulate_global_dimming_brightening != 0:
            self.__simulate_global_brightening = simulate_global_dimming_brightening

        if None not in [self.__air_pressure, self.__wind_speed, self.__temperature,
                        self.__energy_balance_components["lw_radiation_out"]]:
            self.__energy_balance_components["sensible_heat"] = energy_balance.singleton.calculate_sensible_heat(
                self.__air_pressure,
                self.__wind_speed,
                self.__temperature,
                self.__energy_balance_components["lw_radiation_out"]
            )

        if None not in [self.__temperature, self.__rel_moisture, self.__wind_speed, self.__energy_balance_components["lw_radiation_out"]]:
            self.__energy_balance_components["latent_heat"] = energy_balance.singleton.calculate_latent_heat(
                self.__temperature,
                self.__rel_moisture,
                self.__wind_speed,
                self.__energy_balance_components["lw_radiation_out"]
            )

        if None not in [None]:
            self.__energy_balance_components["precipitation_heat"] = energy_balance.singleton.calculate_precipitation_heat()

        if None not in self.__energy_balance_components.values():
            self.__total_energy_balance = sum([self.sw_radiation_in,  # get it over property cause may be glob br. simul
                                               self.__energy_balance_components["sw_radiation_out"],
                                               self.__energy_balance_components["lw_radiation_in"],
                                               self.__energy_balance_components["lw_radiation_out"],
                                               self.__energy_balance_components["sensible_heat"],
                                               self.__energy_balance_components["latent_heat"],
                                               ])

            if not cfg["IGNORE_PRECIPITATION_HEAT"]:
                self.__total_energy_balance += self.__energy_balance_components["precipitation_heat"]

    def calculate_theoretical_melt_rate(self):
        if None not in [self.__total_energy_balance]:
            self.__theoretical_melt_rate = energy_balance.singleton.energy_balance_to_melt_rate(
                self.__total_energy_balance
            )

    @property
    def datetime(self):
        return self.__datetime

    @property
    def temperature(self):
        return self.__temperature

    @property
    def rel_moisture(self):
        return self.__rel_moisture

    @property
    def wind_speed(self):
        return self.__wind_speed

    @property
    def wind_direction(self):
        return self.__wind_direction

    @property
    def air_pressure(self):
        return self.__air_pressure

    @property
    def sw_radiation_in(self):
        if self.__simulate_global_brightening is not None:
            return self.__energy_balance_components["sw_radiation_in"] + self.__simulate_global_brightening
        return self.__energy_balance_components["sw_radiation_in"]

    @property
    def sw_radiation_out(self):
        return self.__energy_balance_components["sw_radiation_out"]

    @property
    def lw_radiation_in(self):
        return self.__energy_balance_components["lw_radiation_in"]

    @property
    def lw_radiation_out(self):
        return self.__energy_balance_components["lw_radiation_out"]

    @property
    def sensible_heat(self):
        return self.__energy_balance_components["sensible_heat"]

    @property
    def latent_heat(self):
        return self.__energy_balance_components["latent_heat"]

    @property
    def precipitation_energy(self):
        return self.__energy_balance_components["precipitation_heat"]

    @property
    def zenith_angle(self):
        return self.__zenith_angle

    @property
    def tiltx(self):
        return self.__tiltx

    @property
    def tilty(self):
        return self.__tilty

    @property
    def snow_depth(self):
        return self.__snow_depth

    @property
    def ablation(self):
        return self.__ablation

    @property
    def cumulated_ablation(self):
        return self.__cumulated_ablation

    @cumulated_ablation.setter
    def cumulated_ablation(self, new_value):
        # for clearning the ablation values
        self.__cumulated_ablation = new_value

    @property
    def total_energy_balance(self):
        return self.__total_energy_balance

    @property
    def theoretical_melt_rate(self):
        return self.__theoretical_melt_rate
