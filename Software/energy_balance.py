import math as m
from manage_config import cfg
import datetime as dt


KARMANS_CONSTANT = 0.4
STEFAN_BOLTZMANN_CONSTANT = 5.670 * 10**-8
ABSOLUTE_ZERO_DEGREE_CELSIUS = -273.15
PURE_ICE_DENSITY_AT_ZERO_DEG = 917  # kg/cubic meter  - taken from P. 142 Cuffey and Paterson
WATER_DENSITY_AT_ZERO_DEG = 1000  # kg/cubic meter  - taken from P. 142 Cuffey and Paterson
PURE_ICE_LATENT_HEAD_OF_FUSION_AT_ZERO_DEG = 3.34 * 10 ** 5  # J/kg  - taken from P. 142 Cuffey and Paterson
ONE_YEAR = dt.timedelta(days=365)
ONE_DAY = dt.timedelta(days=1)


class EnergyBalance:
    singleton_created = False

    def __init__(self):
        if EnergyBalance.singleton_created:
            raise Exception("EnergyBalance is a singleton")
        EnergyBalance.singleton_created = True

        # see AWS-Pasterze-Metadata.xlsx
        # sensor_height_temperature = 1.55  # m  .. not in use
        self.sensor_height_wind = 5  # m

        self.c_star = {
            "ice": self.calculate_c_star(float(cfg["Z_0_ROUGHNESS_ICE"])),
            "snow": self.calculate_c_star(float(cfg["Z_0_ROUGHNESS_SNOW"])),
        }

    def calculate_c_star(self, z_0):
        """
        C* is called the transfer coefficient
        The value of c star depends on measurement height and a bit on surface roughness
        see http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0016-71692015000400299 under eq 10 that
        the sensor_height_wind is meant
        """

        # c - transfer coefficient
        # .. Cuffey and Paterson 2010 state that this is in the range 0.002 to 0.004
        return KARMANS_CONSTANT**2/m.log(self.sensor_height_wind / z_0)**2

    @staticmethod
    def calculate_ice_temperature(outgoing_energy):
        # I = e * STEFAN_BOLTZMANN_CONSTANT * T**4
        # e -> emmissivity ~ 1 -> snow and ice act like a black body in the infrared

        if not cfg["CALCULATE_ICE_TEMPERATURE_WITH_STEFAN_BOLTZMANN"]:
            return 0

        temperature = (abs(outgoing_energy)/STEFAN_BOLTZMANN_CONSTANT)**(1/4) + ABSOLUTE_ZERO_DEGREE_CELSIUS  # 4th sqrt

        if temperature > 0:  # ice cant have positive degrees
            return 0

        return temperature

    def calculate_sensible_heat(self, air_pressure, wind_speed, temperature, longwave_out, snow_depth):  # E_E
        # air_pressure in Pa
        # wind_speed in m/s

        temperature_ice = self.calculate_ice_temperature(longwave_out)  # degree celcius

        surface_type = "ice" if snow_depth <= 0 else "snow"

        return 0.0129 * self.c_star[surface_type] * air_pressure * wind_speed * (temperature - temperature_ice)

    def calculate_latent_heat(self, temperature, rel_moisture, wind_speed, longwave_out, snow_depth,
                              use_standard_fomula=True):
        # E_H
        # https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

        # or https://books.google.at/books?id=Zi1coMyhlHoC&lpg=PP1&pg=PA350&hl=en&redir_esc=y#v=onepage&q&f=false
        # see also post https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit for that

        # e_surface - vapor pressure at the surface [Pa] - assuming saturation  TODO find proof for that function
        # * 1000 for converting to Pa
        e_air_saturated = (0.6108 * m.e ** (17.27 * temperature / (temperature + 237.3))) * 1000
        e_air = rel_moisture / 100 * e_air_saturated

        if use_standard_fomula:
            e_surface_saturated = (0.6108 * m.e ** (
                        17.27 * self.calculate_ice_temperature(longwave_out) /
                        (self.calculate_ice_temperature(longwave_out) + 237.3))) * 1000  # * 1000 for converting to Pa
        else:
            e_surface_saturated = 100 * 6.11 * m.e ** (((2.5 * 10 ** 6) / 461) * (1/273 - 1/(self.calculate_ice_temperature(longwave_out) - ABSOLUTE_ZERO_DEGREE_CELSIUS)))

        # http://www.fao.org/3/X0490E/x0490e07.htm confirms eq 12 states, that unit is kPa even .. TODO proof ..
        # https://www.hydrol-earth-syst-sci.net/17/1331/2013/hess-17-1331-2013-supplement.pdf .. S2.5  kPa here as well
        # -> should be enough proof

        # e_air - vapor pressure above the surface [Pa]

        u = wind_speed
        # http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0016-71692015000400299 PROOFS THAT ITS THE WIND SPEED INDEED
        # TODO take a look in this article above on eq 14,  there P woiuld be the air pressure which we have, take it?

        # e - e_s is actually the vapor Pressure Deficit  -- https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

        # TODO e_air and e_surface is Pa .. yes it is .. proof in 05_VO_Mountainhydrology Page 22

        surface_type = "ice" if snow_depth <= 0 else "snow"

        return 22.2 * self.c_star[surface_type] * u * (e_air - e_surface_saturated)

    @staticmethod
    def calculate_precipitation_heat():
        # not implemented as there sadly is no information given about the rain rate m/s
        return 0

    @staticmethod
    def meter_ablation_to_melt_water(meter_ablation):
        if meter_ablation <= 0:  # if melted
            return abs(meter_ablation) * PURE_ICE_DENSITY_AT_ZERO_DEG
        return 0

    @staticmethod
    def melt_water_per_m2_to_mm_we_per_d(melt_water, time_interval):
        # 1 liter equals one mm
        # melt_water_in liters here
        return melt_water * ONE_DAY/time_interval

    @staticmethod
    def melt_rate_to_mm_we_per_d(melt_rate):
        # 1 liter equals one mm
        return melt_rate * ONE_DAY.total_seconds() * 1000

    @staticmethod
    def melt_water_to_meter_ablation(melt_water):
        if melt_water >= 0:
            return - melt_water / PURE_ICE_DENSITY_AT_ZERO_DEG
        return 0

    @staticmethod
    def meltrate_to_melt_water(melt_rate, timespawn):
        return melt_rate * timespawn.total_seconds() * 1000  # * 1000 cause result is in m^3, and not liter (dm^3)

    @staticmethod
    def energy_balance_to_melt_rate(energy_balance):
        return energy_balance/(WATER_DENSITY_AT_ZERO_DEG * PURE_ICE_LATENT_HEAD_OF_FUSION_AT_ZERO_DEG)


singleton = EnergyBalance()
