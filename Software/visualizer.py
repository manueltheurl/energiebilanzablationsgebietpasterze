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
import functions as fc
import calendar

DAYS_365 = dt.timedelta(days=365)  # hours=5, minutes=48     365.2422 days in year approximately  dont change to that


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

        self.accumulate_plots = False
        self.show_plots = False

        self.ax = None

    plot_type_initialized = {
        "energy_balance": False,
        "trend": False,
        "temperature": False
    }

    def initialize_plot(self, type_):
        """
        :rtype: object
        """

        yet_to_initialize = True

        if type_ is not None:
            if self.accumulate_plots:
                # close other plot types that are open
                for plot_type in self.plot_type_initialized:
                    if type_ != plot_type:
                        if self.plot_type_initialized[plot_type]:
                            self.plot_type_initialized[plot_type] = False
                            plt.close()
                            break

                if self.plot_type_initialized[type_]:
                    yet_to_initialize = False
                else:
                    self.plot_type_initialized[type_] = True
            else:
                plt.close()  # should one be open

        if yet_to_initialize or not bool(cfg["PRO_VERSION"]):
            fig = plt.figure(figsize=(14, 9))
            self.ax = fig.add_subplot(111)

    def modify_axes(self):
        years = mdates.YearLocator()
        months = mdates.MonthLocator()
        year_labels = mdates.DateFormatter('%Y')
        month_labels = mdates.DateFormatter('%b')  # Jan, Feb, ..
        # mondays = mdates.WeekdayLocator(mdates.MONDAY)

        # calculate time_spawn between first and last measurement
        time_spawn = dt.timedelta(days=self.ax.get_xlim()[1] - self.ax.get_xlim()[0])

        time_border_1 = dt.timedelta(days=3*365)
        time_border_2 = dt.timedelta(days=150)
        # time_border_3 = dt.timedelta(days=30*2)

        # major and ax title
        if time_spawn >= time_border_1:
            self.ax.set_xlabel("Year")
            self.ax.xaxis.set_major_locator(years)
            self.ax.xaxis.set_major_formatter(year_labels)
        elif time_border_2 <= time_spawn <= time_border_1:
            self.ax.xaxis.set_major_locator(years)
            self.ax.xaxis.set_major_formatter(year_labels)
            self.ax.set_xlabel("Year")
            self.ax.xaxis.set_tick_params(rotation=45)  # only major are rotated
            self.ax.xaxis.set_minor_formatter(month_labels)
            self.ax.xaxis.set_minor_locator(months)

        # elif time_border_3 <= time_spawn <= time_border_2:
        #     self.ax.xaxis.set_major_locator(months)
        #     self.ax.xaxis.set_major_formatter(month_labels)
        #     self.ax.set_xlabel("Month")
        #     self.ax.xaxis.set_minor_locator(months)
        #     self.ax.xaxis.set_minor_formatter(month_labels)

        # ELSE just take default tick and ticklabels

        self.ax.grid(linestyle="--", alpha=0.5, which='major')
        self.ax.grid(linestyle="--", alpha=0.4, which='minor')

    def show_save_and_close_plot(self, type_, save_name=None):
        if self.show_plots or cfg["GUI"]:
            plt.tight_layout()
            plt.show()

        if save_name is not None:
            plt.savefig(cfg["RESULT_PLOT_PATH"] + "/" + save_name + ".png", dpi=cfg["PLOT_RESOLUTION"],
                        bbox_inches='tight')

        if not self.accumulate_plots or not bool(cfg["PRO_VERSION"]):
            plt.close()
            dict.fromkeys(self.plot_type_initialized, False)

    def plot_total_energy_balance(self, use_summed_measurements=False, ablation_or_water_equivalent=False,
                                  save_name=None):
        self.initialize_plot("energy_balance")

        x_vals = multiple_measurements.singleton.get_all_of("total_energy_balance",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label="Energy Balance")

        if ablation_or_water_equivalent is not False:  # is false if None of the both
            second_ax = self.ax.twinx()

            if ablation_or_water_equivalent == "show_ablation":
                second_ax_vals = multiple_measurements.singleton.get_all_of(
                    "cumulated_ablation", use_summed_measurements=use_summed_measurements)

                second_ax.plot(y_dates, second_ax_vals, label="Ablation", color="red")
                second_ax.set_ylabel("m")
                main_title = "Total Energy balance with Ablation"

            elif ablation_or_water_equivalent == "show_water_equivalent":
                if use_summed_measurements:  # has to be summed here for now
                    actual_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                        "actual_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

                    theoretical_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                        "theoretical_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

                    second_ax.plot(y_dates, actual_melt_water_per_sqm, color="red", label="Measured Meltwater")
                    second_ax.plot(
                        y_dates, theoretical_melt_water_per_sqm, color="green", label="Modelled Meltwater")

                    # calculate correlation coefficient
                    if save_name is not None:
                        none_indexes = []
                        for i, values in enumerate(zip(actual_melt_water_per_sqm, theoretical_melt_water_per_sqm)):
                            if None in values:
                                none_indexes.append(i)

                        actual_melt_water_per_sqm = np.delete(actual_melt_water_per_sqm, none_indexes)
                        theoretical_melt_water_per_sqm = np.delete(theoretical_melt_water_per_sqm, none_indexes)

                        print(save_name, "correlation coefficient:",
                              round(float(np.ma.corrcoef(actual_melt_water_per_sqm, theoretical_melt_water_per_sqm)[0][1]), 2))

                second_ax.set_ylabel("l/m^2 per " + multiple_measurements.singleton.get_time_resolution(of="summed",
                                                                                                    as_beautiful_string=True))
                main_title = "Total Energy balance with actual and theoretical Ablation as water equivalent"

            else:
                return  # shouldnt get there

            self.ax.legend(loc="upper left")
            second_ax.legend(loc="upper right")
        else:
            main_title = "Total Energy balance"
            self.ax.legend()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"
        # self.ax.set_title(main_title + summed_title_appendix)
        self.ax.set_ylabel("W/m^2") 
        self.modify_axes()
        
        self.show_save_and_close_plot("energy_balance", save_name=save_name)

    def plot_single_component(self, component, component_unit, use_summed_measurements=False, save_name=None):
        self.initialize_plot(None)

        x_vals = multiple_measurements.singleton.get_all_of(component,
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label=component)

        self.ax.legend(loc="upper left")

        self.ax.set_ylabel(component_unit)
        self.modify_axes()

        self.show_save_and_close_plot(None, save_name=save_name)

    def plot_temperature_and_water_equivalent(self, use_summed_measurements=False, save_name=None):

        self.initialize_plot("temperature")

        x_vals = multiple_measurements.singleton.get_all_of("snow_depth",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        self.ax.plot(y_dates, x_vals, label="Temperature")

        second_ax = self.ax.twinx()

        if use_summed_measurements:  # has to be summed here for now
            actual_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                "actual_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

            theoretical_melt_water_per_sqm = multiple_measurements.singleton.get_all_of(
                "theoretical_melt_water_per_sqm", use_summed_measurements=use_summed_measurements)

            second_ax.plot(y_dates, actual_melt_water_per_sqm, color="red", label="Measured Meltwater")
            second_ax.plot(
                y_dates, theoretical_melt_water_per_sqm, color="green", label="Modelled Meltwater")

        second_ax.set_ylabel("l/m^2 per " + multiple_measurements.singleton.get_time_resolution(of="summed",
                                                                                            as_beautiful_string=True))
        self.ax.legend(loc="upper left")
        second_ax.legend(loc="upper right")      

        self.modify_axes()
        self.ax.set_ylabel("Temperature °C")
        self.show_save_and_close_plot("temperature", save_name=save_name)

    def plot_energy_balance_components(self,
                                       options, use_summed_measurements=False, save_name=None):
        x_vals, y_dates = self.get_vals_and_dates_of_selected_options(options, use_summed_measurements)

        self.initialize_plot("energy_balance")
        title_used_options = ", ".join([self.title_dict[value_name] for value_name in options])

        self.ax.plot(y_dates, x_vals,
                     zorder=3, label=title_used_options, linewidth=2)

        self.ax.legend()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        # self.ax.set_title(title_used_options + " - Energy input" + summed_title_appendix)
        self.ax.set_ylabel("W/m^2") 
        self.modify_axes()
        self.show_save_and_close_plot("energy_balance", save_name=save_name)

    @staticmethod
    def do_periodic_trend_elimination(x_vals, y_dates, keep_trend):
        # find first actual date where there are values
        reference_index_first_good_measurement = 0
        for i in range(len(x_vals)):
            if x_vals[i] is not None:
                reference_index_first_good_measurement = i
                break

        reference_index_current_measurement = reference_index_first_good_measurement

        if not keep_trend:  # periodic and trend is eliminated by taking always previous year
            diff_vals = list()
            diff_dates = list()
            for x_val, y_date in zip(x_vals[reference_index_first_good_measurement:],
                                     y_dates[reference_index_first_good_measurement:]):
                if None not in [x_val, y_date]:
                    if y_date >= y_dates[reference_index_current_measurement] + DAYS_365:
                        diff_vals.append(x_val - x_vals[reference_index_current_measurement])
                        diff_dates.append(y_date)

                        reference_index_current_measurement += 1

        else:  # trend is not eliminated by taking always the first year as reference
            diff_vals = list()
            diff_dates = list()
            start_date = y_dates[reference_index_first_good_measurement]
            leap_days = dt.timedelta(days=0)

            for x_val, y_date in zip(x_vals[reference_index_first_good_measurement:],
                                     y_dates[reference_index_first_good_measurement:]):
                if None not in [x_val, y_date]:
                    years_passed = int((y_date - start_date).total_seconds() / DAYS_365.total_seconds())
                    if fc.value_changed(years_passed, "years_passed"):
                        if calendar.isleap(y_date.year) and y_date.month <= 2 and y_date.day < 29:
                            leap_days += dt.timedelta(days=1)
                        reference_index_current_measurement = reference_index_first_good_measurement

                    if years_passed >= 1:
                        if y_date >= y_dates[reference_index_current_measurement] + DAYS_365 * years_passed + leap_days:
                            if x_vals[reference_index_current_measurement] is not None:  # can happen .. take it
                                diff_vals.append(x_val - x_vals[reference_index_current_measurement])
                                diff_dates.append(y_date)

                            reference_index_current_measurement += 1
        return diff_vals, diff_dates

    def plot_periodic_trend_eliminated_total_energy_balance(self, use_summed_measurements=False, keep_trend=True,
                                                            save_name=None):
        x_vals = multiple_measurements.singleton.get_all_of("total_energy_balance",
                                                            use_summed_measurements=use_summed_measurements)

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)
        self.initialize_plot("trend")

        if y_dates[-1] - y_dates[0] < DAYS_365:
            print("Cant trend eliminate for data range less than one year")
            return

        diff_vals, diff_dates = self.do_periodic_trend_elimination(x_vals, y_dates, keep_trend)

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, diff_vals)
        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.set_ylabel("W/m^2") 
        self.modify_axes()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        # self.ax.set_title("Total energy balance - Periodic trend eliminated" + summed_title_appendix)
        self.show_save_and_close_plot("trend", save_name=save_name)

    def plot_periodic_trend_eliminated_selected_option(self, options, use_summed_measurements=False, keep_trend=True,
                                                       save_name=None):
        x_vals, y_dates = self.get_vals_and_dates_of_selected_options(options, use_summed_measurements)
        self.initialize_plot("trend")

        days_365 = dt.timedelta(days=365)  # 365.2422 days in year approximately

        if y_dates[-1] - y_dates[0] < days_365:
            print("Cant trend eliminate for data range less than one year")
            return

        diff_vals, diff_dates = self.do_periodic_trend_elimination(x_vals, y_dates, keep_trend)

        z = np.polyfit(range(len(diff_dates)), diff_vals, 1)
        p = np.poly1d(z)

        self.ax.plot(diff_dates, diff_vals)
        self.ax.plot(diff_dates, p(range(len(diff_dates))), "r--")

        self.ax.set_ylabel("W/m^2") 
        self.modify_axes()

        summed_title_appendix = "" if not use_summed_measurements else "\n Used summed measurements"

        title_used_options = ", ".join([self.title_dict[value_name] for value_name in options])
        # self.ax.set_title(title_used_options + " - Periodic trend eliminated" + summed_title_appendix)
        self.show_save_and_close_plot("trend", save_name=save_name)

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

        y_dates = multiple_measurements.singleton.get_all_of("datetime",
                                                             use_summed_measurements=use_summed_measurements)

        return x_vals, y_dates


singleton = Visualize()
