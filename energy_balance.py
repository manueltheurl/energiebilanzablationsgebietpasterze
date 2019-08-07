import math as m
from manage_config import cfg


class EnergyBalance:
    @staticmethod
    def calculate_sensible_heat(air_pressure, wind_speed, temperature, c_star):  # E_E
        t_s = 0  # Temperature of ice surface (0 on melting surfaces)

        return 0.0129 * c_star * air_pressure * wind_speed * (temperature - t_s)

    @staticmethod
    def calculate_latent_heat(temperature, rel_moisture, c_star):  # E_H
        # https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

        # or https://books.google.at/books?id=Zi1coMyhlHoC&lpg=PP1&pg=PA350&hl=en&redir_esc=y#v=onepage&q&f=false
        # see also post https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit for that

        # e_s - vapor pressure at the surface - assuming saturation  TODO find proof for that function
        e_s = 0.6108 * m.e ** (17.27 * temperature / (temperature + 237.3))

        # e - vapor pressure above the surface

        e = rel_moisture / 100 * e_s

        # v - ?? remember that:  L v/s is the latent heat of vaporization or sublimation  .. so maybe the rel humidity?
        v = rel_moisture  # TODO is that correct?

        # e - e_s is actually the vapor Pressure Deficit  -- https://physics.stackexchange.com/questions/4343/how-can-i-calculate-vapor-pressure-deficit-from-temperature-and-relative-humidit

        return 22.2 * c_star * v * (e - e_s)
    @staticmethod
    def calculate_c_star(k_0, z, z_0):
        """
        The value of c star depends on measurement height and a bit on surface roughness
        """
        # k_0 - Kármán’s constant

        # TODO temperature and wind speed are NOT measured at same height (1.55m and 5m)
        #  -> this has to be taken into account

        # c - transer coefficient
        return k_0**2/m.log(z / z_0)**2  # .. Cuffey and Paterson 2010 state that this is in the range 0.002 to 0.004

    """
    Could be done directly in single_measurement but as this is the main and most important part of the program
    it is written separately
    """
    @staticmethod
    def calculate_energy_balance(single_measurement):
        if None in [single_measurement.lw_radiation_in, single_measurement.lw_radiation_out,
                    single_measurement.sw_radiation_in, single_measurement.sw_radiation_out,
                    single_measurement.temperature]:
            return None

        net_radiation = single_measurement.lw_radiation_in - single_measurement.lw_radiation_out + \
                        single_measurement.sw_radiation_in - single_measurement.sw_radiation_out

        energy_balance = net_radiation

        # do some crazy calculations here

        k_0 = 0.4
        # z_0 - surface roughness parameter (Table 5.4 in Cuffey and Paterson 2010 state: Ice in ablation zone 1-5 mm
        z_0 = 0.003  # m
        z = 1.55  # m - see AWS-Pasterze-Metadata.xlsx

        c_star = EnergyBalance.calculate_c_star(k_0, z_0, z)
        e_h = EnergyBalance.calculate_sensible_heat(single_measurement.air_pressure, single_measurement.wind_speed, single_measurement.temperature, c_star)
        e_e = EnergyBalance.calculate_latent_heat(single_measurement.temperature, single_measurement.rel_moisture, c_star)

        energy_balance += e_h + e_e

        # TODO maybe save all components separately to have the possibility to plot all standalone

        # What would be left is E_p which stands for the energy input due to precipitation
        # and E_g  .. the energy stream under the glacier surface

        return energy_balance

