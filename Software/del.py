import unittest
import energy_balance

pressure = 80000  # Pa
rel_moisture = 60  # %
windspeed = 10  # m per second
air_temperature = 5  # degree celcius
longwave_out = 1000  # "to a melting surface"  -> ice temp will be 0 then

energy_balance.singleton.c_star[
    "ice"] = 0.002  # in test setup this is the value given, and with arg snow_depth=0 we force that

for windspeed in range(0, 15, 2):
    sensible_heat = energy_balance.singleton.calculate_sensible_heat(pressure,
                                                                     windspeed, air_temperature, longwave_out, snow_depth=0)

    sensible_heat2 = energy_balance.singleton.calculate_sensible_heat(pressure,
                                                                      windspeed, air_temperature, longwave_out, snow_depth=0,
                                                                      use_bulk=False)
    # print("SENSIBLE: wind speed", windspeed, "we:", sensible_heat, "her:", sensible_heat2)

    latent_heat = energy_balance.singleton.calculate_latent_heat(air_temperature,
                                                                     rel_moisture, windspeed, longwave_out, pressure, 0)

    latent_heat2 = energy_balance.singleton.calculate_latent_heat(air_temperature,
                                                                     rel_moisture, windspeed, longwave_out, pressure, 0, use_bulk=False)

    print("LATENT: wind speed", windspeed, "we:", sensible_heat, "her:", sensible_heat2)



