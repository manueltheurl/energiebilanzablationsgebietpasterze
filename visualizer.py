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


class Visualize:
    def __init__(self, meteorologic_measurements):

        self.__meteorologic_measurements = meteorologic_measurements

        if not os.path.exists(cfg["RESULT_PLOT_PATH"]):
            os.makedirs(cfg["RESULT_PLOT_PATH"])

    def testing(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        ax.plot(self.__meteorologic_measurements.get_all_of("datetime"), self.__meteorologic_measurements.get_all_of("energy_balance"))
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..

        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_minor_locator(months)
        ax.xaxis.set_major_formatter(year_labels)
        ax.xaxis.set_minor_formatter(month_labels)

        ax.xaxis.set_tick_params(rotation=45)  # only major are rotated

        ax.set_xlabel("Year")
        ax.grid(linestyle="--", alpha=0.5, which='major')
        ax.grid(linestyle="--", alpha=0.2, which='minor')

        plt.show()
        # plt.savefig(cfg["RESULT_PLOT_PATH"] + "/with.png", dpi=cfg["PLOT_RESOLUTION"], bbox_inches='tight')

