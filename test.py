import unittest
import energy_balance


class Test(unittest.TestCase):
    def setUp(self):
        pass

    def test_given_values_for_c_star(self):
        """
        See page 157 of Cuffey and Paterson 2010
        Test values are given there which shall result in a C* in range 0.002 to 0.004
        """
        z = 1.5  # m
        k_0 = 0.4
        z_0 = 0.002  # m  # for ice in ablation zone (higher value will cause failing of the test)

        c_star = energy_balance.singleton.calculate_c_star(k_0, z, z_0)
        self.assertTrue(0.002 < c_star < 0.004)

    def test_given_values_for_sensible_heat(self):
        """
        See page 157 of Cuffey and Paterson 2010
        Test values are given there which shall result in about 50 Watt per square meter
        """
        pressure = 80000  # Pa
        windspeed = 5  # m per second
        temperature = 5  # degree celcius
        energy_balance.singleton.c_star = 0.002

        sensible_heat = energy_balance.singleton.calculate_sensible_heat(pressure, windspeed, temperature)
        self.assertTrue(47 < sensible_heat < 53)


if __name__ == '__main__':
    unittest.main()
