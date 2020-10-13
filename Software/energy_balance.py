import math as m
from config_handler import cfg
import datetime as dt


KARMANS_CONSTANT = 0.4
STEFAN_BOLTZMANN_CONSTANT = 5.670 * 10**-8
ABSOLUTE_ZERO_DEGREE_CELSIUS = -273.15
PURE_ICE_DENSITY_AT_ZERO_DEG = 917  # kg/cubic meter  - taken from P. 142 Cuffey and Paterson
WATER_DENSITY_AT_ZERO_DEG = 1000  # kg/cubic meter  - taken from P. 142 Cuffey and Paterson
LATENT_HEAD_OF_FUSION_AT_ZERO_DEG = 3.34 * 10 ** 5  # J/kg  - taken from P. 142 Cuffey and Paterson
ONE_YEAR = dt.timedelta(days=365)
ONE_DAY = dt.timedelta(days=1)


class EnergyBalance:
    # see AWS-Pasterze-Metadata.xlsx
    # sensor_height_temperature = 1.55  # m  .. not in use
    sensor_height_wind = 5  # m
    c_star = {
        "ice": 0,  # will get set right after class definition # todo better way?
        "snow": 0,
    }

    @classmethod
    def set_new_roughness_parameters(cls, z_0_ice, z_0_snow):
        cls.c_star = {
            "ice": cls.calculate_c_star(z_0_ice),
            "snow": cls.calculate_c_star(z_0_snow),
        }

    @classmethod
    def calculate_c_star(cls, z_0):
        """
        C* is called the transfer coefficient
        The value of c star depends on measurement height and a bit on surface roughness
        see http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0016-71692015000400299 under eq 10 that
        the sensor_height_wind is meant
        """

        # c - transfer coefficient
        # .. Cuffey and Paterson 2010 state that this is in the range 0.002 to 0.004
        return KARMANS_CONSTANT**2/m.log(cls.sensor_height_wind / z_0)**2

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

    @classmethod
    def calculate_sensible_heat(cls, air_pressure, wind_speed, temperature, longwave_out, snow_depth, use_bulk=True):  # E_E
        # air_pressure in Pa
        # wind_speed in m/s

        temperature_ice = cls.calculate_ice_temperature(longwave_out)  # degree celcius

        if use_bulk:
            # TODO would it be better to parse surface type already or better that way?
            surface_type = "ice" if snow_depth is None or snow_depth <= 0 else "snow"

            # if 0.0129 * cls.c_star[surface_type] * air_pressure * wind_speed * (temperature - temperature_ice) > 400:
            #     print(cls.c_star[surface_type], air_pressure, wind_speed, temperature, temperature_ice)

            return 0.0129 * cls.c_star[surface_type] * air_pressure * wind_speed * (temperature - temperature_ice)
        else:
            return 5.7*m.sqrt(wind_speed) * (temperature - temperature_ice)

    @staticmethod
    def calculate_saturation_vapor_pressure_above_water(temperature):
        """
        Formula from http://klimedia.ch/kap3/a11.html

        temperature in deg celsius
        return in Pa
        """
        return (6.107 * 10 ** (7.5 * temperature / (temperature + 237))) * 100  # hpa to pa

    @staticmethod
    def calculate_saturation_vapor_pressure_above_ice(temperature):
        """
        Formula from http://klimedia.ch/kap3/a11.html

        temperature in deg celsius
        return in Pa
        """
        return (6.107 * 10 ** (9.5 * temperature / (temperature + 265.5))) * 100  # hpa to pa

        # old approach from
        # https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit
        # or https://books.google.at/books?id=Zi1coMyhlHoC&lpg=PP1&pg=PA350&hl=en&redir_esc=y#v=onepage&q&f=false
        # see also post https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit for that
        # http://www.fao.org/3/X0490E/x0490e07.htm confirms eq 12 states, that unit is kPa even .. TODO proof ..
        # https://www.hydrol-earth-syst-sci.net/17/1331/2013/hess-17-1331-2013-supplement.pdf .. S2.5  kPa here as well
        # -> should be enough proof
        # (0.6108 * m.e ** (17.27 * temperature / (temperature + 237.3))) * 1000  # kpa to pa

    @classmethod
    def calculate_latent_heat(cls, temperature, rel_moisture, wind_speed, longwave_out, air_pressure, snow_depth,
                              use_bulk=True):
        # E_H
        # temperature in degree celsius

        e_air_saturated = cls.calculate_saturation_vapor_pressure_above_water(temperature)
        e_air = rel_moisture / 100 * e_air_saturated

        if True:
            e_surface_saturated = cls.calculate_saturation_vapor_pressure_above_ice(cls.calculate_ice_temperature(longwave_out))
        else:
            # TODO can probably be deleted
            e_surface_saturated = 100 * 6.11 * m.e ** (((2.5 * 10 ** 6) / 461) * (1/273 - 1/(cls.calculate_ice_temperature(longwave_out) - ABSOLUTE_ZERO_DEGREE_CELSIUS)))

        u = wind_speed
        # http://www.scielo.org.mx/scielo.php?script=sci_arttext&pid=S0016-71692015000400299 PROOFS THAT ITS THE WIND SPEED INDEED
        # TODO take a look in this article above on eq 14,  there P would be the air pressure which we have, take it?
        # e - e_s is actually the vapor Pressure Deficit  -- https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

        # TODO e_air and e_surface is Pa .. yes it is .. proof in 05_VO_Mountainhydrology Page 22

        surface_type = "ice" if snow_depth is None or snow_depth <= 0 else "snow"

        if use_bulk:
            return 22.2 * cls.c_star[surface_type] * u * (e_air - e_surface_saturated)
        else:
            L_v = 2.5*10**6  # Sublimationswärme von Eis ..  verdunstungswärme
            c_p = 1005  # spezifische Wärmekapazität von Luft bei konstantem Druck
            T0 = 273.15  # 0 grad celsius
            R_w = 461.5  # gaskonstante wasserdampf
            e_0 = 611  # dampfdruck am Tripelpunkt

            temperature += T0

            e_s = e_0 * m.e ** ((L_v/R_w) * (1/T0 - 1/temperature))
            e = rel_moisture/100*e_s
            q = 0.622 * e / air_pressure  # specific moisture
            q_sat = 0.622 * e_s / air_pressure  # saturated moisture?!
            return 5.7 * L_v/c_p * m.sqrt(wind_speed) * (q - q_sat)

    @staticmethod
    def calculate_precipitation_heat():
        # not implemented as there sadly is no information given about the rain rate m/s
        return 0

    warned_once_about_negative_meter_ablation = False

    @classmethod
    def meter_ablation_to_melt_water(cls, meter_ablation):
        if meter_ablation < 0:  # if melted
            if not cls.warned_once_about_negative_meter_ablation:
                print("WARNING: Ablation must be >= 0, fix measurements with set_negative_relative_ablation_zero_for_summed")
                cls.warned_once_about_negative_meter_ablation = True
        return abs(meter_ablation) * PURE_ICE_DENSITY_AT_ZERO_DEG

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
        if melt_water < 0:
            exit("Melt water must be positive")
        return melt_water / PURE_ICE_DENSITY_AT_ZERO_DEG

    @staticmethod
    def meltrate_to_melt_water(melt_rate, timespawn):
        return melt_rate * timespawn.total_seconds() * 1000  # * 1000 cause result is liters

    @staticmethod
    def energy_balance_to_melt_rate(energy_balance):
        return energy_balance/(WATER_DENSITY_AT_ZERO_DEG * LATENT_HEAD_OF_FUSION_AT_ZERO_DEG)


EnergyBalance.set_new_roughness_parameters(cfg["Z_0_ROUGHNESS_ICE"], cfg["Z_0_ROUGHNESS_SNOW"])
