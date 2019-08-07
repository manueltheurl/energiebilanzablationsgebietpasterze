from datetime import datetime as dt
from energy_balance import EnergyBalance


class SingleMeasurement:
    """
    Object refers to one single measurement
    Values can be read but NOT be modified
    """
    def __init__(
            self, datetime: dt, temperature, rel_moisture, wind_speed, wind_direction, air_pressure, sw_radiation_in,
            sw_radiation_out, lw_radiation_in, lw_radiation_out, zenith_angle, tiltx, tilty, snow_depth, ablation):

        self.__datetime = datetime
        self.__temperature = temperature
        self.__rel_moisture = rel_moisture  # in percent*100 .. e.g. 67
        self.__wind_speed = wind_speed
        self.__wind_direction = wind_direction
        self.__air_pressure = air_pressure
        self.__sw_radiation_in = sw_radiation_in
        self.__sw_radiation_out = sw_radiation_out
        self.__lw_radiation_in = lw_radiation_in
        self.__lw_radiation_out = lw_radiation_out
        self.__zenith_angle = zenith_angle
        self.__tiltx = tiltx
        self.__tilty = tilty
        self.__snow_depth = snow_depth
        self.__ablation = ablation
        self.__energy_balance = None  # not calculated yet

    def calculate_energy_balance(self):
        self.__energy_balance = EnergyBalance.calculate_energy_balance(self)

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
        return self.__sw_radiation_in

    @property
    def sw_radiation_out(self):
        return self.__sw_radiation_out

    @property
    def lw_radiation_in(self):
        return self.__lw_radiation_in

    @property
    def lw_radiation_out(self):
        return self.__lw_radiation_out

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
    def energy_balance(self):
        return self.__energy_balance
