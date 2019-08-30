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

    def plot_total_energy_balance(self, use_summed_measurements=False):
        self.initialize_plot()

        x_vals = multiple_measurements.singleton.get_all_of("total_energy_balance",
                                                            use_summed_measurements=use_summed_measurements)
        if use_summed_measurements:
            y_dates = multiple_measurements.singleton.get_all_of("datetime_begin",
                                                                 use_summed_measurements=use_summed_measurements)
        else:
            y_dates = multiple_measurements.singleton.get_all_of("datetime")

        self.ax.plot(y_dates, x_vals)

        self.modify_axes()
        self.save_and_close_plot()

    def plot_periodic_trend_eliminated(self, options, use_summed_measurements=False):

        x_vals, y_dates = self.get_vals_and_dates_of_selected_options(options, use_summed_measurements)

        self.initialize_plot()

        one_year = dt.timedelta(days=365, hours=5, minutes=48)  # 365.2422 days in year approximately

        if y_dates[-1] - y_dates[0] < one_year:
            print("Cant trend eliminate for data range less than one year")
            return

        with_mean = True

        # find first actual date where there are values
        reference_index = 0
        for i in range(len(x_vals)):
            if x_vals[i] is not None:
                reference_index = i
                break

        reference_index_date = reference_index
        reference_index_value = reference_index

        if not with_mean:
            diff_vals = list()
            diff_dates = list()
            for i, x_val in enumerate(x_vals[reference_index:]):
                if None not in [x_vals[i], y_dates[i]]:
                    if y_dates[i] >= y_dates[reference_index_date] + one_year:
                        diff_vals.append(x_vals[i] - x_vals[reference_index_value])
                        diff_dates.append(y_dates[i])

                        reference_index_value += 1
                        reference_index_date += 1

        else:
            mean_vals = list()
            first_year_dates = list()
            current_first_year_index = 0

            for i, x_val in enumerate(x_vals[reference_index:]):
                if None not in [x_val, y_dates[i]]:
                    if y_dates[i] < y_dates[reference_index_date] + one_year:
                        mean_vals.append([x_vals])
                        first_year_dates.append(y_dates[i])
                    else:
                        reference_index = i-1
                        break

            new_years = 1
            first_year_dates_generator = iter(first_year_dates)
            current_date = next(first_year_dates_generator)

            for i, x_val in enumerate(x_vals[reference_index:]):  # the next year
                if None not in [x_val, y_dates[i]]:

                    while current_date + new_years*one_year <= y_dates[i]:
                        print(current_date)
                        try:
                            current_date = next(first_year_dates_generator)
                        except StopIteration:
                            first_year_dates_generator = iter(first_year_dates)  # reset iterator
                            current_date = next(first_year_dates_generator)
                            new_years += 1

                        current_first_year_index += 1
                    else:
                        mean_vals[current_first_year_index].append(x_val)

            print("bla")

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.plot(diff_dates, diff_vals)

        self.modify_axes()

        title_used_options = ", ".join([self.title_dict[value_name] for value_name in options])
        self.ax.set_title(title_used_options + " - Periodic trend eliminated")
        self.save_and_close_plot()

    @staticmethod
    def save_add(first, second):
        if None not in [first, second]:
            return first + second
        return None

    def get_vals_and_dates_of_selected_options(self, options, use_summed_measurements=False):
        if use_summed_measurements:
            x_vals = [0] * multiple_measurements.singleton.get_measurement_amount(of="summed")
        else:
            x_vals = [0] * multiple_measurements.singleton.get_measurement_amount()

        for option in options:
            x_vals = list(map(
                self.save_add, x_vals,
                multiple_measurements.singleton.get_all_of(option,
                                                           use_summed_measurements=use_summed_measurements)))

        if use_summed_measurements:
            y_dates = multiple_measurements.singleton.get_all_of("datetime_begin",
                                                                 use_summed_measurements=use_summed_measurements)
        else:
            y_dates = multiple_measurements.singleton.get_all_of("datetime")

        return x_vals, y_dates

    def plot_energy_balance_components(self,
                                       options, use_summed_measurements=False
                                       ):
        """
        For better readability all arguments are declared here as False
        """
        x_vals, y_dates = self.get_vals_and_dates_of_selected_options(options, use_summed_measurements)

        self.initialize_plot()
        self.ax.plot(y_dates, x_vals,
                     zorder=3)
        # TODO maybe add that as a checkbox option
        # self.ax.plot(multiple_measurements.singleton.get_all_of("datetime"),
        #              multiple_measurements.singleton.get_all_of("total_energy_balance"), color="orange", alpha=0.3,
        #              zorder=2)

        self.modify_axes()
        self.save_and_close_plot()


singleton = Visualize()
