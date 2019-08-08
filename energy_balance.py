import math as m
from manage_config import cfg


class EnergyBalance:
    def __init__(self):
        k_0 = 0.4

        # z_0 - surface roughness parameter (Table 5.4 in Cuffey and Paterson 2010 state: Ice in ablation zone 1-5 mm
        z_0 = 0.003  # m
        z = 1.55  # m - see AWS-Pasterze-Metadata.xlsx

        self.c_star = self.calculate_c_star(k_0, z_0, z)

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

    def calculate_sensible_heat(self, air_pressure, wind_speed, temperature):  # E_E
        t_s = 0  # Temperature of ice surface (0 on melting surfaces)

        return 0.0129 * self.c_star * air_pressure * wind_speed * (temperature - t_s)

    def calculate_latent_heat(self, temperature, rel_moisture):  # E_H
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

        return 22.2 * self.c_star * v * (e - e_s)


    def calculate_precipitation_heat(self):
        # not implemented as there sadly is no information given about the rain rate m/s
        return 0


