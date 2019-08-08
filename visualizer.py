import os
import matplotlib.pyplot as plt
from manage_config import cfg
import matplotlib.dates
import matplotlib.cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from matplotlib.markers import MarkerStyle
import os
from matplotlib import patches
from operator import add


class Visualize:
    def __init__(self, meteorologic_measurements):

        self.__meteorologic_measurements = meteorologic_measurements

        if not os.path.exists(cfg["RESULT_PLOT_PATH"]):
            os.makedirs(cfg["RESULT_PLOT_PATH"])

        self.ax = None

    def initialize_plot(self):
        fig = plt.figure()
        self.ax = fig.add_subplot(111)

    def modify_axes(self):
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..

        self.ax.xaxis.set_major_locator(years)
        self.ax.xaxis.set_minor_locator(months)
        self.ax.xaxis.set_major_formatter(year_labels)
        self.ax.xaxis.set_minor_formatter(month_labels)

        self.ax.xaxis.set_tick_params(rotation=45)  # only major are rotated

        self.ax.set_xlabel("Year")
        self.ax.grid(linestyle="--", alpha=0.5, which='major')
        self.ax.grid(linestyle="--", alpha=0.2, which='minor')

    @staticmethod
    def save_and_close_plot():
        plt.show()
        plt.close()
        # plt.savefig(cfg["RESULT_PLOT_PATH"] + "/with.png", dpi=cfg["PLOT_RESOLUTION"], bbox_inches='tight')

    def plot_total_energy_balance(self):
        self.initialize_plot()

        self.ax.plot(self.__meteorologic_measurements.get_all_of("datetime"),
                     self.__meteorologic_measurements.get_all_of("total_energy_balance"))

        self.modify_axes()
        self.save_and_close_plot()

    @staticmethod
    def save_add(first, second):
        if None not in [first, second]:
            return first + second
        return 0

    def save_add_lists(self, first, second):
        return list(map(self.save_add, first, second))

    def plot_energy_balance_components(self,
                                       sw_radiation_in=False, sw_radiation_out=False, lw_radiation_in=False,
                                       lw_radiation_out=False, sensible_heat=False, latent_heat=False,
                                       precipitation_heat=False,
                                       ):
        """
        For better readability all arguments are declared here as False
        """

        energy_balance_of_selected_parts = [0] * self.__meteorologic_measurements.get_measurement_amount()

        for component_bool, component_name in zip(
                [sw_radiation_in, sw_radiation_out, lw_radiation_in, lw_radiation_out, sensible_heat, latent_heat,
                 precipitation_heat
                 ],
                ["sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "sensible_heat",
                 "latent_heat", "precipitation_heat"
                 ]):

            if component_bool:
                energy_balance_of_selected_parts = self.save_add_lists(
                    energy_balance_of_selected_parts,
                    self.__meteorologic_measurements.get_all_of(component_name)
                )

        self.initialize_plot()

        self.ax.plot(self.__meteorologic_measurements.get_all_of("datetime"), energy_balance_of_selected_parts)

        self.modify_axes()
        self.save_and_close_plot()
