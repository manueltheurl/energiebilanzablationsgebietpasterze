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
from operator import sub
import datetime as dt
# from matplotlib import rc
# rc('text', usetex=True)
import multiple_measurements
import scipy
import numpy as np
from scipy import optimize


class Visualize:
    singleton_created = False

    def __init__(self):
        if Visualize.singleton_created:
            raise Exception("Reader is a singleton")
        Visualize.singleton_created = True

        if not os.path.exists(cfg["RESULT_PLOT_PATH"]):
            os.makedirs(cfg["RESULT_PLOT_PATH"])

        self.title_dict = {
            "sw_radiation_in": "Short wave in",
            "sw_radiation_out": "Short wave out",
            "lw_radiation_in": "Long wave in",
            "lw_radiation_out": "Long wave out",
            "sensible_heat": "Sensible heat",
            "latent_heat": "Latent heat",
            "precipitation_heat": "Precipitation heat",
            "total_energy_balance": "Total energy balance",
        }

        self.ax = None

    def initialize_plot(self):
        """

        :rtype: object
        """
        fig = plt.figure(figsize=(10, 6))
        self.ax = fig.add_subplot(111)

    def modify_axes(self):
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..

        # calculate time_spawn between first and last measurement
        time_spawn = dt.timedelta(days=self.ax.get_xlim()[1] - self.ax.get_xlim()[0])

        self.ax.xaxis.set_major_locator(years)
        self.ax.xaxis.set_major_formatter(year_labels)

        if dt.timedelta(days=365) > time_spawn:
            self.ax.xaxis.set_minor_locator(months)

            if dt.timedelta(days=3*365) > time_spawn:
                self.ax.xaxis.set_minor_formatter(month_labels)

                self.ax.xaxis.set_tick_params(rotation=45)  # only major are rotated

        self.ax.set_xlabel("Year")
        self.ax.grid(linestyle="--", alpha=0.5, which='major')
        self.ax.grid(linestyle="--", alpha=0.4, which='minor')

        self.ax.set_ylabel("W/m^2")

    @staticmethod
    def save_and_close_plot():
        plt.show()
        plt.close()
        # plt.savefig(cfg["RESULT_PLOT_PATH"] + "/with.png", dpi=cfg["PLOT_RESOLUTION"], bbox_inches='tight')

    def plot_total_energy_balance(self):
        self.initialize_plot()

        self.ax.plot(multiple_measurements.singleton.get_all_of("datetime"),
                     multiple_measurements.singleton.get_all_of("total_energy_balance"))

        # trying to trendeliminate here
        X = multiple_measurements.singleton.get_all_of("total_energy_balance")
        diff = list()
        days_in_year = 365
        for i in range(days_in_year, len(X)):
            if not None in [X[i], X[i - days_in_year]]:
                value = X[i] - X[i - days_in_year]
                diff.append(value)
            else:
                diff.append(None)

        self.ax.plot(multiple_measurements.singleton.get_all_of("datetime")[days_in_year:],
                     diff)

        self.modify_axes()
        self.save_and_close_plot()

    def plot_summed_total_energy_balance(self):
        self.initialize_plot()

        self.ax.plot(multiple_measurements.singleton.mean_get_all_of("datetime_begin"),
                     multiple_measurements.singleton.mean_get_all_of("total_energy_balance"))

        self.modify_axes()
        self.save_and_close_plot()

    def plot_periodic_trend_eliminated(self, value_name):
        self.initialize_plot()

        # self.ax.plot(multiple_measurements.singleton.summed_get_all_of("datetime_begin"),
        #              multiple_measurements.singleton.summed_get_all_of("total_energy_balance"))

        # trying to trendeliminate here

        one_year = dt.timedelta(days=365, hours=5, minutes=48)  # 365.2422 days in year approximately

        values = multiple_measurements.singleton.mean_get_all_of(value_name)
        dates = multiple_measurements.singleton.mean_get_all_of("datetime_begin")

        reference_index = 0
        for i in range(len(values)):
            if values[i] is not None:
                reference_index = i
                break

        reference_index_date = reference_index
        reference_index_value = reference_index

        diff_vals = list()
        diff_dates = list()
        diff_dates_indexes = list()

        for i in range(len(values)):
            if None not in [values[i], dates[i]]:
                if dates[i] >= dates[reference_index_date] + one_year:
                    diff_vals.append(values[i] - values[reference_index_value])
                    diff_dates.append(dates[i])
                    diff_dates_indexes.append(i)

                    # print(dates[reference_index_date], dates[i])  approve that they are one year apart

                    reference_index_value += 1
                    reference_index_date += 1

        z = np.polyfit(range(len(diff_dates)), diff_vals,  1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.plot(diff_dates, diff_vals)

        self.modify_axes()
        self.ax.set_title(self.title_dict[value_name] + " - Periodic trend eliminated")
        self.save_and_close_plot()

    @staticmethod
    def save_add(first, second):
        if None not in [first, second]:
            return first + second
        return None

    def plot_energy_balance_components(self,
                                       sw_radiation_in=False, sw_radiation_out=False, lw_radiation_in=False,
                                       lw_radiation_out=False, sensible_heat=False, latent_heat=False,
                                       precipitation_heat=False, ablation=False
                                       ):
        """
        For better readability all arguments are declared here as False
        """

        energy_balance_of_selected_parts = [0] * multiple_measurements.singleton.get_measurement_amount()

        for component_bool, component_name in zip(
                [sw_radiation_in, sw_radiation_out, lw_radiation_in, lw_radiation_out, sensible_heat, latent_heat,
                 precipitation_heat, ablation
                 ],
                ["sw_radiation_in", "sw_radiation_out", "lw_radiation_in", "lw_radiation_out", "sensible_heat",
                 "latent_heat", "precipitation_heat", "ablation"
                 ]):

            if component_bool:
                energy_balance_of_selected_parts = list(map(
                    self.save_add, energy_balance_of_selected_parts,
                    multiple_measurements.singleton.get_all_of(component_name))
                )

        self.initialize_plot()

        self.ax.plot(multiple_measurements.singleton.get_all_of("datetime"), energy_balance_of_selected_parts,
                     zorder=3)
        self.ax.plot(multiple_measurements.singleton.get_all_of("datetime"),
                     multiple_measurements.singleton.get_all_of("total_energy_balance"), color="orange", alpha=0.3,
                     zorder=2)

        self.modify_axes()
        self.save_and_close_plot()


singleton = Visualize()
