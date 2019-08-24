from single_measurement import SingleMeasurement


class MeanMeasurement:
    """
    Object refers to the sum of multiple single measurements
    Values can be read but NOT be modified
    """

    def __init__(self):
        # sw out and lw out are negative here even though they are technically positive .. sum of the dict is actual
        # energy balance then
        self.__energy_balance_components = {
            "sw_radiation_in": None,
            "sw_radiation_out": None,
            "lw_radiation_in": None,
            "lw_radiation_out": None,
            "sensible_heat": None,
            "latent_heat": None,
            "precipitation_heat": None,
        }

        self.__datetime_begin = None
        self.__datetime_end = None
        self.__total_energy_balance = None

        self.contains_sw_in = 0
        self.contains_sw_out = 0
        self.contains_lw_in = 0
        self.contains_lw_out = 0
        self.contains_sensible_heat = 0
        self.contains_latent_heat = 0
        self.contains_precipitation_heat = 0
        self.contains_total_energy_balance = 0

    def __iadd__(self, single_measurement: SingleMeasurement):
        if self.__datetime_begin is None or single_measurement.datetime < self.__datetime_begin:
            self.__datetime_begin = single_measurement.datetime

        if self.__datetime_end is None or single_measurement.datetime > self.__datetime_end:
            self.__datetime_end = single_measurement.datetime

        if single_measurement.sw_radiation_in is not None:
            self.contains_sw_in += 1

            if self.__energy_balance_components["sw_radiation_in"] is None:
                self.__energy_balance_components["sw_radiation_in"] = single_measurement.sw_radiation_in
            else:
                self.__energy_balance_components["sw_radiation_in"] += single_measurement.sw_radiation_in

        if single_measurement.sw_radiation_out is not None:
            self.contains_sw_out += 1
            if self.__energy_balance_components["sw_radiation_out"] is None:
                self.__energy_balance_components["sw_radiation_out"] = single_measurement.sw_radiation_out
            else:
                self.__energy_balance_components["sw_radiation_out"] += single_measurement.sw_radiation_out

        if single_measurement.lw_radiation_in is not None:
            self.contains_lw_in += 1
            if self.__energy_balance_components["lw_radiation_in"] is None:
                self.__energy_balance_components["lw_radiation_in"] = single_measurement.lw_radiation_in
            else:
                self.__energy_balance_components["lw_radiation_in"] += single_measurement.lw_radiation_in

        if single_measurement.lw_radiation_out is not None:
            self.contains_lw_out += 1
            if self.__energy_balance_components["lw_radiation_out"] is None:
                self.__energy_balance_components["lw_radiation_out"] = single_measurement.lw_radiation_out
            else:
                self.__energy_balance_components["lw_radiation_out"] += single_measurement.lw_radiation_out

        if single_measurement.sensible_heat is not None:
            self.contains_sensible_heat += 1
            if self.__energy_balance_components["sensible_heat"] is None:
                self.__energy_balance_components["sensible_heat"] = single_measurement.sensible_heat
            else:
                self.__energy_balance_components["sensible_heat"] += single_measurement.sensible_heat

        if single_measurement.latent_heat is not None:
            self.contains_latent_heat += 1
            if self.__energy_balance_components["latent_heat"] is None:
                self.__energy_balance_components["latent_heat"] = single_measurement.latent_heat
            else:
                self.__energy_balance_components["latent_heat"] += single_measurement.latent_heat

        if single_measurement.precipitation_energy is not None:
            self.contains_precipitation_heat += 1
            if self.__energy_balance_components["precipitation_heat"] is None:
                self.__energy_balance_components["precipitation_heat"] = single_measurement.precipitation_energy
            else:
                self.__energy_balance_components["precipitation_heat"] += single_measurement.precipitation_energy

        if single_measurement.total_energy_balance is not None:
            self.contains_total_energy_balance += 1
            if self.__total_energy_balance is None:
                self.__total_energy_balance = single_measurement.total_energy_balance
            else:
                self.__total_energy_balance += single_measurement.total_energy_balance

        return self  # important

    def calculate_mean(self):
        if self.__energy_balance_components["sw_radiation_in"] is not None:
            self.__energy_balance_components["sw_radiation_in"] /= self.contains_sw_in

        if self.__energy_balance_components["sw_radiation_out"] is not None:
            self.__energy_balance_components["sw_radiation_out"] /= self.contains_sw_out

        if self.__energy_balance_components["lw_radiation_in"] is not None:
            self.__energy_balance_components["lw_radiation_in"] /= self.contains_lw_in

        if self.__energy_balance_components["lw_radiation_out"] is not None:
            self.__energy_balance_components["lw_radiation_out"] /= self.contains_lw_out

        if self.__energy_balance_components["sensible_heat"] is not None:
            self.__energy_balance_components["sensible_heat"] /= self.contains_sensible_heat

        if self.__energy_balance_components["latent_heat"] is not None:
            self.__energy_balance_components["latent_heat"] /= self.contains_latent_heat

        if self.__energy_balance_components["precipitation_heat"] is not None:
            self.__energy_balance_components["precipitation_heat"] /= self.contains_precipitation_heat

        if self.__total_energy_balance is not None:
            self.__total_energy_balance /= self.contains_total_energy_balance

    @property
    def datetime_begin(self):
        return self.__datetime_begin

    @property
    def sw_radiation_in(self):
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
    def total_energy_balance(self):
        return self.__total_energy_balance