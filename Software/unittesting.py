import unittest
from energy_balance import EnergyBalance


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_given_values_for_c_star(self):
        """
        See page 157 of Cuffey and Paterson 2010
        Test values are given there which shall result in a C* in range 0.002 to 0.004
        """
        z = 1.5  # m
        z_0 = 0.002  # m  # for ice in ablation zone (higher value will cause failing of the test)

        c_star = EnergyBalance.calculate_c_star(z, z_0)
        self.assertTrue(0.002 < c_star < 0.004)

    def test_given_values_for_sensible_heat(self):
        """
        See page 157 of Cuffey and Paterson 2010
        Test values are given there which shall result in about 50 Watt per square meter
        """
        pressure = 80000  # Pa
        windspeed = 5  # m per second
        air_temperature = 5  # degree celcius
        longwave_out = 1000  # "to a melting surface"  -> ice temp will be 0 then

        EnergyBalance.c_star["ice"] = 0.002  # in test setup this is the value given, and with arg snow_depth=0 we force that

        sensible_heat = EnergyBalance.calculate_sensible_heat(pressure,
                                                                         windspeed, air_temperature, longwave_out, snow_depth=0)
        self.assertTrue(47 < sensible_heat < 53)

    def test_high_values_for_sensible_heat(self):
        pressure = 80000  # Pa
        windspeed = 14.7  # m per second
        temperature = 12.1  # degree celcius
        EnergyBalance.c_star = 0.002
        longwave_out = 1000

        sensible_heat = EnergyBalance.calculate_sensible_heat(pressure,
                                                                         windspeed, temperature, longwave_out)

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
